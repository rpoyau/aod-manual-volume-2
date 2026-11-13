"""Exact pilot mass reductions with explicit, separately qualified uncertainty."""
from collections import defaultdict
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
from pathlib import Path

if __package__:
    from . import matter1_m3_producer as producer
    from . import matter1_mass_covariance as covariance
else:
    import matter1_m3_producer as producer
    import matter1_mass_covariance as covariance

SCHEMA = 'matter1.mass-derivations.v1'
FAMILIES = ('binding_energy', 'neutron_separation_energy',
            'proton_separation_energy', 'alpha_decay_q')
FIELDS = {'mass_excess': (28, 42, 42, 54),
          'binding_energy_per_nucleon': (54, 67, 68, 78)}
SD_PREMISE = 'Each retained quoted magnitude is interpreted as the marginal standard deviation of the named source quantity.'


def require(value, message):
    if not value:
        raise ValueError('Mass derivation: ' + message)


def decimal(value):
    value = Fraction(value)
    with localcontext() as context:
        context.prec = 80
        result = format(Decimal(value.numerator) / Decimal(value.denominator), 'f')
    require(Fraction(result) == value, 'nonterminating decimal requires an explicit rounding rule')
    return result


def coefficients(terms):
    """Combine occurrences of a source identity, never equal-valued sources."""
    result = defaultdict(int)
    for term in terms:
        key, coefficient = term['source_quantity_id'], term['coefficient']
        require(type(key) is str and key, 'source quantity identity is missing')
        require(type(coefficient) is int, 'coefficient must be an exact integer')
        result[key] += coefficient
    return [{'source_quantity_id': key, 'coefficient': value}
            for key, value in sorted(result.items()) if value]


def conditional_sd_range(terms, quantities):
    require(all(t['source_quantity_id'] in quantities for t in terms), 'unknown source quantity')
    require(all(quantities[t['source_quantity_id']]['unit'] == 'keV' for t in terms),
            'incompatible mass quantity unit')
    canonical = coefficients(terms)
    missing = [t['source_quantity_id'] for t in canonical
               if quantities[t['source_quantity_id']]['reported_magnitude'] is None]
    result = {'kind': 'range_of_possible_standard_deviations', 'unit': 'keV',
              'premise': SD_PREMISE, 'premise_status': 'not_adopted',
              'joint_covariance_adopted': False, 'coverage': None,
              'lower': None, 'upper': None, 'missing_magnitudes': missing,
              'status': 'missing_marginal_magnitude' if missing else 'conditional_on_marginal_sd'}
    if not missing:
        widths = []
        for term in canonical:
            quantity = quantities[term['source_quantity_id']]
            magnitude = Fraction(quantity['reported_magnitude'])
            require(magnitude >= 0, 'negative quoted uncertainty magnitude')
            widths.append(abs(term['coefficient']) * magnitude)
        total = sum(widths, Fraction())
        result.update(lower=decimal(max(Fraction(), 2 * max(widths, default=Fraction()) - total)),
                      upper=decimal(total))
    return result


def _expression(terms):
    expressions, parameters = [], {}
    for i, term in enumerate(terms):
        name = 'coefficient_' + str(i)
        parameters[name] = {'value': str(term['coefficient'])}
        expressions.append(['mul', ['parameter', name], ['input', term['source_quantity_id']]])
    require(expressions, 'empty mass expression')
    expression = expressions[0]
    for item in expressions[1:]:
        expression = ['add', expression, item]
    return expression, parameters


def _rank(rows):
    columns = sorted({term['source_quantity_id'] for row in rows for term in row})
    matrix = []
    for row in rows:
        values = {term['source_quantity_id']: term['coefficient'] for term in row}
        matrix.append([Fraction(values.get(key, 0)) for key in columns])
    pivot = 0
    for column in range(len(columns)):
        found = next((i for i in range(pivot, len(matrix)) if matrix[i][column]), None)
        if found is None:
            continue
        matrix[pivot], matrix[found] = matrix[found], matrix[pivot]
        scale = matrix[pivot][column]
        matrix[pivot] = [x / scale for x in matrix[pivot]]
        for i in range(len(matrix)):
            if i != pivot:
                scale = matrix[i][column]
                matrix[i] = [x - scale * y for x, y in zip(matrix[i], matrix[pivot])]
        pivot += 1
        if pivot == len(matrix):
            break
    return pivot


