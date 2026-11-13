"""Versioned finite coupled preparations using the authenticated M3 producer.

The inventory, ring, lag bridge and response law are declared application
choices. Native current and retention diagnostics are not atomic frequencies or
nuclear decay predictions. Historical campaign products are never rewritten.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass, replace
from fractions import Fraction as Q
from itertools import product, combinations
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys

import matter1_campaign_engine as legacy
import matter1_m3_producer as producer

ROOT = Path(__file__).resolve().parents[2]
DATA = Path('manual2/data/m1/coupled_preparations')
PROFILE = 'matter1:coupled-preparations:v1'
PRODUCER = '8c3149b9d3d924b80b9385b178da4ba2c39175e8'
LEGACY_SHA = 'ede36a2934a38d9e442fed1bf47b18b248d51b188bc64bdc1f6ad9b26a1f75ef'
PILOTS = tuple((f'H{a}-E{e}', a, e) for a in (1, 2, 3) for e in (0, 1))
SAMPLE_SEEDS = tuple(range(20261111, 20261143))
_RECIPES = {}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def plain(value):
    if is_dataclass(value):
        return plain(asdict(value))
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def canonical(value):
    return (json.dumps(plain(value), sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def default_config(z, a, e=None, *, rounds=2, seed=20261111, feedback=True):
    return legacy.validate_config(dict(z=z, a=a, electron_count=z if e is None else e,
        rounds=rounds, seed=seed, feedback=feedback))


def source_binding(root=ROOT):
    root = Path(root).resolve()
    path = root/'manual2/scripts/matter1_campaign_engine.py'
    require(hashlib.sha256(path.read_bytes()).hexdigest() == LEGACY_SHA,
            'Authenticated historical campaign helpers changed')
    require(path.read_bytes() == Path(legacy.__file__).read_bytes(),
            'Executing historical helper differs from requested source')
    loader_path = root/'manual2/scripts/matter1_m3_producer.py'
    require(loader_path.read_bytes() == Path(producer.__file__).read_bytes(),
            'Executing producer loader differs from requested source')
    api = producer.load(root)
    recipe = legacy.bound.check_sources(root)
    return api, {'producer_commit': PRODUCER,
        'native_sha256': hashlib.sha256(Path(api.native.__file__).read_bytes()).hexdigest(),
        'producer_binding_sha256': digest(api.binding),
        'producer_loader_sha256': hashlib.sha256(loader_path.read_bytes()).hexdigest(),
        'historical_helper_sha256': LEGACY_SHA, 'constructor_recipe': recipe,
        'implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def _recipe(root, api):
    key = (str(Path(root).resolve()), id(api.native))
    if key not in _RECIPES:
        # Only the constructor recipe is reused. Its native import is replaced
        # by the authenticated successor's exact module, never the old export.
        previous = sys.modules.get('aod_native_closure_wave')
        saved_path = list(sys.path)
        name = '_coupled_constructor_'+hashlib.sha256(str(key).encode()).hexdigest()[:12]
        spec = importlib.util.spec_from_file_location(name,
            Path(root)/legacy.bound.DATA/'source_packet/constructed_coupling.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            sys.modules['aod_native_closure_wave'] = api.native
            spec.loader.exec_module(module)
        finally:
            sys.path[:] = saved_path
            if previous is None:
                sys.modules.pop('aod_native_closure_wave', None)
            else:
                sys.modules['aod_native_closure_wave'] = previous
        require(module.n is api.native, 'Constructor used another native authority')
        if not hasattr(api.native, '_campaign_original_validators'):
            legacy._memoize_native(api.native)
        api.native._campaign_cache_types += (module.CountTrace,)
        _RECIPES[key] = module
    return _RECIPES[key]


@dataclass
class Session:
    config: dict
    names: tuple
    construction: object
    binding: dict
    state: dict
    rng: object


def initialize(config, root=ROOT, *, names=None, cached=True):
    config = legacy.validate_config(config)
    api, binding = source_binding(root)
    c = _recipe(root, api)
    c.n._campaign_cache_enabled = cached
    for cache in c.n._campaign_validation_cache.values():
        cache.clear()
    original = legacy.inventory(config)
    names = tuple(x[0] for x in original) if names is None else tuple(names)
    require(len(names) == len(original) and all(type(x) is str and x for x in names)
            and len(set(names)) == len(names), 'Distinct complete constituent names required')
    specs = tuple((name, p, q) for name, (_, p, q) in zip(names, original))
    parent = c.FoldedField('coupled-parent', specs, 0)
    reference = c.FoldedField('coupled-reference', (('coupled-reference', 3, 3),), 0)
    c.n.validate_wave(parent.wave()); c.n.validate_wave(reference.wave())
    summary = {'z': config['z'], 'a': config['a'], 'electron_count': config['electron_count'],
        'charge': config['z']-config['electron_count'], 'constituents': [
            {'id': s[0], 'p': s[1], 'q': s[2], 'wave_identity': w.identity,
             'scope': w.scope, 'scale': w.scale,
             'formation_return_ids': [t.return_id for t in w.returns],
             'certificate_sha256': [x.certificate_digest for x in w.certificates]}
            for s, w in zip(specs, parent.inner)],
        'outward_occurrences': parent.branch, 'structural_RD': parent.rd,
        'scope': parent.wave().scope, 'scale': parent.wave().scale,
        'parent_identity': parent.identity,
        'inner_to_outer_maps': [list(x[:5]) for x in parent.proposal],
        'formation_return_ids': [t.return_id for t, _, _ in parent.records],
        'fold_proposal_sha256': c.n.digest(parent.proposal)}
    construction = legacy.Construction(config, c, parent, reference, summary)
    waves = list(parent.inner)
    state = {'specs': specs, 'waves': waves, 'channels': {},
        'responses': [0]*len(specs), 'rcds': [0]*len(specs),
        'response_cuts': [0]*len(specs), 'contacts': [], 'returns': [], 'decisions': [],
        'round': 0, 'cursor': parent.returns[-1]+1, 'pending': [], 'path_mass': Q(1)}
    for receiver in range(len(specs)):
        sender = (receiver-1) % len(specs)
        if receiver == sender:
            continue
        events = []
        for occurrence in range(2):
            event = legacy._contact(c, waves[receiver], waves[sender], specs[sender],
                state['cursor'], f'formation:{sender}:{receiver}:{occurrence}', 0, 1)
            state['cursor'] = event.committed+1
            events.append(event)
            state['contacts'].append({'id': event.identity, 'receiver': receiver, 'sender': sender,
                'emitted': event.support_trace.indices[0]-1, 'committed': event.committed,
                'lag_at_emission': 0, 'orientation': 1, 'formation': True,
                'support_return_id': event.support_trace.return_id,
                'left_prefix': event.left_prefix, 'right_prefix': event.right_prefix,
                'support_trace_sha256': event.support_trace.trace_digest,
                'signed_response': 0, 'opposite_response': 0})
        state['channels'][receiver] = events
        state['rcds'][receiver] = legacy._rcd(c, waves[receiver], waves[sender], events,
            2*len(c.constituent(*specs[sender])[1])+1).duration()
        state['response_cuts'][receiver] = events[-1].committed
    state['start'] = state['cursor']
    return Session(config, names, construction, binding, state, random.Random(config['seed']))


def advance(session, forced=None):
    """Commit one entire round; pending contacts settle before its checkpoint."""
    s = session.state; c = session.construction.module; n = c.n
    specs, waves = s['specs'], s['waves']; r = s['round']
    require(r < session.config['rounds'], 'Declared round horizon reached')
    require(not s['pending'], 'Round barrier contains pending emissions')
    if forced is not None:
        require(len(forced) == len(specs) and all(type(x) is int and x in (-1, 1) for x in forced),
                'Complete exact forced orientation round required')
    start = s['cursor']; new_waves = []; current = []; orientations = []
    for i, (spec, wave) in enumerate(zip(specs, waves)):
        feedback = session.config['feedback'] or r == 0
        response = s['responses'][i] if feedback else 0
        weights, probabilities = legacy.kernel(response)
        draw = session.rng.randrange(sum(weights))
        orientation = (1 if draw < weights[0] else -1) if forced is None else forced[i]
        probability = probabilities[0 if orientation == 1 else 1]
        s['path_mass'] *= probability
        rd = 2*len(c.constituent(*spec)[1])+1
        pace = rd+(s['rcds'][i]+max(0, response) if feedback else 0)
        require(s['response_cuts'][i] < start, 'Uncommitted response consumed')
        wave2, row = legacy._inner_return(c, spec, wave, start, pace, orientation, r)
        row.update(round=r, constituent=i, constituent_id=spec[0], pacing=pace)
        current.append(row); new_waves.append(wave2); orientations.append(orientation)
        s['decisions'].append({'round': r, 'constituent': i, 'start': start,
            'response_cut': s['response_cuts'][i], 'response': response, 'rcd': s['rcds'][i],
            'feedback_active': feedback, 'pacing': pace, 'weights': list(weights),
            'probabilities': list(map(str, probabilities)), 'draw': draw,
            'orientation': orientation, 'selected_probability': str(probability),
            'consumed_contact_ids': [x.identity for x in s['channels'].get(i, [])[-2:]],
            'prior_wave_prefix': n.wave_prefix(wave, start-1)})
    s['returns'].extend(current)
    s['cursor'] = max(x['committed'] for x in current)+1
    for receiver in range(len(specs)):
        sender = (receiver-1) % len(specs)
        if receiver == sender:
            continue
        emitted = current[sender]['committed']
        source, target = new_waves[sender], new_waves[receiver]
        lag = sum(t.indices[-1] <= emitted for t in target.returns)-sum(
            t.indices[-1] <= emitted for t in source.returns)
        event = legacy._contact(c, target, source, specs[sender], emitted+1,
            f'current:{r}:{sender}:{receiver}', lag, orientations[sender])
        s['pending'].append((event.committed, receiver, sender, emitted, lag, event))
    for _, receiver, sender, emitted, lag, event in sorted(s['pending']):
        s['channels'][receiver].append(event)
        rcd = legacy._rcd(c, new_waves[receiver], new_waves[sender], s['channels'][receiver],
            2*len(c.constituent(*specs[sender])[1])+1)
        response = orientations[sender]*rcd.duration()*lag
        s['responses'][receiver] = response
        s['rcds'][receiver] = rcd.duration()
        s['response_cuts'][receiver] = event.committed
        s['contacts'].append({'id': event.identity, 'receiver': receiver, 'sender': sender,
            'emitted': emitted, 'committed': event.committed, 'source_return_id': current[sender]['return_id'],
            'lag_at_emission': lag, 'orientation': orientations[sender], 'formation': False,
            'support_return_id': event.support_trace.return_id, 'left_prefix': event.left_prefix,
            'right_prefix': event.right_prefix, 'support_trace_sha256': event.support_trace.trace_digest,
            'rcd_contact_ids': list(rcd.contact_ids), 'rcd': rcd.duration(),
            'signed_response': response, 'opposite_response': -response,
            'nonnegative_burden': abs(response)})
        s['cursor'] = max(s['cursor'], event.committed+1)
    s['pending'] = []; s['waves'] = new_waves; s['round'] += 1
    for wave in new_waves:
        n.validate_wave(wave)
    return session


def checkpoint(session):
    require(not session.state['pending'], 'Only completed round barriers can be checkpointed')
    return {'profile': PROFILE, 'config': deepcopy(session.config), 'names': list(session.names),
        'source_binding': deepcopy(session.binding), 'state': plain(session.state),
        'rng_state': plain(session.rng.getstate()),
        'scope': 'Complete committed state at a round barrier; terminal outer/reference observations not yet inserted.'}


def restore_checkpoint(record, original_config, root=ROOT, *, names=None, forced_prefix=None):
    """Authorize a full checkpoint by original-prefix replay, then resume it."""
    session = initialize(original_config, root, names=names)
    require(record.get('config') == session.config and record.get('names') == list(session.names),
            'Checkpoint belongs to another original preparation')
    state = record.get('state', {})
    rounds = state.get('round')
    require(type(rounds) is int and 0 <= rounds <= session.config['rounds'], 'Invalid checkpoint round')
    count = len(session.names)
    decisions = state.get('decisions', [])
    require(len(decisions) == rounds*count, 'Incomplete checkpoint decisions')
    if forced_prefix is not None:
        require(len(forced_prefix) == rounds*count, 'Independent forced prefix is incomplete')
    for k in range(rounds):
        advance(session, None if forced_prefix is None else forced_prefix[k*count:(k+1)*count])
    require(canonical(record) == canonical(checkpoint(session)),
            'Checkpoint differs from original-input full-state replay')
    return session


def _attempts(session, trajectory):
    e = session.config['electron_count']
    ids = [x['return_id'] for x in trajectory['inner_returns']]
    return {'physical_preparation': {'status': 'incomplete_dependent_output',
        'attempt': 'Construct distinct inventory motifs, execute coupled returns, and retain an independent outer certificate.',
        'actual_return_ids': ids,
        'missing': 'State/apparatus correspondence selecting nuclear and electronic prepared states.'},
        'frg': {'status': 'incomplete_dependent_output',
            'attempt': 'Bind ring adjacency to actual directed contact supports and candidate per-constituent bins.',
            'candidate_gate_ids': list(session.names),
            'actual_support_return_ids': [x['support_return_id'] for x in trajectory['contacts']],
            'missing': 'Admitted tesseract-boundary gate/bin/path-cycle correspondence; a ring list or scalar sum is insufficient.'},
        'retention_loss': {'status': 'incomplete_dependent_output',
            'attempt': 'Retain completed inner and outer closure, signed contact current and accumulated burden.',
            'missing': 'Configuration-derived nuclear closure-load/cost bridge and identified loss/daughter/channel map.',
            'observation_end': 'declared computational horizon; not physical loss or survival censoring'},
        'atomic_transition': {'status': 'not_applicable' if e == 0 else 'incomplete_dependent_output',
            'attempt': 'Check electron participation and requested electronic transition domain.',
            'missing': None if e == 0 else 'Distinct prepared endpoint or transition construction and emitted-phase map.',
            'reason': 'Electron-coupled atomic hyperfine requires electrons.' if e == 0 else None},
        'physical_clock': {'status': 'incomplete_dependent_output',
            'attempt': 'Count actual generic reference returns in the same local observation window.',
            'missing': 'Observed reference-cycle correspondence and physical realization; generic reference is not Cs-133.'}}


def finish(session, observer=True):
    require(type(observer) is bool, 'Observer switch must be Boolean')
    s = session.state; require(s['round'] == session.config['rounds'], 'Incomplete round horizon')
    # Finalization must not mutate a checkpoint or consume its random input.
    constructed = replace(session.construction, reference=deepcopy(session.construction.reference))
    execution = {'waves': s['waves'], 'start': s['start'], 'end': s['cursor']}
    observed = legacy._outer_and_reference(constructed, execution)
    trajectory = {'inner_returns': deepcopy(s['returns']), 'contacts': deepcopy(s['contacts']),
        'decisions': deepcopy(s['decisions']), 'outer_return': observed['outer_return'],
        'reference_returns': observed['reference_returns'], 'outer_contacts': observed['outer_contacts']}
    result = {'schema_version': 1, 'profile': PROFILE, 'original_config': deepcopy(session.config),
        'names': list(session.names), 'source_binding': session.binding,
        'construction': session.construction.summary, 'trajectory': trajectory,
        'trajectory_sha256': digest(trajectory),
        'execution': {'rounds': s['round'], 'conditional_path_probability': str(s['path_mass']),
            'rng_state_sha256': digest(session.rng.getstate()), 'complete_state_sha256': digest(checkpoint(session)),
            'status': 'conditional_native_construction_executed',
            'pending_at_round_barrier': 0, 'inner_reclosures': len(s['returns']),
            'new_outer_reclosures': 1, 'contact_records': len(s['contacts']),
            'reference_window': [s['start']-1, observed['outer_return']['committed']]},
        'observation': observed['observation'] if observer else None,
        'observation_dependency': observed['observation_dependency'] if observer else 'Passive projection disabled',
        'attempts': _attempts(session, trajectory), 'empirical_inputs_read': [],
        'physical_frequency_hz': None, 'physical_half_life_seconds': None}
    result['readouts'] = readouts(result)
    return result


def run_case(config, root=ROOT, *, observer=True, forced=None, checkpoint_after=None, names=None, cached=True):
    session = initialize(config, root, names=names, cached=cached)
    count = len(session.names)
    if forced is not None:
        forced = tuple(forced)
        require(len(forced) == count*session.config['rounds']
                and all(type(x) is int and x in (-1, 1) for x in forced),
                'Forced path must contain every exact orientation')
    if checkpoint_after is not None:
        require(type(checkpoint_after) is int and 0 <= checkpoint_after < session.config['rounds'],
                'Checkpoint must precede the final round')
    for k in range(session.config['rounds']):
        if checkpoint_after == k:
            session = restore_checkpoint(checkpoint(session), config, root, names=names,
                forced_prefix=None if forced is None else forced[:k*count])
        advance(session, None if forced is None else forced[k*count:(k+1)*count])
    return finish(session, observer)


def readouts(result):
    """Several exact native diagnostics from the same committed history."""
    trajectory = result['trajectory']
    contacts = [x for x in trajectory['contacts'] if not x['formation']]
    count = len(result['construction']['constituents'])
    divergence = [0]*count
    for row in contacts:
        value = row['signed_response']
        divergence[row['receiver']] += value
        divergence[row['sender']] -= value
    require(sum(divergence) == 0, 'Internal oriented channel balance failed')
    return {'signed_current': sum(x['signed_response'] for x in contacts),
        'accumulated_burden': sum(x['nonnegative_burden'] for x in contacts),
        'outer_commit': trajectory['outer_return']['committed'],
        'inner_reclosures': len(trajectory['inner_returns']), 'contact_count': len(trajectory['contacts']),
        'node_divergence': divergence,
        'scope': 'Finite native contact/current/count arithmetic; no physical SI interpretation.'}


def verify_case(config, result, root=ROOT, *, forced=None, names=None):
    require(canonical(result) == canonical(run_case(config, root, forced=forced, names=names)),
            'Coupled result differs from original-input replay')
    return True


def readout_cache(config, window, root=ROOT):
    result = run_case(config, root)
    require(type(window) in (tuple, list) and len(window) == 2
            and all(type(x) is int for x in window) and 0 <= window[0] < window[1],
            'Exact ordered native window required')
    lo, hi = window
    contacts = [x for x in result['trajectory']['contacts']
                if not x['formation'] and lo < x['committed'] <= hi]
    return {'original_config': config, 'trajectory_sha256': result['trajectory_sha256'],
        'source_binding': result['source_binding'], 'window': list(window),
        'population': result['construction']['constituents'],
        'readouts': {'signed_current': sum(x['signed_response'] for x in contacts),
            'accumulated_burden': sum(x['nonnegative_burden'] for x in contacts),
            'included_contact_ids': [x['id'] for x in contacts]}}


def replay_readout_cache(cache, original_config, window, root=ROOT):
    require(canonical(cache) == canonical(readout_cache(original_config, window, root)),
            'Readout cache has stale history, window, current, population or authority')
    return True


def enumerate_paths(config, root=ROOT):
    config = legacy.validate_config(config)
    count = len(legacy.inventory(config))*config['rounds']
    require(count <= 6, 'Exact enumeration is scoped to at most six binary choices')
    rows = []
    for signs in product((1, -1), repeat=count):
        result = run_case(config, root, forced=signs)
        rows.append({'orientations': list(signs),
            'probability': result['execution']['conditional_path_probability'],
            'readouts': result['readouts'], 'trajectory_sha256': result['trajectory_sha256'],
            'observation': result['observation']})
    require(sum(Q(x['probability']) for x in rows) == 1, 'Enumerated path mass differs from one')
    fields = ('signed_current', 'accumulated_burden', 'outer_commit', 'inner_reclosures')
    means = {k: sum(Q(x['probability'])*x['readouts'][k] for x in rows) for k in fields}
    covariance = [[str(sum(Q(x['probability'])*(x['readouts'][i]-means[i])*(x['readouts'][j]-means[j])
        for x in rows)) for j in fields] for i in fields]
    return {'config': config, 'paths': rows, 'total_probability': '1',
        'observable_order': list(fields), 'means': {k: str(v) for k, v in means.items()},
        'covariance': covariance,
        'scope': 'Complete enumerated histories of the declared finite law; per-history readouts precede averaging.'}


def sampling_comparison(exact, root=ROOT):
    """Predeclared multinomial marginal checks; preserve every sampled run."""
    support = {tuple(p['orientations']): p for p in exact['paths']}
    counts = {p: 0 for p in support}; runs = []
    for seed in SAMPLE_SEEDS:
        config = dict(exact['config'], seed=seed)
        result = run_case(config, root)
        path = tuple(x['orientation'] for x in result['trajectory']['decisions'])
        require(path in support, 'Sampler produced a path outside enumerated support')
        require(result['readouts'] == support[path]['readouts'],
                'Sampled and enumerated path readouts differ')
        require(result['execution']['conditional_path_probability'] == support[path]['probability'],
                'Sampler and enumeration use different conditional probability laws')
        counts[path] += 1
        runs.append({'seed': seed, 'orientations': list(path), 'trajectory_sha256': result['trajectory_sha256'],
            'probability': support[path]['probability'], 'readouts': result['readouts'],
            'trajectory': result['trajectory'], 'status': 'completed_declared_horizon',
            'rng_state_sha256': result['execution']['rng_state_sha256']})
    # Union-bound Hoeffding criterion on K path indicators, alpha=1/100.
    # It is a sampling diagnostic under the declared pseudorandom strategy,
    # not a probability guarantee about the deterministic seed list.
    size, k, alpha = len(runs), len(support), Q(1, 100)
    epsilon = math.sqrt(math.log(2*k/float(alpha))/(2*size))
    errors = [abs(Q(counts[path], size)-Q(row['probability'])) for path, row in support.items()]
    moments = {}
    for field in exact['observable_order']:
        mean = sum(Q(x['readouts'][field]) for x in runs)/size
        sample_variance = sum((Q(x['readouts'][field])-mean)**2 for x in runs)/(size-1)
        moments[field] = {'sample_mean': str(mean), 'unbiased_sample_variance': str(sample_variance),
            'estimated_sample_mean_variance': str(sample_variance/size),
            'scope': 'IID sampling diagnostic under the declared kernel; deterministic seed strategy is disclosed.'}
    return {'config': exact['config'], 'seeds': list(SAMPLE_SEEDS), 'sample_size': size,
        'strategy': 'One exact integer conditional sampler per declared seed; all trajectories retained.',
        'criterion': 'max path-frequency deviation <= sqrt(log(2*K/alpha)/(2*N)), alpha=1/100',
        'criterion_scope': 'Predeclared finite-sample diagnostic; deterministic PRNG seeds are execution provenance.',
        'epsilon': epsilon, 'max_path_frequency_error': str(max(errors)),
        'criterion_passed': float(max(errors)) <= epsilon,
        'sample_moments': moments,
        'counts': [{'orientations': list(path), 'count': counts[path], 'probability': row['probability']}
                   for path, row in support.items()], 'runs': runs,
        'failed_runs': [], 'discarded_runs': [], 'physical_survival_estimate': None}


def boundary_rows(result, root=ROOT):
    n = producer.load(root).native
    ids = [x['wave_identity'] for x in result['construction']['constituents']]
    terms = [(ids[x['receiver']], ids[x['sender']], x['rcd'],
              x['orientation']*x['lag_at_emission'], x['id'])
             for x in result['trajectory']['contacts'] if not x['formation']]
    flux = n.aod_flux(terms)
    regions = []
    require(len(ids) <= 10, 'Exhaustive boundary control is limited to ten constituents')
    for mask in range(2**len(ids)):
        region = {x for j, x in enumerate(ids) if mask & (1 << j)}
        row = n.stokes(flux, region)
        regions.append({'members': [j for j, x in enumerate(ids) if x in region],
                        'internal': str(row['internal']), 'divergence': str(row['divergence']),
                        'boundary': str(row['boundary'])})
    return {'channels': plain(terms), 'regions': regions,
        'boundary_motion': 'fixed; no sweep term is selected in this profile',
        'shed_transport': 'not selected in the campaign law; separate diagnostic control below'}


def _reduced_state(session):
    s = session.state
    return {'responses': s['responses'], 'rcds': s['rcds'], 'cursor': s['cursor'],
            'round': s['round'], 'return_counts': [len(w.returns) for w in s['waves']]}


def finite_reduction_control(root=ROOT):
    """Check next-state/readout laws over all four H1 first-round histories."""
    config = default_config(1, 1, 1, rounds=2)
    histories = []
    for prefix in product((1, -1), repeat=2):
        start = initialize(config, root); advance(start, prefix)
        key = _reduced_state(start); law = {}
        for suffix in product((1, -1), repeat=2):
            session = restore_checkpoint(checkpoint(start), config, root, forced_prefix=prefix)
            before_mass = session.state['path_mass']; advance(session, suffix)
            mass = session.state['path_mass']/before_mass
            output = {'next_reduced_state': _reduced_state(session), 'readouts': finish(session)['readouts']}
            encoded = canonical(output).decode()
            law[encoded] = law.get(encoded, Q(0))+mass
        require(sum(law.values()) == 1, 'Conditional reduced transition law loses mass')
        histories.append({'prefix': list(prefix), 'reduced_state': key,
            'boundary_net': sum(key['responses']),
            'burden': sum(abs(x) for x in key['responses']),
            'law': {x: str(p) for x, p in sorted(law.items())}})
    groups = {}
    for row in histories:
        groups.setdefault(digest(row['reduced_state']), []).append(row)
    require(all(all(x['law'] == rows[0]['law'] for x in rows) for rows in groups.values()),
            'Declared finite reduction fails next-state/readout law')
    collisions = [{'left': a['prefix'], 'right': b['prefix'], 'shared_burden': a['burden']}
        for a, b in combinations(histories, 2) if a['burden'] == b['burden'] and a['law'] != b['law']]
    require(collisions, 'Coarse burden-only negative control failed to distinguish feedback')
    return {'histories': histories, 'groups': [len(x) for x in groups.values()],
        'adequate_reduction': 'responses, directional RCD, cut, round and per-wave return counts',
        'joint_next_state_and_observable_laws_equal': True,
        'burden_only_counterexamples': collisions,
        'scope': 'All four first-round H1 histories and one following transition under this fixed two-node law and listed readouts. No reconstruction, future-all-horizon, physical or universal scale claim.'}


def shedding_availability_control(root=ROOT):
    """Actual native debit from a two-contact cancellation history.

    The diagnostic cost is the compatible part of two owned signed supports.
    This declared bridge does not identify nuclear capacity or physical loss.
    """
    config = default_config(1, 1, 1, rounds=2)
    session = initialize(config, root)
    advance(session, (1, 1)); advance(session, (1, -1))
    c = session.construction.module; n = c.n; s = session.state
    terms = [x for x in s['contacts'] if not x['formation'] and x['receiver'] == 0]
    require(len(terms) == 2 and sum(x['signed_response'] for x in terms) == 0,
            'Cancellation witness does not have two opposite owned contacts')
    chi = s['waves'][0].motif_witnesses[-1].chirality
    retained = [x for x in terms if chi*x['signed_response'] >= 0]
    exported = [x for x in terms if chi*x['signed_response'] < 0]
    load = sum(abs(x['signed_response']) for x in terms)
    cost = sum(abs(x['signed_response']) for x in retained)
    old_current = sum(x['signed_response'] for x in terms)
    outgoing = sum(x['signed_response'] for x in exported)
    state = replace(n.initial_state(s['waves'][0]), committed=s['cursor']-1,
                    orientation=chi, current=Q(old_current))
    inner = tuple(s['waves']); parent = session.construction.field
    proposal = n.fold_proposal(inner, c.OUTER, 1)
    t = c.bound_trace(parent.lineage, 'coupled:availability-control', parent.vertices,
        c.indices_for(s['cursor']+1, parent.branch), parent.branch, c.OUTER, 1,
        'fold:'+n.digest(proposal))
    cert = n.certify(t, 'outer', inner=inner)
    folded = n.fold(inner, (t, cert, {cert.certificate_digest: cert}))
    bridge = {'rule': 'diagnostic compatible signed-support partition', 'chi': chi,
              'contact_ids': [x['id'] for x in terms], 'load': load, 'cost': cost}
    shed = n.shedding(folded, state, load, cost, source_event_digest=n.digest(terms),
        model_bridge=n.digest(bridge), committed=t.indices[-1]+1,
        route='redirected_support', target_scope='declared:coupled:diagnostic-receiver', target_scale=1)
    held = replace(state, committed=shed.committed)
    after = n.update(held, -Q(outgoing)*held.pressure, held.committed)
    retained_current = sum(x['signed_response'] for x in retained)
    require(after.current == retained_current and after.current != state.current,
            'Export debit did not change subsequent operative current')
    route = n.trace(state.identity+'|declared:coupled:diagnostic-receiver', 'coupled:route',
        scope='declared:coupled:diagnostic-receiver', scale=1, start_index=after.committed+1,
        chirality=-chi)
    rc = n.certify(route); n.admitted(route, rc, {rc.certificate_digest: rc})
    ownership = [{'cut': after.committed, 'retained': cost, 'reserved': load-cost, 'pending': 0, 'arrived': 0},
        {'cut': route.indices[0], 'retained': cost, 'reserved': 0, 'pending': load-cost, 'arrived': 0},
        {'cut': route.indices[-1], 'retained': cost, 'reserved': 0, 'pending': 0, 'arrived': load-cost}]
    require(all(sum(x[k] for k in ('retained', 'reserved', 'pending', 'arrived')) == load for x in ownership),
            'Availability transport duplicated or lost burden')
    rd = 2*len(c.constituent(*s['specs'][0])[1])+1
    rcd = s['rcds'][0]
    continuations = {}
    for label, response in [('export_disabled', state.current), ('export_enabled', after.current)]:
        pace = rd+rcd+max(0, int(response))
        w, row = legacy._inner_return(c, s['specs'][0], s['waves'][0], after.committed+1,
            pace, chi, 'coupled:matched-next')
        n.validate_wave(w)
        continuations[label] = {'response': str(response), 'pacing': pace, 'return': row}
    require(continuations['export_disabled']['return']['committed'] !=
            continuations['export_enabled']['return']['committed'],
            'Availability intervention did not affect actual next admitted return')
    return {'source_contacts': terms, 'bridge': bridge, 'source_state': plain(state),
        'post_debit_state': plain(after), 'shedding': plain(shed),
        'route': {'trace': plain(route), 'certificate': plain(rc)}, 'ownership': ownership,
        'retained_contact_ids': [x['id'] for x in retained], 'exported_contact_ids': [x['id'] for x in exported],
        'net_only_before': old_current, 'retained_after_export': str(after.current),
        'next_kernel_before': list(map(str, legacy.kernel(int(state.current))[1])),
        'next_kernel_after': list(map(str, legacy.kernel(int(after.current))[1])),
        'matched_continuations': continuations,
        'scope': 'Native signed-support ownership, transport and next-kernel control under an explicit diagnostic load/cost bridge; not an isotope loss law.'}


def pressure_memory_control(root=ROOT):
    session = initialize(default_config(1, 1, 1, rounds=1), root)
    advance(session, (1, 1))
    n = session.construction.module.n; wave = session.state['waves'][0]
    states = [n.initial_state(wave, pressure=Q(p)) for p in (1, 2)]
    after = [n.update(s, Q(1), s.committed) for s in states]
    require(states[0].closure_memory == states[1].closure_memory
            and states[0].current == states[1].current == 0
            and after[0].current == 1 and after[1].current == Q(1, 2),
            'Pressure-memory intervention does not exercise the declared native response')
    return {'states': plain(states), 'attention': '1', 'next_states': plain(after),
        'same_admitted_history': True, 'same_present_current': True,
        'retained_operand': 'positive native pressure supplied explicitly to initial_state',
        'net_current_only_reduction_fails': True,
        'scope': 'Matched native response states with one declared pressure operand changed; not an inferred nuclear memory law.'}


def controls(root=ROOT):
    config = default_config(1, 1, 1, rounds=2)
    baseline = run_case(config, root)
    passive = run_case(config, root, observer=False)
    resumed = run_case(config, root, checkpoint_after=1)
    require(baseline['trajectory'] == passive['trajectory'] == resumed['trajectory'],
            'Passive observation or full-state continuation changed a trajectory')
    require(baseline['execution']['rng_state_sha256'] == passive['execution']['rng_state_sha256']
            == resumed['execution']['rng_state_sha256'], 'Passive/continuation RNG state differs')
    path = tuple(x['orientation'] for x in baseline['trajectory']['decisions'])
    fixed = run_case(config, root, forced=path)
    off = run_case(dict(config, feedback=False), root, forced=path)
    first = lambda x: [r for r in x['trajectory']['inner_returns'] if r['round'] == 0]
    require(first(fixed) == first(off), 'Feedback intervention lost common first-round history')
    require(fixed['readouts']['outer_commit'] != off['readouts']['outer_commit'],
            'Feedback control did not change the declared later pacing')
    renamed = run_case(config, root, names=('arbitrary-A', 'arbitrary-B'))
    require(renamed['readouts'] == baseline['readouts'], 'Name-only permutation changed native outputs')
    key = lambda x: [(r['round'], r['constituent'], r['committed'], r['orientation'], r['pacing'])
                    for r in x['trajectory']['inner_returns']]
    require(key(renamed) == key(baseline), 'Name-only permutation changed corresponding events')
    window = baseline['execution']['reference_window']
    cached = readout_cache(config, window, root)
    rejected = []
    for kind in ('window', 'current', 'population'):
        bad = deepcopy(cached)
        if kind == 'window':
            bad['window'][0] += 1
        elif kind == 'current':
            bad['readouts']['signed_current'] += 1
        else:
            bad['population'].pop()
        try:
            replay_readout_cache(bad, config, window, root)
        except ValueError:
            rejected.append(kind)
    require(rejected == ['window', 'current', 'population'], 'Stale cache guard failed')
    return {'passive': {'trajectory_equal': True, 'rng_equal': True},
        'continuation': {'trajectory_equal': True, 'rng_equal': True, 'checkpoint_after_rounds': 1,
            'scope': 'Restore complete state/RNG at the round barrier; insert one terminal outer observation only after continuation.'},
        'feedback': {'fixed_orientations': list(path), 'first_round_equal': True,
            'baseline_outer_commit': fixed['readouts']['outer_commit'], 'off_outer_commit': off['readouts']['outer_commit'],
            'baseline_probability': fixed['execution']['conditional_path_probability'],
            'off_probability': off['execution']['conditional_path_probability'],
            'scope': 'Matched admissible-path intervention; different conditional mass is not an unconditional sampling effect.'},
        'name_permutation': {'map': dict(zip(baseline['names'], renamed['names'])),
            'corresponding_events_equal': True, 'readouts_equal': True},
        'cache_rejections': rejected,
        'reduction': finite_reduction_control(root), 'availability': shedding_availability_control(root),
        'pressure_memory': pressure_memory_control(root)}


def protocol():
    return {'schema_version': 1, 'profile': PROFILE, 'producer_commit': PRODUCER,
        'pilot_setups': [{'id': name, 'config': default_config(1, a, e, rounds=1)} for name, a, e in PILOTS],
        'law': legacy.RULE, 'law_role': 'Authenticated application choices reused with successor native admission.',
        'finite_domains': 'All six pilots at one round; H1-E1 also two rounds; at most six binary choices.',
        'sample_seeds': list(SAMPLE_SEEDS), 'sample_size_per_domain': len(SAMPLE_SEEDS),
        'sampling_criterion': 'Union-bound path-indicator Hoeffding diagnostic, alpha=1/100; no favorable-seed selection.',
        'observation': 'Shared native history before any averaging; terminal window is configuration-specific.',
        'clock': 'Generic independently admitted 3:3:6 reference, not a physical Cs clock.',
        'exposure': 'Retrospective known-target setting; target files are not read by this generator.',
        'checkpoint': 'Complete state and RNG at round barriers; no unfinished pending emission may be dropped.',
        'diagnostic_shedding': 'Separate explicit signed-support compatible-cost control; not the pilot nuclear loss law.',
        'physical_prediction_claim': False}


def build_report(root=ROOT):
    fixed = protocol(); pilots = {}; exact = {}; samples = {}; summaries = []
    for name, a, e in PILOTS:
        config = default_config(1, a, e, rounds=1)
        run = run_case(config, root); pilots[name] = run
        exact[name] = enumerate_paths(config, root)
        samples[name] = sampling_comparison(exact[name], root)
        summaries.append({'id': name, 'z': 1, 'a': a, 'n': a-1, 'e': e, 'charge': 1-e,
            'rounds': 1, 'branch_occurrences': run['construction']['outward_occurrences'],
            'structural_RD': run['construction']['structural_RD'], **run['readouts'],
            'reference_window': run['execution']['reference_window'],
            'reference_returns': len(run['trajectory']['reference_returns']),
            'cadence_ratio': run['observation']['cadence_ratio'] if run['observation'] else None,
            'retention_status': run['attempts']['retention_loss']['status'],
            'atomic_transition_status': run['attempts']['atomic_transition']['status'],
            'boundary_balance': boundary_rows(run, root)})
    exact['H1-E1-feedback'] = enumerate_paths(default_config(1, 1, 1, rounds=2), root)
    samples['H1-E1-feedback'] = sampling_comparison(exact['H1-E1-feedback'], root)
    checks = controls(root)
    pairs = [{'isotope': a, 'bare': f'H{a}-E0', 'electron_containing': f'H{a}-E1',
        'fixed': ['Z', 'A', 'constituent templates', 'conditional law', 'round horizon', 'seed provenance'],
        'changed': ['electron inventory', 'directed contacts', 'parent boundary', 'configuration terminal window'],
        'readout_difference': {k: pilots[f'H{a}-E1']['readouts'][k]-pilots[f'H{a}-E0']['readouts'][k]
                              for k in ('signed_current', 'accumulated_burden', 'outer_commit', 'inner_reclosures')},
        'scope': 'Declared preparation intervention; differing topology/window are explicit operands, not a physical electron-effect claim.'}
        for a in (1, 2, 3)]
    report = {'schema_version': 1, 'profile': PROFILE, 'protocol_sha256': digest(fixed),
        'producer_commit': PRODUCER, 'pilots': summaries, 'paired_preparations': pairs,
        'exact_domains': {k: {'path_count': len(v['paths']), 'total_probability': v['total_probability'],
            'means': v['means'], 'covariance': v['covariance'], 'observable_order': v['observable_order']} for k, v in exact.items()},
        'sample_domains': {k: {x: v[x] for x in ('sample_size', 'criterion_passed', 'max_path_frequency_error', 'epsilon')}
                           for k, v in samples.items()},
        'controls_sha256': digest(checks), 'physical_prediction_complete': False,
        'claim': 'Executed conditional six-preparation method, exact and sampled history diagnostics, scoped continuation and reduction controls.'}
    return {'protocol.json': fixed, 'pilots.json': pilots, 'ensembles.json': {'exact': exact, 'sampled': samples},
            'controls.json': checks, 'report.json': report}


def generate(root=ROOT, output_root=None):
    products = build_report(root)
    folder = Path(root if output_root is None else output_root)/DATA
    folder.mkdir(parents=True, exist_ok=True)
    for name, value in products.items():
        (folder/name).write_bytes(canonical(value))
    return {'status': 'GENERATED_CONDITIONAL_COUPLED_PREPARATIONS', 'products': list(products),
            'physical_prediction_complete': False}


def verify(root=ROOT):
    products = build_report(root)
    for name, value in products.items():
        require((Path(root)/DATA/name).read_bytes() == canonical(value),
                'Stored coupled product differs from original-input replay: '+name)
    return {'status': 'PASS_COUPLED_PREPARATIONS_REPLAY', 'products': list(products),
            'physical_prediction_complete': False}
