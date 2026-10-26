"""Executable atomic-map obstruction and separate conventional benchmark.

The predictor reads finite dynamics and a target-free contract. It emits an
explicit incomplete atomic attempt plus unselected countermodels, not a fitted
hyperfine prediction. The scorer alone reads the evaluation target. Conventional
spin-Hamiltonian calculations are a separate externally calibrated lane.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

SUBDIR = Path('manual2/data/m1/atomic')
INPUTS = ('model_contract.json', 'evaluation_target.json', 'benchmark_inputs.json')
OUTPUTS = ('prediction.json', 'comparison.json', 'benchmark.json', 'obligations.json', 'atomic_report.json')
CS_HZ = Q(9192631770)
PROFILE = 'matter1-atomic-map-obstruction-v2'
SOURCE_PATHS = {
    'sections/05_curl_closure_duon_current.tex': ['eq:key-proposed-admitted-trace'],
    'sections/06_wave_state_relational_time.tex': ['eq:wave-update-trace', 'eq:rcd-duration-participation', 'eq:cadence-ratio'],
}


class ValidationError(ValueError):
    """An atomic application claim or evidence record is inconsistent."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, f'Duplicate JSON key: {k}')
            result[k] = v
        return result
    try:
        return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs)
    except (OSError, ValueError) as exc:
        raise ValidationError(f'{path}: {exc}') from exc


def keys(value, expected, name):
    require(isinstance(value, dict) and set(value) == set(expected.split()), f'{name}: missing or unexpected fields')