def build(root, ame, catalog, source, *, pilots):
    root = Path(root)
    raw = (root / source['path']).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == source['sha256'], 'AME source bytes changed')
    lines = raw.decode().splitlines()
    api = producer.load(root)
    catalog_rows = {row['id']: row for row in catalog['properties']}
    quantities, rows = {}, []

    def quantity(z, a, field):
        row = ame.get((z, a))
        if row is None or row[field] is None:
            return None
        require(row['raw'] == lines[row['line'] - 1], 'source locator differs from raw AME row')
        require((int(row['raw'][9:14]), int(row['raw'][14:19])) == (z, a),
                'source nuclide identity differs from raw AME row')
        lo, hi, ulo, uhi = FIELDS[field]
        value_field = row['raw'][lo:hi].strip().replace('#', '.')
        magnitude_field = row['raw'][ulo:uhi].strip().replace('#', '.')
        require(Fraction(value_field) == Fraction(row[field]), 'parsed source value differs')
        magnitude = row[field + '_uncertainty']
        if magnitude is not None:
            require(Fraction(magnitude_field) == Fraction(magnitude), 'parsed magnitude differs')
        key = f"{source['id']}:{source['sha256']}:{field}:Z{z}:A{a}:ground"
        quantities[key] = {'id': key, 'source_id': source['id'], 'source_sha256': source['sha256'],
                          'z': z, 'a': a, 'state': 'ground', 'quantity': field, 'unit': 'keV',
                          'convention': 'AME2020 neutral-atom mass table; neutron reference at Z=0,A=1',
                          'value': row[field], 'reported_magnitude': magnitude,
                          'uncertainty_convention': 'source_reported_magnitude_convention_not_reconstructed',
                          'estimated': row['estimated'][field],
                          'locator': {'line': row['line'], 'value_columns': [lo + 1, hi],
                                      'magnitude_columns': [ulo + 1, uhi]}, 'raw_row': row['raw']}
        return key

    for z, a, symbol in pilots:
        entity = f'isotope:{symbol}-{a}:ground'
        formulas = {
            'binding_energy': [(z, a, 'binding_energy_per_nucleon', a)],
            'neutron_separation_energy': [(z, a - 1, 'mass_excess', 1), (0, 1, 'mass_excess', 1), (z, a, 'mass_excess', -1)],
            'proton_separation_energy': [(z - 1, a - 1, 'mass_excess', 1), (1, 1, 'mass_excess', 1), (z, a, 'mass_excess', -1)],
            'alpha_decay_q': [(z, a, 'mass_excess', 1), (z - 2, a - 4, 'mass_excess', -1), (2, 4, 'mass_excess', -1)],
        }
        for family in FAMILIES:
            original = catalog_rows[family + ':' + entity]
            require(original['unit'] == 'keV' and original['physical_prediction'] is False,
                    'catalog unit or physical scope changed')
            terms, missing, requested = [], [], []
            for iz, ia, field, coefficient in formulas[family]:
                identity = quantity(iz, ia, field)
                requested.append({'z': iz, 'a': ia, 'state': 'ground', 'quantity': field,
                                  'coefficient': coefficient, 'source_quantity_id': identity})
                if identity is None:
                    missing.append({'z': iz, 'a': ia, 'state': 'ground', 'quantity': field,
                                    'coefficient': coefficient})
                else:
                    terms.append({'source_quantity_id': identity, 'coefficient': coefficient})
            row = {'id': original['id'], 'entity_id': entity, 'property': family, 'unit': 'keV',
                   'value': original['value'], 'catalog_uncertainty': original['uncertainty'],
                   'requested_inputs': requested,
                   'coefficients': None, 'missing_inputs': missing, 'm3_nominal': None,
                   'magnitude_scaling': None, 'conditional_sd_range': None,
                   'physical_prediction': False}
            if missing:
                require(original['value'] is None and original['uncertainty']['value'] is None,
                        'missing source input acquired an invented value')
                row.update(status='missing_source_inputs', reason=original['qualification'])
            else:
                require(original['source_id'] == source['id'], 'catalog source identity differs')
                canonical = coefficients(terms)
                expression, parameters = _expression(canonical)
                values = {t['source_quantity_id']: quantities[t['source_quantity_id']]['value'] for t in canonical}
                result = api.mapping.evaluate(expression, values, parameters)
                require(result == Fraction(original['value']), 'nominal reduction differs from catalog')
                row.update(status='exact_decimal_reduction', coefficients=canonical,
                           m3_nominal={'expression': expression, 'parameters': parameters,
                                       'input_values': values, 'result': str(result)})
                if family == 'binding_energy':
                    magnitude = quantities[canonical[0]['source_quantity_id']]['reported_magnitude']
                    scaled = None if magnitude is None else decimal(a * Fraction(magnitude))
                    quoted = original['uncertainty']['value']
                    require((scaled is None and quoted is None) or
                            (scaled is not None and quoted is not None and Fraction(scaled) == Fraction(quoted)),
                            'exact A scaling differs from catalog')
                    row['magnitude_scaling'] = {'coefficient': a, 'value': scaled,
                                                'kind': 'scaled_source_reported_magnitude',
                                                'statistical_convention': 'not_reconstructed'}
                else:
                    require(original['uncertainty']['value'] is None
                            and original['uncertainty']['kind'] == 'joint_covariance_not_supplied',
                            'unbound joint uncertainty in baseline catalog')
                    row['conditional_sd_range'] = conditional_sd_range(canonical, quantities)
            rows.append(row)

    by_id = {row['id']: row for row in rows}
    def identifier(family, isotope): return family + ':isotope:' + isotope + ':ground'
    d_ids = [identifier(family, 'H-2') for family in ('neutron_separation_energy', 'proton_separation_energy')]
    require(by_id[d_ids[0]]['coefficients'] == by_id[d_ids[1]]['coefficients'], 'D source identity differs')
    relation = [{'record_id': identifier(family, isotope), 'coefficient': coefficient}
                for family, isotope, coefficient in (
                    ('neutron_separation_energy', 'He-4', 1), ('proton_separation_energy', 'He-4', -1),
                    ('neutron_separation_energy', 'H-3', -1), ('proton_separation_energy', 'He-3', 1))]
    combined = [{'source_quantity_id': term['source_quantity_id'],
                 'coefficient': entry['coefficient'] * term['coefficient']}
                for entry in relation for term in by_id[entry['record_id']]['coefficients']]
    require(not coefficients(combined), 'shared-mass path identity failed')
    combinations = [row['coefficients'] for row in rows
                    if row['property'] != 'binding_energy' and row['coefficients'] is not None]
    report = {'schema': SCHEMA, 'scope': 'complete_six_isotope_pilot_mass_derivations',
            'counts': {'records': len(rows), 'numeric': sum(row['value'] is not None for row in rows),
                       'null': sum(row['value'] is None for row in rows), 'isotopes': len(pilots)},
            'source': {'id': source['id'], 'path': source['path'], 'sha256': source['sha256']},
            'producer': {'commit': api.binding['upstream_head'], 'tree': api.binding['upstream_tree'],
                         'binding_sha256': producer.BINDING_SHA256,
                         'route': 'mapping.evaluate and mapping.propagate raw exact affine arithmetic'},
            'source_quantities': quantities, 'rows': rows,
            'dependencies': {'identical_outputs': [d_ids], 'zero_output_combinations': [relation],
                             'mass_combination_rows': len(combinations), 'coefficient_rank': _rank(combinations),
                             'interpretation': 'Algebraic rank does not establish uncorrelated outputs or independent experiments.'},
            'typed_m3_acceptance': False, 'physical_budget_complete': False,
            'limits': ['Retained decimal reductions are retrospective source calculations, not physical predictions.',
                       'A conditional SD range is not a deterministic error bound or coverage interval.',
                       'Different output SD endpoints need not be attainable together under one joint covariance.',
                       'Binding-per-nucleon and mass-excess fields retain distinct source representations.']}
    report['covariance_adoption'] = covariance.build(root, report, api.mapping)
    adoption = report['covariance_adoption']
    convention = adoption['method']['sigma_convention']
    require(convention['status'] == 'source_confirmed'
            and convention['kind'] == 'one_standard_deviation', 'uncertainty convention not authenticated')
    document = next(s for s in adoption['sources'] if s['id'] == convention['source_id'])
    report['source_convention'] = {
        'status': 'source_documented_rounded_marginals', 'kind': convention['kind'],
        'source_id': document['id'], 'source_sha256': document['sha256'],
        'locator': convention['locator'], 'manifest': adoption['manifest'],
        'scope': 'Selected evaluated inputs without a systematics marker.',
        'precision': 'Quoted decimal magnitudes are retained; precise covariance diagonals do not replace them.'}
    for quantity in quantities.values():
        quantity['catalog_uncertainty_kind'] = quantity['uncertainty_convention']
        if not quantity['estimated']:
            quantity['uncertainty_convention'] = 'one_standard_deviation'
            quantity['convention_evidence'] = 'source_convention'
    for row in rows:
        if row['coefficients'] is None or any(quantities[t['source_quantity_id']]['estimated']
                                               for t in row['coefficients']):
            continue
        if row['conditional_sd_range'] is not None:
            row['conditional_sd_range']['premise_status'] = 'source_documented_rounded_marginals'
            row['conditional_sd_range']['convention_evidence'] = 'source_convention'
        if row['magnitude_scaling'] is not None:
            row['magnitude_scaling']['statistical_convention'] = 'source_documented_rounded_marginals'
            row['magnitude_scaling']['convention_evidence'] = 'source_convention'
    return report
