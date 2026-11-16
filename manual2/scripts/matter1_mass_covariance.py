"""AME2020 covariance adoption, separate from retained mass-excess reductions."""
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import zipfile

INPUTS = Path('manual2/data/m1/properties/covariance_inputs.json')
INPUTS_SHA256 = '2431db81fe58f3973efa0658b19abb9c118c1880d36a21202a525db9ffaaee7c'
HEADER = 'Variances and Covariances in nano-amu**2'
SCHEMA = 'matter1.mass-covariance-adoption.v1'


def require(condition, message):
    if not condition:
        raise ValueError('Mass covariance: ' + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _read_inputs(root):
    raw = (Path(root) / INPUTS).read_bytes()
    require(sha(raw) == INPUTS_SHA256, 'adoption manifest changed')
    inputs = json.loads(raw)
    require(inputs['schema'] == 'matter1.mass-covariance-inputs.v1'
            and inputs['edition'] == 'AME2020', 'source edition differs')
    return inputs


def input_paths(root):
    inputs = _read_inputs(root)
    return [str(INPUTS)] + [s['path'] for s in inputs['sources']]


def validate_matrix(matrix, order):
    """Check a complete published matrix exactly; never clip or repair it."""
    require(len(order) == len(set(order)) and bool(order), 'distinct nonempty nuclide order required')
    require(len(matrix) == len(order) and all(len(r) == len(order) for r in matrix),
            'incomplete covariance matrix')
    a = [[Fraction(x) for x in r] for r in matrix]
    require(all(a[i][j] == a[j][i] for i in range(len(a)) for j in range(len(a))),
            'asymmetric covariance')
    work = [r[:] for r in a]
    rank = 0
    for k in range(len(a)):
        pivot = work[k][k]
        require(pivot >= 0, 'covariance is not positive semidefinite')
        if pivot == 0:
            require(all(work[k][j] == 0 for j in range(k + 1, len(a))),
                    'zero covariance pivot has a nonzero residual row')
            continue
        rank += 1
        for i in range(k + 1, len(a)):
            for j in range(i, len(a)):
                work[j][i] = work[i][j] = work[i][j] - work[i][k] * work[j][k] / pivot
    return a, rank


def parse_matrix(raw, order):
    """Read the archive's declared triangular format and retain exact locators."""
    lines = raw.decode('ascii').splitlines()
    require(lines and lines[0] == HEADER, 'unknown covariance scale or unit')
    require('nuclides coded as AAAZZZi i=isomeric state' in lines[1],
            'unknown nuclide/state coding')
    require(len(order) == len(set(order)) and all(type(x) is int and x > 0 for x in order),
            'invalid nuclide order')
    selected, codes = {}, set(order)
    for number, line in enumerate(lines[5:], 6):
        if not line.strip():
            continue
        fields = line.split()
        require(len(fields) == 3 and fields[0].isdigit() and fields[1].isdigit(),
                'malformed covariance row')
        left, right = map(int, fields[:2])
        if left not in codes or right not in codes:
            continue
        key = tuple(sorted((left, right)))
        require(key not in selected, 'duplicate or mirrored covariance entry')
        number_value = Decimal(fields[2])
        require(number_value.is_finite(), 'nonfinite covariance entry')
        selected[key] = {'line': number, 'row': left, 'column': right,
                         'token': fields[2], 'value': str(Fraction(number_value))}
    missing = [(a, b) for i, a in enumerate(order) for b in order[:i + 1]
               if tuple(sorted((a, b))) not in selected]
    require(not missing, 'missing covariance entries: ' + str(missing))
    matrix = [[selected[tuple(sorted((a, b)))]['value'] for b in order] for a in order]
    _, rank = validate_matrix(matrix, order)
    return {'order': order, 'unit': '(nano-u)^2', 'matrix': matrix,
            'entries': list(selected.values()), 'exact_psd_rank': rank,
            'rounding': 'Published decimal coefficients retained exactly; no PSD correction.'}


def diagonal_compatible(variance, magnitude, quantum):
    """Explicit nearest-rounding compatibility test; not a diagonal replacement."""
    v, s, q = map(Fraction, (variance, magnitude, quantum))
    require(v >= 0 and s >= 0 and q > 0, 'invalid variance or quoted magnitude')
    return max(Fraction(), s - q / 2) ** 2 <= v <= (s + q / 2) ** 2


def _sqrt_display(value):
    with localcontext() as context:
        context.prec = 70
        context.rounding = ROUND_HALF_EVEN
        q = Fraction(value)
        root = (Decimal(q.numerator) / Decimal(q.denominator)).sqrt()
        return format(root, '.10g')


def _expression(order, coefficients):
    parameters = {'c' + str(i): {'value': str(c)} for i, c in enumerate(coefficients)}
    terms = [['mul', ['parameter', 'c' + str(i)], ['input', name]]
             for i, name in enumerate(order)]
    result = terms[0]
    for term in terms[1:]:
        result = ['add', result, term]
    return result, parameters


def build(root, baseline_report, mapping):
    root = Path(root)
    inputs = _read_inputs(root)
    sources = {}
    for source in inputs['sources']:
        data = (root / source['path']).read_bytes()
        require(sha(data) == source['sha256'], 'source bytes changed: ' + source['id'])
        sources[source['id']] = (source, data)
    archive, data = sources['ame2020-covariance']
    with zipfile.ZipFile(io.BytesIO(data)) as zipped:
        require(zipped.namelist() == [archive['member']], 'unexpected archive members')
        raw = zipped.read(archive['member'])
    require(sha(raw) == archive['member_sha256'], 'covariance member changed')
    mass_source, mass_raw = sources['ame2020-atomic-masses']
    require(baseline_report['source']['sha256'] == mass_source['sha256'],
            'baseline and covariance mean source differ')
    candidates = [r for r in baseline_report['rows']
                  if r['property'] != 'binding_energy' and r['value'] is not None]
    quantities = baseline_report['source_quantities']
    mass_lines = mass_raw.decode('ascii').splitlines()
    code_for = {}
    for row in candidates:
        require(row['unit'] == 'keV' and row['coefficients'], 'invalid baseline reduction')
        for term in row['coefficients']:
            q = quantities[term['source_quantity_id']]
            require(q['quantity'] == 'mass_excess' and q['state'] == 'ground'
                    and q['source_sha256'] == mass_source['sha256'], 'incompatible source quantity')
            expected = f"ame2020:{mass_source['sha256']}:mass_excess:Z{q['z']}:A{q['a']}:ground"
            require(term['source_quantity_id'] == expected and q['id'] == expected, 'source quantity alias')
            source_line = mass_lines[q['locator']['line'] - 1]
            require(q['raw_row'] == source_line
                    and (int(source_line[9:14]), int(source_line[14:19])) == (q['z'], q['a'])
                    and Fraction(source_line[28:42].strip()) == Fraction(q['value']),
                    'source quantity locator or value differs')
            code_for[term['source_quantity_id']] = q['a'] * 10000 + q['z'] * 10
    order = sorted(set(code_for.values()))
    block = parse_matrix(raw, order)
    mass_rows = {}
    for number, line in enumerate(mass_raw.decode('ascii').splitlines(), 1):
        try:
            z, a = int(line[9:14]), int(line[14:19])
        except ValueError:
            continue
        code = a * 10000 + z * 10
        if code not in order:
            continue
        require('#' not in line[106:135] and '*' not in line[106:135],
                'estimated or unavailable atomic mass is not adopted')
        mass = Fraction(line[106:109].strip()) + Fraction(line[110:123].strip()) / 1000000
        magnitude_token = line[123:135].strip()
        d = Decimal(magnitude_token)
        magnitude = Fraction(d) * 1000
        quantum = Fraction(10) ** d.as_tuple().exponent * 1000
        index = order.index(code)
        variance = block['matrix'][index][index]
        mass_rows[code] = {'code': code, 'z': z, 'a': a, 'state': 'ground',
                          'source_id': mass_source['id'], 'source_sha256': mass_source['sha256'],
                          'line': number, 'raw_row': line, 'mean_nano_u': str(mass * 10**9),
                          'quoted_sigma_nano_u': str(magnitude),
                          'sigma_last_place_nano_u': str(quantum),
                          'covariance_variance_nano_u2': variance,
                          'diagonal_compatible': diagonal_compatible(variance, magnitude, quantum),
                          'mean_status': 'Retained printed atomic mass used as an estimated mean; source precision retained.'}
    require(set(mass_rows) == set(order), 'missing atomic mass mean')
    precise = inputs['precise_atomic_masses']
    require(precise['unit'] == 'micro-u', 'precise atomic mass unit differs')
    precise_source = sources[precise['source_id']][0]
    seen = set()
    for entry in precise['rows']:
        code = entry['code']
        require(code in mass_rows and code not in seen, 'precise mass identity duplicate or absent')
        seen.add(code)
        q = mass_rows[code]
        electronic = dict(q)
        sigma = Decimal(entry['sigma'])
        magnitude = Fraction(sigma) * 1000
        quantum = Fraction(10) ** sigma.as_tuple().exponent * 1000
        q.update(source_id=precise_source['id'], source_sha256=precise_source['sha256'],
                 locator=precise['locator'] + '; ' + entry['row_label'],
                 mean_nano_u=str(Fraction(entry['mean']) * 1000),
                 quoted_sigma_nano_u=str(magnitude), sigma_last_place_nano_u=str(quantum),
                 mean_status='Precise Table A printed atomic mass used as an estimated mean; not exact physical knowledge.',
                 electronic_table_record=electronic,
                 diagonal_compatible=diagonal_compatible(q['covariance_variance_nano_u2'], magnitude, quantum))
        del q['line'], q['raw_row']
    row_coefficients, adopted, held = [], [], []
    for row in candidates:
        c = [sum(t['coefficient'] for t in row['coefficients']
                 if code_for[t['source_quantity_id']] == code) for code in order]
        requested = {q['a'] * 10000 + q['z'] * 10: 0 for q in row['requested_inputs']}
        for q in row['requested_inputs']:
            require(q['state'] == 'ground' and q['quantity'] == 'mass_excess', 'requested mass identity changed')
            requested[q['a'] * 10000 + q['z'] * 10] += q['coefficient']
        require(c == [requested.get(code, 0) for code in order], 'source coefficients differ from requested inputs')
        nominal = sum(Fraction(t['coefficient']) * Fraction(quantities[t['source_quantity_id']]['value'])
                      for t in row['coefficients'])
        require(nominal == Fraction(row['value']), 'baseline source expression differs from retained value')
        require(sum(k * mass_rows[code]['a'] for k, code in zip(c, order)) == 0,
                'atomic mass-number offsets do not cancel')
        incompatible = [code for code, coefficient in zip(order, c)
                        if coefficient and not mass_rows[code]['diagonal_compatible']]
        if incompatible:
            held.append({'record_id': row['id'], 'status': 'held', 'incompatible_codes': incompatible,
                         'reason': 'Covariance diagonal and retained atomic-mass marginal are incompatible under nearest last-place rounding.'})
            continue
        used = [i for i, value in enumerate(c) if value]
        names = [str(order[i]) for i in used]
        covariance = [[block['matrix'][i][j] for j in used] for i in used]
        means = {str(order[i]): mass_rows[order[i]]['mean_nano_u'] for i in used}
        expression, parameters = _expression(names, [c[i] for i in used])
        propagation = mapping.propagate(expression, names, parameters,
                                        means=means, covariance=covariance)
        row_coefficients.append(c)
        adopted.append({'record_id': row['id'], 'coefficients': c,
                        'atomic_mass_reduction': propagation,
                        'unit': 'nano-u', 'variance_unit': '(nano-u)^2',
                        'standard_deviation': {'expression': 'sqrt(' + propagation['output_variance'] + ')',
                                               'display': _sqrt_display(propagation['output_variance']),
                                               'display_rule': '10 significant digits, round half even'},
                        'baseline_mass_excess_value_keV': row['value']})
    covariance = [[sum(Fraction(a[i]) * Fraction(block['matrix'][i][j]) * b[j]
                       for i in range(len(order)) for j in range(len(order)))
                   for b in row_coefficients] for a in row_coefficients]
    for i, row in enumerate(adopted):
        require(covariance[i][i] == Fraction(row['atomic_mass_reduction']['output_variance']),
                'M3 variance differs from independent C Sigma C transpose')
    return {'schema': SCHEMA, 'status': 'partial' if held else 'adopted',
            'reason': 'Complete published covariance applied only to source-compatible atomic-mass reductions.',
            'manifest': {'path': str(INPUTS), 'sha256': INPUTS_SHA256},
            'sources': inputs['sources'], 'method': inputs['method'],
            'coverage': {'required_codes': order, 'entries': len(block['entries']),
                         'candidate_rows': len(candidates), 'adopted_rows': len(adopted), 'held_rows': len(held)},
            'source_matrix': block, 'atomic_mass_inputs': [mass_rows[k] for k in order],
            'adopted': adopted, 'held': held, 'output_order': [r['record_id'] for r in adopted],
            'output_covariance_nano_u2': [[str(v) for v in r] for r in covariance],
            'typed_m3_acceptance': False, 'physical_budget_complete': False,
            'limits': ['Source masses and decimal covariance coefficients remain evaluated estimates.',
                       'No normal distribution, finite support or deterministic measurement bound is inferred.',
                       'No covariance is transferred to separately printed binding-energy-per-nucleon inputs.',
                       'Baseline mass-excess reductions and uncertainty fields remain unchanged.']}