def rational(value):
    require(isinstance(value, (str, int, Q)) and not isinstance(value, bool), 'Expected exact rational input')
    try:
        result = Q(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValidationError('Invalid rational input') from exc
    return result


def decimal(value, precision=34):
    value = rational(value)
    with localcontext() as ctx:
        ctx.prec = precision
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def sources(root):
    records = []
    for name, labels in SOURCE_PATHS.items():
        try:
            blob = (Path(root) / name).read_bytes()
        except OSError as exc:
            raise ValidationError(f'Missing source binding: {name}') from exc
        require(all(('\\label{' + label + '}').encode() in blob for label in labels), 'Source premise label absent')
        lines = blob.decode().splitlines()
        records.append({'path': name, 'sha256': hashlib.sha256(blob).hexdigest(), 'labels': labels,
                        'label_lines': {label: next(i+1 for i, line in enumerate(lines) if '\\label{' + label + '}' in line) for label in labels}})
    return records


def default_contract(root):
    return {
        'schema_version': 1, 'profile': PROFILE,
        'status': 'executable_underdetermination_attempt',
        'source_bindings': sources(root),
        'reference': {'isotope': 'Cs-133', 'z': 55, 'frequency_hz': str(CS_HZ),
                      'role': 'exact_si_definition', 'source': 'https://www.bipm.org/en/si-base-units/second'},
        'external_states': [
            {'isotope': 'H-1', 'z': 1, 'a': 1, 'I': '1/2', 'J': '1/2', 'F_pair': ['0', '1'], 'm_F': '0'},
            {'isotope': 'Cs-133', 'z': 55, 'a': 133, 'I': '7/2', 'J': '1/2', 'F_pair': ['3', '4'], 'm_F': '0'},
        ],
        'state_sources': {'H-1': 'https://tf.nist.gov/general/pdf/13.pdf',
                          'Cs-133': 'https://steck.us/alkalidata/cesiumnumbers.pdf'},
        'dependency_gates': {'P4a': 'external_state_inventory_only',
                             'P2': 'native_atomic_construction_and_accessor_unresolved',
                             'P3': 'native_atomic_coupled_lineages_unresolved',
                             'P4': 'physical_atomic_observation_map_unresolved'},
        'native_configuration_status': 'not_constructed_for_these_atomic_states',
        'state_assignment_status': 'hypothetical_labels_for_counterexample_only',
        'diagnostic_assignment': {'H-1': 'outer_plus', 'Cs-133': 'outer_minus'},
        'map_family': {
            'formula': 'g_lambda(Z)=1+lambda*(55-Z)/54; R_lambda=(N_plus/N_minus)*g_lambda(1)/g_lambda(55)',
            'domain': 'lambda > -1 on Z in {1,55}',
            'witness_values': ['0', '1'], 'selection_status': 'no_member_selected_as_atomic_model',
            'purpose': 'Show Cs normalization and finite traces do not determine the missing atomic observation map.',
        },
        'target_policy': 'prediction_stage_does_not_read_evaluation_or_benchmark_inputs',
        'exposure': 'H_and_Rb_previously_exposed; no_independent_prediction_claim',
        'uncertainty_status': 'physical_model_discrepancy_and_mapping_unresolved',
        'admission_status': 'native_atomic_admission_pending',
    }


def validate_contract(root, contract):
    expected = default_contract(root)
    require(contract == expected, 'Atomic contract differs: unsupported state, source, map selection, target access or status')
    return contract


def default_target():
    return {
        'schema_version': 1, 'profile': PROFILE, 'classification': 'retrospective_measurement',
        'isotope': 'H-1', 'observable': 'unperturbed_ground_state_hyperfine_frequency',
        'frequency_hz': '1420405751.768', 'standard_uncertainty_hz': '0.002',
        'source': 'https://tf.nist.gov/general/pdf/13.pdf', 'locator': 'printed page 200; rendered evidence bound in v1 inventory',
        'source_uncertainty_scope': 'published_aggregate_one_sigma; no independent recombination',
        'exposure_status': 'known_before_model_selection',
        'prediction_measurement_covariance_hz2': None,
        'covariance_status': 'unknown; no independence assumed',
    }


def validate_target(target, allow_synthetic=False):
    expected = default_target()
    keys(target, ' '.join(expected), 'evaluation target')
    if allow_synthetic and target['classification'] == 'synthetic_evaluation_mutation':
        require(rational(target['frequency_hz']) > 0 and rational(target['standard_uncertainty_hz']) >= 0, 'Invalid synthetic evaluation')
        copy = deepcopy(target)
        for key in ('frequency_hz', 'standard_uncertainty_hz', 'classification'):
            copy[key] = expected[key]
        require(copy == expected, 'Synthetic evaluation may change only numeric value/uncertainty and classification')
    else:
        require(target == expected, 'Historical evaluation input/provenance differs')
    return target


def default_benchmark():
    return {
        'schema_version': 1, 'profile': PROFILE, 'classification': 'conventional_external_calibrated_benchmark',
        'hamiltonian': 'H/h=A_over_h I.dot.J+(mu_B/h) B (g_J J_z+g_I I_z); m_F=0 block',
        'hamiltonian_source': 'https://steck.us/alkalidata/cesiumnumbers.pdf',
        'source_locator': 'revision 2.3.4, section 3, hyperfine and Zeeman Hamiltonians; Breit-Rabi expression',
        'approximation': 'Leading spin-only g_J=2, g_I=0 for both species; neglect bound-state, nuclear-Zeeman and environmental corrections. Numerical benchmark, not precision spectroscopy.',
        'g_J': '2', 'g_I': '0',
        'mu_B_over_h_hz_per_tesla': '13996244917.1', 'mu_B_over_h_standard_uncertainty': '4.4',
        'constant_source': 'https://physics.nist.gov/cuu/Constants/Table/allascii.txt',
        'constant_version': '2022 CODATA; Bohr magneton in Hz/T row',
        'field_values_tesla': ['-0.0001', '-0.000001', '0', '0.000001', '0.0001'],
        'field_status': 'stipulated_ideal_field_values; no measured field calibration',
        'species': [
            {'isotope': 'H-1', 'I': '1/2', 'J': '1/2', 'splitting_hz': '1420405751.768',
             'splitting_standard_uncertainty_hz': '0.002', 'splitting_role': 'imported_measured_benchmark_calibrant',
             'source': 'https://tf.nist.gov/general/pdf/13.pdf'},
            {'isotope': 'Cs-133', 'I': '7/2', 'J': '1/2', 'splitting_hz': str(CS_HZ),
             'splitting_standard_uncertainty_hz': '0', 'splitting_role': 'exact_si_definition',
             'source': 'https://www.bipm.org/en/si-base-units/second'},
        ],
        'uncertainty_status': 'partial; g approximation, field calibration and covariance not supplied',
        'native_admission_status': 'not_a_native_AOD_model',
    }


def validate_benchmark(model):
    require(model == default_benchmark(), 'Conventional benchmark input/source/status differs')
    return model


def clock_block(splitting, spin_i, beta, field):
    """Exact mF=0 product-basis matrix; eigenvalue radicals are external decimals."""
    splitting, spin_i, beta, field = map(rational, (splitting, spin_i, beta, field))
    require(splitting > 0 and spin_i >= Q(1, 2) and (spin_i-Q(1, 2)).denominator == 1, 'Invalid hyperfine block')
    a = splitting / (spin_i + Q(1, 2))
    diag = -a / 4
    return [[diag + beta*field/2, splitting/2], [splitting/2, diag-beta*field/2]]


def benchmark(model):
    validate_benchmark(model)
    beta = (rational(model['g_J'])-rational(model['g_I']))*rational(model['mu_B_over_h_hz_per_tesla'])
    results = []
    with localcontext() as ctx:
        ctx.prec = 42
        for atom in model['species']:
            delta = rational(atom['splitting_hz'])
            for field in model['field_values_tesla']:
                matrix = clock_block(delta, atom['I'], beta, field)
                # Discriminant from the Hamiltonian, independently compared with
                # the closed mF=0 Breit-Rabi square in exact arithmetic.
                discriminant = (matrix[0][0]-matrix[1][1])**2 + 4*matrix[0][1]*matrix[1][0]
                breit_rabi_square = delta**2 + (beta*rational(field))**2
                require(discriminant == breit_rabi_square, 'Hamiltonian/Breit-Rabi disagreement')
                gap = (Decimal(discriminant.numerator)/Decimal(discriminant.denominator)).sqrt()
                center = matrix[0][0]+matrix[1][1]
                center_d = Decimal(center.numerator)/Decimal(center.denominator)
                delta_d = Decimal(delta.numerator)/Decimal(delta.denominator)
                results.append({'isotope': atom['isotope'], 'field_tesla': field,
                                'matrix_hz': [[str(x) for x in row] for row in matrix],
                                'm_F': '0', 'state_tracking': 'lower_and_upper_mF0_eigenbranches_continued_from_F=I-1/2,I+1/2',
                                'eigenvalues_hz': [str((center_d-gap)/2), str((center_d+gap)/2)],
                                'frequency_hz': str(gap), 'shift_hz': str(gap-delta_d),
                                'frequency_squared_exact_hz2': str(discriminant),
                                'weak_field_quadratic_coefficient_hz_per_tesla2': str(beta**2/(2*delta)),
                                'complete_standard_uncertainty_hz': None,
                                'uncertainty_status': 'partial_benchmark_not_precision_measurement'})
    return {'schema_version': 1, 'classification': model['classification'], 'inputs_sha256': digest(model),
            'native_atomic_prediction': False, 'rows': results,
            'input_uncertainties': {s['isotope']: s['splitting_standard_uncertainty_hz'] for s in model['species']},
            'zero_field_agreement_role': 'calibrant_reproduction_only',
            'uncertainty_status': model['uncertainty_status'], 'approximation': model['approximation']}


def _dynamics(root):
    from matter1_stateful import prepare
    return prepare(root)


def _counts(trace):
    summary = trace['summary']
    counts = summary['observed_reclosure_counts']
    require(set(counts) == {'outer_plus', 'outer_minus'}, 'Unexpected finite lineage counts')
    require(all(type(v) is int and v >= 0 for v in counts.values()) and counts['outer_minus'] > 0, 'Invalid finite recurrence counts')
    return counts


def predict(root):
    """Read target-free inputs only, and execute the non-identifiability witness."""
    root = Path(root)
    contract = validate_contract(root, read_json(root/SUBDIR/'model_contract.json'))
    products = _dynamics(root)
    rows = []
    from matter1_metrology import frequency_from_ratio
    for scenario_id in ('baseline', 'early_loss'):
        trace = products[scenario_id+'_trace']
        counts = _counts(trace)
        cadence = Q(counts['outer_plus'], counts['outer_minus'])
        for lam_string in contract['map_family']['witness_values']:
            lam = rational(lam_string)
            g = lambda z: 1 + lam*Q(55-z, 54)
            require(g(55) == 1 and g(1) > 0, 'Cs normalization or positive-map witness failed')
            ratio = cadence*g(1)/g(55)
            # Pure unit conversion. No atomic uncertainty or calibration is invented.
            conversion = frequency_from_ratio(ratio, ratio_variance=None)
            rows.append({'scenario': scenario_id, 'lambda': lam_string,
                         'classification': 'unselected_observation_map_countermodel_not_atomic_prediction',
                         'trace_sha256': digest(trace), 'counts': counts,
                         'finite_cadence_ratio': str(cadence), 'Cs_gain': str(g(55)), 'H_gain': str(g(1)),
                         'mapped_ratio': str(ratio), 'conditional_unit_conversion': conversion,
                         'physical_standard_uncertainty_hz': None,
                         'atomic_map_status': 'unjustified; witness_of_missing_constraint'})
    require(rows[0]['mapped_ratio'] != rows[1]['mapped_ratio'], 'Countermodels do not separate outcomes')
    require(rows[0]['mapped_ratio'] != rows[2]['mapped_ratio'], 'Dynamic intervention has no mapped consequence')
    calibration = {'reference_hz': str(CS_HZ), 'reference_kind': 'exact_si_definition',
                   'realized_device_calibration': 'not_performed', 'fitted_parameters': []}
    # Bind the actual executable modules as well as the fixed model contract.
    # __file__ identifies the running engine even when --root is a disposable
    # data fixture; this does not read any evaluation or benchmark input.
    engine = [{ 'path': 'manual2/scripts/'+name,
                'sha256': hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()}
              for name in ('matter1_atomic.py', 'matter1_stateful.py', 'matter1_temporal.py',
                           'matter1_folding.py', 'matter1_metrology.py')]
    return {'schema_version': 1, 'profile': PROFILE,
            'status': 'prediction_objective_incomplete_observation_map_underdetermined',
            'model_contract_sha256': digest(contract),
            'engine_bindings': engine, 'calibration': calibration,
            'calibration_sha256': digest(calibration),
            'dependency_gates': contract['dependency_gates'],
            'source_bindings': contract['source_bindings'],
            'atomic_prediction': {'ratio': None, 'frequency_hz': None, 'transition_period_seconds': None,
                                  'standard_uncertainty_hz': None, 'admission_status': contract['admission_status']},
            'target_access': 'not_read', 'exposure': contract['exposure'],
            'countermodels': rows,
            'proof': {'fixed': ['finite histories within each scenario', 'Cs normalization', 'single map family for both Z values'],
                      'free_parameter': 'lambda in g_lambda(Z)',
                      'consequence': 'For positive cadence r, R_lambda=r*(1+lambda); any positive ratio is obtained by lambda=R/r-1. Cs calibration does not select lambda.',
                      'scope': 'non-identifiability from the presently established finite constraints, not proof that AOD cannot determine a ratio with additional atomic construction',
                      'minimum_extra_premise': 'A source-justified atomic configuration/update and observation rule fixing relative H/Cs phase or cycle gain independently of the tested H splitting.'}}


def validate_prediction(root, prediction):
    require(prediction == predict(root), 'Prediction record, target access, source, conversion or status differs')
    return prediction


def compare(prediction, target):
    """Evaluate unselected countermodel residuals without promoting them to predictions."""
    validate_target(target, allow_synthetic=True)
    require(prediction.get('status') == 'prediction_objective_incomplete_observation_map_underdetermined', 'Unsupported prediction status')
    require(prediction.get('target_access') == 'not_read', 'Prediction consumed evaluation target')
    require(prediction['atomic_prediction']['ratio'] is None and prediction['atomic_prediction']['frequency_hz'] is None, 'Unselected diagnostic cannot become atomic prediction')
    observed = rational(target['frequency_hz'])
    rows = []
    for row in prediction['countermodels']:
        require(row['classification'] == 'unselected_observation_map_countermodel_not_atomic_prediction', 'Countermodel promotion rejected')
        value = rational(row['conditional_unit_conversion']['frequency_hz'])
        rows.append({'scenario': row['scenario'], 'lambda': row['lambda'],
                     'classification': 'diagnostic_residual_for_unselected_map_not_empirical_test_of_AOD',
                     'frequency_hz': str(value), 'observed_frequency_hz': str(observed),
                     'residual_hz': str(value-observed), 'relative_residual': str((value-observed)/observed),
                     'standardized_residual': None,
                     'uncertainty_status': 'incomplete; no justified atomic-map uncertainty or joint covariance'})
    return {'schema_version': 1, 'profile': PROFILE, 'prediction_sha256': digest(prediction),
            'evaluation_sha256': digest(target), 'classification': 'retrospective_underdetermination_diagnostic',
            'atomic_prediction_test_status': 'not_executed_no_selected_atomic_map',
            'atomic_empirical_score': None, 'observed_frequency_hz': target['frequency_hz'],
            'published_aggregate_standard_uncertainty_hz': target['standard_uncertainty_hz'],
            'prediction_measurement_covariance_hz2': target['prediction_measurement_covariance_hz2'],
            'covariance_status': target['covariance_status'], 'rows': rows,
            'frequency_period_tests_independent': False,
            'selection_policy': 'No countermodel selected, fitted or retuned using these residuals.'}


def obligations(prediction):
    return {'schema_version': 1, 'objective_status': 'incomplete', 'items': [
        {'id': 'ATOM-01', 'status': 'unresolved', 'premise': 'Cs/H hyperfine state configurations under one AOD construction',
         'source_labels': ['eq:key-proposed-admitted-trace'],
         'evidence_needed': 'Retained state-specific construction and support-accessor witnesses; external I,J,F labels alone are insufficient.'},
        {'id': 'ATOM-02', 'status': 'unresolved', 'premise': 'Atomic update and cycle/phase observation law',
         'source_labels': ['eq:wave-update-trace', 'eq:rcd-duration-participation', 'eq:cadence-ratio'],
         'evidence_needed': 'Fix relative gain across Cs/H without tested H splitting; discriminate the explicit lambda countermodels.',
         'countermodel_prediction_sha256': digest(prediction)},
        {'id': 'ATOM-03', 'status': 'unresolved', 'premise': 'Physical realization/uncertainty and common-reference covariance',
         'evidence_needed': 'Applicable calibration, parameter/model uncertainty and shared-reference budget; partial conditional reports remain possible.'},
        {'id': 'ATOM-04', 'status': 'unresolved', 'premise': 'Independent empirical evaluation design',
         'evidence_needed': 'Eligible additional target/condition with exposure and selection history; known H is retrospective.'},
    ], 'source_bindings': prediction['source_bindings'],
        'atomic_word_scope': 'Main atomic H1 events are indivisible encoded distinction events; that terminology alone does not identify an atomic spectroscopy state.',
        'next_experiment': 'Supply one target-independent atomic state-to-observable law; execute it on both species, freeze its prediction artifact, then score H without retuning.'}


def generated_products(root):
    root = Path(root)
    # Execute prediction before either external evaluation file is read.
    prediction = predict(root)
    target = validate_target(read_json(root/SUBDIR/'evaluation_target.json'))
    comparison = compare(prediction, target)
    external = benchmark(read_json(root/SUBDIR/'benchmark_inputs.json'))
    ledger = obligations(prediction)
    report = {'schema_version': 1, 'profile': PROFILE, 'status': 'scoped_attempt_and_benchmark_executed',
              'atomic_prediction_objective': 'incomplete', 'native_atomic_admission': 'pending',
              'countermodel_count': len(prediction['countermodels']), 'benchmark_rows': len(external['rows']),
              'prediction_sha256': digest(prediction), 'comparison_sha256': digest(comparison),
              'benchmark_sha256': digest(external), 'obligations_sha256': digest(ledger),
              'PRED_01': 'incomplete; executable underdetermination evidence',
              'PRED_02': 'Cs normalization and no target read verified for diagnostic; atomic map unresolved',
              'PRED_03': 'separate target-independent artifact; no atomic point prediction',
              'PRED_04': 'separate diagnostic residuals; atomic uncertainty/score unresolved',
              'PRED_05': 'finite-model intervention changes diagnostic observable; atomic identification unresolved'}
    return dict(zip(OUTPUTS, (prediction, comparison, external, ledger, report)))


def verify(root):
    root = Path(root)
    products = generated_products(root)
    for name, value in products.items():
        try:
            blob = (root/SUBDIR/name).read_bytes()
        except OSError as exc:
            raise ValidationError(f'Missing atomic output: {name}') from exc
        require(blob == canonical(value), f'{name} differs; verifier does not regenerate or repair')
    return products['atomic_report.json']
