"""Source-bound external atomic inventory and pending physical observation map.

This module is deliberately downstream of native generation. Its decimal-ratio
arithmetic transcribes a retrospective measurement, and is not an atomic model.
Validation is non-mutating and remains active with Python optimization enabled.
"""
from __future__ import annotations

import csv
import hashlib
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

PROFILE = 'historical-H1-Cs133-reference-v1'
SUBDIR = Path('manual2/data/m1/hyperfine')
INPUTS = ('target_inventory.json', 'target_exposure.json', 'observation_map.json')
OUTPUT = 'hyperfine_report.json'
H_ID = 'atom:Z001:A001:q0:ground:clock'
CS_ID = 'atom:Z055:A133:q0:ground:clock'
SOURCES = {
    'hellwig1970': 'https://tf.nist.gov/general/pdf/13.pdf',
    'bipm-second': 'https://www.bipm.org/en/si-base-units/second',
    'nist-clock-operation': 'https://www.nist.gov/atomic-clocks/how-atomic-clocks-work/beams-atoms-first-atomic-clocks',
    'nist-hydrogen': 'https://physics.nist.gov/PhysRefData/Handbook/Tables/hydrogentable1_a.htm',
    'nist-cesium': 'https://www.nist.gov/document/jpcrd690pdf',
}
CORRECTIONS = ['wall_collisions', 'cavity_pulling', 'spin_exchange', 'magnetic_fields', 'second_order_doppler']
EVIDENCE_SHA = '94d0dfbe049c66f1e259183abc3ef74dd227d40cc1b0920fc68c98c263f6a3cf'
PDF_SHA = 'e8bba435fbb9e6b54f41fa1d60f9c02df8e06b6a73ce8fab323afb3ea7d02dc4'


