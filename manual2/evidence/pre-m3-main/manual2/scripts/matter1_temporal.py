#!/usr/bin/env python3
"""Finite declared closure/fold model and exact, read-only temporal validation.

The certificates below witness the enumerated finite predicates. They are not
AOD motif admission certificates. A fixed, declared edge sequencer supplies the
model dynamics; no atomic target, physical period, or fitted frequency is read.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from matter1_folding import ValidationError, canonical_bytes, check_fixture, hamming, require, sha

STATUSES = {'record_class': 'declared_finite_folding_model',
            'native_admission_status': 'pending', 'native_execution_status': 'not_claimed',
            'atomic_mapping_status': 'pending', 'empirical_status': 'not_tested'}
CERTIFICATE_KIND = 'finite_predicate_witness_not_motif_admission'
COMPARISON_SCOPE = 'm1:finite:comparison'
DOMAIN = 'declared_model_commit_index'
SOURCE_LABELS = {
    'sections/03_afc_basis.tex': ['eq:atomic-h1', 'eq:hinge-grammar'],
    'sections/04_cut_running_fractal_tesseract.tex': [
        'eq:closure-trace', 'eq:closure-certificate', 'eq:closure-phase-step-count',
        'eq:return-identity', 'eq:beat-reclosure', 'eq:closure-phase-window'],
    'sections/05_curl_closure_duon_current.tex': [
        'eq:branch-hinge-rd', 'eq:fold-outer-closure', 'eq:expose-inner-lineage',
        'eq:hinge-chirality-tag'],
    'sections/06_wave_state_relational_time.tex': [
        'eq:wave-update-trace', 'eq:coupling-trace', 'eq:rcd-coupling',
        'eq:rcd-additive-realization', 'eq:cadence-ratio', 'eq:count-comparator-realization'],
    'sections/06_field.tex': [
        'eq:sadar-operator-expanded', 'eq:sadar-orientation-antisymmetry',
        'eq:temporal-sadar-burden', 'eq:closure-residual', 'eq:shedding-excess'],
}
UNRESOLVED = [
    'Complete AOD motif admission and inherited primitive support accessors for these declared cells.',
    'A source-derived dynamics rule replacing the declared edge sequencer, dwell and capacity inputs.',
    'A physical observation map from the fixed-isotope electronic/nuclear states to admitted complexes.',
    'A bound metrological duration/frequency map, calibration and uncertainty/covariance model.',
    'Independent prediction design after recording prior hydrogen-target exposure.',
]


def keys(obj, expected, context):
    require(isinstance(obj, dict) and set(obj) == set(expected), f'{context}: missing or unsupported fields')


def integer(value, context, minimum=0):
    require(type(value) is int and value >= minimum, f'{context}: expected integer >= {minimum}')
    return value


def rational(value, context='rational'):
    require(isinstance(value, str), f'{context}: exact rational string required')
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValidationError(f'{context}: invalid rational') from exc
    require(str(result) == value, f'{context}: noncanonical rational')
    return result


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f'{path}: duplicate JSON key {key}')
            result[key] = value
        return result
    try:
        return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs)
    except (OSError, ValueError, UnicodeError) as exc:
        raise ValidationError(f'{path}: invalid JSON: {exc}') from exc


def repository_root(root):
    root = Path(root).resolve()
    return root.parent if root.name == 'manual2' else root


def source_bindings(root):
    bindings = []
    for name, labels in SOURCE_LABELS.items():
        try:
            data = (Path(root) / name).read_bytes()
        except OSError as exc:
            raise ValidationError(f'Missing authority source: {name}') from exc
        for label in labels:
            require(('\\label{' + label + '}').encode() in data, f'Missing authority label: {label}')
        bindings.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest(), 'labels': labels})
    return bindings


def default_model(root, fixture):
    return {
        'schema_version': 1, 'model_id': 'm1:finite-fold-recurrence:v1', 'statuses': dict(STATUSES),
        'geometry_sha256': sha(fixture), 'source_bindings': source_bindings(root),
        'update_rule': {
            'name': 'declared_oriented_edge_sequencer',
            'rule': 'At k+1 commit the next declared edge; after a return commit a distinct next-start sample; optional dwell is a zero-edge hinge sample.',
            'initialization_samples_per_cycle': 1,
            'inner_cycles': 4, 'outer_cycles': 5,
            'outer_dwell_samples': {'outer_plus': 0, 'outer_minus': 1},
            'clock_domain': DOMAIN,
            'predictive_status': 'finite_model_only_no_atomic_prediction',
        },
        'support_map': {
            'kind': 'declared_count_to_support_fixture',
            'branch_unit': 'one_support_unit_per_H1_traversal',
            'structural_hinge_support': 1,
            'warning': 'The declared support map is not an admitted RD accessor or a duration identity.',
        },
        'comparison': {
            'window_start': 20, 'cuts': [43, 47, 54], 'contact_cuts': [35, 40, 45, 52],
            'biases': {'outer_plus': '1/4', 'outer_minus': '-1/4'},
            'duration_map': {'kind': 'declared_additive_reflection_count', 'domain': DOMAIN,
                             'forward_reflections': [1, 1], 'reverse_reflections': [2, 2]},
        },
        'response': {
            'boundary_weight': '1', 'oriented_current': '1', 'capacities': ['10', '10', '3'],
            'burden_domain': 'declared_boundary_load',
            'retention_rule': 'At k+1 retain outer_plus iff the committed compatible burden at k does not exceed the declared capacity; expose retained inner provenance otherwise.',
            'route_destination': 'm1:declared-excess-reservoir',
            'radiation_identification': 'not_asserted',
        },
    }


def validate_model(model, fixture, root):
    keys(model, default_model(root, fixture), 'model')
    require(model['schema_version'] == 1 and type(model['schema_version']) is int, 'Model schema')
    require(model['model_id'] == 'm1:finite-fold-recurrence:v1', 'Model identity')
    require(model['statuses'] == STATUSES, 'Unsupported or missing model status')
    check_fixture(fixture)
    require(model['geometry_sha256'] == sha(fixture), 'Geometry binding')
    require(model['source_bindings'] == source_bindings(root), 'Authority source binding')
    # This is one declared fixture, not a tunable period-selection interface.
    # New dynamics must receive a new reviewed model identity and validation.
    template = default_model(root, fixture)
    for field in ('update_rule', 'support_map', 'comparison', 'response'):
        require(canonical_bytes(model[field]) == canonical_bytes(template[field]), f'Unsupported {field}; no target/period/status substitution')
    return model


def trace_core(trace):
    return {key: value for key, value in trace.items() if key != 'certificate'}


def certificate_for(trace):
    core = trace_core(trace)
    events = trace['events']
    return {
        'kind': CERTIFICATE_KIND, 'native_admission_status': 'pending',
        'scope': trace['scope'], 'scale': trace['scale'], 'lineage': trace['lineage'],
        'first_event_id': events[0]['event_id'], 'last_event_id': events[-1]['event_id'],
        'trace_sha256': sha(core),
        'return_id': 'return:' + sha([trace['scope'], trace['scale'], trace['lineage'],
                                     events[0]['event_id'], events[-1]['event_id'], sha(core)]),
        'witness_sha256': sha(trace['retained_return']),
        'fold_sha256': sha(trace['fold']) if trace['fold'] is not None else None,
        'status': 'finite_predicates_satisfied',
    }


def make_trace(name, scope, scale, lineage, path, coords, start, chi, dwell=0, fold=None):
    """Execute the declared transition rule, including typed zero-edge dwell."""
    require(len(path) % 2 == 1, 'Even length closed traversal required')
    turn_step = (len(path) - 1) // 2
    events = []
    for edge, label in enumerate(path):
        events.append({'event_id': f'{name}:event:{len(events)}', 'cut': start + len(events),
                       'kind': 'start' if edge == 0 else 'traversal',
                       'label': label, 'address': coords[label]})
        if edge == turn_step:
            for _ in range(dwell):
                events.append({'event_id': f'{name}:event:{len(events)}', 'cut': start + len(events),
                               'kind': 'optional_hinge_dwell', 'label': label, 'address': coords[label]})
    trace = {
        'trace_id': name, 'scope': scope, 'scale': scale, 'lineage': lineage,
        'chirality': chi, 'roles': [chi] + [0] * (1 + dwell) + [-chi],
        'events': events, 'fold': deepcopy(fold),
        'retained_return': {
            'scope': scope, 'lineage': lineage, 'retained_start_id': events[0]['event_id'],
            'hinge_event_id': events[turn_step]['event_id'],
            'hinge_cut': events[turn_step]['cut'], 'return_event_id': events[-1]['event_id'],
            'committed_at': events[-1]['cut'],
            'outbound_ids': [e['event_id'] for e in events[1:turn_step + 1]],
            'returning_ids': [e['event_id'] for e in events[turn_step + 1:] if e['kind'] == 'traversal'],
        },
    }
    trace['certificate'] = certificate_for(trace)
    return trace


def validate_trace(trace, fixture):
    keys(trace, ['trace_id', 'scope', 'scale', 'lineage', 'chirality', 'roles', 'events',
                 'fold', 'retained_return', 'certificate'], 'trace')
    for key in ('trace_id', 'scope', 'lineage'):
        require(isinstance(trace[key], str) and bool(trace[key]), f'Trace {key}')
    integer(trace['scale'], 'Trace scale')
    require(type(trace['chirality']) is int and trace['chirality'] in (-1, 1), 'Trace chirality')
    roles = trace['roles']
    require(isinstance(roles, list) and len(roles) >= 3 and all(type(r) is int for r in roles), 'Mandatory structural hinge')
    require(roles[0] == trace['chirality'] and roles[-1] == -trace['chirality'] and
            all(r == 0 for r in roles[1:-1]), 'Retained branch/hinge/return grammar')
    events = trace['events']
    require(isinstance(events, list) and len(events) >= 3, 'At least two traversals per closure')
    for index, event in enumerate(events):
        keys(event, ['event_id', 'cut', 'kind', 'label', 'address'], 'event')
        require(event['event_id'] == f"{trace['trace_id']}:event:{index}", 'Immutable event identity')
        integer(event['cut'], 'Event cut')
        require(isinstance(event['label'], str) and bool(event['label']), 'Event label')
        require(hamming(event['address'], event['address']) == 0, 'Q4 address')
        if index == 0:
            require(event['kind'] == 'start', 'Own retained-start sample')
        else:
            previous = events[index - 1]
            require(event['cut'] == previous['cut'] + 1, 'One committed sequencer transition per cut')
            require(event['kind'] in ('traversal', 'optional_hinge_dwell'), 'Typed trace transition')
            require(hamming(previous['address'], event['address']) == (event['kind'] == 'traversal'), 'H1 traversal or zero-edge dwell')
    require(len({e['event_id'] for e in events}) == len(events), 'Duplicate event identity')
    require(events[0]['address'] == events[-1]['address'] and events[0]['label'] == events[-1]['label'], 'Return to own retained start')
    traversals = [e for e in events if e['kind'] == 'traversal']
    require(len(traversals) >= 2, 'Closure traversal bound')
    witness = trace['retained_return']
    keys(witness, ['scope', 'lineage', 'retained_start_id', 'hinge_event_id', 'hinge_cut',
                   'return_event_id', 'committed_at', 'outbound_ids', 'returning_ids'], 'return witness')
    require(witness['scope'] == trace['scope'] and witness['lineage'] == trace['lineage'], 'Return witness own scope/lineage')
    require(witness['retained_start_id'] == events[0]['event_id'], 'Retained start identity')
    require(witness['return_event_id'] == events[-1]['event_id'] and witness['committed_at'] == events[-1]['cut'], 'Committed return identity')
    hinge = next((i for i, e in enumerate(events) if e['event_id'] == witness['hinge_event_id']), -1)
    require(0 < hinge < len(events) - 1 and events[hinge]['kind'] == 'traversal', 'Mandatory witnessed structural hinge')
    require(witness['hinge_cut'] == events[hinge]['cut'] < events[-1]['cut'], 'Earlier committed hinge')
    require(witness['outbound_ids'] == [e['event_id'] for e in events[1:hinge + 1] if e['kind'] == 'traversal'], 'Outbound witness coverage')
    require(witness['returning_ids'] == [e['event_id'] for e in events[hinge + 1:] if e['kind'] == 'traversal'], 'Return witness coverage')
    dwells = [e for e in events if e['kind'] == 'optional_hinge_dwell']
    require(len(dwells) == len(roles) - 3, 'Dwell/structural hinge separation')
    require(all(e['address'] == events[hinge]['address'] and events[hinge]['cut'] < e['cut'] < events[-1]['cut'] for e in dwells), 'Dwell retained at hinge')
    require(canonical_bytes(trace['certificate']) == canonical_bytes(certificate_for(trace)), 'Finite certificate binding; a label is insufficient')
    if trace['fold'] is not None:
        path = [e['label'] for e in events if e['kind'] != 'optional_hinge_dwell']
        expected = fixture['outer_walk'] if trace['chirality'] == 1 else list(reversed(fixture['outer_walk']))
        require(path == expected, 'Oriented outer trace for actual fold')
        require(all(e['address'] == fixture['vertices'][e['label']] for e in events), 'Outer coordinate map')
    return {'traversals': len(traversals), 'dwell_samples': len(dwells),
            'support_sum': len(traversals) + 1, 'return_cut': events[-1]['cut']}


def make_wave(name, path, coords, scale, start, cycles, chi, dwell=0, fold=None):
    scope, lineage = f'm1:finite:scope:{name}', f'm1:finite:lineage:{name}'
    returns = []
    cursor = start
    for occurrence in range(cycles):
        trace = make_trace(f'{name}:cycle:{occurrence}', scope, scale, lineage, path, coords,
                           cursor, chi, dwell, fold)
        returns.append(trace)
        cursor = trace['events'][-1]['cut'] + 1
    return {'name': name, 'scope': scope, 'scale': scale, 'lineage': lineage,
            'identity': 'wave:' + sha([scope, scale, lineage, returns[0]['certificate']['return_id']]),
            'chirality': chi, 'returns': returns}


def history_prefix(wave, cut):
    return [trace['certificate']['return_id'] for trace in wave['returns'] if trace['events'][-1]['cut'] <= cut]


def fold_proposal(inners, outer_name, fixture):
    maps = []
    for wave, labels in zip(inners, (['A', 'B', 'C', 'D'], ['B', 'A', 'E', 'F'])):
        maps.append({
            'inner_identity': wave['identity'], 'inner_scope': wave['scope'],
            'inner_scale': wave['scale'], 'inner_lineage': wave['lineage'],
            'inner_chirality': wave['chirality'],
            'inner_returns': [t['certificate']['return_id'] for t in wave['returns']],
            'inner_certificates': [deepcopy(t['certificate']) for t in wave['returns']],
            'map_kind': 'injective_cell_embedding',
            'outer_scope': f'm1:finite:scope:{outer_name}', 'outer_scale': 1,
            'vertex_map': dict(zip(('u', 'v', 'w', 'z'), labels)),
        })
    return {'kind': 'declared_cell_fold_proposal', 'geometry_sha256': sha(fixture),
            'inner_maps': maps, 'outer_lineage': f'm1:finite:lineage:{outer_name}',
            'retention_status': 'inner_provenance_retained'}


def validate_fold(proposal, wave, inner_by_id, fixture):
    keys(proposal, ['kind', 'geometry_sha256', 'inner_maps', 'outer_lineage', 'retention_status'], 'fold')
    require(proposal['kind'] == 'declared_cell_fold_proposal' and proposal['retention_status'] == 'inner_provenance_retained', 'Fold status')
    require(proposal['geometry_sha256'] == sha(fixture) and proposal['outer_lineage'] == wave['lineage'], 'Fold outer binding')
    require(isinstance(proposal['inner_maps'], list) and len(proposal['inner_maps']) == 2, 'Two explicit inner-to-outer maps')
    require(len({m['inner_identity'] for m in proposal['inner_maps']}) == 2, 'Distinct retained inner identities')
    for mapping, expected_labels in zip(proposal['inner_maps'], (['A', 'B', 'C', 'D'], ['B', 'A', 'E', 'F'])):
        keys(mapping, ['inner_identity', 'inner_scope', 'inner_scale', 'inner_lineage', 'inner_chirality',
                       'inner_returns', 'inner_certificates', 'map_kind', 'outer_scope', 'outer_scale', 'vertex_map'], 'inner map')
        require(mapping['inner_identity'] in inner_by_id, 'Mapped inner identity exists')
        inner = inner_by_id[mapping['inner_identity']]
        for key in ('scope', 'scale', 'lineage', 'chirality'):
            require(mapping['inner_' + key] == inner[key], f'Preserved inner {key}')
        require(mapping['map_kind'] == 'injective_cell_embedding', 'Explicit cell embedding')
        require(mapping['outer_scope'] == wave['scope'] and mapping['outer_scale'] == wave['scale'] > inner['scale'], 'Mapped distinct inner/outer scopes and scales')
        require(mapping['inner_scope'] != wave['scope'], 'Cross-scale scope equality is not a map')
        require(mapping['vertex_map'] == dict(zip(('u', 'v', 'w', 'z'), expected_labels)), 'Inner-to-outer incidence map')
        require(mapping['inner_returns'] == [t['certificate']['return_id'] for t in inner['returns']], 'Inner return history preserved')
        require(mapping['inner_certificates'] == [t['certificate'] for t in inner['returns']], 'Inner certificates preserved')
        require(inner['returns'][-1]['events'][-1]['cut'] < wave['returns'][0]['events'][0]['cut'], 'Outer consumes only committed inner history')
    require(proposal['inner_maps'][0]['inner_scope'] != proposal['inner_maps'][1]['inner_scope'], 'Distinct inner scopes admitted through maps')


def validate_wave(wave, fixture, inner_by_id=None):
    keys(wave, ['name', 'scope', 'scale', 'lineage', 'identity', 'chirality', 'returns'], 'wave')
    require(len(wave['returns']) >= 2, 'Recurrence needs distinct retained returns')
    ids, event_ids, previous_end = set(), set(), -1
    for trace in wave['returns']:
        validate_trace(trace, fixture)
        for key in ('scope', 'scale', 'lineage', 'chirality'):
            require(trace[key] == wave[key], f'Wave {key} binding')
        rid = trace['certificate']['return_id']
        require(rid not in ids, 'Replayed return cannot add beat')
        ids.add(rid)
        require(previous_end < trace['events'][0]['cut'], 'Distinct return events after previous completion')
        previous_end = trace['events'][-1]['cut']
        for event in trace['events']:
            require(event['event_id'] not in event_ids, 'Reissued event cannot add beat')
            event_ids.add(event['event_id'])
        if inner_by_id is None:
            require(trace['fold'] is None, 'Primitive declared trace cannot conceal fold')
            require([e['label'] for e in trace['events']] == ['u', 'v', 'w', 'z', 'u'], 'Declared inner square rule')
        else:
            require(trace['fold'] is not None, 'Orientation alone does not certify outer fold')
            validate_fold(trace['fold'], wave, inner_by_id, fixture)
    require(wave['identity'] == 'wave:' + sha([wave['scope'], wave['scale'], wave['lineage'], wave['returns'][0]['certificate']['return_id']]), 'Wave origin identity')
    return {'closures': len(ids), 'beats_from_origin': len(ids) - 1,
            'completion_cuts': [t['events'][-1]['cut'] for t in wave['returns']],
            'cadence': [b['events'][-1]['cut'] - a['events'][-1]['cut'] for a, b in zip(wave['returns'], wave['returns'][1:])]}


def comparison_maps(waves, cut):
    return [{'map_kind': 'identity_preserving_committed_history_projection',
             'source_identity': w['identity'], 'source_scope': w['scope'],
             'source_lineage': w['lineage'], 'source_scale': w['scale'],
             'target_scope': COMPARISON_SCOPE, 'committed_cut': cut,
             'return_prefix': history_prefix(w, cut), 'prefix_sha256': sha(history_prefix(w, cut))}
            for w in waves]


def make_contact(index, cut, waves):
    support = make_trace(f'contact:{index}', COMPARISON_SCOPE, 1, f'm1:finite:contact:{index}',
                         ['p', 'q', 'p'], {'p': '0000', 'q': '1000'}, cut - 2, 1)
    return {'contact_id': f'm1:finite:contact:{index}', 'cut': cut, 'scope': COMPARISON_SCOPE,
            'direction': [w['identity'] for w in waves], 'maps': comparison_maps(waves, cut),
            'support': support, 'status': 'declared_bound_contact'}


def validate_contact(contact, waves, fixture):
    keys(contact, ['contact_id', 'cut', 'scope', 'direction', 'maps', 'support', 'status'], 'contact')
    require(contact['status'] == 'declared_bound_contact', 'Contact status')
    require(contact['scope'] == COMPARISON_SCOPE, 'Contact comparison scope')
    require(contact['direction'] == [w['identity'] for w in waves], 'Distinct directional contact identities')
    require(len(set(contact['direction'])) == 2, 'Coupling requires distinct recurrent identities')
    integer(contact['cut'], 'Contact cut')
    require(contact['maps'] == comparison_maps(waves, contact['cut']), 'Contact maps bind exact committed prefixes')
    require(all(len(m['return_prefix']) >= 2 for m in contact['maps']), 'Contact requires already recurrent prefixes')
    validate_trace(contact['support'], fixture)
    require(contact['support']['scope'] == COMPARISON_SCOPE and contact['support']['events'][-1]['cut'] == contact['cut'], 'Contact return/window binding')
    require(contact['support']['fold'] is None and len(contact['support']['events']) == 3, 'Declared contact support')


def beat_count(wave, start, end):
    # The first return supplies the origin once. Later windows do not subtract
    # another origin; count already distinguished reclosures in (start,end].
    return sum(start < t['events'][-1]['cut'] <= end for t in wave['returns'][1:])


def compare(waves, contacts, start, cut, biases, duration_map, previous=None):
    require(len(waves) == 2 and waves[0]['identity'] != waves[1]['identity'], 'Two distinct lineages')
    require(type(start) is int and type(cut) is int and 0 <= start < cut, 'Common integer comparison window')
    relevant = [c for c in contacts if start <= c['cut'] <= cut]
    require(len(relevant) >= 2 and len({c['contact_id'] for c in relevant}) == len(relevant) and
            len({c['cut'] for c in relevant}) == len(relevant), 'Repeated independent bound contacts required')
    require(len({c['support']['certificate']['return_id'] for c in relevant}) == len(relevant), 'Contact-return replay')
    require(all(c['maps'] == comparison_maps(waves, c['cut']) and c['direction'] == [w['identity'] for w in waves] for c in relevant), 'Compatible mapped contact histories')
    keys(duration_map, ['kind', 'domain', 'forward_reflections', 'reverse_reflections'], 'duration map')
    require(duration_map['kind'] == 'declared_additive_reflection_count' and duration_map['domain'] == DOMAIN, 'Explicit typed duration map')
    counts = [beat_count(w, start, cut) for w in waves]
    require(all(count > 0 for count in counts), 'Positive recurrent comparison counts')
    phase_bias = rational(biases[waves[0]['name']]) - rational(biases[waves[1]['name']])
    cumulative = [beat_count(w, -1, cut) for w in waves]
    lag = Fraction(cumulative[0] - cumulative[1]) + phase_bias
    directions = []
    for index, key in enumerate(('forward_reflections', 'reverse_reflections')):
        reflections = duration_map[key]
        require(isinstance(reflections, list) and len(reflections) == 2, 'Directional reflected support binding')
        require(all(type(r) is int and r >= 0 for r in reflections), 'Nonnegative exact reflection counts')
        rd = 3  # declared two-edge contact support plus structural hinge support
        duration = rd + sum(reflections)
        directions.append({'ratio': str(Fraction(counts[index], counts[1 - index])),
                           'bias': str(phase_bias if index == 0 else -phase_bias),
                           'unwrapped_lag': str(lag if index == 0 else -lag),
                           'declared_contact_support': rd, 'reflection_counts': reflections,
                           'duration_domain': DOMAIN, 'duration': duration,
                           'participation': min(duration, cut - start)})
    return {'comparison_id': f'm1:finite:comparison:{cut}', 'scope': COMPARISON_SCOPE,
            'window': [start, cut], 'maps': comparison_maps(waves, cut),
            'contact_ids': [c['contact_id'] for c in relevant], 'beat_counts': counts,
            'cumulative_reclosure_counts': cumulative,
            'boundary_support': {'contact_id': relevant[-1]['contact_id'],
                                 'certificate': deepcopy(relevant[-1]['support']['certificate']),
                                 'oriented_edge': [relevant[-1]['support']['events'][0]['address'],
                                                   relevant[-1]['support']['events'][1]['address']]},
            'forward': directions[0], 'reverse': directions[1],
            'previous_comparison_id': previous['comparison_id'] if previous else None,
            'lag_drift': str(lag - rational(previous['forward']['unwrapped_lag'])) if previous else None,
            'status': 'declared_model_comparison_executed'}


def boundary_pair(comparison, weight, current, rho, lag):
    support = comparison['boundary_support']
    common = {'boundary_id': 'boundary:' + support['contact_id'],
              'scope': comparison['scope'], 'window': deepcopy(comparison['window']),
              'history_maps': deepcopy(comparison['maps']),
              'contact_certificate': deepcopy(support['certificate']),
              'participation': rho, 'boundary_weight': str(weight), 'signed_lag': str(lag)}
    forward = {**deepcopy(common), 'oriented_edge': support['oriented_edge'],
               'orientation': 1, 'oriented_current': str(current),
               'value': str(weight * rho * lag * current)}
    reverse = {**deepcopy(common), 'oriented_edge': list(reversed(support['oriented_edge'])),
               'orientation': -1, 'oriented_current': str(-current),
               'value': str(-weight * rho * lag * current)}
    return {'kind': 'same_boundary_orientation_pair', 'forward': forward, 'reverse': reverse}


def validate_boundary_pair(pair):
    keys(pair, ['kind', 'forward', 'reverse'], 'SADAR boundary pair')
    require(pair['kind'] == 'same_boundary_orientation_pair', 'SADAR pair type')
    forward, reverse = pair['forward'], pair['reverse']
    fields = ['boundary_id', 'scope', 'window', 'history_maps', 'contact_certificate',
              'participation', 'boundary_weight', 'signed_lag', 'oriented_edge',
              'orientation', 'oriented_current', 'value']
    keys(forward, fields, 'Forward boundary witness')
    keys(reverse, fields, 'Reverse boundary witness')
    for field in fields[:8]:
        require(forward[field] == reverse[field], f'Same boundary pairing preserves {field}')
    require(forward['orientation'] == 1 and reverse['orientation'] == -1, 'Opposite boundary orientations')
    edge = forward['oriented_edge']
    require(len(edge) == 2 and hamming(*edge) == 1 and reverse['oriented_edge'] == list(reversed(edge)), 'Actual reversed H1 boundary incidence')
    require(rational(reverse['oriented_current']) == -rational(forward['oriented_current']), 'Reversed boundary current')
    for witness in (forward, reverse):
        rho = integer(witness['participation'], 'Boundary participation')
        expected = rational(witness['boundary_weight']) * rho * rational(witness['signed_lag']) * rational(witness['oriented_current'])
        require(rational(witness['value']) == expected, 'SADAR value from bound operands')
    require(rational(reverse['value']) == -rational(forward['value']), 'Same-boundary antisymmetry')


def response(comparison, capacity, model, outer, previous_response=None):
    setup = model['response']
    cut = comparison['window'][1]
    weight, current = rational(setup['boundary_weight']), rational(setup['oriented_current'])
    rho = comparison['forward']['participation']
    lag = rational(comparison['forward']['unwrapped_lag'])
    sadar = weight * rho * lag * current
    burden = weight * rho * abs(lag)
    cap = rational(capacity)
    require(weight >= 0 and cap >= 0, 'Compatible nonnegative burden/capacity')
    residual, excess = burden - cap, max(Fraction(0), burden - cap)
    retained = excess == 0
    prefix = history_prefix(outer, cut)
    active = next(t for t in reversed(outer['returns']) if t['events'][-1]['cut'] <= cut)
    inner = active['fold']['inner_maps']
    prior = rational(previous_response['returned_current_after']) if previous_response else Fraction(0)
    return {
        'response_id': f'm1:finite:response:{cut + 1}', 'input_cut': cut, 'committed_cut': cut + 1,
        'input_comparison_id': comparison['comparison_id'], 'input_comparison_sha256': sha(comparison),
        'input_history_maps': deepcopy(comparison['maps']),
        'previous_response_id': previous_response['response_id'] if previous_response else None,
        'boundary_weight': str(weight), 'oriented_current': str(current), 'participation': rho,
        'signed_lag': str(lag), 'sadar': str(sadar), 'same_boundary_reversed_sadar': str(-sadar),
        'boundary_pair': boundary_pair(comparison, weight, current, rho, lag),
        'returned_current_before': str(prior), 'returned_current_after': str(prior + sadar),
        'burden_domain': setup['burden_domain'], 'capacity_domain': setup['burden_domain'],
        'burden': str(burden), 'capacity': str(cap), 'residual': str(residual), 'excess': str(excess),
        'outer_identity': outer['identity'], 'outer_return_prefix': prefix,
        'outer_certificate': deepcopy(active['certificate']),
        'outer_retention': 'retained' if retained else 'lost_by_declared_capacity_rule',
        'retention_bridge': setup['retention_rule'],
        'route': None if retained else {'kind': 'declared_excess_route', 'destination': setup['route_destination'],
                                       'source_scope': outer['scope'], 'window': comparison['window'],
                                       'amount': str(excess), 'radiation_identification': 'not_asserted',
                                       'next_scope_reclosure': 'pending'},
        'preserved_inner_maps': deepcopy(inner),
        'exposure': [] if retained else deepcopy(inner),
        'status': 'declared_next_step_response_executed',
    }


def generate_trace(model, fixture):
    coords = {'u': '0000', 'v': '1000', 'w': '1100', 'z': '0100'}
    path = ['u', 'v', 'w', 'z', 'u']
    inners = [make_wave(name, path, coords, 0, 0, model['update_rule']['inner_cycles'], chi)
              for name, chi in (('inner_minus', 1), ('inner_plus', -1))]
    start = max(w['returns'][-1]['events'][-1]['cut'] for w in inners) + 1
    outers = []
    for name, chi in (('outer_plus', 1), ('outer_minus', -1)):
        outer_path = fixture['outer_walk'] if chi == 1 else list(reversed(fixture['outer_walk']))
        outers.append(make_wave(name, outer_path, fixture['vertices'], 1, start,
                               model['update_rule']['outer_cycles'], chi,
                               model['update_rule']['outer_dwell_samples'][name],
                               fold_proposal(inners, name, fixture)))
    contacts = [make_contact(i, cut, outers) for i, cut in enumerate(model['comparison']['contact_cuts'])]
    comparisons, responses = [], []
    for cut, cap in zip(model['comparison']['cuts'], model['response']['capacities']):
        comparison = compare(outers, contacts, model['comparison']['window_start'], cut,
                             model['comparison']['biases'], model['comparison']['duration_map'],
                             comparisons[-1] if comparisons else None)
        comparisons.append(comparison)
        responses.append(response(comparison, cap, model, outers[0], responses[-1] if responses else None))
    return {'schema_version': 1, 'model_sha256': sha(model), 'geometry_sha256': sha(fixture),
            'statuses': dict(STATUSES), 'inner_waves': inners, 'outer_waves': outers,
            'contacts': contacts, 'comparisons': comparisons, 'responses': responses}


def validate_trace_bundle(bundle, model, fixture):
    keys(bundle, ['schema_version', 'model_sha256', 'geometry_sha256', 'statuses', 'inner_waves',
                  'outer_waves', 'contacts', 'comparisons', 'responses'], 'temporal trace bundle')
    require(bundle['schema_version'] == 1 and type(bundle['schema_version']) is int, 'Trace schema')
    require(bundle['statuses'] == STATUSES, 'Unsupported or missing trace status')
    require(bundle['model_sha256'] == sha(model) and bundle['geometry_sha256'] == sha(fixture), 'Trace input bindings')
    require(len(bundle['inner_waves']) == 2 and len(bundle['outer_waves']) == 2, 'Two inner and two outer histories')
    inners = {w['identity']: w for w in bundle['inner_waves']}
    require(len(inners) == 2, 'Distinct inner wave identities')
    summaries = {}
    for wave in bundle['inner_waves']:
        summaries[wave['name']] = validate_wave(wave, fixture)
    for wave in bundle['outer_waves']:
        summaries[wave['name']] = validate_wave(wave, fixture, inners)
    all_traces = [t for w in bundle['inner_waves'] + bundle['outer_waves'] for t in w['returns']]
    all_ids = [e['event_id'] for t in all_traces for e in t['events']]
    require(len(set(all_ids)) == len(all_ids), 'Inner/outer event identity reuse')
    all_returns = [t['certificate']['return_id'] for t in all_traces]
    require(len(set(all_returns)) == len(all_returns), 'Inner return cannot become outer beat')
    waves = bundle['outer_waves']
    require(len({w['scope'] for w in waves}) == 2 and len({w['lineage'] for w in waves}) == 2, 'Comparator lineages remain distinct')
    contacts = bundle['contacts']
    for contact in contacts:
        validate_contact(contact, waves, fixture)
    require([c['cut'] for c in contacts] == model['comparison']['contact_cuts'], 'Declared contact schedule')
    previous = previous_response = None
    require(len(bundle['comparisons']) == len(bundle['responses']) == len(model['comparison']['cuts']), 'Complete comparison/response records')
    for index, (comparison, result) in enumerate(zip(bundle['comparisons'], bundle['responses'])):
        expected = compare(waves, contacts, model['comparison']['window_start'], model['comparison']['cuts'][index],
                           model['comparison']['biases'], model['comparison']['duration_map'], previous)
        require(comparison == expected, 'Comparison, status, lag, duration or committed-prefix mismatch')
        require(result.get('committed_cut') == result.get('input_cut', -1) + 1, 'Causal response must follow input at k+1')
        validate_boundary_pair(result.get('boundary_pair', {}))
        expected_response = response(comparison, model['response']['capacities'][index], model,
                                     waves[0], previous_response)
        require(result == expected_response, 'SADAR/residual/route/exposure or status mismatch')
        previous, previous_response = comparison, result
    # Independent predicate validation above runs before deterministic replay.
    require(canonical_bytes(bundle) == canonical_bytes(generate_trace(model, fixture)), 'Persisted trace differs from the declared sequencer execution')
    return summaries


def report_for(model, fixture, bundle):
    summaries = validate_trace_bundle(bundle, model, fixture)
    return {
        'schema_version': 1, 'statuses': dict(STATUSES),
        'finite_model_execution': 'executed',
        'assertion_scope': 'H1/hinge/own-return, finite witness bindings, explicit cell embeddings, distinct recurrence, committed comparison, declared causal response; no complete motif admission.',
        'model_sha256': sha(model), 'geometry_sha256': sha(fixture), 'trace_sha256': sha(bundle),
        'wave_summaries': summaries,
        'outer_traversals_per_closure': 6, 'declared_outer_support_sum': 7,
        'opposite_chirality_preserved_at_equal_support': True,
        'comparison_rows': [{'window': c['window'], 'beat_counts': c['beat_counts'],
                             'ratio': c['forward']['ratio'], 'reverse_ratio': c['reverse']['ratio'],
                             'bias': c['forward']['bias'], 'lag': c['forward']['unwrapped_lag'],
                             'drift': c['lag_drift'], 'directional_durations': [c['forward']['duration'], c['reverse']['duration']]}
                            for c in bundle['comparisons']],
        'response_rows': [{key: r[key] for key in ('input_cut', 'committed_cut', 'sadar',
                          'same_boundary_reversed_sadar', 'burden', 'capacity', 'residual',
                          'excess', 'outer_retention')} for r in bundle['responses']],
        'kernel': 'not_used_deterministic_declared_edge_rule',
        'certificates': CERTIFICATE_KIND,
        'unresolved_dependencies': UNRESOLVED,
        'acceptance_scope': {
            key: 'finite_declared_model_assertions_only_not_native_or_empirical_admission'
            for key in ['P2-01', 'P2-02', 'P2-03', 'P2-04', 'P2-05', 'P2-06',
                        'P3-01', 'P3-02', 'P3-03', 'P3-04', 'P3-05',
                        'F-01', 'F-02', 'F-03', 'F-04', 'F-08', 'P5-04', 'P5-06']},
    }


def paths(root):
    root = repository_root(root)
    return root, root / 'manual2' / 'data' / 'm1' / 'folding'


def generate(root, output_root=None):
    root, directory = paths(root)
    fixture = read_json(directory / 'two_square_fold.json')
    model = read_json(directory / 'temporal_model.json')
    validate_model(model, fixture, root)
    bundle = generate_trace(model, fixture)
    report = report_for(model, fixture, bundle)
    outputs = {'temporal_trace.json': bundle, 'temporal_report.json': report}
    target = paths(output_root)[1] if output_root is not None else directory
    target.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        (target / name).write_bytes(canonical_bytes(value))
    return report


def verify(root):
    root, directory = paths(root)
    fixture = read_json(directory / 'two_square_fold.json')
    model = read_json(directory / 'temporal_model.json')
    validate_model(model, fixture, root)
    bundle = read_json(directory / 'temporal_trace.json')
    expected = report_for(model, fixture, bundle)
    require(canonical_bytes(read_json(directory / 'temporal_report.json')) == canonical_bytes(expected), 'Persisted temporal report/status differs')
    return expected
