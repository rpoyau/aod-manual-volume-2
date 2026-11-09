"""Matter I applications of the pinned M3 observer and comparison interfaces.

The existing R03 law and four unselected atomic countermodels are replayed.
Historical reductions and incomplete isotope inputs do not supply an atomic law.
"""
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

import matter1_atomic as atomic
import matter1_m3_observation as observation
import matter1_m3_metrology_vendor as vendor
from matter1_m3_metrology_vendor import verify_vendor

ROOT = Path(__file__).resolve().parents[2]
DATA = Path('manual2/data/m1/m3_metrology')
OUTPUTS = ('prediction.json', 'comparison.json', 'metrology_report.json')
PROFILE = 'matter1:m3-metrology:applications:v1'
INPUTS_SHA256 = '01875e3e7efe4ee834916710040098742f58c8428dd39ae712af0fd154b87d1c'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _api(root, temporal_api=None, metrology_api=None):
    if metrology_api is None:
        return vendor.metrology(root, temporal_api)
    return vendor.validate_api(metrology_api, root, temporal_api)


def _native_case(root, case, api):
    original = observation.default_input(root, case)
    context = observation.observation_context(root, original, api.t)
    prediction = api.t.predict(context)
    binding = api.bind_native_prediction(prediction, context)
    native = prediction['complete_temporal_record']
    observations = {}
    for channel in ('compared', 'reference'):
        # These are projections of the whole replayed temporal artifact, not a
        # second observation law or an independently authenticated experiment.
        observations[channel] = {'kind': 'native_reclosure_count',
            'channel': channel, 'count': native['counts'][channel],
            'window': native['window'], 'scope': native['native_scope'],
            'prediction_sha256': binding['prediction_sha256']}
    return {'original_input': original, 'native_binding': binding,
            'context_sha256': digest(api.t.plain(asdict(context))),
            'population_size': len(context.population), 'pending_count': len(context.pending),
            'native_observations': observations,
            'conditional_outputs': {k: v['value'] for k, v in prediction['mapped']['outputs'].items()},
            'physical_elapsed_seconds': None, 'physical_half_life': None}


def predict(root=ROOT, *, temporal_api=None, metrology_api=None):
    """Execute existing recipes without reading an evaluation target."""
    root = Path(root)
    api = _api(root, temporal_api, metrology_api)
    native = {case: _native_case(root, case, api)
              for case in observation.r.default_contract(root)['cases']}
    diagnostics = atomic.predict(root)
    windows = {}
    for scenario in ('baseline', 'early_loss'):
        path = root/'manual2/data/m1/stateful'/(scenario+'_trace.json')
        trace = atomic.read_json(path)
        require(all(row['trace_sha256'] == atomic.digest(trace)
                    for row in diagnostics['countermodels'] if row['scenario'] == scenario),
                'Persisted diagnostic trace differs from executed prediction')
        windows[scenario] = trace['summary']['window']
    return {'schema_version': 1, 'profile': PROFILE, 'vendor': verify_vendor(root),
            'application_code_sha256': sha(Path(__file__)),
            'loader_code_sha256': sha(Path(vendor.__file__)),
            'target_access': 'not_read', 'native_r03': native,
            'atomic_diagnostics': diagnostics, 'diagnostic_windows': windows,
            'physical_atomic_prediction': None,
            'scope': 'Existing declared recipes and unselected observation-map countermodels; no isotope gain selected.'}


def _unknown(reason):
    return {'kind': 'unknown', 'reason': reason}


def _influence(identity, reason, sources):
    return {'id': identity, 'stage': 'setup', 'mechanism': reason, 'source_ids': sources,
            'correction': _unknown(reason), 'residual_uncertainty': _unknown(reason),
            'evaluation_method': 'unknown', 'conditions': _unknown(reason),
            'materiality': {'kind': 'unresolved', 'reason': reason}}


