"""Paired reference preparations and source-bound joint diagnostic uncertainty.

The finite law is the executed coupled preparation law. Published atomic values
remain separate comparison inputs until a physical observation map is supplied.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

import matter1_campaign as history
import matter1_properties as properties
import matter1_coupled_preparations as coupled
import matter1_m3_producer as producer
import matter1_preparation_freeze as freeze

ROOT = Path(__file__).resolve().parents[2]
DATA = Path('manual2/data/m1/preparation_workflow')
PROFILE = 'matter1:paired-preparation-workflow:v1'
OUTPUTS = ('reference_preparations.json', 'uncertainty.json', 'frozen_diagnostic.json', 'comparisons.json')
TARGET_PATHS = ('manual2/data/m1/properties/catalog.json',
                'manual2/data/m1/external_transitions/catalog.json',
                'manual2/data/m1/isotopes/catalog.json')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def reference_preparations(root=ROOT):
    """Prepare every retained reference; counts do not imply executed physics."""
    rows = []
    for reference in history.reference_inputs(root):
        z, a = int(reference['z']), int(reference['mass_a'])
        for name, electrons in (('bare', 0), ('neutral', z)):
            config = coupled.default_config(z, a, electrons, rounds=1, seed=20261111)
            rows.append({
                'id': f'Z{z:03d}-A{a:03d}-{name}',
                'z': z, 'a': a, 'n': a-z, 'electron_count': electrons,
                'charge': z-electrons, 'preparation': name,
                'reference_selection': deepcopy(reference),
                'configuration': config, 'status': 'prepared_not_executed',
                'physical_preparation': 'unresolved_reference_state_correspondence',
                'electronic_hyperfine': 'not_applicable' if electrons == 0 else 'observation_map_unresolved',
                'retention': 'configuration_loss_map_unresolved',
                'conditional_output': None, 'physical_prediction': None,
            })
    require(len(rows) == 236 and len({r['id'] for r in rows}) == 236,
            'All 118 distinct bare/neutral reference pairs required')
    return rows


def execute_reference(z, preparation, root=ROOT):
    """Execute the declared finite law for one explicitly selected reference."""
    require(type(z) is int and 1 <= z <= 118, 'Exact retained element number required')
    require(preparation in ('bare', 'neutral'), 'Bare or neutral preparation required')
    row = next(r for r in reference_preparations(root)
               if r['z'] == z and r['preparation'] == preparation)
    result = coupled.run_case(row['configuration'], root)
    row.update(status='conditional_construction_executed',
               conditional_output=coupled.readouts(result),
               trajectory_sha256=result['trajectory_sha256'])
    return row, result


def quantity_binding(module, source, name):
    return {'schema': module.QUANTITY_SCHEMA, 'source_id': source['id'],
            'source_sha256': source['sha256'], 'quantity_id': name,
            'quantity': deepcopy(source['payload']['quantities'][name])}


def propagate_ensemble(ensemble, modules):
    """Propagate the joint executed law without replacing it by independent marginals."""
    paths = ensemble['paths']
    require(type(paths) is list and paths, 'Executed finite paths required')
    order = ensemble['observable_order']
    require(type(order) is list and order and len(order) == len(set(order)) and
            all(set(order) <= set(p['readouts']) for p in paths),
            'Complete common diagnostic output set required')
    support = [[p['probability'], {name: str(Q(p['readouts'][name])) for name in order}]
               for p in paths]
    require(sum(Q(p) for p, point in support) == 1, 'Path probabilities must normalize')
    m, mt = modules.mapping, modules.metrology
    types = {
        'signed_current': ('native_signed_response', '1', [0, 0, 0], 'Signed response in the declared native arithmetic'),
        'accumulated_burden': ('native_response_magnitude', '1', [0, 0, 0], 'Accumulated magnitude before signed cancellation'),
        'outer_commit': ('native_cut_index', '1', [0, 0, 0], 'Ordinal in the declared cut coordinate; not elapsed time'),
        'inner_reclosures': ('native_reclosure_count', 'count', [0, 0, 1], 'Number of completed inner returns'),
    }
    require(set(order) == set(types), 'Declared diagnostic quantity inventory differs')
    quantities = {}
    for name in order:
        values = [Q(point[name]) for probability, point in support]
        kind, unit, dimension, meaning = types[name]
        quantities[name] = {
            'kind': kind, 'unit': unit, 'dimension': dimension,
            'domain': [str(min(values)), str(max(values))], 'window': None,
            'locator': 'Complete admitted paths under the frozen preparation: ' + name,
            'role': 'model', 'meaning': meaning,
            'value': None, 'uncertainty': {'category': 'finite_joint_law'},
            'components': [], 'corrections': {},
        }
    source = m.source('matter1:coupled-paths:' + digest(ensemble), 'model', {
        'ensemble_sha256': digest(ensemble), 'quantities': quantities,
        'configuration': ensemble['config'],
        'trajectory_sha256': [p['trajectory_sha256'] for p in paths],
    })
    inputs = {name: quantity_binding(mt, source, name) for name in order}
    outputs = {name: {'kind': types[name][0], 'unit': types[name][1], 'dimension': types[name][2],
                      'domain': None, 'expression': ['input', name], 'conversion': None}
               for name in order}
    model = {'method': 'finite_joint_law', 'input_order': order,
             'input_bindings': {name: {'source_sha256': source['sha256'], 'quantity_id': name}
                                for name in order},
             'parameter_bindings': {}, 'outputs': outputs, 'support': support,
             'means': None, 'covariance': None, 'bounds': None,
             'interpretation': 'Exact conditional variation of shared native histories; no physical measurement distribution'}
    law = m.source('matter1:coupled-law:' + digest(model), 'model',
                   {'uncertainty_models': {'joint': model}})
    request = {'schema': mt.PROPAGATION_SCHEMA, 'stage': 'prediction',
               'inputs': inputs, 'parameters': {}, 'model_source_id': law['id'],
               'model_id': 'joint', 'model': model}
    trusted = {s['id']: s for s in (source, law)}
    propagated = mt.propagate_quantities(request, trusted)
    # Verify the producer's covariance against direct path summation.
    means = {n: sum(Q(p)*Q(point[n]) for p, point in support) for n in order}
    covariance = [[str(sum(Q(p)*(Q(point[i])-means[i])*(Q(point[j])-means[j])
                           for p, point in support)) for j in order] for i in order]
    require(propagated['output_order'] == order and propagated['output_covariance'] == covariance,
            'Producer covariance differs from direct joint path sum')
    return {'ensemble_sha256': digest(ensemble), 'request': request,
            'trusted_sources': trusted, 'result': propagated,
            'physical_input_budget': {
                'declared_configuration': 'exact_model_choice',
                'intrinsic_variation': 'joint_finite_law_propagated',
                'measured_preparation_environment': 'unknown_no_applicable_setup_evidence',
                'state_assignment': 'physical_correspondence_unresolved',
                'clock_realization': 'generic_relational_reference_not_a_realized_SI_clock',
                'physical_model_discrepancy': 'unknown',
                'arithmetic': 'exact_rational',
            }}


def target_quantities(root, modules):
    """Authenticate retained numerical targets without inventing uncertainty semantics."""
    root = Path(root)
    catalog = read(root / TARGET_PATHS[0])
    require(canonical(catalog) == canonical(properties.build(root)['catalog.json']),
            'Comparison catalog differs from independently reconstructed source records')
    rows = [r for r in catalog['properties'] if r['id'] in
            ('hyperfine:H-1', 'hyperfine:H-2', 'hyperfine:H-3') and r['selection_status'] == 'adopted']
    require(len(rows) == 3 and len({r['id'] for r in rows}) == 3, 'Three adopted H/D/T targets required')
    m, mt = modules.mapping, modules.metrology
    quantities = {}
    for row in rows:
        require(row['unit'] == 'Hz' and row['value_kind'] == 'numeric', 'Typed target frequency required')
        original = row['uncertainty']
        if original['kind'] == 'reported_standard_uncertainty':
            uncertainty = {'category': 'standard_uncertainty', 'value': str(Q(original['value'])),
                           'printed_token': original['value']}
        else:
            uncertainty = {'category': 'unknown',
                           'reason': 'Reported magnitude retained separately; a standard deviation or probability law is not established'}
        quantities[row['id']] = {
            'kind': 'atomic_ground_hyperfine_frequency', 'unit': 'Hz', 'dimension': [0, -1, 0],
            'domain': ['0', '100000000000'], 'window': None, 'locator': row['locator'],
            'role': 'evaluation', 'meaning': row['transition'] + '; ' + row['entity_id'],
            'value': str(Q(row['value'])), 'uncertainty': uncertainty, 'components': [], 'corrections': {},
        }
    source = m.source('matter1:retained-hdt-targets', 'evaluation', {
        'catalog_sha256': hashlib.sha256((root/TARGET_PATHS[0]).read_bytes()).hexdigest(),
        'records': rows, 'quantities': quantities,
    })
    registry = {source['id']: source}
    bindings = {n: quantity_binding(mt, source, n) for n in quantities}
    for binding in bindings.values():
        mt.validate_quantity(binding, registry)
    return source, bindings


def comparisons(root, native_prediction, modules):
    """Read targets only after native outputs have been frozen."""
    root = Path(root)
    source, bindings = target_quantities(root, modules)
    rows = []
    for a in (1, 2, 3):
        for electrons in (0, 1):
            rows.append({'id': f'H-{a}-' + ('bare' if electrons == 0 else 'neutral'),
                         'atomic_transition': {
                             'status': 'not_applicable' if electrons == 0 else 'missing_observation_map',
                             'target': None if electrons == 0 else bindings[f'hyperfine:H-{a}'],
                             'prediction_hz': None, 'residual_hz': None,
                             'residual_variance': None,
                             'variance_rule': 'Var(P)+Var(O)-2*Cov(P,O)',
                             'reason': 'No electron-coupled readout in bare scope' if electrons == 0 else
                             'Prepared state splitting, emitted phase and realized reference are not supplied by the finite recurrence law'},
                         'retention': {'status': 'missing_loss_observation_map',
                                       'half_life_seconds': None,
                                       'reason': 'No configuration-derived closure-load/cost law and daughter/channel correspondence'},
                         'claim': 'conditional_native_diagnostics_with_unresolved_physical_comparison'})
    isotope_catalog = read(root / TARGET_PATHS[2])
    isotope_rows = [r for r in isotope_catalog['isotopes'] if r.get('Z') == 1 and r.get('A') in (1, 2, 3)]
    inputs_path = root/properties.INPUTS
    require(properties.sha(inputs_path) == properties.INPUTS_SHA256,
            'Property source selection changed')
    input_manifest = properties.read(inputs_path)
    nubase = next(s for s in input_manifest['sources'] if s['id'] == 'nubase2020')
    source_path = properties.source_path(root, nubase['path'])
    require(properties.sha(source_path) == nubase['sha256'], 'Retained NUBASE source changed')
    parsed = properties.parse_nubase(source_path.read_text())
    retained_lifetimes = []
    for a in (1, 2, 3):
        original = parsed[(1, a, 0)]
        raw = original['raw']
        value, unit, uncertainty = raw[69:78].strip(), raw[78:80].strip(), raw[81:88].strip()
        retained_lifetimes.append({
            'id': f'H-{a}:ground', 'source': nubase, 'line': original['line'], 'raw': raw,
            'half_life_token': value, 'unit_token': unit,
            'reported_uncertainty_token': uncertainty,
            'meaning': 'observationally_stable_not_infinite_measured_lifetime' if value == 'stbl' else 'evaluated_half_life',
            'uncertainty_semantics': 'verbatim dT field; distribution and coverage not inferred',
            'decay_branching_token': original['branches_raw'],
            'charge_state_correspondence': 'not_assigned_to_bare_or_neutral_preparation_by_this_nuclide_table',
            'physical_prediction': None,
        })
    return {'profile': PROFILE, 'native_prediction_sha256': digest(native_prediction),
            'target_source': source, 'rows': rows, 'retained_isotope_measurements': retained_lifetimes,
            'retained_evaluated_catalog_records': isotope_rows,
            'external_transition_records': read(root/TARGET_PATHS[1])['records'],
            'source_sha256': {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
                              for name in (*TARGET_PATHS, str(properties.INPUTS), nubase['path'])},
            'exposure': 'retrospective_targets_previously_available',
            'complete_physical_predictions': 0,
            'joint_covariance': 'not_supplied; independent files do not establish independence',
            'target_policy': 'Measurements retained; unavailable raw protocols limit only dependent inferences'}


def validate_reference_matrix(rows):
    require(type(rows) is list and len(rows) == 236, '236 preparation slots required')
    expected = {(z, name) for z in range(1, 119) for name in ('bare', 'neutral')}
    require({(r['z'], r['preparation']) for r in rows} == expected,
            'Missing, duplicate or substituted reference preparation')
    for row in rows:
        require(all(type(row[k]) is int for k in ('z', 'a', 'n', 'electron_count', 'charge')),
                'Exact inventory counts required')
        require(row['n'] == row['a']-row['z'] and row['electron_count'] ==
                (0 if row['preparation'] == 'bare' else row['z']) and
                row['charge'] == row['z']-row['electron_count'], 'Bare/neutral inventory mismatch')
        config = row['configuration']
        require(type(config) is dict and all(type(config.get(k)) is int for k in
                ('z', 'a', 'electron_count', 'rounds', 'seed')) and type(config.get('feedback')) is bool,
                'Exact nested preparation configuration required')
        require(config == coupled.default_config(row['z'], row['a'], row['electron_count'],
                                                rounds=1, seed=20261111),
                'Nested configuration differs from reference preparation')
        require(row['status'] in ('prepared_not_executed', 'conditional_construction_executed') and
                row['physical_prediction'] is None, 'Execution scope promoted')
        require((row['conditional_output'] is None) == (row['status'] == 'prepared_not_executed'),
                'Execution status and output disagree')
    return True


def build_predictions(root=ROOT):
    """Execute the frozen finite tranche before opening any comparison source."""
    root = Path(root)
    modules = producer.load(root)
    source_names = ('manual2/scripts/matter1_preparation_workflow.py',
                    'manual2/scripts/matter1_coupled_preparations.py',
                    'manual2/scripts/matter1_m3_producer.py',
                    'manual2/scripts/matter1_preparation_freeze.py',
                    'manual2/data/m1/reference_inputs.csv')
    sources = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in source_names}
    require((root/source_names[0]).read_bytes() == Path(__file__).read_bytes(),
            'Executing preparation workflow differs from the selected source')
    rows = reference_preparations(root)
    executions = {}
    # This tranche is fixed by inventory size, before reading any targets.
    for z in (1, 2, 3):
        for preparation in ('bare', 'neutral'):
            row, result = execute_reference(z, preparation, root)
            rows[2*(z-1) + (preparation == 'neutral')] = row
            executions[row['id']] = result
    validate_reference_matrix(rows)
    propagated = {}
    for a in (1, 2, 3):
        for electrons in (0, 1):
            identity = f'H-{a}-' + ('bare' if electrons == 0 else 'neutral')
            config = coupled.default_config(1, a, electrons, rounds=1, seed=20261111)
            ensemble = coupled.enumerate_paths(config, root)
            propagated[identity] = propagate_ensemble(ensemble, modules)
    feedback_config = coupled.default_config(1, 1, 1, rounds=2, seed=20261111)
    propagated['H-1-neutral-feedback'] = propagate_ensemble(coupled.enumerate_paths(feedback_config, root), modules)
    reference = {
        'profile': PROFILE, 'selection': 'retained 118 reference mass-number selections',
        'source_sha256': sources,
        'rule': 'current coupled preparation law with one committed inner round',
        'executed_tranche': {'z': [1, 2, 3], 'preparations': ['bare', 'neutral'],
                            'selection_basis': 'small finite constructions; not target agreement'},
        'rows': rows, 'raw_executions': executions,
        'counts': {'element_reference_identities': 118, 'preparation_slots': 236,
                   'construction_executions': len(executions), 'prepared_remaining': 236-len(executions),
                   'physical_predictions': 0, 'historical_neutral_configurations': 135},
        'extension_command': 'python -B manual2/scripts/generate_matter1_preparation_workflow.py --execute-reference Z --preparation bare|neutral --output-root EXTERNAL_DIRECTORY',
        'extension_scope': 'Runs the same declared law. Atomic preparation and gate correspondence remain separate obligations for every row.',
    }
    uncertainty = {'profile': PROFILE, 'source_sha256': sources, 'cases': propagated,
                   'scope': 'Joint exact native diagnostics, with unresolved physical input and observation budgets retained'}
    return {'reference_preparations.json': reference, 'uncertainty.json': uncertainty,
            'frozen_diagnostic.json': freeze.build(root, modules)}


def build_products(root=ROOT):
    products = build_predictions(root)
    products['comparisons.json'] = comparisons(root, products, producer.load(root))
    return products


def generate(root=ROOT, output_root=None):
    root = Path(root)
    destination = Path(output_root) if output_root is not None else root
    products = build_products(root)
    for name, value in products.items():
        path = destination/DATA/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical(value))
    return {'status': 'GENERATED_PAIRED_PREPARATION_WORKFLOW', 'outputs': list(products),
            'physical_predictions': 0}


def verify(root=ROOT):
    root = Path(root)
    expected = build_products(root)
    require(set(expected) == set(OUTPUTS), 'Preparation product inventory differs')
    for name, value in expected.items():
        require((root/DATA/name).read_bytes() == canonical(value),
                'Original-input preparation replay differs: ' + name)
    matrix = expected['reference_preparations.json']
    return {'status': 'PASS_PAIRED_PREPARATION_ORIGINAL_INPUT_REPLAY',
            'outputs': {name: digest(value) for name, value in expected.items()},
            'counts': matrix['counts'], 'joint_uncertainty_cases': 7,
            'physical_comparison': 'unresolved_observation_and_loss_maps',
            'historical_profiles': 'preserved_separately'}
