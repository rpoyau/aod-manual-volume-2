#!/usr/bin/env python3
"""Sequential v2 finite model. No atomic identification or seconds-per-cut.

One declared rule advances a retained path by one token per commit. Bound
contacts compare only committed recurrent prefixes. Their capacity response is
applied at the following cut, before either path/contact can advance. Loss is
absorbing in this version; it exposes inner provenance without deleting events.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
from pathlib import Path

import matter1_temporal as t
from matter1_folding import ValidationError, canonical_bytes, check_fixture, require, sha

DATA = Path('manual2/data/m1/stateful')
GEOMETRY = Path('manual2/data/m1/folding/two_square_fold.json')
STATUS = {'record_class': 'sequential_declared_finite_model',
          'execution_status': 'executed', 'native_admission_status': 'pending',
          'native_atomic_mapping_status': 'not_established', 'empirical_status': 'not_tested'}
SCENARIO_STATUS = {**STATUS, 'execution_status': 'declared_inputs'}
RULE = {
    'name': 'retention_gated_oriented_edge_sequencer_v2',
    'ordering': ['commit_previous_response', 'advance_retained_paths',
                 'advance_retained_contact', 'compare_committed_histories', 'queue_next_response'],
    'clock_domain': 'declared_model_commit_index',
    'structural_hinge': 'mandatory_turn_vertex_role_not_an_added_H1_edge',
    'optional_dwell': 'zero_edge_hinge_samples',
    'loss_rule': 'burden_exceeding_capacity_commits_absorbing_outer_plus_loss_at_next_cut',
    'readmission': 'not_implemented_no_automatic_readmission',
    'contact_rule': 'start_with_retained_returned_pair_bind_on_completion_only_if_recurrent',
    'burden_domain': 'declared_boundary_load',
    'support_map': 'contact_two_H1_edges_plus_one_structural_hinge_support_unit',
    'radiation_identification': 'not_asserted',
}
FILES = ('baseline_scenario.json', 'early_loss_scenario.json', 'baseline_trace.json',
         'early_loss_trace.json', 'stateful_report.json')


def default_scenario(root, fixture=None):
    root = t.repository_root(root)
    fixture = fixture if fixture is not None else t.read_json(root / GEOMETRY)
    return {
        'schema_version': 2, 'model_id': 'm1:sequential-fold-recurrence:v2',
        'statuses': dict(SCENARIO_STATUS), 'geometry_sha256': sha(fixture),
        'source_bindings': t.source_bindings(root), 'rule': deepcopy(RULE),
        'parameters': {
            'inner_cycles': 4, 'end_cut': 68,
            'outer_dwell_samples': {'outer_plus': 0, 'outer_minus': 1},
            'contact_completion_cuts': [36, 40, 44, 48, 52, 56, 60, 64],
            'phase_biases': {'outer_plus': '1/4', 'outer_minus': '-1/4'},
            'boundary_weight': '1', 'oriented_current': '1',
            'capacity_schedule': [{'from_cut': 0, 'capacity': '100'}],
        },
        'parameter_provenance': 'Declared finite scenario inputs; no isotope or frequency targets consumed.',
    }


def early_loss_scenario(root, fixture=None):
    scenario = default_scenario(root, fixture)
    scenario['parameters']['capacity_schedule'].append({'from_cut': 40, 'capacity': '2'})
    return scenario


def validate_scenario(scenario, fixture, root):
    t.keys(scenario, default_scenario(root, fixture), 'v2 scenario')
    require(type(scenario['schema_version']) is int and scenario['schema_version'] == 2, 'v2 schema')
    require(scenario['model_id'] == 'm1:sequential-fold-recurrence:v2', 'v2 model identity')
    require(scenario['statuses'] == SCENARIO_STATUS, 'v2 consumed statuses')
    check_fixture(fixture)
    require(scenario['geometry_sha256'] == sha(fixture), 'v2 geometry binding')
    require(scenario['source_bindings'] == t.source_bindings(root), 'v2 source bindings')
    require(scenario['rule'] == RULE, 'Unsupported v2 evolution rule')
    require(scenario['parameter_provenance'] == default_scenario(root, fixture)['parameter_provenance'], 'Parameter provenance')
    p = scenario['parameters']
    t.keys(p, default_scenario(root, fixture)['parameters'], 'v2 parameters')
    require(type(p['inner_cycles']) is int and p['inner_cycles'] == 4, 'Bound initial inner history')
    require(type(p['end_cut']) is int and 40 <= p['end_cut'] <= 256, 'Finite horizon 40..256')
    for field in ('outer_dwell_samples', 'phase_biases'):
        t.keys(p[field], ['outer_plus', 'outer_minus'], field)
    require(all(type(v) is int and 0 <= v <= 4 for v in p['outer_dwell_samples'].values()), 'Dwell domain 0..4')
    require(all(abs(t.rational(v)) <= 1 for v in p['phase_biases'].values()), 'Phase bias domain [-1,1]')
    require(0 < t.rational(p['boundary_weight']) <= 10, 'Positive finite boundary weight')
    require(t.rational(p['oriented_current']) in (Fraction(-1), Fraction(1)), 'Oriented current +/-1')
    cuts = p['contact_completion_cuts']
    require(isinstance(cuts, list) and 2 <= len(cuts) <= 64 and
            all(type(v) is int and 24 <= v <= p['end_cut'] for v in cuts), 'Contact schedule domain')
    require(cuts == sorted(set(cuts)) and all(b-a >= 3 for a, b in zip(cuts, cuts[1:])), 'Distinct nonoverlapping contact attempts')
    schedule = p['capacity_schedule']
    require(isinstance(schedule, list) and 1 <= len(schedule) <= 64, 'Capacity schedule domain')
    for item in schedule:
        t.keys(item, ['from_cut', 'capacity'], 'Capacity intervention')
        require(type(item['from_cut']) is int and 0 <= item['from_cut'] <= p['end_cut'], 'Capacity cut domain')
        require(0 <= t.rational(item['capacity']) <= 1000000, 'Capacity domain')
    times = [x['from_cut'] for x in schedule]
    require(times[0] == 0 and times == sorted(set(times)), 'Ordered capacity schedule starts at zero')
    return scenario


def _capacity(parameters, cut):
    return next(x['capacity'] for x in reversed(parameters['capacity_schedule']) if x['from_cut'] <= cut)


def _machine(name, chi, path, coords, start, dwell, fold):
    tokens = [('start', path[0])]
    for i, label in enumerate(path[1:], 1):
        tokens.append(('traversal', label))
        if i == (len(path)-1)//2:
            tokens.extend([('optional_hinge_dwell', label)] * dwell)
    scope, lineage = f'm1:finite:scope:{name}', f'm1:finite:lineage:{name}'
    wave = {'name': name, 'scope': scope, 'scale': 1, 'lineage': lineage,
            'identity': None, 'chirality': chi, 'returns': []}
    return {'wave': wave, 'tokens': tokens, 'cursor': 0, 'events': [], 'start': start,
            'cycle': 0, 'path': path, 'coords': coords, 'dwell': dwell, 'fold': fold,
            'retained': True, 'loss_cut': None, 'exposure': [], 'aborted': []}


def _advance(machine, cut):
    if not machine['retained']:
        return None, None
    wave = machine['wave']
    if machine['cursor'] == 0:
        machine['start'] = cut
    kind, label = machine['tokens'][machine['cursor']]
    event = {'event_id': f"{wave['name']}:cycle:{machine['cycle']}:event:{machine['cursor']}",
             'cut': cut, 'kind': kind, 'label': label, 'address': machine['coords'][label]}
    machine['events'].append(event)
    machine['cursor'] += 1
    completed = None
    if machine['cursor'] == len(machine['tokens']):
        trace = t.make_trace(f"{wave['name']}:cycle:{machine['cycle']}", wave['scope'], 1,
                             wave['lineage'], machine['path'], machine['coords'], machine['start'],
                             wave['chirality'], machine['dwell'], machine['fold'])
        require(trace['events'] == machine['events'], 'Return may only certify already committed events')
        t.validate_trace(trace, {'vertices': machine['coords'],
                                'outer_walk': machine['path'] if wave['chirality'] == 1 else list(reversed(machine['path']))})
        wave['returns'].append(trace)
        if wave['identity'] is None:
            wave['identity'] = 'wave:' + sha([wave['scope'], 1, wave['lineage'], trace['certificate']['return_id']])
        completed = trace['certificate']['return_id']
        machine['cycle'] += 1
        machine['cursor'] = 0
        machine['events'] = []
    return event, completed


def _snapshot(machine):
    wave = machine['wave']
    return {'name': wave['name'], 'identity': wave['identity'], 'scope': wave['scope'],
            'lineage': wave['lineage'], 'retained': machine['retained'], 'loss_cut': machine['loss_cut'],
            'completed_return_ids': [x['certificate']['return_id'] for x in wave['returns']],
            'partial_event_ids': [x['event_id'] for x in machine['events']],
            'next_token_index': machine['cursor'], 'inner_maps_sha256': sha(machine['fold']['inner_maps']),
            'exposure_sha256': sha(machine['exposure'])}


def simulate(scenario, fixture=None, root=None):
    """Execute a validated scenario cut by cut; no future event is precomputed."""
    root = t.repository_root(root or Path(__file__).resolve().parents[2])
    fixture = fixture if fixture is not None else t.read_json(root / GEOMETRY)
    validate_scenario(scenario, fixture, root)
    p = scenario['parameters']
    # These initial histories end at 19. They are committed inputs to the fold at 20.
    inners = [t.make_wave(name, ['u','v','w','z','u'],
                         {'u':'0000','v':'1000','w':'1100','z':'0100'}, 0, 0, 4, chi)
              for name, chi in (('inner_minus', 1), ('inner_plus', -1))]
    start = 1 + max(w['returns'][-1]['events'][-1]['cut'] for w in inners)
    machines = [_machine(name, chi, fixture['outer_walk'] if chi == 1 else list(reversed(fixture['outer_walk'])),
                         fixture['vertices'], start, p['outer_dwell_samples'][name], t.fold_proposal(inners, name, fixture))
                for name, chi in (('outer_plus', 1), ('outer_minus', -1))]
    contacts, comparisons, responses, records, attempts = [], [], [], [], []
    pending_response = pending_contact = None
    duration = {'kind':'declared_additive_reflection_count', 'domain':t.DOMAIN,
                'forward_reflections':[1,1], 'reverse_reflections':[2,2]}
    response_model = {'response': {'boundary_weight': p['boundary_weight'], 'oriented_current': p['oriented_current'],
                                   'burden_domain': RULE['burden_domain'], 'retention_rule': RULE['loss_rule'],
                                   'route_destination': 'm1:v2:declared-excess-reservoir'}}
    previous_hash = sha({'initial_inner_histories': inners, 'start_cut': start})
    starts = {c-2: (i,c) for i,c in enumerate(p['contact_completion_cuts'])}
    for cut in range(start, p['end_cut'] + 1):
        applied, events, returned, contact_events = [], [], [], []
        if pending_response is not None:
            require(pending_response['committed_cut'] == cut, 'Response applies at strictly next cut')
            applied.append(pending_response['response_id'])
            if pending_response['outer_retention'] == 'lost_by_declared_capacity_rule':
                machine = machines[0]
                machine['retained'], machine['loss_cut'] = False, cut
                machine['exposure'] = deepcopy(machine['fold']['inner_maps'])
                if machine['events']:
                    machine['aborted'].append({'cut': cut, 'reason': 'retention_lost_before_completion',
                                               'committed_events': deepcopy(machine['events'])})
                machine['events'] = []
                machine['cursor'] = 0
            pending_response = None
        for machine in machines:
            event, rid = _advance(machine, cut)
            if event is not None:
                events.append(event)
            if rid is not None:
                returned.append(rid)
        waves = [m['wave'] for m in machines]
        retained = all(m['retained'] for m in machines)
        recurrent = all(len(w['returns']) >= 2 for w in waves)
        if cut in starts:
            index, end = starts[cut]
            ready = retained and all(w['returns'] for w in waves)
            attempt = {'contact_index':index, 'start_cut':cut, 'completion_cut':end,
                       'status':'started' if ready else 'unavailable_retention_or_return',
                       'reason': None if ready else 'both_retained_returned_lineages_required'}
            attempts.append(attempt)
            if ready:
                pending_contact = {'index':index, 'end':end, 'start':cut, 'events':[], 'attempt':attempt}
        if pending_contact is not None:
            if not retained:
                pending_contact['attempt']['status'] = 'cancelled_by_retention_loss'
                pending_contact['attempt']['reason'] = 'no_contact_after_loss'
                pending_contact = None
            else:
                i = cut - pending_contact['start']
                event = {'event_id':f"contact:{pending_contact['index']}:event:{i}", 'cut':cut,
                         'kind':'start' if i == 0 else 'traversal', 'label':'q' if i == 1 else 'p',
                         'address':'1000' if i == 1 else '0000'}
                pending_contact['events'].append(event)
                contact_events.append(event)
                if cut == pending_contact['end']:
                    if recurrent:
                        contact = t.make_contact(pending_contact['index'], cut, waves)
                        require(contact['support']['events'] == pending_contact['events'], 'Contact certifies actual committed events')
                        contacts.append(contact)
                        pending_contact['attempt']['status'] = 'completed_bound_recurrent_contact'
                    else:
                        pending_contact['attempt']['status'] = 'unbound_nonrecurrent_completion'
                        pending_contact['attempt']['reason'] = 'two_recurrent_histories_required_at_binding'
                    pending_contact = None
        queued = []
        if contacts and contacts[-1]['cut'] == cut and len(contacts) >= 2:
            comparison = t.compare(waves, contacts, start, cut, p['phase_biases'], duration,
                                   comparisons[-1] if comparisons else None)
            comparisons.append(comparison)
            result = t.response(comparison, _capacity(p, cut), response_model, waves[0],
                                responses[-1] if responses else None)
            result['status'] = 'sequential_response_queued'
            responses.append(result)
            pending_response = result
            queued.append({'response_id':result['response_id'], 'sha256':sha(result)})
        record = {'cut':cut, 'events':events, 'contact_events':contact_events,
                  'completed_return_ids':returned, 'applied_response_ids':applied,
                  'queued_responses':queued, 'states':[_snapshot(m) for m in machines],
                  'coupling_available':retained and recurrent, 'previous_record_sha256':previous_hash}
        record['record_sha256'] = sha(record)
        previous_hash = record['record_sha256']
        records.append(record)
    counts = {w['name']: t.beat_count(w, start, p['end_cut']) for w in waves}
    ratio = str(Fraction(counts['outer_plus'], counts['outer_minus'])) if counts['outer_minus'] else None
    summary = {'window':[start,p['end_cut']], 'observed_reclosure_counts':counts,
               'count_ratio_scope':'finite_window_reclosure_count_comparison_not_stationary_frequency',
               'model_count_ratio':ratio, 'ratio_status':'defined' if ratio is not None else 'undefined_zero_reference_increment',
               'contact_count':len(contacts), 'completed_return_cuts':{w['name']:[r['events'][-1]['cut'] for r in w['returns']] for w in waves},
               'final_retention':{m['wave']['name']:m['retained'] for m in machines},
               'loss_cuts':{m['wave']['name']:m['loss_cut'] for m in machines},
               'physical_frequency_ratio':None, 'physical_map_status':'not_established'}
    return {'schema_version':2, 'model_sha256':sha(scenario), 'statuses':dict(STATUS),
            'initial_inner_waves':inners, 'outer_waves':waves, 'cut_records':records,
            'contacts':contacts, 'contact_attempts':attempts, 'comparisons':comparisons, 'responses':responses,
            'exposures':{m['wave']['name']:m['exposure'] for m in machines},
            'aborted_cycles':{m['wave']['name']:m['aborted'] for m in machines},
            'pending_response':deepcopy(pending_response), 'summary':summary}


def validate_simulation(trace, scenario, fixture, root):
    validate_scenario(scenario, fixture, root)
    require(isinstance(trace, dict) and trace.get('statuses') == STATUS, 'Trace consumed statuses')
    require(trace.get('model_sha256') == sha(scenario), 'Trace model binding')
    inners = {w['identity']: w for w in trace['initial_inner_waves']}
    for w in trace['initial_inner_waves']:
        t.validate_wave(w, fixture)
    for w in trace['outer_waves']:
        # Some valid short/dwell scenarios have not yet established recurrence.
        if len(w['returns']) >= 2:
            t.validate_wave(w, fixture, inners)
        else:
            for item in w['returns']:
                t.validate_trace(item, fixture)
    for contact in trace['contacts']:
        t.validate_contact(contact, trace['outer_waves'], fixture)
    for result in trace['responses']:
        require(result['status'] == 'sequential_response_queued', 'Response status')
        t.validate_boundary_pair(result['boundary_pair'])
    expected = simulate(scenario, fixture, root)
    require(canonical_bytes(trace) == canonical_bytes(expected), 'Sequential trace differs from replayed committed evolution')
    return trace['summary']


def prepare(root):
    root = t.repository_root(root)
    fixture = t.read_json(root / GEOMETRY)
    baseline, intervention = default_scenario(root, fixture), early_loss_scenario(root, fixture)
    left, right = simulate(baseline, fixture, root), simulate(intervention, fixture, root)
    for trace, scenario in ((left, baseline), (right, intervention)):
        validate_simulation(trace, scenario, fixture, root)
    same_prefix = [x for x in left['cut_records'] if x['cut'] < 40] == [x for x in right['cut_records'] if x['cut'] < 40]
    require(same_prefix, 'Intervention cannot rewrite earlier committed history')
    require(left['summary']['model_count_ratio'] != right['summary']['model_count_ratio'], 'Controlled dynamics intervention must alter later observable count ratio')
    require(right['summary']['loss_cuts']['outer_plus'] == 41, 'Early loss commit')
    report = {'schema_version':2, 'statuses':dict(STATUS), 'model_id':baseline['model_id'],
              'baseline_scenario_sha256':sha(baseline), 'early_loss_scenario_sha256':sha(intervention),
              'baseline_trace_sha256':sha(left), 'early_loss_trace_sha256':sha(right),
              'baseline':left['summary'], 'early_loss':right['summary'],
              'controlled_input':{'field':'parameters.capacity_schedule', 'at_cut':40, 'before':'100', 'after':'2'},
              'identical_committed_prefix_through_cut':39, 'prefix_equality_verified':same_prefix,
              'suppressed_post_loss_returns':[c for c in left['summary']['completed_return_cuts']['outer_plus'] if c > 41],
              'preserved_inner_maps': right['exposures']['outer_plus'] == right['outer_waves'][0]['returns'][0]['fold']['inner_maps'],
              'no_re_admission':True,
              'uncertainty_scope':'Exact declared-model arithmetic; no physical uncertainty or atomic frequency inferred.'}
    return {'baseline_scenario':baseline, 'early_loss_scenario':intervention,
            'baseline_trace':left, 'early_loss_trace':right, 'report':report}


def generate(root, output_root=None):
    root = t.repository_root(root)
    outputs = prepare(root)
    target = t.repository_root(output_root) if output_root is not None else root
    (target / DATA).mkdir(parents=True, exist_ok=True)
    for filename, key in zip(FILES, ('baseline_scenario','early_loss_scenario','baseline_trace','early_loss_trace','report')):
        (target / DATA / filename).write_bytes(canonical_bytes(outputs[key]))
    return outputs['report']


def verify(root):
    root = t.repository_root(root)
    fixture = t.read_json(root / GEOMETRY)
    values = [t.read_json(root / DATA / name) for name in FILES]
    for scenario, trace in ((values[0],values[2]), (values[1],values[3])):
        validate_simulation(trace, scenario, fixture, root)
    expected = prepare(root)
    for value, key in zip(values, ('baseline_scenario','early_loss_scenario','baseline_trace','early_loss_trace','report')):
        require(canonical_bytes(value) == canonical_bytes(expected[key]), 'Delivered v2 comparison artifact differs: '+key)
    return expected['report']
