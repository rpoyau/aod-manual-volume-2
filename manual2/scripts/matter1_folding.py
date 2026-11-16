#!/usr/bin/env python3
"""Finite cellular construction and externally supplied traversal-ledger validation.

These checks establish the declared Q4 illustration and its counting contract.
They do not admit an AOD motif, certify a native return, or predict spectroscopy.
All evaluators and verifiers are read-only. The separate generator owns writes.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path


class ValidationError(ValueError):
    """The finite illustration or persisted contract is inconsistent."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def sha(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def read_json(path):
    try:
        return json.loads(Path(path).read_bytes())
    except (OSError, ValueError) as exc:
        raise ValidationError(f'{path}: cannot read JSON: {exc}') from exc


def exact_integer(value, message):
    require(type(value) is int, message)
    return value


def keys(value, expected, name):
    require(isinstance(value, dict) and set(value) == set(expected), f'{name}: missing or unsupported fields')


def text(value, name):
    require(isinstance(value, str) and bool(value.strip()), f'{name}: expected nonempty string')


def hamming(a, b):
    require(all(isinstance(v, str) and len(v) == 4 and set(v) <= {'0', '1'} for v in (a, b)),
            'Invalid Q4 address')
    return sum(x != y for x, y in zip(a, b))


def chain(path):
    result = Counter()
    for a, b in zip(path, path[1:]):
        edge = tuple(sorted((a, b)))
        result[edge] += 1 if (a, b) == edge else -1
    return {edge: coefficient for edge, coefficient in result.items() if coefficient}


def add_chains(*parts):
    result = Counter()
    for part in parts:
        result.update(part)
    return {edge: coefficient for edge, coefficient in result.items() if coefficient}


FIXTURE_STATUSES = {'status': 'ILLUSTRATIVE_CELLULAR_COUNT_FIXTURE',
                    'admission_status': 'not_asserted',
                    'native_execution_status': 'not_asserted', 'empirical_status': 'not_tested'}
LEDGER_STATUSES = {**FIXTURE_STATUSES, 'status': 'ILLUSTRATIVE_TRAVERSAL_LEDGER'}
SOURCE_BINDINGS = ['eq:atomic-h1', 'eq:hinge-grammar', 'eq:afc-stokes-used', 'eq:fold-outer-closure']
FIXTURE_FIELDS = set(FIXTURE_STATUSES) | {'vertices', 'minus_face', 'plus_face', 'shared_interface',
                  'outer_walk', 'outgoing_leg', 'returning_leg', 'vertex_roles',
                  'repetition_domain', 'tick_definition', 'hinge_policy', 'limitation'}
SCOPE = {'scope_id': 'm1:two-square:illustrative-q4', 'resolution': 0,
         'lineage_id': 'm1:two-square:counted-pattern'}
EVENT_FIELDS = {'record_id', 'event_id', 'predecessor_event_id', 'ordinal', 'scope_id',
                'lineage_id', 'resolution', 'repetition', 'edge_index', 'kind', 'leg',
                'source_label', 'target_label', 'source_address', 'target_address',
                'changed_coordinate', 'hamming_distance'}


def validate_statuses(value, expected):
    for field, status in expected.items():
        require(value.get(field) == status, 'Unsupported or missing fixture status: ' + field)


