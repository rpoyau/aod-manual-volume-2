"""Bound R02 aggregate-field execution and a separate paired construction.

The original engine and native admission source are preserved byte-for-byte.
The application supplies strict original-context replay, explicit preparations,
and the capacity/loss obstruction; it does not add a nuclear retention law.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile

from matter1_atomic import canonical, read_json, require

DATA = Path('manual2/data/m1/constructed_coupling')
PROFILE = 'matter1:constructed-coupling-r02:v1'
PAIRED_PROFILE = 'matter1:paired-aggregate-configurations:v1'
MEMBERS_SHA256 = '72f9f2a84ef2280a9b8d3cd52e6d8c1114da615bfb2c91831501505209c8ea4b'
PACKET_NOTE_SHA256 = 'c1fac55a2de9c924ba4c5febf4d3475b1b60ecf1be818e4a298baebe80cda4bd'
R02_CASES = ('baseline', 'add_346_to_parent', 'same_addition_feedback_disabled', 'one_fewer_346_constituent')
CASE_IDS = tuple('r02/'+case for case in R02_CASES) + ('configurations/Fl-286', 'configurations/Fl-289')
ORIGINAL_FILES = ('checks.json', 'constructed_state.json', 'closures.csv', 'windowed_relations.csv',
    'directional_rd_rcd.csv', 'atomic_and_hinge_events.jsonl.gz', 'tick_events.jsonl.gz',
    'click_and_rcd_events.jsonl.gz', 'pressure_events.jsonl.gz', 'nonnegative_load_terms.jsonl.gz',
    'outer_return_witnesses.jsonl.gz', 'terminal_survival.csv', 'prediction.json')
CASE_FILES = ORIGINAL_FILES + ('input_context.json', 'application_binding.json')
OUTPUTS = tuple(case+'/'+name for case in CASE_IDS for name in CASE_FILES) + ('constructed_report.json',)
_MODULES = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def check_sources(root):
    root = Path(root)
    packet = root/DATA/'source_packet'
    require(sha(packet/'ORIGINAL_MEMBER_BINDINGS.json') == MEMBERS_SHA256, 'R02 member authority changed')
    require(sha(packet/'PACKET_NOTE.md') == PACKET_NOTE_SHA256, 'R02 packet scope changed')
    members = read_json(packet/'ORIGINAL_MEMBER_BINDINGS.json')
    require({str(p.relative_to(packet)) for p in packet.rglob('*') if p.is_file()} ==
            set(members['members']) | {'ORIGINAL_MEMBER_BINDINGS.json', 'PACKET_NOTE.md'},
            'R02 selected packet inventory differs')
    for name, binding in members['members'].items():
        path = packet/name
        require(path.stat().st_size == binding['bytes'] and sha(path) == binding['sha256'], 'R02 original member changed: '+name)
    manifest = read_json(packet/'BUNDLE_MANIFEST.json')['sha256']
    for name, binding in members['members'].items():
        if name != 'BUNDLE_MANIFEST.json':
            require(manifest[binding['original_archive_member']] == binding['sha256'], 'Original archive membership differs')
    bindings = read_json(packet/'source_bindings.json')
    for name, expected in bindings['sha256'].items():
        require(sha(packet/name) == expected, 'R02 bound input changed: '+name)
        if name.startswith(('upstream/sections/', 'upstream/appendices/')):
            require(sha(root/name.removeprefix('upstream/')) == expected, 'R02 mathematical source differs from application')
    require(sha(root/'manual2/scripts/matter1_model.py') == bindings['sha256']['inputs/matter1_model.py'], 'R02 inventory source differs')
    return {'member_binding_sha256': MEMBERS_SHA256, 'selected_original_members': len(members['members']),
            'bound_inputs': len(bindings['sha256']), 'original_archive': members['archive'],
            'archive_verification_scope': 'selected member bytes and original manifest bindings; full archive is not present',
            'engine_sha256': members['members']['constructed_coupling.py']['sha256'],
            'native_sha256': bindings['sha256']['upstream/manual/scripts/aod_native_closure_wave.py']}


def engine_module(root):
    """Load the bound native source, never a same-named ambient module."""
    root = Path(root).resolve()
    check_sources(root)
    key = str(root)
    if key not in _MODULES:
        packet = root/DATA/'source_packet'
        tag = hashlib.sha256(key.encode()).hexdigest()[:16]
        def load(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            return module
        native = load('_matter1_r02_native_'+tag, packet/'upstream/manual/scripts/aod_native_closure_wave.py')
        previous = sys.modules.get('aod_native_closure_wave')
        paths = list(sys.path)
        try:
            sys.modules['aod_native_closure_wave'] = native
            module = load('_matter1_r02_engine_'+tag, packet/'constructed_coupling.py')
        finally:
            sys.path[:] = paths
            if previous is None:
                sys.modules.pop('aod_native_closure_wave', None)
            else:
                sys.modules['aod_native_closure_wave'] = previous
        require(module.n is native, 'Native admission import was substituted')
        _MODULES[key] = module
    return _MODULES[key]


def default_contract(root):
    root = Path(root)
    bindings = check_sources(root)
    return {'schema_version': 1, 'profile': PROFILE, 'paired_profile': PAIRED_PROFILE,
        'source_bindings': bindings,
        'application_source_sha256': {name: sha(root/'manual2/scripts'/name) for name in (
            'matter1_constructed_coupling.py', 'generate_matter1_constructed_coupling.py', 'verify_matter1_constructed_coupling.py')},
        'r02_contract': read_json(root/DATA/'source_packet/contract.json'),
        'preparations': [{'id': label+':ground', 'symbol': label.split('-')[0], 'Z': z, 'A': a, 'N': a-z,
            'state': 'externally selected ground-state label; physical state identification unproved',
            'preparation': 'ordered distinct proton-facing then neutron-facing two-return constituent seeds; declared outer fold; fixed reference and background seeds',
            'physical_preparation': None, 'internal_nuclear_couplings': None,
            'operative_couplings': 'same R02 five-aggregate-field directed channel law',
            'comparison_status': 'retrospective; no measured lifetime is read'}
            for label,z,a in (('Fl-286',114,286), ('Fl-289',114,289), ('Og-294',118,294))],
        'common_law': {'id': 'matter1-constructed-coupling-v1', 'engine_sha256': bindings['engine_sha256'],
            'update': 'R02 immutable next-deadline inverse-pressure sequencer',
            'capacity': None, 'retention': None, 'loss': None,
            'normalization': 'native RCD times absolute committed emission lag; no R03 unit imported',
            'reference': 'R02 reference 3:3:6 field; not an identified atomic clock'},
        'target_policy': 'No lifetime, hazard, per-isotope multiplier, fitted capacity or evaluation catalogue is read by execution.',
        'Fl-298': 'unscored; outside this paired investigation'}


def validate_contract(root, contract):
    require(canonical(contract) == canonical(default_contract(root)), 'Constructed-coupling original input context changed')
    return contract


def contexts(contract):
    result = {}
    for case in R02_CASES:
        result['r02/'+case] = {'profile': PROFILE, 'case': case,
            'contract': deepcopy(contract['r02_contract']), 'preparation': contract['preparations'][2]}
    for preparation in contract['preparations'][:2]:
        declared = deepcopy(contract['r02_contract'])
        declared.update(Z=preparation['Z'], N=preparation['N'], selected_label=preparation['id']+' declared aggregate')
        result['configurations/'+preparation['id'].split(':')[0]] = {'profile': PAIRED_PROFILE,
            'case': 'baseline', 'contract': declared, 'preparation': preparation}
    return result


def case_summary(engine):
    c = sys.modules[engine.__class__.__module__]
    counts = [row for row in c.window_rows(engine) if row['kind'] == 'cumulative'][-1]
    parent = engine.fields['P']
    lo = parent.returns[1]
    by_id = {packet['id']: packet for packet in engine.packets}
    terms = [row for row in engine.loads if lo < row['cut'] <= engine.end]
    signed = sum(row['rho']*by_id[row['contact_id']]['lag_at_emission'] for row in terms)
    burden = sum(row['nonnegative_term'] for row in terms)
    return {'counts': counts, 'parent_return_cuts': parent.returns[2:],
        'parent_formation_return_ids': [t.return_id for t,_,_ in parent.records[:2]],
        'parent_identity': parent.identity, 'scope_map_sha256': c.digest(parent.occurrence_map),
        'branch_occurrences': parent.branch, 'structural_RD': parent.rd,
        'distinct_constituent_waves': len(parent.inner), 'evolving_aggregate_fields': len(engine.fields),
        'internal_nuclear_dynamics': None, 'directed_channels': [list(key) for key in sorted(engine.channels)],
        'signed_response_diagnostic': signed, 'nonnegative_burden': burden,
        'response_operands': 'same committed contact rho and lag as nonnegative_load_terms and click_and_rcd_events',
        'parent_hinges': sum(row['kind'] == 'hinge' for row in parent.actions),
        'parent_extra_dwell_events': 0,
        'parent_partial_return_atomic_traversals': max(0,len(parent.current_indices)-1) if parent.action>=0 else 0,
        'channel_ticks': len(engine.packets), 'channel_clicks': sum(not row['formation'] for row in engine.clicks),
        'pending_currents': len(engine.pending), 'parent_loss_witness': None,
        'reference_count_at_loss': None, 'ensemble_median': None, 'survival_probability': None,
        'finite_execution_status': 'horizon reached; loss observable undefined', 'physical_seconds': None,
        'capacity_countermodels': [{'capacity': str(capacity), 'residual': str(Fraction(burden)-capacity),
            'surplus': str(max(Fraction(0),Fraction(burden)-capacity))}
            for capacity in (Fraction(burden,2), Fraction(burden), Fraction(burden+1))],
        'capacity_countermodel_status': 'unselected algebraic alternatives on the identical committed trace'}


def write_case(root, context, destination):
    """Execute one explicit context; callers supply the independently retained input."""
    root, destination = Path(root), Path(destination)
    c = engine_module(root)
    engine = c.Engine(deepcopy(context['contract']), context['case']).run()
    checks = engine.validate()
    with tempfile.TemporaryDirectory(prefix='matter1-r02-case-') as temp:
        generated = Path(temp)
        prediction = c.export(engine, generated, checks)
        if context['profile'] == PAIRED_PROFILE:
            # The historical exporter names its fixed packet contract. Bind the
            # paired context explicitly without relabelling it as an R02 result.
            prediction['schema'] = 'matter1-paired-counted-construction-v1'
            prediction['source_contract_sha256'] = prediction.pop('contract_sha256')
            prediction['effective_contract_sha256'] = digest(context['contract'])
            prediction.pop('prediction_sha256')
            prediction['prediction_sha256'] = c.digest(prediction)
            c.write_json(generated/'prediction.json', prediction)
        (generated/'input_context.json').write_bytes(canonical(context))
        summary = case_summary(engine)
        binding = {'profile': context['profile'], 'input_context_sha256': sha(generated/'input_context.json'),
            'application_sha256': sha(Path(__file__)), 'source_bindings': check_sources(root),
            'effective_contract_sha256': digest(context['contract']), 'summary': summary,
            'file_sha256': {name: sha(generated/name) for name in ORIGINAL_FILES+('input_context.json',)}}
        (generated/'application_binding.json').write_bytes(canonical(binding))
        destination.mkdir(parents=True, exist_ok=True)
        for name in CASE_FILES:
            shutil.copyfile(generated/name, destination/name)
    del engine
    gc.collect()
    return summary


def verify_case(root, expected_context, destination, *, replay=True):
    destination = Path(destination)
    require({p.name for p in destination.iterdir()} == set(CASE_FILES), 'Incomplete or unexpected constructed case artifact')
    require((destination/'input_context.json').read_bytes() == canonical(expected_context), 'Case original input context differs')
    binding = read_json(destination/'application_binding.json')
    require(binding['application_sha256'] == sha(Path(__file__)), 'Case application source differs')
    require(binding['source_bindings'] == check_sources(root), 'Case source context differs')
    require(binding['effective_contract_sha256'] == digest(expected_context['contract']), 'Case effective contract differs')
    require(set(binding['file_sha256']) == set(ORIGINAL_FILES+('input_context.json',)), 'Case inventory differs')
    require(binding['input_context_sha256'] == sha(destination/'input_context.json'), 'Case input hash differs')
    for name, expected in binding['file_sha256'].items():
        require(sha(destination/name) == expected, 'Case artifact bytes changed: '+name)
    if replay:
        with tempfile.TemporaryDirectory(prefix='matter1-r02-replay-') as temp:
            write_case(root, expected_context, Path(temp))
            require(all((destination/name).read_bytes() == (Path(temp)/name).read_bytes() for name in CASE_FILES),
                    'Whole constructed artifact differs from original-context execution')
    return binding['summary']


def make_report(contract, summaries):
    baseline = summaries['r02/baseline']
    feedback = summaries['r02/add_346_to_parent']
    disabled = summaries['r02/same_addition_feedback_disabled']
    return {'profile': PROFILE, 'paired_profile': PAIRED_PROFILE, 'model_contract_sha256': digest(contract),
        'cases': summaries, 'Og-294_control': 'r02/baseline',
        'feedback_return_delays': [b-a for a,b in zip(baseline['parent_return_cuts'], feedback['parent_return_cuts'])],
        'feedback_disabled_restores_return_cuts': disabled['parent_return_cuts'] == baseline['parent_return_cuts'],
        'paired_configuration_changes': {
            'constituent_difference': summaries['configurations/Fl-289']['distinct_constituent_waves']-summaries['configurations/Fl-286']['distinct_constituent_waves'],
            'scope_map_changed': summaries['configurations/Fl-289']['scope_map_sha256'] != summaries['configurations/Fl-286']['scope_map_sha256'],
            'return_cuts_equal': summaries['configurations/Fl-289']['parent_return_cuts'] == summaries['configurations/Fl-286']['parent_return_cuts']},
        'R02_R03_adapter': {'status': 'not supplied; no combined model executed',
            'required': ['map actual aggregate state and evolving histories to retention kernel state',
                'bind committed contacts to a strictly later kernel decision',
                'justify aggregate burden normalization; square raw unit 5 does not transfer',
                'supply an independently justified aggregate capacity or capacity family selection',
                'bind reference returns and exposure; R02 reference RD 61 is not the R03 reference RD 5',
                'supply parent loss, retained/exposed inner lineage and any daughter transformation witness']},
        'scientific_obligations': {
            'SURV-ATOM-01': 'Generic constituent/fold recurrence and aggregate coupling admitted; physical isotope/state/preparation identification and resolved internal nuclear couplings absent.',
            'SURV-ATOM-02': 'Common finite update law executed; nuclear normalization/capacity/retention/loss law unresolved. Countermodels are unselected.',
            'SURV-ATOM-03': 'No parent loss endpoint, daughter transformation or reference-to-SI map supplied.',
            'SURV-ATOM-04': 'Physical preparation, discrepancy, realization, detection/censoring and dependent uncertainty remain unknown.'},
        'label_only_invariance': 'Executable matched-state control in test_matter1_constructed_coupling; labels never enter update operands.',
        'Fl-298': 'unscored', 'physical_half_life': None}


def generate(root, output_root=None):
    root = Path(root)
    destination = Path(output_root or root)/DATA
    contract = validate_contract(root, read_json(root/DATA/'model_contract.json'))
    destination.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for case, context in contexts(contract).items():
        print('executing constructed '+case, file=sys.stderr, flush=True)
        summaries[case] = write_case(root, context, destination/case)
        if case.startswith('r02/'):
            expected = read_json(root/DATA/'source_packet/BUNDLE_MANIFEST.json')['sha256']
            for name in ORIGINAL_FILES:
                require(sha(destination/case/name) == expected['results/'+context['case']+'/'+name],
                        'R02 original execution differs: '+case+'/'+name)
    report = make_report(contract, summaries)
    (destination/'constructed_report.json').write_bytes(canonical(report))
    return report


def verify(root, artifact_root=None):
    root = Path(root)
    destination = Path(artifact_root or root)/DATA
    contract = validate_contract(root, read_json(root/DATA/'model_contract.json'))
    actual = {str(p.relative_to(destination)) for p in destination.rglob('*') if p.is_file()
              and p.relative_to(destination).parts[0] != 'source_packet'
              and p.relative_to(destination) != Path('model_contract.json')}
    require(actual == set(OUTPUTS), 'Constructed output inventory incomplete or unexpected')
    for case, context in contexts(contract).items():
        verify_case(root, context, destination/case, replay=False)
    # Recreate all outputs only in a disposable directory. The input root and
    # supplied artifact tree remain untouched, including on rejection.
    with tempfile.TemporaryDirectory(prefix='matter1-r02-whole-replay-') as temp:
        generate(root, Path(temp))
        for name in OUTPUTS:
            require((destination/name).read_bytes() == (Path(temp)/DATA/name).read_bytes(),
                    'Whole constructed artifact differs from original-context execution: '+name)
    return {'profile': PROFILE, 'status': 'passed', 'outputs_verified': len(OUTPUTS),
            'r02_original_outputs_reproduced': 52, 'paired_configurations': ['Fl-286', 'Fl-289'],
            'larger_control': 'Og-294', 'physical_isotope_prediction': False}
