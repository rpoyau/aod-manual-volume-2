"""Freeze an actual coupled-preparation readout through the current M3 API."""
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction as Q
import hashlib
from pathlib import Path
from unittest.mock import patch

import matter1_coupled_preparations as coupled
import matter1_m3_producer as producer

ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAMES = ('manual2/scripts/matter1_preparation_freeze.py',
                'manual2/scripts/matter1_coupled_preparations.py',
                'manual2/scripts/matter1_m3_producer.py')


def original(root=ROOT, modules=None):
    """Construct the original typed context and separately trusted full plan."""
    root = Path(root)
    api = producer.load(root) if modules is None else modules
    m, t, mt, e = api.mapping, api.temporal, api.metrology, api.experimental
    config = coupled.default_config(1, 1, 1, rounds=1)
    with patch.object(coupled.producer, 'load', return_value=api):
        session = coupled.initialize(config, root)
        coupled.advance(session)
    state = session.state
    population = tuple(state['waves']) + (session.construction.field.wave(),
                                         session.construction.reference.wave())
    contacts = tuple(event for channel in state['channels'].values() for event in channel)
    left, right = population[:2]
    pair = tuple(event for event in contacts if (event.left, event.right) == (left.identity, right.identity))
    window = (0, state['cursor'])
    preparation = {'id': 'matter1:coupled-neutral-H1:one-round:v1', 'parameters': {
        'original_config': config, 'checkpoint_sha256': coupled.digest(coupled.checkpoint(session)),
        'source_binding': session.binding,
        'code_sha256': {n: hashlib.sha256((root/n).read_bytes()).hexdigest() for n in SOURCE_NAMES},
        'comparison': 'Actual proton-motif/electron-motif internal pair; no physical clock identification'}}
    source = m.source('matter1:coupled-neutral-H1:original-setup', 'model', preparation)
    record = t.TemporalInput(left, right, pair, window, biases=(Q(0), Q(0)), prior_lag=Q(0))
    law = t.observation_law([t.domain_for(population, contacts, preparation, window)],
        law_id='matter1:coupled-preparation:stipulated-unit-gains:v1',
        coordinate='stipulated:internal-native-count')
    context = t.ObservationContext(record, population, contacts, preparation, (), (source,), law)
    t.validate_observation_context(context)
    value = t.readouts(context, [{'id': 'count', 'quantity': 'compared_reclosures'}])['outputs']['count']['value']
    base = {'kind': 'native_reclosure_count', 'unit': 'count', 'dimension': [0, 0, 1],
        'domain': [value, value],
        'window': {'coordinate': law['coordinate'], 'epoch': law['epoch_seconds'], 'bounds': list(window)},
        'locator': 'Original executed full population and directed contact history',
        'role': 'model', 'meaning': 'Exact completed native returns under the declared original setup',
        'value': value, 'uncertainty': {'category': 'exact_definition'}, 'components': [], 'corrections': {}}
    unit = {**deepcopy(base), 'kind': 'dimensionless_scale', 'unit': '1', 'window': None,
        'dimension': [0, 0, 0], 'domain': ['1', '1'],
        'value': '1', 'locator': 'Identity readout convention',
        'meaning': 'Exact identity multiplier; no physical gain or gain uncertainty'}
    quantities = m.source('matter1:coupled-neutral-H1:exact-readout', 'model',
                          {'quantities': {'count': base, 'identity': unit}})
    def binding(name):
        return {'schema': mt.QUANTITY_SCHEMA, 'source_id': quantities['id'],
            'source_sha256': quantities['sha256'], 'quantity_id': name,
            'quantity': deepcopy(quantities['payload']['quantities'][name])}
    inputs, parameters = {'identity': binding('identity')}, {'count': binding('count')}
    model = {'method': 'finite_joint_law', 'input_order': ['identity'],
        'input_bindings': {'identity': {'source_sha256': quantities['sha256'], 'quantity_id': 'identity'}},
        'parameter_bindings': {'count': {'source_sha256': quantities['sha256'], 'quantity_id': 'count'}},
        'outputs': {'count': {'kind': base['kind'], 'unit': 'count', 'dimension': [0, 0, 1],
            'domain': None, 'expression': ['mul', ['input', 'identity'], ['parameter', 'count']], 'conversion': None}},
        'support': [['1', {'identity': '1'}]], 'means': None, 'covariance': None, 'bounds': None,
        'interpretation': 'Singleton exact identity convention conditional on this executed path; physical discrepancy is unknown'}
    model_source = m.source('matter1:coupled-neutral-H1:readout-law', 'model',
                            {'uncertainty_models': {'identity': deepcopy(model)}})
    request = {'schema': mt.PROPAGATION_SCHEMA, 'stage': 'prediction', 'inputs': inputs,
        'parameters': parameters, 'model_source_id': model_source['id'], 'model_id': 'identity', 'model': model}
    plan = {'original_context_sha256': m.digest(t.plain(asdict(context))),
        'code_bindings': e.code_bindings(), 'uncertainty_request': request,
        'readout_definitions': [{'id': 'count', 'quantity': 'compared_reclosures'}],
        'readout_parameter_links': {'count': 'count'}, 'reduction_window': list(window),
        'selection': {'candidate_id': preparation['id'], 'rule': 'single_declared_candidate', 'source_ids': [source['id']]},
        'stopping': {'rule': 'fixed_context_window', 'source_ids': [source['id']]},
        'output_definition': {'name': 'count', 'estimator': 'propagated_mean'},
        'comparison_criterion': {'kind': 'signed_residual', 'uncertainty': 'joint_if_supplied_else_partial'},
        'calibration_source_ids': [], 'exposure': 'declared_fixture'}
    owner = m.source('matter1:coupled-neutral-H1:complete-plan', 'model',
                     {'prediction_plans': {'native-count': deepcopy(plan)}})
    plan_binding = {'schema': e.PLAN_SCHEMA, 'id': 'native-count', 'source_id': owner['id'],
                    'source_sha256': owner['sha256'], 'plan': plan}
    trusted = {s['id']: s for s in (source, quantities, model_source, owner)}
    return plan_binding, trusted, context


def build(root=ROOT, modules=None):
    api = producer.load(root) if modules is None else modules
    plan, trusted, context = original(root, api)
    prediction = api.experimental.predict(plan, trusted, original_context=context)
    replayed = api.experimental.predict(plan, trusted, original_context=context)
    if api.mapping.canonical(prediction) != api.mapping.canonical(replayed):
        raise ValueError('Complete application freeze did not replay')
    return {'schema': 'matter1:coupled-preparation-frozen-readout:v1',
        'original_context': api.temporal.plain(asdict(context)),
        'plan_binding': plan, 'trusted_sources': trusted, 'prediction': prediction,
        'replayed': True, 'empirical_inputs_read': [],
        'scope': 'Actual neutral-H1 declared native construction, full internal contact history and explicit parent/reference population; count includes completed formation returns. Exact conditional readout, no physical transition or clock prediction.'}
