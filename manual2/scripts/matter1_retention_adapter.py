"""Replay the constructed inputs and state the missing aggregate retention map.

This assessment introduces no transition, capacity or loss law. R02 and R03
remain separate models. Their original contexts, rather than an artifact's
embedded summaries or resealed hashes, authorize each reconstructed record.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import gc
import hashlib
import json
from pathlib import Path
import sys

from matter1_atomic import canonical, read_json, require
import matter1_constructed_coupling as constructed
import matter1_witnessed_retention as retention
from matter1_constructed_source import historical_recipe_digest

ROOT = Path(__file__).resolve().parents[2]
DATA = Path('manual2/data/m1/retention_adapter')
PROFILE = 'matter1:retention-adapter-assessment:v1'
PRODUCTS = ('assessment.json', 'sha256.json')
SELECTION = ('configurations/Fl-286', 'configurations/Fl-289', 'r02/baseline')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def history(rows):
    """Compact identity of the complete ordered records, without duplicating them."""
    value = hashlib.sha256()
    count = 0
    for row in rows:
        value.update(canonical(row)); value.update(b'\n'); count += 1
    return {'records': count, 'sha256': value.hexdigest()}


def validate_context(root, context):
    require(constructed.sha(Path(root)/'manual2/scripts/matter1_retention_adapter.py') ==
            constructed.sha(Path(__file__)), 'Root assessment implementation differs from executing source')
    require(type(context) is dict and set(context) == {'profile', 'case', 'contract', 'preparation'},
            'Complete original construction context required')
    require(context['profile'] in (constructed.PROFILE, constructed.PAIRED_PROFILE),
            'Unknown constructed model identity')
    declared = context['contract']
    frozen = read_json(Path(root)/constructed.DATA/'source_packet/contract.json')
    require(type(declared) is dict and set(declared) == set(frozen),
            'Construction contract fields differ')
    varying = {'Z', 'N', 'selected_label', 'engine_start_cut', 'intervention_cut',
               'horizon_cut', 'window_endpoints'}
    require(all(canonical(declared[k]) == canonical(frozen[k]) for k in frozen if k not in varying),
            'The frozen common construction law changed')
    require(context['case'] in constructed.R02_CASES, 'Unknown constructed case')
    require(all(type(declared[k]) is int for k in ('Z', 'N', 'engine_start_cut',
                'intervention_cut', 'horizon_cut')), 'Exact construction integers required')
    require(declared['Z'] > 0 and declared['N'] > 0, 'Positive constituent counts required')
    require(type(declared['window_endpoints']) is list and
            all(type(x) is int for x in declared['window_endpoints']), 'Exact window endpoints required')
    preparation = context['preparation']
    require(type(preparation) is dict and set(preparation) == set(constructed.default_contract(root)['preparations'][0]),
            'Complete preparation record required')
    require(all(type(preparation[k]) is int for k in ('Z', 'N', 'A')) and
            (preparation['Z'], preparation['N'], preparation['A']) ==
            (declared['Z'], declared['N'], declared['Z'] + declared['N']),
            'Preparation and actual constituent inventory differ')
    require(preparation['physical_preparation'] is None and preparation['internal_nuclear_couplings'] is None,
            'The constructed source does not supply physical preparation or internal nuclear dynamics')
    return deepcopy(context)


def case_assessment(root, *, original_context):
    """Reexecute one independently supplied construction, including its admission."""
    root = Path(root)
    context = validate_context(root, original_context)
    engine_module = constructed.engine_module(root)
    engine = engine_module.Engine(deepcopy(context['contract']), context['case']).run()
    admission = engine.validate()
    parent = engine.fields['P']; reference = engine.fields['R']
    summary = constructed.case_summary(engine)
    ordered_terms = [row for row in engine.loads if parent.returns[1] < row['cut'] <= engine.end]
    packets = {row['id']: row for row in engine.packets}
    response_terms = [{**row, 'signed_term': row['rho'] * packets[row['contact_id']]['lag_at_emission'],
                       'emission_cut': packets[row['contact_id']]['emitted'],
                       'emission_prefix': packets[row['contact_id']]['source_prefix']}
                      for row in ordered_terms]
    require(all(row['emission_cut'] < row['cut'] for row in response_terms),
            'Returned burden reads an uncommitted emission')
    require(sum(row['nonnegative_term'] for row in response_terms) == summary['nonnegative_burden'],
            'Burden differs from the committed contribution history')
    responses = {row['binding']: row for row in engine.pressures if row['field'] == 'P'}
    clicks = {row['id']: row for row in engine.clicks}
    witness = None
    for action in parent.actions:
        response = responses.get(action['pressure_binding'])
        if response is None or action['kind'] == 'start':
            continue
        ids = sorted({identity for term in response['terms'] for identity in term.get('contact_ids', [])})
        if not ids:
            continue
        require(response['cut'] < action['cut'] and all(clicks[i]['committed'] < action['cut'] for i in ids),
                'Construction response is not strictly earlier than its affected action')
        witness = {'response_cut': response['cut'], 'affected_action': action,
                   'contact_ids': ids, 'contact_commit_cuts': [clicks[i]['committed'] for i in ids],
                   'pressure_binding': response['binding']}
        break
    require(witness is not None, 'No actual later response/action witness')
    constituent_rows = [{'identity': w.identity, 'scope': w.scope, 'scale': w.scale,
                         'return_ids': [t.return_id for t in w.returns],
                         'trace_digests': [t.trace_digest for t in w.returns],
                         'certificate_digests': [c.certificate_digest for c in w.certificates]}
                        for w in parent.inner]
    record = {'schema': 'matter1-retention-adapter-case-v1',
        'original_context': context, 'original_context_sha256': digest(context),
        'source_bindings': constructed.check_sources(root),
        'actual_construction': {
            'parent_identity': parent.identity, 'scope': parent.wave().scope, 'scale': parent.wave().scale,
            'distinct_constituents': len(parent.inner), 'constituent_histories': history(constituent_rows),
            'frozen_inner_formation_histories': True, 'evolving_aggregate_fields': len(engine.fields),
            'scope_map_sha256': engine_module.digest(parent.occurrence_map),
            'fold_proposal_sha256': engine_module.n.digest(parent.proposal),
            'outward_occurrences': parent.branch, 'structural_RD': parent.rd,
            'complete_parent_returns': [{'id': t.return_id, 'committed': t.indices[-1],
                'trace_sha256': t.trace_digest, 'certificate_sha256': cert.certificate_digest}
                for t, cert, _ in parent.records],
            'committed_parent_prefix': parent.prefix(engine.end),
            'directed_channels': [list(key) for key in sorted(engine.channels)],
            'full_wave_prefixes': {name: field.prefix(engine.end) for name, field in engine.fields.items()}},
        'reference': {'identity': reference.identity, 'structural_RD': reference.rd,
                      'prefix_sha256': reference.prefix(engine.end),
                      'new_bips': summary['counts']['reference_bips'],
                      'physical_clock_identification': None},
        'native_admission': {'admitted_outer_waves': admission['admitted_outer_waves'],
                            'admitted_distinct_parent_constituents': admission['admitted_distinct_parent_constituents'],
                            'directional_comparisons': admission['native_P_R_comparisons']},
        'complete_history': {'actions': history(engine.actions), 'emitted_currents': history(engine.packets),
            'returned_currents': history(engine.clicks), 'pressure_updates': history(engine.pressures),
            'burden_operands': history(response_terms),
            'directed_contacts': {receiver+'<-'+sender: history(asdict(e) for e in channel.events)
                                  for (receiver, sender), channel in sorted(engine.channels.items())},
            'pending_currents': history(engine.pending[k] for k in sorted(engine.pending))},
        'existing_cadence_law_causal_witness': witness,
        'counts': summary['counts'],
        'burden': {'signed_response': str(summary['signed_response_diagnostic']),
                   'nonnegative_sum': str(summary['nonnegative_burden']),
                   'contributing_contacts': len(response_terms), 'contributions_retained': True},
        'retention_mapping': {'kernel_state': None, 'decision_schedule': None, 'normalization': None,
            'capacity': None, 'loss_predicate': None, 'exposure_operation': None,
            'status': 'unprovided; the cadence response witness does not define a retention decision'},
        'survival_probability': None, 'loss_reference_count': None, 'ensemble_median': None,
        'horizon_status': 'construction horizon reached; no defined loss observable or survival censoring claim',
        'physical_seconds': None, 'physical_isotope_admission': False}
    record['record_sha256'] = digest(record)
    del engine
    gc.collect()
    return record


def verify_case_assessment(record, *, original_context, root=ROOT):
    require(canonical(record) == canonical(case_assessment(root, original_context=original_context)),
            'Adapter case differs from independent original-context replay')
    return True


def square_domain(root):
    """Recreate the original cancellation case; none of its choices transfer."""
    retention.verify_sources(root)
    contract = retention.default_contract(root)
    frame, _, _ = retention.prepare_prefix(contract, 'burden', '+-')
    decision = frame.prepare_next(); frame.validate()
    return {'model_id': retention.MODEL_ID, 'original_contract_sha256': digest(contract),
        'case': 'burden', 'prefix': '+-', 'reference_identity': frame.reference.identity,
        'reference_structural_RD': frame.channel_operands('reference')['support_RD'],
        'raw_normalization_unit': frame.unit, 'raw_capacity': str(frame.capacity),
        'raw_signed_response': str(frame.raw_signed()), 'raw_burden': str(frame.raw_burden()),
        'decision_exit_probability': decision['probabilities']['exit'],
        'complete_context_sha256': retention.digest(frame.proofs()),
        'inner_model': 'one evolving candidate square retained through outer folds',
        'loss_model': contract['loss'], 'transferred_to_aggregate': False}


def original_contexts(root=ROOT):
    contract = constructed.validate_contract(root, read_json(Path(root)/constructed.DATA/'model_contract.json'))
    contexts = constructed.contexts(contract)
    return {key: contexts[key] for key in SELECTION}


def assess(root=ROOT, *, originals):
    root = Path(root)
    require(canonical(originals) == canonical(original_contexts(root)),
            'The three bound investigation contexts differ')
    records = {}
    for key in SELECTION:
        print('assessing retention map '+key, file=sys.stderr, flush=True)
        records[key] = case_assessment(root, original_context=originals[key])
    result = {'schema': 'matter1-retention-adapter-assessment-v1', 'profile': PROFILE,
        'classification': 'replayed construction and unprovided adapter; no combined model executed',
        'implementation_sha256': historical_recipe_digest(root, 'manual2/scripts/matter1_retention_adapter.py'),
        'constructed_application_sha256': historical_recipe_digest(root),
        'retention_application_sha256': constructed.sha(Path(retention.__file__)),
        'common_cadence_law': 'matter1-constructed-coupling-v1',
        'cases': records, 'R03_square_domain': square_domain(root),
        'missing_bindings': {
            'state': 'No map from the many-constituent aggregate and frozen inner formation histories to the evolving R03 square candidate is supplied.',
            'event_order': 'Existing strictly later cadence responses are witnessed; a retention decision schedule and its committed-input selection remain unspecified.',
            'normalization': 'R02 reference structural RD is 61; R03 raw unit is 5. No aggregate burden-to-kernel normalization is supplied.',
            'capacity': 'The square raw capacity 5 is a fixture choice. An aggregate capacity law or independently selected family member is not supplied.',
            'reference': 'R02 has its own complete reference-return history. No map to R03 rounds or observed elapsed time is supplied.',
            'loss': 'No aggregate loss predicate, exposure operation or daughter transformation is supplied; emitted currents are not parent decay.'},
        'scientific_obligations': {
            'SURV-ATOM-01': 'Physical isotope/state/preparation identification and resolved internal nuclear dynamics remain unprovided.',
            'SURV-ATOM-02': 'A common cadence law is executed; aggregate retention normalization, capacity, update and loss bindings remain unprovided.',
            'SURV-ATOM-03': 'Physical loss endpoint, daughter identity and reference-to-observed-time mapping remain unprovided.',
            'SURV-ATOM-04': 'Physical preparation, discrepancy, realization, detection/censoring and dependent uncertainty remain unprovided.'},
        'experimental_inputs_read': [], 'fitted_parameters': [], 'combined_loss_model': None,
        'physical_half_life': None, 'Fl-298': 'unscored'}
    result['assessment_sha256'] = digest(result)
    return result


def verify_assessment(record, *, originals, root=ROOT):
    require(canonical(record) == canonical(assess(root, originals=originals)),
            'Adapter assessment differs from complete original-context replay')
    return True


def generate(root=ROOT):
    report = canonical(assess(root, originals=original_contexts(root)))
    return {'assessment.json': report,
            'sha256.json': canonical({'assessment.json': hashlib.sha256(report).hexdigest()})}


def verify(root=ROOT, artifact_root=None):
    root = Path(root); destination = Path(artifact_root or root)/DATA
    require({p.name for p in destination.iterdir()} == set(PRODUCTS),
            'Adapter product inventory differs')
    actual = {name: (destination/name).read_bytes() for name in PRODUCTS}
    require(actual == generate(root), 'Persisted adapter assessment differs from original-context replay')
    return {'profile': PROFILE, 'status': 'PASS_SCOPED_ASSESSMENT', 'products': list(PRODUCTS),
            'cases': list(SELECTION), 'combined_loss_model': False, 'physical_prediction': False}
