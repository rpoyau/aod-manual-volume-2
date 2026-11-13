"""Typed M3 observation of the unchanged R03 finite retention protocol.

All native objects come from replaying the original R03 contract and choices.
The one-cycle gains are stipulated; the resulting SI expressions do not identify
a physical clock, decay, daughter or half-life.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import fields, is_dataclass, asdict
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

import matter1_witnessed_retention as r
from matter1_m3 import temporal, verify_vendor, VENDOR

ROOT = Path(__file__).resolve().parents[2]
DATA = Path('manual2/data/m1/m3_observation')
OUTPUTS = ('observation_report.json',)
PROFILE = 'matter1:r03:m3-observation:v1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def default_input(root=ROOT, case='burden', prefix='++', reverse_extra=0):
    root = Path(root)
    r.verify_sources(root)
    verify_vendor(root)
    return {'schema': PROFILE, 'contract': r.default_contract(root), 'case': case,
            'retained_prefix': prefix, 'reverse_extra': reverse_extra,
            'endpoint': 'third prepared decision before its selected outcome',
            'sources': {'retention_code_sha256': sha(root/'manual2/scripts/matter1_witnessed_retention.py'),
                        'native_code_sha256': r.NATIVE_SHA,
                        'adapter_code_sha256': sha(Path(__file__)),
                        'vendor_binding_sha256': sha(root/VENDOR/'binding.json')}}


def validate_input(root, original):
    require(isinstance(original, dict), 'Independent original input is required')
    require(original.get('case') in r.default_contract(root)['cases'], 'Undeclared R03 case')
    require(original.get('retained_prefix') in ('++', '+-', '-+', '--'), 'Two actual retained choices required')
    require(type(original.get('reverse_extra')) is int and original['reverse_extra'] in (0, 1),
            'Declared directional control required')
    expected = default_input(root, original['case'], original['retained_prefix'], original['reverse_extra'])
    require(canonical(original) == canonical(expected), 'Original R03 observation inputs changed')


def _transport(value, native):
    """Transport identical native dataclasses across isolated module identities."""
    if is_dataclass(value):
        cls = getattr(native, type(value).__name__, None)
        require(cls is not None and is_dataclass(cls)
                and tuple(f.name for f in fields(cls)) == tuple(f.name for f in fields(value)),
                'Native record has no exact typed transport')
        return cls(**{f.name: _transport(getattr(value, f.name), native) for f in fields(value)})
    if isinstance(value, tuple):
        return tuple(_transport(item, native) for item in value)
    if isinstance(value, list):
        return [_transport(item, native) for item in value]
    if isinstance(value, dict):
        return {key: _transport(item, native) for key, item in value.items()}
    return value


def _execute(root, original, api):
    validate_input(root, original)
    require(sha(Path(api.n.__file__)) == r.NATIVE_SHA, 'R03 and M3 native definitions differ')
    fixture = r.Fixture(deepcopy(original['contract']), original['case'])
    preparation = {'id': 'matter1:r03:committed-preparation:v1',
                   'parameters': {'original_contract_sha256': digest(original['contract']),
                       'execution_code_sha256': {name: original['sources'][name] for name in
                           ('retention_code_sha256', 'adapter_code_sha256')},
                       'case': original['case'], 'formation_event_count': fixture.formation_event_count,
                       'measurement_origin': fixture.measurement_origin,
                       'retained_prefix': original['retained_prefix'],
                       'reverse_extra': original['reverse_extra'],
                       'endpoint': original['endpoint']}}
    def population():
        return tuple(_transport(field.wave(), api.n) for field in
                     (fixture.candidate, fixture.reference, fixture.background)) + (
                         _transport(r.n.wave(fixture.parent_records), api.n),)
    def contacts():
        return tuple(_transport(event, api.n) for channel in fixture.channels.values() for event in channel.events)
    law = api.observation_law([api.domain_for(population(), contacts(), preparation,
                                tuple(original['contract']['horizon']['allowed_cut_window']))],
                law_id='matter1:r03:stipulated-cycle-equivalents:v1',
                compared_gain='1', reference_gain='1', coordinate='declared:r03:reference')
    for symbol in original['retained_prefix']:
        fixture.prepare_next(reverse_extra=original['reverse_extra'])
        fixture.retain(symbol)
    decision = fixture.prepare_next(reverse_extra=original['reverse_extra'])
    fixture.validate()
    waves = population(); events = contacts()
    a, b = waves[:2]; lo, hi = fixture.measurement_origin, fixture.clock.cut
    pair = tuple(event for event in events if (event.left, event.right) == (a.identity, b.identity))
    previous = api.TemporalInput(a, b, tuple(event for event in pair if event.committed <= lo),
                                (0, lo), biases=(Q(0), Q(0)), prior_lag=Q(0))
    previous_lag = Q(api.adapt(previous)['forward']['lag'])
    initial = tuple(Q(sum(trace.indices[-1] <= lo for trace in wave.returns[1:])) for wave in (a, b))
    record = api.TemporalInput(a, b, tuple(event for event in pair if lo < event.committed <= hi),
                              (lo, hi), biases=initial, prior_lag=previous_lag)
    pending = ()
    if fixture.background.pending is not None:
        pending = ({'wave_identity': waves[2].identity, 'kind': 'incomplete_return',
                    'committed_cut': fixture.background.pending['last_cut'],
                    'prefix_sha256': api.n.wave_prefix(waves[2], hi),
                    'payload': deepcopy(fixture.background.pending)},)
    dependencies = (api.m.source('matter1:r03:original-input', 'model', deepcopy(original)),
                    api.m.source('matter1:r03:committed-engine', 'model',
                        {'clock_events_sha256': digest(fixture.clock.events),
                         'responses_sha256': digest(fixture.responses),
                         'decision_sha256': digest(decision)}))
    context = api.ObservationContext(record, waves, events, preparation, pending, dependencies, law, previous)
    api.validate_observation_context(context)
    evidence = {'measurement_origin': lo, 'endpoint_cut': hi,
        'clock_events': deepcopy(fixture.clock.events), 'responses': deepcopy(fixture.responses),
        'pending_decision': deepcopy(decision),
        'parent_completed_returns_after_origin': len(fixture.parent_records)-original['contract']['formation_returns']['outer_parent'],
        'retained_inner_identity': fixture.candidate.identity,
        'native_transport': 'field-for-field dataclass transport between byte-identical native definitions',
        'native_source_sha256': r.NATIVE_SHA}
    return context, evidence


def observation_context(root, original, temporal_api=None):
    api = temporal(root) if temporal_api is None else temporal_api
    return _execute(Path(root), original, api)[0]


def predict(root, original, temporal_api=None):
    api = temporal(root) if temporal_api is None else temporal_api
    context, evidence = _execute(Path(root), original, api)
    return {'profile': PROFILE, 'original_input_sha256': digest(original),
        'complete_observation_context': api.plain(asdict(context)),
        'execution': evidence, 'prediction': api.predict(context),
        'scope': {'native': 'admitted generic R03 wave/contact records under declared preparation',
                  'observation': 'stipulated one cycle per reclosure; no physical calibration',
                  'physical_elapsed_seconds': None, 'physical_decay': None,
                  'daughter_identity': None, 'physical_half_life': None}}


def replay(root, artifact, *, original_context, temporal_api=None):
    regenerated = predict(root, original_context, temporal_api)
    require(canonical(artifact) == canonical(regenerated), 'Whole observation artifact differs from original-input replay')
    return regenerated


def report(root=ROOT, temporal_api=None):
    root = Path(root)
    api = temporal(root) if temporal_api is None else temporal_api
    cases = {case: predict(root, default_input(root, case), api) for case in r.default_contract(root)['cases']}
    baseline = cases['burden']['prediction']['mapped']['outputs']
    require(all(row['prediction']['complete_temporal_record']['counts'] == {'compared': 2, 'reference': 3}
                for row in cases.values()), 'R03 temporal count projection changed')
    return {'schema_version': 1, 'profile': PROFILE, 'vendor': verify_vendor(root),
            'cases': cases, 'conditional_outputs': {name: item['value'] for name, item in baseline.items()},
            'physical_uncertainty': 'unknown',
            'claims': 'Exact R03 native input replay and typed conditional observation; no new retention law or isotope identification'}


def generate(root=ROOT, output_root=None):
    root = Path(root)
    destination = root if output_root is None else Path(output_root)
    path = destination/DATA/OUTPUTS[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report(root), indent=2, sort_keys=True)+'\n')
    return {'status': 'generated', 'output': str(path)}


def verify(root=ROOT):
    root = Path(root)
    path = root/DATA/OUTPUTS[0]
    require({item.name for item in (root/DATA).iterdir()} == set(OUTPUTS), 'Observation output inventory differs')
    data = json.loads(path.read_text())
    require(canonical(data) == canonical(report(root)), 'Stored observation report differs from original-input replay')
    return {'status': 'PASS_M3_OBSERVATION', 'profile': PROFILE, 'cases': 5,
            'report_sha256': sha(path), 'physical_calibration': 'not established'}