class ValidationError(ValueError):
    """The external pilot contract is incomplete, inconsistent, or overstated."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def keys(obj, expected, name):
    require(isinstance(obj, dict) and set(obj) == set(expected.split()), f'{name}: missing or unexpected fields')


def nonempty(value, name):
    require(isinstance(value, str) and bool(value.strip()), f'{name}: required text missing')


def status(obj, field, expected, name):
    require(obj.get(field) == expected, f'{name}.{field}: expected {expected!r}')


def read_bytes(path):
    try:
        return Path(path).read_bytes()
    except OSError as exc:
        raise ValidationError(f'{path}: {exc.strerror}') from exc


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'{path}: duplicate JSON key {key}')
            result[key] = value
        return result
    try:
        return json.loads(read_bytes(path), object_pairs_hook=unique)
    except (ValueError, UnicodeError) as exc:
        raise ValidationError(f'{path}: invalid JSON: {exc}') from exc


def canonical(obj):
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def header(obj):
    require(type(obj['schema_version']) is int and obj['schema_version'] == 1, 'schema version must be 1')
    status(obj, 'profile', PROFILE, 'document')


def fraction(value, name):
    require(isinstance(value, str), f'{name}: rational quantum number must be a string')
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValidationError(f'{name}: invalid rational number') from exc
    require(str(result) == value, f'{name}: noncanonical rational number')
    return result


def validate_inventory(root, inventory):
    keys(inventory, 'schema_version profile inventory_status sources isotopes states transitions clock_operation', 'inventory')
    header(inventory)
    status(inventory, 'inventory_status', 'external_inventory', 'inventory')
    require(isinstance(inventory['sources'], list), 'sources must be a list')
    require({s.get('source_id') for s in inventory['sources']} == set(SOURCES) and len(inventory['sources']) == len(SOURCES), 'primary source IDs differ')
    for source in inventory['sources']:
        source_id = source['source_id']
        fields = 'source_id title url locator accessed status'
        if source_id == 'hellwig1970':
            fields += ' authors publication pdf_sha256 rendered_evidence rendered_sha256 transcription_status transcription_note'
        keys(source, fields, source_id)
        status(source, 'status', 'external_primary_source', source_id)
        require(source['url'] == SOURCES[source_id], f'{source_id}: primary URL binding differs')
        for field in ('title', 'locator', 'accessed'):
            nonempty(source[field], f'{source_id}.{field}')
        if source_id == 'hellwig1970':
            require(source['pdf_sha256'] == PDF_SHA and source['rendered_sha256'] == EVIDENCE_SHA, 'Hellwig source hashes differ')
            require(source['rendered_evidence'] == 'sources/hellwig1970-page200.png', 'rendered evidence path differs')
            require(digest(read_bytes(root / SUBDIR / source['rendered_evidence'])) == EVIDENCE_SHA, 'rendered primary uncertainty evidence differs')
            status(source, 'transcription_status', 'visually_verified', source_id)
            nonempty(source['transcription_note'], 'uncertainty transcription note')
            require('200' in source['locator'], 'primary printed-page locator missing')
    isotopes = inventory['isotopes']
    require(isinstance(isotopes, list) and len(isotopes) == 2, 'pilot requires H-1 and Cs-133 isotopes')
    expected = {
        'atom:Z001:A001:q0': (1, 1, 'H', '1/2', '1s', 'nist-hydrogen'),
        'atom:Z055:A133:q0': (55, 133, 'Cs', '7/2', '[Xe]6s', 'nist-cesium'),
    }
    require({i.get('isotope_id') for i in isotopes} == set(expected), 'isotope identities differ')
    try:
        with (root / 'manual2/data/m1/matter1_elements_1_118_ledger.csv').open(newline='') as stream:
            rows = list(csv.DictReader(stream))
            elements = [row for row in rows if row.get('record_kind') == 'element_reference']
    except (OSError, csv.Error, UnicodeError) as exc:
        raise ValidationError(f'element ledger unreadable: {exc}') from exc
    require(len(elements) == 118, 'element join requires 118 reference rows')
    element_map = {r['declaration_id']: r for r in elements}
    isotope_map = {}
    for isotope in isotopes:
        keys(isotope, 'isotope_id z a symbol charge element_reference_id nuclear_spin_I electronic_configuration term electronic_J label_source_id', 'isotope')
        z, a, symbol, spin, config, source_id = expected[isotope['isotope_id']]
        require(type(isotope['z']) is int and type(isotope['a']) is int and type(isotope['charge']) is int, 'atomic counts must be integers')
        require((isotope['z'], isotope['a'], isotope['symbol'], isotope['charge']) == (z, a, symbol, 0), 'atomic identity or charge differs')
        require((isotope['nuclear_spin_I'], isotope['electronic_J'], isotope['electronic_configuration'], isotope['term'], isotope['label_source_id']) == (spin, '1/2', config, '2S1/2', source_id), 'source-bound atomic ground-state labels differ')
        element_id = f'matter1:reference:Z{z:03d}:A{a:03d}'
        require(isotope['element_reference_id'] == element_id and element_id in element_map, 'element reference join missing')
        require((element_map[element_id]['z'], element_map[element_id]['symbol']) == (str(z), symbol), 'element join changes Z or symbol')
        isotope_map[isotope['isotope_id']] = isotope
    states = inventory['states']
    require(isinstance(states, list) and len(states) == 4, 'four distinct external hyperfine states required')
    state_map = {}
    for state in states:
        keys(state, 'state_id isotope_id electronic_state F m_F quantum_number_status source_id native_configuration_id', 'state')
        require(state['isotope_id'] in isotope_map, 'state isotope foreign key missing')
        isotope = isotope_map[state['isotope_id']]
        i, j = fraction(isotope['nuclear_spin_I'], 'I'), fraction(isotope['electronic_J'], 'J')
        f, mf = fraction(state['F'], 'F'), fraction(state['m_F'], 'm_F')
        require(abs(i - j) <= f <= i + j and (f - abs(i - j)).denominator == 1 and -f <= mf <= f and (f - mf).denominator == 1, 'invalid angular-momentum labels')
        require(mf == 0 and state['electronic_state'] == 'ground', 'pilot must bind m_F=0 ground-state clock levels')
        require(state['state_id'] == state['isotope_id'] + f':ground:F{f}:mF0' and state['state_id'] not in state_map, 'state identity reused or inconsistent')
        status(state, 'quantum_number_status', 'external_state_label', 'state')
        require(state['source_id'] == 'hellwig1970' and state['native_configuration_id'] is None, 'external state must not acquire an unproved native configuration')
        state_map[state['state_id']] = state
    transitions = inventory['transitions']
    require(isinstance(transitions, list) and len(transitions) == 2 and {t.get('transition_id') for t in transitions} == {H_ID, CS_ID}, 'transition inventory differs')
    transition_map = {}
    common = 'transition_id isotope_id state_ids observable unit role source_id native_mapping_status frequency_hz standard_uncertainty_hz uncertainty_kind conditions'
    for transition in transitions:
        tid = transition['transition_id']
        extra = (' measurement_interval corrections reference_transition_id reference_group evaluation_count aggregation_status covariance_status covariance_hz2 evaluation_relation uncertainty_scope' if tid == H_ID else ' realization_uncertainty_hz realization_uncertainty_status')
        keys(transition, common + extra, tid)
        require(transition['isotope_id'] in isotope_map and tid == transition['isotope_id'] + ':ground:clock', 'transition isotope join differs')
        ids = transition['state_ids']
        require(isinstance(ids, list) and len(ids) == 2 and len(set(ids)) == 2 and all(s in state_map for s in ids), 'transition needs two distinct existing states')
        require(all(state_map[s]['isotope_id'] == transition['isotope_id'] for s in ids), 'transition changes isotope')
        require({state_map[s]['F'] for s in ids} == ({'0', '1'} if tid == H_ID else {'3', '4'}), 'clock level pair differs')
        require(transition['observable'] == 'unperturbed_ground_state_hyperfine_frequency' and transition['unit'] == 'Hz', 'detection or other observable cannot replace frequency')
        status(transition, 'native_mapping_status', 'pending', tid)
        nonempty(transition['conditions'], tid + '.conditions')
        if tid == H_ID:
            require((transition['frequency_hz'], transition['standard_uncertainty_hz'], transition['uncertainty_kind'], transition['role'], transition['source_id']) == ('1420405751.768', '0.002', 'reported_one_sigma', 'retrospective_target', 'hellwig1970'), 'H-1 primary transcription or retrospective role differs; printed page 200 gives 0.002 Hz')
            require(transition['measurement_interval'] == '1969-11 through 1970-02' and transition['corrections'] == CORRECTIONS, 'historical conditions/corrections missing')
            require(transition['reference_transition_id'] == CS_ID and transition['reference_group'] == 'NBS-III_shared_reference' and type(transition['evaluation_count']) is int and transition['evaluation_count'] == 2, 'shared reference chain missing')
            status(transition, 'aggregation_status', 'published_combined_result', tid)
            status(transition, 'covariance_status', 'shared_reference_quantitative_covariance_not_transcribed', tid)
            require(transition['covariance_hz2'] is None, 'unknown covariance cannot be replaced by zero')
            for field in ('evaluation_relation', 'uncertainty_scope'):
                nonempty(transition[field], tid + '.' + field)
        else:
            require((transition['frequency_hz'], transition['standard_uncertainty_hz'], transition['uncertainty_kind'], transition['role'], transition['source_id']) == ('9192631770', '0', 'exact_si_definition', 'defining_reference', 'bipm-second'), 'Cs definition binding differs')
            require(transition['realization_uncertainty_hz'] is None, 'unknown realization uncertainty cannot be zero')
            status(transition, 'realization_uncertainty_status', 'not_transcribed', tid)
        transition_map[tid] = transition
    operation = inventory['clock_operation']
    keys(operation, 'source_id counted_observable feedback_observable native_closure_identification', 'clock operation')
    require(operation['source_id'] == 'nist-clock-operation' and operation['counted_observable'] == 'stabilized_oscillator_cycles' and operation['feedback_observable'] == 'detected_state_populations', 'clock feedback and counted recurrence must be distinct')
    status(operation, 'native_closure_identification', 'pending', 'clock operation')
    return transition_map


def validate_exposure(exposure):
    keys(exposure, 'schema_version profile target_transition_id reference_transition_id exposure_status known_by_date first_exposure_date evidence classification independence_evidence_status independence_evidence model_selection_status decision_history native_target_access_policy calibrant_is_held_out per_line_fitting independent_score', 'exposure')
    header(exposure)
    require((exposure['target_transition_id'], exposure['reference_transition_id']) == (H_ID, CS_ID), 'exposure target/reference binding differs')
    for field, expected in {
        'exposure_status': 'known_prior_exposure', 'classification': 'retrospective',
        'independence_evidence_status': 'not_established', 'model_selection_status': 'physical_model_not_selected',
        'native_target_access_policy': 'forbidden',
    }.items():
        status(exposure, field, expected, 'exposure')
    require(exposure['known_by_date'] == '2026-10-26' and exposure['first_exposure_date'] is None, 'record known exposure without inventing earliest exposure')
    require(isinstance(exposure['evidence'], list) and len(exposure['evidence']) >= 2 and all(isinstance(e, str) and e.strip() for e in exposure['evidence']), 'prior exposure evidence missing')
    require(exposure['independence_evidence'] is None and exposure['independent_score'] is None, 'known pilot has no independent prediction evidence or score')
    require(exposure['calibrant_is_held_out'] is False, 'calibrant cannot be held out')
    require(exposure['per_line_fitting'] is False, 'per-line fitting cannot support common-model prediction')
    history = exposure['decision_history']
    require(isinstance(history, list) and len(history) >= 1, 'model decision history missing')
    for event in history:
        keys(event, 'date decision target_visible', 'model decision')
        require(event['target_visible'] is True, 'a later freeze cannot erase prior target exposure')
        nonempty(event['date'], 'decision date')
        nonempty(event['decision'], 'decision description')


def validate_map(mapping, transitions):
    keys(mapping, 'schema_version profile map_status required_stages native_model_id native_model_sha256 scope_id native_admission_status native_execution_status empirical_status model_policy spin_role_identification phase_map_status configuration_bindings recurrence_observable_map transferred_radiation_map predicted_frequency_ratio predicted_phase_lag empirical_score unresolved_dependencies', 'physical observation map')
    header(mapping)
    for field, expected in {
        'map_status': 'pending', 'native_admission_status': 'pending', 'native_execution_status': 'not_executed',
        'empirical_status': 'not_compared', 'model_policy': 'one_frozen_common_fusion_reclosure_model',
        'spin_role_identification': 'not_established', 'phase_map_status': 'pending',
    }.items():
        status(mapping, field, expected, 'physical observation map')
    require(mapping['required_stages'] == ['P4a', 'P2', 'P3'], 'native atomic mapping requires P4a/P2/P3')
    for field in ('native_model_id', 'native_model_sha256', 'scope_id', 'predicted_frequency_ratio', 'predicted_phase_lag', 'empirical_score'):
        require(mapping[field] is None, f'{field}: physical binding/result not established')
    bindings = mapping['configuration_bindings']
    require(isinstance(bindings, list) and len(bindings) == 2 and {b.get('transition_id') for b in bindings} == set(transitions), 'configuration transition bindings differ')
    for binding in bindings:
        keys(binding, 'transition_id state_ids native_before_id native_after_id native_model_id', 'configuration binding')
        require(binding['state_ids'] == transitions[binding['transition_id']]['state_ids'], 'before/after external states differ')
        require(all(binding[f] is None for f in ('native_before_id', 'native_after_id', 'native_model_id')), 'atomic state configuration map not established')
    recurrence = mapping['recurrence_observable_map']
    keys(recurrence, 'external_observable native_observable binding_status binding_id', 'recurrence map')
    require(recurrence['external_observable'] == 'stabilized_oscillator_cycles' and recurrence['native_observable'] == 'distinct_certified_retained_reclosures', 'observable substitution rejected')
    status(recurrence, 'binding_status', 'pending', 'recurrence map')
    require(recurrence['binding_id'] is None, 'no physical recurrence binding established')
    radiation = mapping['transferred_radiation_map']
    keys(radiation, 'status source_window_id destination_window_id physical_map_id sheddic_output_id', 'radiation map')
    status(radiation, 'status', 'pending', 'radiation map')
    require(all(radiation[f] is None for f in ('source_window_id', 'destination_window_id', 'physical_map_id', 'sheddic_output_id')), 'detection cannot be promoted to sheddic output without physical transfer binding')
    deps = mapping['unresolved_dependencies']
    require(isinstance(deps, list) and len(deps) == 6 and all(isinstance(d, str) and d.strip() for d in deps), 'six scoped unresolved physical dependencies must remain recorded')


def evaluate(root):
    """Validate all external inputs, then compute only transcribed ratio arithmetic."""
    root = Path(root)
    inventory, exposure, mapping = [read_json(root / SUBDIR / name) for name in INPUTS]
    transitions = validate_inventory(root, inventory)
    validate_exposure(exposure)
    validate_map(mapping, transitions)
    h, cs = transitions[H_ID], transitions[CS_ID]
    exact_transcription_ratio = Fraction(Decimal(h['frequency_hz'])) / Fraction(Decimal(cs['frequency_hz']))
    with localcontext() as ctx:
        ctx.prec = 40
        ratio = Decimal(h['frequency_hz']) / Decimal(cs['frequency_hz'])
        uncertainty = Decimal(h['standard_uncertainty_hz']) / Decimal(cs['frequency_hz'])
    return {
        'schema_version': 1, 'profile': PROFILE,
        'classification': 'external_retrospective_reference_arithmetic',
        'P4a_status': 'inventory_verified', 'atomic_native_admission_status': 'pending',
        'atomic_native_execution_status': 'not_executed', 'empirical_status': 'not_compared',
        'source_count': len(inventory['sources']), 'isotope_count': len(inventory['isotopes']),
        'state_count': len(inventory['states']), 'transition_count': len(transitions),
        'known_target_exposure_by': exposure['known_by_date'],
        'measured_ratio': {'numerator_transition_id': H_ID, 'denominator_transition_id': CS_ID,
            'decimal_display': format(ratio, '.16f'), 'reported_standard_uncertainty_display': format(uncertainty, '.4E'),
            'transcribed_input_fraction': str(exact_transcription_ratio),
            'arithmetic_scope': 'Exact rational arithmetic of quoted decimal inputs; the measured physical frequency is not exact.',
            'uncertainty_scope': 'Published hydrogen one-sigma uncertainty divided by the exact defining Cs value. No new evaluation or independent recombination of the two shared-reference evaluations.'},
        'physical_map_status': mapping['map_status'], 'required_stages': mapping['required_stages'],
        'unresolved_dependencies': mapping['unresolved_dependencies'],
        'predicted_frequency_ratio': None, 'empirical_score': None,
        'input_sha256': {name: digest(read_bytes(root / SUBDIR / name)) for name in INPUTS},
        'primary_page_sha256': EVIDENCE_SHA,
    }


def generated_bytes(root):
    return canonical(evaluate(root))


def verify(root):
    expected = generated_bytes(root)
    require(read_bytes(Path(root) / SUBDIR / OUTPUT) == expected, 'hyperfine report differs; use explicit generation after validating inputs')
    return json.loads(expected)