def assessment_record(prediction, row, target, api):
    """Bind supplied diagnostic/evaluation endpoints; never fit or correct them."""
    identity = row['scenario']+':lambda='+row['lambda']
    model = api.m.source('matter1:diagnostic:'+identity, 'model', {
        'prediction_sha256': digest(prediction), 'countermodel': deepcopy(row),
        'comparison_quantities': {'frequency': {'kind': 'oscillator_phase_advance', 'unit': 'Hz',
            'value': str(Q(row['conditional_unit_conversion']['frequency_hz']))}}})
    evaluation = api.m.source('matter1:historical-H-target', 'evaluation', {
        'target': deepcopy(target), 'comparison_quantities': {'frequency': {
            'kind': 'oscillator_phase_advance', 'unit': 'Hz', 'value': str(Q(target['frequency_hz']))}}})
    definition = api.m.source('SI:Cs133-definition', 'definition', {'defining_frequency_hz': api.CS})
    source_ids = [model['id'], evaluation['id']]
    influences = [
        _influence('atomic-observation-law', 'No justified atomic state-to-observable law selects this countermodel.', [model['id']]),
        _influence('historical-window-match', 'Simulation cuts and historical apparatus interval are unmatched; no physical transfer is asserted.', source_ids),
        _influence('joint-uncertainty', 'Model, realization and shared-reference covariance are incomplete.', source_ids),
        {'id': 'published-target-reduction', 'stage': 'input',
         'mechanism': 'Published unperturbed H frequency already includes the source reduction.',
         'source_ids': [evaluation['id']],
         'correction': {'kind': 'not_applied', 'reason': 'Use the already corrected published endpoint without adding its corrections again.'},
         'residual_uncertainty': {'kind': 'source_reported_uncertainty',
             'value': str(Q(target['standard_uncertainty_hz'])), 'unit': 'Hz',
             'category_or_coverage_status': target['source_uncertainty_scope']},
         'evaluation_method': 'unknown',
         'conditions': _unknown('Historical measurement conditions are not the simulation preparation.'),
         'materiality': {'kind': 'retained', 'reason': 'Retain the published uncertainty separately from the missing joint budget.'}}]
    record = {'id': 'matter1:assessment:'+identity, 'source_id': 'matter1:assessment-declaration:'+identity,
        'sources': [model, evaluation, definition],
        'measurand': 'retrospective diagnostic frequency versus published H endpoint; physical correspondence unestablished',
        'kind': 'oscillator_phase_advance', 'unit': 'Hz',
        'coordinate': 'declared_model_commit_index', 'epoch': 'declared_simulation_origin',
        'window': prediction['diagnostic_windows'][row['scenario']],
        'reflection_duration': _unknown('No reflection-duration-to-observation map is supplied.'),
        'prediction': {'value': str(Q(row['conditional_unit_conversion']['frequency_hz'])),
            'source_id': model['id'], 'quantity_id': 'frequency', 'dependency_ids': [definition['id']]},
        'comparison': {'value': str(Q(target['frequency_hz'])), 'source_id': evaluation['id'],
            'quantity_id': 'frequency', 'dependency_ids': [definition['id']]},
        'reference_role': 'reference_dependent_evaluation', 'influences': influences}
    declaration = {k: deepcopy(v) for k, v in record.items() if k not in ('source_id', 'sources')}
    source = api.m.source(record['source_id'], 'model', {'comparison_assessment': declaration})
    record['sources'].append(source)
    return record, {s['id']: s for s in record['sources']}


def _comparison(root, prediction, api, evaluation_target=None):
    target = atomic.read_json(Path(root)/atomic.SUBDIR/'evaluation_target.json') if evaluation_target is None else deepcopy(evaluation_target)
    atomic.validate_target(target, allow_synthetic=evaluation_target is not None)
    metadata = deepcopy(target)
    if evaluation_target is not None and target['classification'] == 'synthetic_evaluation_mutation':
        for key in ('classification', 'frequency_hz', 'standard_uncertainty_hz'):
            metadata[key] = atomic.default_target()[key]
    require(canonical(metadata) == canonical(atomic.default_target()),
            'Evaluation metadata differs from the retained typed target')
    rows = []
    for row in prediction['atomic_diagnostics']['countermodels']:
        record, trusted = assessment_record(prediction, row, target, api)
        rows.append({'scenario': row['scenario'], 'lambda': row['lambda'],
            'classification': 'retrospective_unselected_countermodel_diagnostic',
            'historical_window_match': 'unestablished',
            'record_window_role': 'simulation_window_only; historical measurement has no matched native-cut window',
            'record': record, 'assessment': api.assess_comparison(record, trusted)})
    return {'schema_version': 1, 'profile': PROFILE, 'prediction_sha256': digest(prediction),
            'evaluation_target': target, 'evaluation_sha256': digest(target), 'rows': rows,
            'model_selection': 'none; no gain selected or retuned',
            'atomic_empirical_score': None, 'physical_atomic_prediction': None,
            'independent_physical_validation': False,
            'scope': 'Exact residual and metadata assessment; historical applicability and complete joint uncertainty remain unresolved.'}


def compare(root, prediction, *, temporal_api=None, metrology_api=None, evaluation_target=None):
    api = _api(root, temporal_api, metrology_api)
    replayed = predict(root, temporal_api=api.t, metrology_api=api)
    require(canonical(prediction) == canonical(replayed), 'Metrology prediction differs from original-input replay')
    return _comparison(root, replayed, api, evaluation_target)


def application_inputs(root=ROOT):
    path = Path(root)/DATA/'application_inputs.json'
    require(sha(path) == INPUTS_SHA256, 'Metrology application inputs changed')
    data = json.loads(path.read_text())
    for name, expected in data['livermorium']['source_files'].items():
        require(sha(Path(root)/name) == expected, 'Livermorium source bytes changed: '+name)
    return data


