"""Target-free, isotope-indexed finite inner-recurrence campaign.

Native primitives admit the retained construction and its subsequent reclosures.
The ring preparation, round barrier, orientation kernel and pacing rule below
are declared application choices. They do not identify an atomic preparation,
FRG ring gate, nuclear loss channel, emitted photon or physical clock.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, replace, fields, is_dataclass
from fractions import Fraction as Q
import hashlib
import importlib.util
import sys
from itertools import product
import json
from pathlib import Path
import random

import matter1_constructed_coupling as bound

ROOT = Path(__file__).resolve().parents[2]
PROFILE = 'matter1:inner-recurrence-campaign:v1'
CONFIG_KEYS = {'z', 'a', 'electron_count', 'rounds', 'seed', 'feedback'}
CURRENT_NATIVE_SHA = '3ba98c7097bc104aeb6218265b8531f94f2ca5a35239d0df097aba096675dfdf'
CURRENT_HEAD = '71cbcf7e637ababcde3b2e073fb4ceec4b1681b9'
_MODULES = {}
RULE = {
    'preparation': 'distinct p(3,3), n(3,4), e(1,2) seeds; ordered directed ring; common outer enclosure',
    'rounds': 'all inner returns and their emitted cross-returns commit before the next round',
    'kernel': '(1+max(0,R),1+max(0,-R)), normalized exactly, orientations (+1,-1)',
    'pacing': 'own RD + last-two-contact RCD + max(0,R); feedback-off uses own RD after the first common round',
    'response': 'R = orientation_at_emission * RCD * committed receiver-minus-sender recurrence lag',
    'reflection_map': 'declared application bridge: (max(0,lag),max(0,-lag)) directional reflection counts; max(0,lag) adds reflected support extent; admission does not derive this map',
    'outer_return': 'one new outer closure after all inner rounds, bound to their extended prefixes',
    'reference': 'independent 3:3:6 recurrence with RD-paced traversals, one-cut restart',
    'state': 'complete ordered inner returns, contacts, pending/current round, and RNG state; no histories merged',
    'loss_rule': None,
    'physical_identification': None,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def default_config(z, a, electron_count=None):
    return validate_config({'z': z, 'a': a, 'electron_count': z if electron_count is None else electron_count,
                            'rounds': 3, 'seed': 20261109, 'feedback': True})


def validate_config(config):
    require(type(config) is dict and set(config) == CONFIG_KEYS, 'Complete campaign configuration required')
    require(all(type(config[k]) is int for k in CONFIG_KEYS - {'feedback'}), 'Exact campaign integer required')
    require(type(config['feedback']) is bool, 'Feedback switch must be Boolean')
    require(1 <= config['z'] <= 118 and config['z'] <= config['a'] <= 400, 'Invalid isotope inventory')
    require(0 <= config['electron_count'] <= config['z'], 'Electron count outside declared neutral/ion domain')
    require(1 <= config['rounds'] <= 8 and 0 <= config['seed'] < 2**32, 'Campaign budget or seed invalid')
    return deepcopy(config)


def inventory(config):
    c = validate_config(config)
    return tuple([(f'p{j:03d}', 3, 3) for j in range(c['z'])] +
                 [(f'n{j:03d}', 3, 4) for j in range(c['a'] - c['z'])] +
                 [(f'e{j:03d}', 1, 2) for j in range(c['electron_count'])])


def remove_neutron(config):
    c = validate_config(config)
    require(c['a'] > c['z'], 'Neutron removal is inapplicable to N=0')
    c['a'] -= 1
    return c


def kernel(response):
    require(type(response) is int, 'Exact signed response required')
    weights = (1 + max(0, response), 1 + max(0, -response))
    return weights, tuple(Q(w, sum(weights)) for w in weights)


@dataclass
class Construction:
    config: dict
    module: object
    field: object
    reference: object
    summary: dict


def _memoize_native(module):
    """Cache pure checks only for the same immutable native object, per case.

    Strong references prevent Python id reuse. Every newly constructed/replaced
    trace, wave or motif is checked by the unchanged original function. Registry
    membership checks in admitted() are never cached. Caches are cleared at the
    start of each independent case and cannot authorize a supplied artifact.
    """
    cache = {'wave': {}, 'motif': {}, 'certificate': {}, 'immutable': {}}
    module._campaign_cache_enabled = True
    module._campaign_cache_types = (module.Trace, module.Certificate, module.ReflectionWitness, module.Wave, module.MotifWitness)
    originals = {name: getattr(module, name) for name in ('validate_wave','validate_motif','certify')}
    def immutable(value):
        if type(value) in (str, int, bool, bytes, type(None), Q):
            return True
        if id(value) in cache['immutable']:
            return True
        if type(value) is tuple:
            valid = all(immutable(x) for x in value)
        elif type(value) in module._campaign_cache_types and is_dataclass(value):
            valid = value.__dataclass_params__.frozen and all(immutable(getattr(value, f.name)) for f in fields(value))
        else:
            valid = False
        if valid:
            cache['immutable'][id(value)] = value
        return valid
    def checked_wave(w):
        if not module._campaign_cache_enabled or not immutable(w):
            return originals['validate_wave'](w)
        key = id(w)
        if key not in cache['wave']:
            result = originals['validate_wave'](w)
            cache['wave'][key] = (w, result)
        return cache['wave'][key][1]
    def checked_motif(m):
        if not module._campaign_cache_enabled or not immutable(m):
            return originals['validate_motif'](m)
        key = id(m)
        if key not in cache['motif']:
            result = originals['validate_motif'](m)
            cache['motif'][key] = (m, result)
        return cache['motif'][key][1]
    def checked_certificate(t, motif='Monon', *, inner=()):
        inner = tuple(inner)
        if not module._campaign_cache_enabled or not immutable(t) or not immutable(inner) or type(motif) is not str:
            return originals['certify'](t, motif, inner=inner)
        key = (id(t), motif, tuple(map(id, inner)))
        if key not in cache['certificate']:
            result = originals['certify'](t, motif, inner=inner)
            cache['certificate'][key] = (t, inner, result)
        return cache['certificate'][key][2]
    module.validate_wave = checked_wave
    module.validate_motif = checked_motif
    module.certify = checked_certificate
    module._campaign_validation_cache = cache
    module._campaign_original_validators = originals


def _engine(root):
    """Reuse the historical constructor recipe with the current bound native API.

    Neither the historical module nor its import binding is modified. This
    adapter executes a separately imported constructor class, whose native
    types and every admission call come from the current 71cbcf7 export.
    """
    root = Path(root).resolve()
    historical = bound.check_sources(root)
    native_path = root/'manual2/vendor/aod_m3/current/aod_native_closure_wave.py'
    require(hashlib.sha256(native_path.read_bytes()).hexdigest() == CURRENT_NATIVE_SHA,
            'Current native campaign authority changed')
    binding = json.loads((root/'manual2/vendor/aod_m3/binding.json').read_text())
    require(binding['upstream_head'] == CURRENT_HEAD and
            binding['files']['current/aod_native_closure_wave.py']['sha256'] == CURRENT_NATIVE_SHA,
            'Current native binding differs')
    key = str(root)
    if key not in _MODULES:
        tag = hashlib.sha256(key.encode()).hexdigest()[:16]
        def load(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            return module
        native = load('_campaign_current_native_'+tag, native_path)
        _memoize_native(native)
        previous = sys.modules.get('aod_native_closure_wave')
        paths = list(sys.path)
        try:
            sys.modules['aod_native_closure_wave'] = native
            module = load('_campaign_constructor_'+tag,
                          root/bound.DATA/'source_packet/constructed_coupling.py')
        finally:
            sys.path[:] = paths
            if previous is None:
                sys.modules.pop('aod_native_closure_wave', None)
            else:
                sys.modules['aod_native_closure_wave'] = previous
        require(module.n is native, 'Campaign admission used an ambient native implementation')
        native._campaign_cache_types += (module.CountTrace,)
        _MODULES[key] = module
    return _MODULES[key], {'constructor_recipe': historical,
                          'native_head': CURRENT_HEAD, 'native_sha256': CURRENT_NATIVE_SHA,
                          'native_role': 'current admission/execution API; historical constructor recipe reused explicitly',
                          'optimization': 'per-case identity cache of pure immutable-object validation; original predicates retained'}


def construct(config, root=ROOT, *, _cached=True):
    config = validate_config(config)
    module, source_binding = _engine(root)
    module.n._campaign_cache_enabled = _cached
    for cache in module.n._campaign_validation_cache.values():
        cache.clear()
    specs = inventory(config)
    parent = module.FoldedField('campaign-parent', specs, 0)
    reference = module.FoldedField('campaign-reference', (('campaign-reference', 3, 3),), 0)
    module.n.validate_wave(parent.wave())
    module.n.validate_wave(reference.wave())
    inner = [{'id': spec[0], 'p': spec[1], 'q': spec[2], 'wave_identity': wave.identity,
              'scope': wave.scope, 'scale': wave.scale,
              'return_ids': [t.return_id for t in wave.returns],
              'certificate_sha256': [c.certificate_digest for c in wave.certificates]}
             for spec, wave in zip(specs, parent.inner)]
    summary = {'profile': PROFILE, 'z': config['z'], 'a': config['a'],
               'electron_count': config['electron_count'], 'constituents': inner,
               'native_construction_admitted': True, 'native_atomic_identification': False,
               'parent_identity': parent.identity, 'scope': parent.wave().scope, 'scale': parent.wave().scale,
               'outward_occurrences': parent.branch, 'structural_RD': parent.rd,
               'formation_returns': [t.return_id for t, _, _ in parent.records],
               'scope_map_sha256': module.digest(parent.occurrence_map),
               'fold_proposal_sha256': module.n.digest(parent.proposal),
               'inner_to_outer_maps': [list(item[:5]) for item in parent.proposal],
               'reference_identity': reference.identity, 'reference_RD': reference.rd,
               'execution_source_binding': source_binding}
    return Construction(config, module, parent, reference, summary)


def _trace_record(module, t):
    cert = module.n.certify(t)
    return t, cert, {cert.certificate_digest: cert}


def _return_row(t, cert):
    return {'return_id': t.return_id, 'start': t.indices[0], 'committed': t.indices[-1],
            'trace_sha256': t.trace_digest, 'certificate_sha256': cert.certificate_digest,
            'orientation': t.roles[0], 'atomic_traversals': len(t.vertices) - 1,
            'hinge_count': len(t.roles) - 2}


def _inner_return(module, spec, old_wave, start, pacing, orientation, occurrence):
    name, p, q = spec
    seed, catalogue, components = module.constituent(*spec)
    axes = tuple(item[-1] for item in catalogue)
    if orientation < 0:
        axes = tuple(reversed(axes))
    vertices = module.vertices_from_axes(axes)
    branch = len(axes)
    indices = tuple(start + (k - start) * pacing for k in module.indices_for(start, branch))
    t = module.bound_trace(seed.lineage, f'campaign:{occurrence}', vertices, indices,
                           branch, seed.scope, seed.scale)
    t = replace(t, roles=(orientation, 0, -orientation))
    cert = module.n.certify(t)
    registry = {c.certificate_digest: c for c in (*seed.certificates, cert)}
    registry.update({c.certificate_digest: c for _, c, _ in components})
    ids = tuple(c.return_id for _, c, _ in components)
    motif = module.n.motif_witness(f'{p}:{q}', t, (tuple(ids for _ in range(p)), ids),
                                   tuple((x, c) for x, c, _ in components), registry,
                                   enclosure=6, chirality=orientation)
    records = [(x, c, {c.certificate_digest: c}) for x, c in zip(old_wave.returns, old_wave.certificates)]
    records.append((t, cert, registry))
    wave = module.n.wave(records, (*old_wave.motif_witnesses, motif))
    require(wave.identity == old_wave.identity, 'Inner identity changed during recurrence')
    return wave, _return_row(t, cert)


def _contact(module, left, right, sender_spec, start, identity, lag, orientation):
    _, catalogue, _ = module.constituent(*sender_spec)
    branch = len(catalogue)
    vertices = module.vertices_from_axes(tuple(item[-1] for item in catalogue))
    t = module.bound_trace(left.identity + '|' + right.identity, identity, vertices,
                           module.indices_for(start, branch, max(0, lag)), branch,
                           left.scope, left.scale)
    t = replace(t, roles=(orientation, 0, -orientation))
    cert = module.n.certify(t)
    event = module.n.Contact(identity, left.identity, right.identity, left.scope, t.indices[-1],
                            module.n.wave_prefix(left, t.indices[-1]),
                            module.n.wave_prefix(right, t.indices[-1]),
                            (max(0, lag), max(0, -lag)), t, cert)
    module.n.admitted(t, cert, {cert.certificate_digest: cert})
    return event


def _rcd(module, left, right, events, support):
    selected = events[-2:]
    require(len(selected) == 2, 'Two distinct committed contacts required')
    measured = module.n.compare(left, right, tuple(selected),
                                window=(0, selected[-1].committed))
    require(measured['rcd'].support == support, 'Channel support accessor differs from its admitted traces')
    return measured['rcd']


def _execute(config, construction, forced=None):
    c = construction.module
    n = c.n
    specs = inventory(config)
    waves = list(construction.field.inner)
    rng = random.Random(config['seed'])
    count = len(specs)
    channels = {}
    responses = [0] * count
    rcds = [0] * count
    response_cuts = [0] * count
    contact_rows, return_rows, decisions = [], [], []
    end_formation = construction.field.returns[-1]
    cursor = end_formation + 1
    # One incoming ring edge per constituent; a one-constituent construction
    # has no artificial self-coupling. Two contacts precede all execution.
    for receiver in range(count):
        sender = (receiver - 1) % count
        if sender == receiver:
            continue
        events = []
        for occurrence in range(2):
            event = _contact(c, waves[receiver], waves[sender], specs[sender], cursor,
                             f'formation:{sender}:{receiver}:{occurrence}', 0, 1)
            cursor = event.committed + 1
            events.append(event)
            contact_rows.append({'id': event.identity, 'receiver': receiver, 'sender': sender,
                                 'emitted': event.support_trace.indices[0] - 1,
                                 'committed': event.committed, 'lag_at_emission': 0,
                                 'orientation': 1, 'formation': True,
                                 'support_return_id': event.support_trace.return_id,
                                 'left_prefix': event.left_prefix, 'right_prefix': event.right_prefix,
                                 'support_trace_sha256': event.support_trace.trace_digest,
                                 'signed_response': 0, 'opposite_response': 0})
        channels[receiver] = events
        rcd = _rcd(c, waves[receiver], waves[sender], events, 2*len(c.constituent(*specs[sender])[1])+1)
        rcds[receiver] = rcd.duration()
        response_cuts[receiver] = events[-1].committed
    execution_start = cursor
    conditional_mass = Q(1)
    forced_iterator = iter(forced) if forced is not None else None
    for round_index in range(config['rounds']):
        round_start = cursor
        next_waves = []
        current = []
        orientations = []
        for i, (spec, wave) in enumerate(zip(specs, waves)):
            feedback_active = config['feedback'] or round_index == 0
            response = responses[i] if feedback_active else 0
            weights, probabilities = kernel(response)
            draw = rng.randrange(sum(weights))
            orientation = 1 if draw < weights[0] else -1
            if forced_iterator is not None:
                orientation = next(forced_iterator)
                require(orientation in (-1, 1), 'Invalid forced orientation')
            probability = probabilities[0 if orientation == 1 else 1]
            conditional_mass *= probability
            rd = 2*len(c.constituent(*spec)[1])+1
            pace = rd + (rcds[i] + max(0, response) if feedback_active else 0)
            require(response_cuts[i] < round_start, 'Same-step or future response consumed')
            new_wave, row = _inner_return(c, spec, wave, round_start, pace, orientation, round_index)
            row.update({'round': round_index, 'constituent': i, 'constituent_id': spec[0], 'pacing': pace})
            current.append(row)
            next_waves.append(new_wave)
            orientations.append(orientation)
            decisions.append({'round': round_index, 'constituent': i, 'start': round_start,
                              'response_cut': response_cuts[i], 'response': response,
                              'rcd': rcds[i], 'feedback_active': feedback_active, 'pacing': pace, 'weights': list(weights),
                              'probabilities': list(map(str, probabilities)), 'draw': draw,
                              'orientation': orientation, 'selected_probability': str(probability),
                              'consumed_contact_ids': [e.identity for e in channels.get(i, [])[-2:]],
                              'prior_wave_prefix': n.wave_prefix(wave, round_start-1)})
        return_rows.extend(current)
        cursor = max(row['committed'] for row in current) + 1
        # Build emissions at each genuine reclosure, then commit their returned
        # supports in temporal order. Prefixes include only returns by that cut.
        pending = []
        for receiver in range(count):
            sender = (receiver - 1) % count
            if sender == receiver:
                continue
            emitted = current[sender]['committed']
            source = next_waves[sender]
            target = next_waves[receiver]
            source_phase = sum(t.indices[-1] <= emitted for t in source.returns)-1
            target_phase = sum(t.indices[-1] <= emitted for t in target.returns)-1
            lag = target_phase-source_phase
            event = _contact(c, target, source, specs[sender], emitted+1,
                             f'current:{round_index}:{sender}:{receiver}', lag, orientations[sender])
            pending.append((event.committed, receiver, sender, emitted, lag, event))
        for _, receiver, sender, emitted, lag, event in sorted(pending):
            channels[receiver].append(event)
            support = 2*len(c.constituent(*specs[sender])[1])+1
            rcd = _rcd(c, next_waves[receiver], next_waves[sender], channels[receiver], support)
            response = orientations[sender]*rcd.duration()*lag
            # One source contribution has two antisymmetric views; neither is
            # discarded when another contribution cancels the aggregate.
            flux = n.aod_flux([(next_waves[receiver].identity, next_waves[sender].identity,
                               rcd.duration(), orientations[sender]*lag, event.identity)])
            n.stokes(flux, {next_waves[receiver].identity})
            responses[receiver] = response
            rcds[receiver] = rcd.duration()
            response_cuts[receiver] = event.committed
            contact_rows.append({'id': event.identity, 'receiver': receiver, 'sender': sender,
                                 'emitted': emitted, 'committed': event.committed,
                                 'source_return_id': current[sender]['return_id'],
                                 'lag_at_emission': lag, 'orientation': orientations[sender], 'formation': False,
                                 'support_return_id': event.support_trace.return_id,
                                 'left_prefix': event.left_prefix, 'right_prefix': event.right_prefix,
                                 'support_trace_sha256': event.support_trace.trace_digest,
                                 'rcd_contact_ids': list(rcd.contact_ids), 'rcd': rcd.duration(),
                                 'signed_response': response, 'opposite_response': -response,
                                 'nonnegative_burden': abs(response)})
            cursor = max(cursor, event.committed+1)
        waves = next_waves
    for wave in waves:
        n.validate_wave(wave)
    return {'waves': waves, 'start': execution_start, 'end': cursor,
            'returns': return_rows, 'contacts': contact_rows, 'decisions': decisions,
            'conditional_path_probability': str(conditional_mass),
            'rng_state_sha256': digest(rng.getstate())}


def _outer_and_reference(construction, execution):
    c = construction.module
    n = c.n
    parent = construction.field
    inner = tuple(execution['waves'])
    proposal = n.fold_proposal(inner, c.OUTER, 1)
    start = execution['end'] + 1
    t = c.bound_trace(parent.lineage, 'campaign:outer', parent.vertices,
                      c.indices_for(start, parent.branch), parent.branch, c.OUTER, 1,
                      'fold:'+n.digest(proposal))
    cert = n.certify(t, 'outer', inner=inner)
    record = (t, cert, {cert.certificate_digest: cert})
    n.fold(inner, record)
    outer = n.wave([*parent.records, record])
    n.validate_wave(outer)
    lo, hi = execution['start']-1, t.indices[-1]
    reference = construction.reference
    period = reference.rd*reference.rd + 1
    ref_start = lo+1
    reference_rows = []
    while ref_start + reference.rd*reference.rd <= hi:
        indices = tuple(ref_start+(k-ref_start)*reference.rd
                        for k in c.indices_for(ref_start, reference.branch))
        rt, rc = reference.add_return(indices, f'campaign:ref:{len(reference_rows)}')
        reference_rows.append(_return_row(rt, rc))
        ref_start += period
    rw = reference.wave()
    n.validate_wave(rw)
    contacts = []
    for index, rr in enumerate(reference_rows):
        contact_start = rr['committed'] + 1
        if contact_start + reference.rd > hi:
            continue
        ct = c.bound_trace(outer.identity+'|'+rw.identity, f'outer-contact:{index}',
                           reference.vertices, c.indices_for(contact_start, reference.branch),
                           reference.branch, c.OUTER, 1)
        cc = n.certify(ct)
        source_phase = sum(x.indices[-1] <= rr['committed'] for x in rw.returns)-1
        target_phase = sum(x.indices[-1] <= rr['committed'] for x in outer.returns)-1
        lag = target_phase-source_phase
        contacts.append(n.Contact(f'outer-contact:{index}', outer.identity, rw.identity, c.OUTER,
                                  ct.indices[-1], n.wave_prefix(outer, ct.indices[-1]),
                                  n.wave_prefix(rw, ct.indices[-1]), (max(0,lag),max(0,-lag)), ct, cc))
    observation = None
    if len(contacts) >= 2:
        measured = n.compare(outer, rw, tuple(contacts), window=(lo, hi))
        observation = {'cadence_ratio': str(measured['ratio']), 'lag': str(measured['lag']),
                       'drift': str(measured['drift']), 'directional_rcd': measured['duration'],
                       'window': [lo, hi], 'parent_new_returns': 1,
                       'reference_new_returns': len(reference_rows),
                       'contact_ids': [e.identity for e in contacts],
                       'reference_identification': 'declared 3:3:6 support; not Cs-133',
                       'phase_unit': 'complete retained return', 'physical_frequency_hz': None}
    return {'outer_return': _return_row(t,cert),
            'outer_wave_identity': outer.identity,
            'new_fold_proposal_sha256': n.digest(proposal),
            'inner_prefixes_extended': all(len(w.returns) == 2+construction.config['rounds'] for w in inner),
            'reference_returns': reference_rows, 'reference_period_cuts': period,
            'outer_contacts': [{'id': e.identity, 'committed': e.committed,
                                'support_return_id': e.support_trace.return_id,
                                'left_prefix': e.left_prefix, 'right_prefix': e.right_prefix}
                               for e in contacts],
            'observation': observation,
            'observation_dependency': None if observation else 'Fewer than two committed cross-returns in this bounded window'}


def run_case(config, root=ROOT, observer=True, *, _forced=None, _cached=True):
    """Execute from original inputs. ``observer`` controls projection only.

    Private forced orientation paths are used solely by the small exact ensemble
    checker; persisted campaign cases use the frozen seeded integer sampler.
    """
    config = validate_config(config)
    construction = construct(config, root, _cached=_cached)
    executed = _execute(config, construction, _forced)
    observed = _outer_and_reference(construction, executed)
    trajectory = {'inner_returns': executed['returns'], 'contacts': executed['contacts'],
                  'decisions': executed['decisions'], 'outer_return': observed['outer_return'],
                  'reference_returns': observed['reference_returns'], 'outer_contacts': observed['outer_contacts']}
    source = bound.check_sources(root)
    return {'schema_version': 1, 'profile': PROFILE, 'original_config': config,
            'configuration_sha256': digest(config), 'rule': RULE, 'rule_sha256': digest(RULE),
            'source_bindings': construction.summary['execution_source_binding'],
            'implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'construction': construction.summary, 'trajectory': trajectory,
            'trajectory_sha256': digest(trajectory),
            'execution': {'status': 'bounded_declared_model_executed',
                          'rounds': config['rounds'], 'inner_reclosures': len(executed['returns']),
                          'new_outer_reclosures': 1, 'contact_records': len(executed['contacts']),
                          'conditional_path_probability': executed['conditional_path_probability'],
                          'rng_state_sha256': executed['rng_state_sha256'],
                          'native_inner_and_outer_returns_admitted': True,
                          'native_frg_gate_executed': False,
                          'sufficient_state': 'complete history retained; no quotient or lumpability claim',
                          'reference_window': [executed['start']-1, observed['outer_return']['committed']]},
            'observation': observed['observation'] if observer else None,
            'observation_dependency': observed['observation_dependency'] if observer else 'Passive projection disabled',
            'updated_fold_proposal_sha256': observed['new_fold_proposal_sha256'],
            'inner_prefixes_extended': observed['inner_prefixes_extended'],
            'physical': {'atomic_state_identification': None, 'emitted_phase_map': None,
                         'nuclear_loss_rule': None, 'survival_probability': None,
                         'half_life_seconds': None, 'frequency_hz': None,
                         'unresolved_dependencies': ['atomic preparation and internal coupling identification',
                             'emitted phase observation map', 'configuration-derived nuclear retention/loss law',
                             'physical calibration and full uncertainty']},
            'empirical_inputs_read': []}


def verify_case(config, result, root=ROOT):
    expected = run_case(config, root)
    require(canonical(result) == canonical(expected), 'Campaign case differs from original-input execution')
    return True


def exact_small_ensemble(config, root=ROOT):
    """Enumerate actual coupled histories, with no scalar-state compression."""
    config = validate_config(config)
    size = len(inventory(config))*config['rounds']
    require(size <= 6, 'Exact control is bounded to at most six binary choices')
    total = Q(0)
    rows = []
    for orientations in product((1,-1), repeat=size):
        result = run_case(config, root, _forced=orientations)
        mass = Q(result['execution']['conditional_path_probability'])
        total += mass
        rows.append({'orientations': list(orientations), 'probability': str(mass),
                     'trajectory_sha256': result['trajectory_sha256'],
                     'outer_commit': result['trajectory']['outer_return']['committed'],
                     'observation': result['observation']})
    require(total == 1, 'Exact path ensemble loses probability')
    return {'profile': PROFILE, 'config': config, 'paths': rows, 'total_probability': str(total),
            'scope': 'exact enumerated conditional histories; no physical isotope assignment'}


def _projection_inputs(result):
    """Validate every field consumed by the compact projection.

    These consistency checks do not replace original-input native replay.
    In particular, a status cannot be promoted by the projection itself.
    """
    require(type(result) is dict and result['profile'] == PROFILE and
            type(result['schema_version']) is int and result['schema_version'] == 1,
            'Unknown campaign engine profile')
    config = validate_config(result['original_config'])
    require(result['configuration_sha256'] == digest(config), 'Configuration binding differs')
    require(result['rule'] == RULE and result['rule_sha256'] == digest(RULE), 'Model rule binding differs')
    source = result['source_bindings']
    require(source['native_head'] == CURRENT_HEAD and source['native_sha256'] == CURRENT_NATIVE_SHA,
            'Native source authority differs')
    c = result['construction']; x = result['execution']; t = result['trajectory']
    require(c['native_construction_admitted'] is True and c['native_atomic_identification'] is False,
            'Construction admission/status is not established by this result')
    require(all(type(c[k]) is int and c[k] == config[k] for k in ('z','a','electron_count')),
            'Construction inventory differs')
    require(x['status'] == 'bounded_declared_model_executed' and
            x['native_inner_and_outer_returns_admitted'] is True and
            x['native_frg_gate_executed'] is False and result['inner_prefixes_extended'] is True,
            'Execution status or admission flag differs')
    expected = {'rounds':config['rounds'],
                'inner_reclosures':(config['a']+config['electron_count'])*config['rounds'],
                'new_outer_reclosures':1, 'contact_records':len(t['contacts'])}
    require(all(type(x[k]) is int and x[k] == v for k,v in expected.items()),
            'Execution count differs from original configuration')
    require(len(t['inner_returns']) == expected['inner_reclosures'] and
            len({r['return_id'] for r in t['inner_returns']}) == expected['inner_reclosures'],
            'Inner return coverage differs')
    require(len(c['constituents']) == config['a']+config['electron_count'] and
            len({r['wave_identity'] for r in c['constituents']}) == len(c['constituents']),
            'Distinct construction constituent count differs')
    require(result['trajectory_sha256'] == digest(t), 'Trajectory binding differs')
    window = x['reference_window']
    require(type(window) is list and len(window)==2 and all(type(v) is int for v in window)
            and window[0] < window[1], 'Invalid exact observation window')
    require(all(type(r[k]) is int for r in t['inner_returns'] for k in ('start','committed')),
            'Invalid inner event cut')
    require(window[0] == min(r['start'] for r in t['inner_returns'])-1 and
            type(t['outer_return']['committed']) is int and t['outer_return']['committed'] == window[1],
            'Observation window not bound to execution')
    physical = result['physical']
    names = ('atomic_state_identification','emitted_phase_map','nuclear_loss_rule',
             'survival_probability','half_life_seconds','frequency_hz')
    require(all(name in physical and physical[name] is None for name in names),
            'Unsupported physical result in generic campaign')
    require(result['empirical_inputs_read'] == [], 'Generic prediction consumed empirical targets')
    observation = result['observation']
    if observation is None:
        require(type(result['observation_dependency']) is str and bool(result['observation_dependency']),
                'Missing observation has no explicit dependency')
    else:
        require(observation['window'] == window and all(type(v) is int for v in observation['window']),
                'Observation and execution windows differ')
        require(all(type(r['committed']) is int for r in t['reference_returns']), 'Invalid reference cut')
        count = sum(window[0] < r['committed'] <= window[1] for r in t['reference_returns'])
        require(count > 0 and type(observation['parent_new_returns']) is int and
                observation['parent_new_returns'] == 1 and type(observation['reference_new_returns']) is int and
                observation['reference_new_returns'] == count, 'Observation return counts differ')
        for key,value in (('cadence_ratio',Q(1,count)),('lag',Q(1-count)),('drift',Q(1-count))):
            require(type(observation[key]) is str and Q(observation[key]) == value,
                    'Observation '+key+' differs from executed return counts')
        require(observation['contact_ids'] == [r['id'] for r in t['outer_contacts']] and
                len(observation['contact_ids']) >= 2 and
                observation['physical_frequency_hz'] is None and
                observation['phase_unit'] == 'complete retained return' and
                result['observation_dependency'] is None, 'Observation support or scope differs')
    return c,x,observation


def summary(result):
    try:
        construction, execution, observation = _projection_inputs(result)
    except (KeyError,TypeError,ZeroDivisionError) as exc:
        raise ValueError('Incomplete or malformed campaign projection input') from exc
    return {'construction_status': 'native_generic_fold_admitted',
            'execution_status': 'declared_finite_dynamics_executed',
            'cadence_ratio': observation['cadence_ratio'] if observation else None,
            'lag': observation['lag'] if observation else None,
            'reference_identity': construction['reference_identity'],
            'reference_window': execution['reference_window'],
            'window_policy': 'from first internal round to one newly completed outer reclosure; configuration-specific endpoints',
            'cadence_definition': 'new parent returns / new independent reference returns in (lo,hi]',
            'lag_definition': 'parent-minus-reference retained-return count, zero declared phase bias',
            'phase_unit': 'complete retained return',
            'cross_configuration_frequency_ratio_identified': False,
            'survival_probability': None, 'half_life_seconds': None,
            'physical_atomic_identification': False,
            'observation_dependency': result['observation_dependency']}