def check_fixture(f):
    """Validate a six-vertex, two-square Q4 construction using coordinates."""
    require(isinstance(f, dict), 'Fixture must be an object')
    validate_statuses(f, FIXTURE_STATUSES)
    keys(f, FIXTURE_FIELDS, 'Cell fixture')
    vertices = f['vertices']
    require(isinstance(vertices, dict) and len(vertices) == 6, 'Exactly six declared vertices required')
    path_fields = ('minus_face', 'plus_face', 'outer_walk', 'outgoing_leg', 'returning_leg')
    interface = f['shared_interface']
    require(isinstance(interface, list) and len(interface) == 2 and len(set(interface)) == 2,
            'Invalid shared interface')
    used = set(interface)
    for field in path_fields:
        path = f[field]
        require(isinstance(path, list) and len(path) >= 2 and all(isinstance(v, str) for v in path),
                'Invalid vertex path')
        require(all(v in vertices for v in path), 'Unknown vertex')
        used.update(path)
    require(used == set(vertices), 'Unknown or unused interface/vertex')
    addresses = [vertices[v] for v in used]
    for address in addresses:
        hamming(address, address)
    require(len(addresses) == len(set(addresses)), 'Distinct used vertices must have distinct Q4 addresses')
    for field in path_fields:
        for a, b in zip(f[field], f[field][1:]):
            require(hamming(vertices[a], vertices[b]) == 1, 'Non-Hamming-1 edge')
    minus, plus = f['minus_face'], f['plus_face']
    for face in (minus, plus):
        require(face[0] == face[-1] and len(face) - 1 == len(set(face[:-1])) == 4,
                'Face is not a simple square walk')
    minus_coords, plus_coords = ([vertices[v] for v in face] for face in (minus, plus))
    cminus, cplus = chain(minus_coords), chain(plus_coords)
    shared = tuple(sorted(vertices[v] for v in interface))
    require(set(minus_coords) & set(plus_coords) == set(shared),
            'Faces must meet only at the declared interface vertices')
    require(set(cminus) & set(cplus) == {shared}, 'Faces must share exactly the declared edge')
    require(cminus[shared] + cplus[shared] == 0, 'Interface orientations do not cancel')
    boundary = add_chains(cminus, cplus)
    require(shared not in boundary and len(boundary) == 6, 'Outer boundary must have six edges')
    require(all(abs(v) == 1 for v in boundary.values()), 'Non-unit boundary coefficient')
    outer = f['outer_walk']
    require(outer[0] == outer[-1] and len(outer) == 7 and len(set(outer[:-1])) == 6,
            'Outer walk must be the simple six-edge boundary')
    require(chain([vertices[v] for v in outer]) == boundary, 'Outer walk differs from summed boundary')
    out, ret = f['outgoing_leg'], f['returning_leg']
    require(len(out) == len(ret) == 4, 'Legs must have three traversals')
    require(out[0] == ret[-1] and out[-1] == ret[0], 'Leg endpoints disagree')
    require(out + ret[1:] == outer, 'Legs do not compose the outer walk')
    require({out[0], out[-1]} == set(interface), 'Leg endpoints must bind the interface')
    expected_roles = {v: (0 if v in interface else -1 if v in minus else 1) for v in vertices}
    roles = f['vertex_roles']
    require(isinstance(roles, dict) and all(type(v) is int for v in roles.values())
            and roles == expected_roles, 'Incorrect or missing ternary vertex roles')
    domain = f['repetition_domain']
    keys(domain, {'min', 'max_checked'}, 'Repetition domain')
    require(type(domain['min']) is int and type(domain['max_checked']) is int
            and domain == {'min': 1, 'max_checked': 64}, 'Repetition domain differs')
    for field in ('tick_definition', 'hinge_policy', 'limitation'):
        text(f[field], field)
    return {'distinct_q4_vertices': 6, 'outer_edge_count': 6, 'per_leg_edges': 3,
            'shared_edge_retained_in_fixture': list(interface), 'shared_edge_outer_coefficient': 0,
            'incidence_representation': 'Q4 addresses', 'coordinate_map': 'injective',
            'validated_fixture_statuses': dict(FIXTURE_STATUSES)}


def build_event_ledger(fixture, repetitions=3):
    """Declare repeated illustration events, not a dynamically predicted cadence."""
    check_fixture(fixture)
    exact_integer(repetitions, 'Repetition count must be an integer')
    require(1 <= repetitions <= 64, 'Repetition count outside checked illustration domain')
    events = []
    predecessor = None
    for repetition in range(repetitions):
        for edge_index, (a, b) in enumerate(zip(fixture['outer_walk'], fixture['outer_walk'][1:])):
            ordinal = len(events) + 1
            event_id = f'illustrative-event-{ordinal:04d}'
            source, target = fixture['vertices'][a], fixture['vertices'][b]
            events.append({'record_id': f'ledger-row-{ordinal:04d}', 'event_id': event_id,
                           'predecessor_event_id': predecessor, 'ordinal': ordinal, **SCOPE,
                           'repetition': repetition, 'edge_index': edge_index,
                           'kind': 'committed_h1_traversal', 'leg': 'outgoing' if edge_index < 3 else 'returning',
                           'source_label': a, 'target_label': b, 'source_address': source, 'target_address': target,
                           'changed_coordinate': next(i for i, (x, y) in enumerate(zip(source, target)) if x != y),
                           'hamming_distance': 1})
            predecessor = event_id
    return {'schema_version': 1, **LEDGER_STATUSES, 'fixture_binding': sha(fixture),
            'source_bindings': list(SOURCE_BINDINGS), 'scope': dict(SCOPE),
            'event_unit': 'one_oriented_hamming1_traversal', 'repetitions': repetitions,
            'events': events}