def isotope_inputs(root=ROOT):
    inputs = application_inputs(root)
    missing = ['prepared_state_and_dynamics_recipe', 'native_to_observable_map',
               'source_bound_transition_target_and_apparatus', 'realization_and_joint_uncertainty']
    deferred = {name: {'status': 'missing_input', 'missing': missing,
                      'frequency_hz': None, 'physical_prediction': None}
                for name in inputs['deferred_isotopes']}
    source = inputs['livermorium']
    text = (Path(root)/'manual2/data/m1/isotopes/sources/gates2024.txt').read_text()
    rows = []
    for event in source['events']:
        require(event['text_witness'] in text, 'Lv interval source witness missing')
        interval = Q(event['interval'])/1000
        require(interval > 0, 'Positive published event interval required')
        rows.append({**deepcopy(event), 'interval_seconds': str(interval),
            'origin': source['origin'], 'timestamp_origin': source['origin'],
            'classification': 'published_implantation_to_decay_interval',
            'transcription_status': 'source_bound_exact_decimal_reduction',
            'm3_event_timing_status': 'missing_input',
            'missing': ['actual_timestamp_resolution', 'detector_timebase_calibration'],
            'resolution': None, 'timebase_calibration': 'unknown',
            'timing_uncertainty': 'unknown', 'lifetime_prediction': None})
    return {'deuterium_tritium': deferred, 'livermorium': {
        'source_files': source['source_files'], 'events': rows,
        'selection': source['selection'], 'selection_conditions': source['selection_conditions'],
        'transport': source['transport'], 'detector': source['detector'],
        'digitizer_limit': source['digitizer_limit'], 'formation_timestamp_inferred': False,
        'half_life_inferred_from_two_intervals': False, 'nuclear_dynamics': 'not_implemented'}}


def _products(root=ROOT, *, temporal_api=None, metrology_api=None):
    root = Path(root)
    api = _api(root, temporal_api, metrology_api)
    prediction = predict(root, temporal_api=api.t, metrology_api=api)
    comparison = _comparison(root, prediction, api)  # Target first read after the complete prediction exists.
    hydrogen = api.load_profile('hydrogen')
    cesium = api.load_profile('cesium')
    result = {'schema_version': 1, 'profile': PROFILE,
        'prediction_sha256': digest(prediction), 'comparison_sha256': digest(comparison),
        'vendor_binding_sha256': vendor.BINDING_SHA256, 'application_inputs_sha256': INPUTS_SHA256,
        'native_r03_cases': list(prediction['native_r03']), 'atomic_diagnostic_count': len(comparison['rows']),
        'hydrogen': {name: api.reduce_hydrogen(hydrogen, name) for name in ('table_iv', 'table_vi', 'published_mean')},
        'cesium': {name: api.reduce_cesium(cesium, name) for name in ('August2013', 'typical_Table1')},
        'isotope_applications': isotope_inputs(root),
        'physical_calibration': 'not established', 'independent_physical_prediction': False,
        'atomic_prediction_objective': 'incomplete',
        'complete_physical_uncertainty': deepcopy(api.UNKNOWN),
        'historical_consumer_recovery': 'not claimed; this application profile is new',
        'preserved_applications': ['R02 constructed coupling', 'R03 witnessed retention',
                                   'Fl-286/Fl-289 common-law investigation', 'Og-294 control']}
    return dict(zip(OUTPUTS, (prediction, comparison, result)))


def report(root=ROOT, *, temporal_api=None, metrology_api=None):
    """Complete coupled artifacts for vendored versus actual-upstream comparison."""
    return _products(root, temporal_api=temporal_api, metrology_api=metrology_api)


def generate(root=ROOT, output_root=None):
    destination = Path(root if output_root is None else output_root)/DATA
    products = report(root)
    destination.mkdir(parents=True, exist_ok=True)
    for name, value in products.items():
        (destination/name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')
    return {'status': 'generated', 'outputs': list(OUTPUTS)}


def verify(root=ROOT):
    root = Path(root)
    expected = report(root)
    require({p.name for p in (root/DATA).iterdir()} == set(OUTPUTS)|{'application_inputs.json'},
            'Metrology application output inventory differs')
    for name, value in expected.items():
        require(canonical(json.loads((root/DATA/name).read_text())) == canonical(value),
                'Stored metrology artifact differs from original-input replay: '+name)
    return {'status': 'PASS_M3_METROLOGY_APPLICATIONS', 'profile': PROFILE,
            'outputs': {name: sha(root/DATA/name) for name in OUTPUTS},
            'native_cases': 5, 'atomic_diagnostics': 4, 'physical_calibration': 'not established',
            'independent_physical_prediction': False}