def validate_event_ledger(fixture, ledger):
    """Read and validate arbitrary persisted ledger records, including their identities."""
    check_fixture(fixture)
    require(isinstance(ledger, dict), 'Event ledger must be an object')
    validate_statuses(ledger, LEDGER_STATUSES)
    keys(ledger, set(LEDGER_STATUSES) | {'schema_version', 'fixture_binding', 'source_bindings',
                                      'scope', 'event_unit', 'repetitions', 'events'}, 'Event ledger')
    require(type(ledger['schema_version']) is int and ledger['schema_version'] == 1, 'Unknown event-ledger version')
    require(ledger['fixture_binding'] == sha(fixture), 'Wrong fixture binding')
    require(ledger['source_bindings'] == SOURCE_BINDINGS, 'Wrong source bindings')
    require(ledger['scope'] == SCOPE and type(ledger['scope'].get('resolution')) is int, 'Wrong ledger scope/lineage')
    require(ledger['event_unit'] == 'one_oriented_hamming1_traversal', 'Role names or support weights are not event ticks')
    n = exact_integer(ledger['repetitions'], 'Repetition count must be an integer')
    require(1 <= n <= 64, 'Repetition count outside checked illustration domain')
    events = ledger['events']
    require(isinstance(events, list) and len(events) == 6*n, 'Ledger event count must equal six times repetitions')
    ids, records, positions = set(), set(), set()
    predecessor = None
    counts = Counter()
    for index, event in enumerate(events):
        keys(event, EVENT_FIELDS, 'Traversal event')
        for field in ('record_id', 'event_id'):
            text(event[field], field)
        require(event['event_id'] not in ids, 'Duplicate or replayed event identity')
        require(event['record_id'] not in records, 'Duplicate serialization record')
        ids.add(event['event_id']); records.add(event['record_id'])
        require(event['predecessor_event_id'] == predecessor, 'Wrong retained event predecessor')
        predecessor = event['event_id']
        for field in ('ordinal', 'resolution', 'repetition', 'edge_index', 'changed_coordinate', 'hamming_distance'):
            exact_integer(event[field], f'{field}: expected exact integer')
        require(event['ordinal'] == index + 1, 'Wrong committed ordinal')
        require(all(event[k] == v for k, v in SCOPE.items()), 'Wrong event scope/lineage/resolution binding')
        repetition, edge_index = divmod(index, 6)
        require(event['repetition'] == repetition and event['edge_index'] == edge_index, 'Wrong traversal occurrence binding')
        position = (event['scope_id'], event['lineage_id'], event['repetition'], event['edge_index'])
        require(position not in positions, 'Recounted traversal occurrence')
        positions.add(position)
        require(event['kind'] == 'committed_h1_traversal', 'A support weight or sample is not an H1 traversal')
        leg = 'outgoing' if edge_index < 3 else 'returning'
        require(event['leg'] == leg, 'Wrong leg binding')
        a, b = fixture['outer_walk'][edge_index:edge_index+2]
        require((event['source_label'], event['target_label']) == (a, b), 'Wrong traversal endpoints')
        source, target = fixture['vertices'][a], fixture['vertices'][b]
        require((event['source_address'], event['target_address']) == (source, target), 'Wrong coordinate witness')
        require(hamming(source, target) == event['hamming_distance'] == 1, 'Invalid Hamming witness')
        changed = [j for j, (x, y) in enumerate(zip(source, target)) if x != y]
        require(changed == [event['changed_coordinate']], 'Wrong changed-coordinate witness')
        counts[leg] += 1
    require(counts['outgoing'] == counts['returning'] == 3*n, 'Leg traversal count differs')
    return {'repetitions': n, 'outgoing_traversals': counts['outgoing'], 'returning_traversals': counts['returning'],
            'total_traversals': len(events), 'distinct_event_ids': len(ids),
            'native_closure_count': None, 'native_beat_count': None,
            'native_count_status': 'not_asserted', 'fixture_binding': ledger['fixture_binding']}


def evaluate(fixture, ledger):
    geometry = check_fixture(fixture)
    events = validate_event_ledger(fixture, ledger)
    repetition_results = [validate_event_ledger(fixture, build_event_ledger(fixture, n)) for n in range(1, 65)]
    q4 = [''.join(v) for v in product('01', repeat=4)]
    directed_edges = [(a, b) for a in q4 for b in q4 if hamming(a, b) == 1]
    require(all(sum(map(int, a)) % 2 != sum(map(int, b)) % 2 for a, b in directed_edges), 'Q4 parity failure')
    square = ['0000', '1000', '1100', '0100', '0000']
    require(all(hamming(a, b) == 1 for a, b in zip(square, square[1:])), 'Counterexample is not an H1 walk')
    return {'schema_version': 1, 'verification_status': 'verified_illustrative_contract',
            'assertion_scope': 'Finite Q4 incidence and externally supplied traversal counting only',
            'source_bindings': list(SOURCE_BINDINGS), 'geometry': geometry, 'events': events,
            'repetition_cases_checked': len(repetition_results), 'q4_directed_edges_checked': len(directed_edges),
            'four_edge_counterexample': {'addresses': square, 'traversals': 4, 'multiple_of_six': False,
                                        'native_admission': 'not_asserted'},
            'fixture_sha256': sha(fixture), 'event_ledger_sha256': sha(ledger),
            'native_admission': 'not_asserted', 'native_execution': 'not_asserted',
            'empirical_status': 'not_tested'}


def verify(root):
    directory = Path(root) / 'manual2/data/m1/folding'
    fixture = read_json(directory / 'two_square_fold.json')
    ledger = read_json(directory / 'event_ledger.json')
    report = evaluate(fixture, ledger)
    path = directory / 'folding_report.json'
    try:
        require(path.read_bytes() == canonical_bytes(report), 'Persisted folding report differs from evaluated contract')
    except OSError as exc:
        raise ValidationError(f'{path}: {exc}') from exc
    return report
