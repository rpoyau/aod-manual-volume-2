"""Exact finite-history retention/loss experiment, separate from isotope admission.

Main supplies the conditional kernel, paired response and excess construction.
This application explicitly declares the state/weight/response maps which Main
does not select for a nucleus. No measured lifetime is read by the predictor.
The comparison tests the identity-insensitive/shared-clock specialization; it
does not promote this finite example to a native atomic prediction.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import hashlib
from pathlib import Path

from matter1_atomic import ValidationError, canonical, digest, read_json, require, rational
from matter1_m3 import mapping, verify_vendor

DATA = Path('manual2/data/m1/survival')
CATALOG = Path('manual2/data/m1/isotopes/catalog.json')
PROFILE = 'm1:finite-history-retention-survival:v3'
CS_HZ = Q(9192631770)
CASES = [('H', 1, 1), ('Cs', 55, 133), ('Fe', 26, 56), ('Ni', 28, 62),
         ('Pb', 82, 208), ('Og', 118, 294), ('Lv', 116, 290), ('Fl', 114, 286),
         ('Lv', 116, 293), ('Fl', 114, 289), ('Fl', 114, 298)]
SOURCE_LABELS = {
    'sections/03_afc_basis.tex': ['eq:atomic-h1', 'eq:hinge-grammar'],
    'sections/04_cut_running_fractal_tesseract.tex': ['eq:closure-certificate', 'eq:closure-phase-step-count'],
    'sections/05_curl_closure_duon_current.tex': ['eq:expose-inner-lineage', 'eq:key-proposed-admitted-trace'],
    'sections/06_wave_state_relational_time.tex': ['eq:admitted-kernel', 'eq:cadence-ratio', 'eq:wave-update-trace'],
    'sections/06_field.tex': ['eq:sadar-orientation-antisymmetry', 'eq:closure-residual', 'eq:shedding-excess'],
    'sections/07_cell_measures_mappings.tex': ['eq:m3-finite-law', 'prop:m3-atomic-gain'],
}
STATUS = {'construction': 'declared_Q4_finite_predicate_model', 'execution': 'executed_exact_finite_histories',
          'native_motif_admission': 'not_established', 'native_isotope_state_map': 'not_established',
          'physical_loss_map': 'not_established', 'reference_clock_map': 'not_established',
          'physical_uncertainty': 'unknown', 'empirical_agreement': 'not_claimed'}
GEOMETRY = {
    'vertices': {'O': '0000', 'A': '1000', 'B': '1001', 'I': '0001',
                 'C': '0100', 'D': '0101', 'L': '0010', 'E': '1010', 'F': '0110'},
    'return_plus': ['O', 'A', 'B', 'I', 'O'], 'return_minus': ['O', 'C', 'D', 'I', 'O'],
    'reference': ['O', 'A', 'B', 'I', 'O'], 'exit': ['O', 'L'],
    'alpha_route': ['L', 'E'], 'sf_route': ['L', 'F'],
    'incoming_ancestor': 'I', 'retained_hinge_role': {'plus': 'B', 'minus': 'D', 'reference': 'B'},
    'coordinate_scope': 'one_injective_Q4_encoding_per_declared_lineage',
    'nuclear_identification': 'hypothetical_route_labels_only',
}
RULE = {
    'order': ['complete_reference_return', 'bind_committed_prefix_contact', 'normalize_admissible_weights',
              'execute_selected_path', 'commit_paired_response_for_next_contact'],
    'memory': 'R=sum(committed oriented returned-current responses)',
    'excess': 'X=max(0,abs(R)-C)',
    'kernel': '(w_plus,w_minus,w_exit)=(1,1,lambda*X); P=w/sum(w)',
    'response': 'retained plus/minus return commits antisymmetric (sigma,-sigma); R_next=R+sigma',
    'support_specialization': 'declared p=2 and lag=1/2 give response magnitude 1; not an admitted RD accessor',
    'exit_partition': 'alpha-labelled and SF-labelled routes each have conditional weight 1',
    'loss': 'absorbing outer loss; prior events and inner lineage retained',
    'merge_policy': 'none; every finite choice prefix remains a distinct history',
    'clock': 'count of completed reference reclosures after two initial witnessed returns',
    'isotope_assignment': 'identity-insensitive surrogate; no species-specific native construction',
}
VARIANTS = {
    'baseline': {'capacity': '1', 'loss_gain': '1', 'disable_feedback_from_count': None},
    'loss_gain_2': {'capacity': '1', 'loss_gain': '2', 'disable_feedback_from_count': None},
    'feedback_off': {'capacity': '1', 'loss_gain': '1', 'disable_feedback_from_count': 2},
    'capacity_0': {'capacity': '0', 'loss_gain': '1', 'disable_feedback_from_count': None},
}
OUTPUTS = ('prediction.json', 'comparison.json', 'survival_report.json')


def source_bindings(root):
    result = []
    for name, labels in SOURCE_LABELS.items():
        blob = (Path(root)/name).read_bytes()
        require(all(('\\label{'+label+'}').encode() in blob for label in labels), 'Survival source premise label absent')
        result.append({'path': name, 'sha256': hashlib.sha256(blob).hexdigest(), 'labels': labels})
    verify_vendor(root)
    vendor = Path('manual2/vendor/aod_m3/aod_mapping_error.py')
    result.append({'path': str(vendor), 'sha256': hashlib.sha256((Path(root)/vendor).read_bytes()).hexdigest(),
                   'labels': ['propagate', 'joint_moments']})
    return result


def grouping(z, a):
    require(type(z) is int and type(a) is int and 1 <= z <= a, 'Nucleon identity domain')
    n = a-z
    q = min(z//2, n//2)
    return {'Z': z, 'A': a, 'N': n, 'q': q, 'r_p': z-2*q, 'r_n': n-2*q,
            'interpretation': 'formal_2p_2n_groups_not_physical_alpha_clusters'}


def default_contract(root):
    return {'schema_version': 3, 'profile': PROFILE, 'statuses': dict(STATUS),
            'source_bindings': source_bindings(root), 'geometry': deepcopy(GEOMETRY), 'rule': deepcopy(RULE),
            'horizon_reference_returns': 8, 'initial_witnessed_returns_per_lineage': 2,
            'initial_memory': '0', 'variants': deepcopy(VARIANTS),
            'cases': [{'id': f'{s}-{a}:ground', 'symbol': s, **grouping(z, a),
                       'state_assignment': 'external_identity_label_only_no_native_state_identification'} for s,z,a in CASES],
            'parameter_provenance': 'Common exact demonstration inputs selected without consuming isotope lifetime values; no fitted parameters.',
            'target_policy': 'predictor_reads_only_contract_and_bound_mathematical_sources',
            'exposure': 'Og/Lv/Fl evaluated lifetimes were available before this model; comparisons are retrospective.',
            'unobserved_target': 'Fl-298:ground',
            'scientific_dependencies': [
                {'id': 'SURV-ATOM-01', 'status': 'unresolved', 'requires': 'Isotope/state-specific admitted native configurations and support accessors.'},
                {'id': 'SURV-ATOM-02', 'status': 'unresolved', 'requires': 'Independent state-to-kernel/retention/loss-channel law selecting the common parameters or replacing the surrogate.'},
                {'id': 'SURV-ATOM-03', 'status': 'unresolved', 'requires': 'Observation map connecting loss and reference reclosure to physical decay and calibrated elapsed time.'},
                {'id': 'SURV-ATOM-04', 'status': 'unresolved', 'requires': 'Realization, model discrepancy and cross-source uncertainty/covariance; external confidence convention.'}],
            'uncertainty_policy': {'finite_arithmetic': 'exact_rational', 'ensemble_spread': 'exact_declared_joint_law',
                                   'physical_model': 'unknown', 'calibration': 'not_performed', 'covariance': 'not_assumed_independent'}}


def validate_geometry(g):
    require(g == GEOMETRY, 'Unsupported geometry or coordinate alias')
    vertices = g['vertices']
    require(len(set(vertices.values())) == len(vertices), 'Q4 encoding must be injective')
    for key in ('return_plus', 'return_minus', 'reference', 'exit', 'alpha_route', 'sf_route'):
        path = g[key]
        for a, b in zip(path, path[1:]):
            require(sum(x != y for x,y in zip(vertices[a], vertices[b])) == 1, 'Every committed traversal must be H1')
    for name in ('return_plus', 'return_minus', 'reference'):
        require(g[name][0] == g[name][-1] and len(g[name])-1 >= 2, 'Retained start and phase-bearing closure bound')


def validate_contract(root, contract):
    validate_geometry(contract['geometry'])
    require(canonical(contract) == canonical(default_contract(root)), 'Survival contract: unsupported premise, status, parameter, source or target access')
    return contract


def _witness(lineage, identity, path, count, prefix):
    return {'return_id': identity, 'lineage': lineage, 'scope': f'{PROFILE}:{lineage}',
            'reference_count': count, 'path': path, 'event_ids': [f'{identity}:edge:{i}' for i in range(len(path)-1)],
            'start': GEOMETRY['vertices'][path[0]], 'end': GEOMETRY['vertices'][path[-1]],
            'phase_bearing_traversals': len(path)-1, 'committed_prefix': prefix,
            'certificate_kind': 'finite_predicate_witness_not_native_motif_admission'}


def _finite_moments(root, probability):
    p = Q(probability)
    support = [(str(q), {'retained': str(v)}) for q,v in ((1-p, 0), (p, 1)) if q > 0]
    return mapping(root).propagate(['input', 'retained'], ['retained'], {}, support=support)


def simulate(root, contract, variant='baseline'):
    """Expand every choice history exactly; matching memory never merges histories."""
    validate_contract(root, contract)
    require(variant in VARIANTS, 'Undeclared survival variant')
    p = contract['variants'][variant]
    capacity, gain = rational(p['capacity']), rational(p['loss_gain'])
    initial = [_witness(lineage, f'{lineage}:seed:{i}', GEOMETRY['reference'], i-2, '')
               for lineage in ('candidate', 'reference') for i in (0, 1)]
    candidate_seeds = [x for x in initial if x['lineage']=='candidate']
    inner_seeds = [_witness('retained-inner',f'inner:seed:{i}',GEOMETRY['reference'],i-2,'') for i in (0,1)]
    candidate_seed_ids = [x['return_id'] for x in candidate_seeds]
    inner = {'lineage': 'retained-inner', 'witness_ids': [x['return_id'] for x in inner_seeds],
             'witnesses': inner_seeds, 'mapping_semantics': 'injective_scope_reexpression_of_committed_initial_history_not_additional_returns',
             'scope_map': {'source': f'{PROFILE}:retained-inner', 'target': f'{PROFILE}:candidate',
                           'return_map': {source['return_id']:target['return_id'] for source,target in zip(inner_seeds,candidate_seeds)},
                           'event_map': {a:b for source,target in zip(inner_seeds,candidate_seeds)
                                         for a,b in zip(source['event_ids'],target['event_ids'])}}}
    # The empty prefix is a state after the same two committed initial returns.
    live = [('', Q(1), Q(0))]
    rows, nodes, losses, references = [], [], [], []
    cumulative = {'alpha_label': Q(0), 'sf_label': Q(0)}
    rows.append({'c': 0, 'survival': '1', 'loss_alpha': '0', 'loss_sf': '0', 'cumulative_loss': '0', 'total_mass': '1'})
    for c in range(1, contract['horizon_reference_returns']+1):
        reference = _witness('reference', f'reference:reclosure:{c}', GEOMETRY['reference'], c, '')
        references.append(reference)
        new_live = []
        for prefix, mass, memory in live:
            excess = max(Q(0), abs(memory)-capacity)
            weights = (Q(1), Q(1), gain*excess)
            norm = sum(weights)
            kernel = [{'port': port, 'admissible': True, 'weight': str(w), 'probability': str(w/norm)}
                      for port,w in zip(('plus', 'minus', 'exit'), weights)]
            kernel.append({'port': 'incoming_ancestor', 'admissible': False, 'weight': '0', 'probability': '0'})
            require(sum(Q(row['probability']) for row in kernel) == 1, 'Exact kernel normalization')
            node = {'prefix': prefix, 'reference_count': c, 'incoming_mass': str(mass), 'memory_before': str(memory),
                    'capacity': str(capacity), 'excess': str(excess), 'kernel': kernel,
                    'contact': {'reference_return_id': reference['return_id'],
                                'candidate_completed_prefix': prefix,
                                'candidate_seed_ids': candidate_seed_ids, 'binds_only_committed_history': True},
                    'retained_children': [], 'loss_children': []}
            for symbol, sign, w in (('+', 1, weights[0]), ('-', -1, weights[1])):
                child = prefix+symbol
                child_mass = mass*w/norm
                feedback = p['disable_feedback_from_count'] is None or c < p['disable_feedback_from_count']
                response = Q(sign) if feedback else Q(0)
                next_memory = memory+response
                new_live.append((child, child_mass, next_memory))
                return_id = f'candidate:prefix:{child}'
                witness = _witness('candidate', return_id, GEOMETRY['return_plus' if sign==1 else 'return_minus'], c, prefix)
                node['retained_children'].append({'prefix': child, 'probability_mass': str(child_mass),
                    'return_witness': witness, 'response_pair': [str(response), str(-response)],
                    'response_committed_after_contact': True, 'memory_next': str(next_memory),
                    'inner_lineage_sha256': digest(inner)})
            exit_mass = mass*weights[2]/norm
            if exit_mass:
                for channel, path in (('alpha_label', 'alpha_route'), ('sf_label', 'sf_route')):
                    item = {'prefix': prefix, 'channel': channel, 'reference_count': c,
                            'probability_mass': str(exit_mass/2), 'path': GEOMETRY['exit']+GEOMETRY[path][1:],
                            'committed_candidate_return_ids': candidate_seed_ids+[f'candidate:prefix:{prefix[:i]}' for i in range(1,len(prefix)+1)],
                            'inner_lineage_sha256': digest(inner), 'absorbing': True,
                            'physical_channel_identification': 'not_established'}
                    node['loss_children'].append(item)
                    losses.append(item)
                    cumulative[channel] += exit_mass/2
            nodes.append(node)
        live = new_live
        survival = sum(mass for _,mass,_ in live)
        total = survival+sum(cumulative.values())
        require(total == 1, 'Finite-history probability mass conservation')
        require(Q(rows[-1]['survival']) >= survival, 'Monotone survival')
        rows.append({'c': c, 'survival': str(survival), 'loss_alpha': str(cumulative['alpha_label']),
                     'loss_sf': str(cumulative['sf_label']), 'cumulative_loss': str(sum(cumulative.values())), 'total_mass': str(total)})
    crossing = next((r['c'] for r in rows if Q(r['survival']) <= Q(1,2)), None)
    median = ({'kind': 'first_discrete_crossing', 'interval_reference_returns': [crossing-1,crossing],
               'interval_convention': '(lower,upper]', 'crossing': crossing} if crossing is not None else
              {'kind': 'right_censored', 'lower_bound_reference_returns': rows[-1]['c'], 'bound_convention': 'strictly_greater'})
    moment = _finite_moments(root, rows[-1]['survival'])
    require(Q(moment['output_mean']) == Q(rows[-1]['survival']), 'M3 finite-law survival mean')
    return {'profile': PROFILE, 'variant': variant, 'parameters': deepcopy(p), 'statuses': dict(STATUS),
            'contract_sha256': digest(contract), 'initial_returns': initial, 'retained_inner': inner,
            'reference_returns': references, 'rows': rows, 'nodes': nodes, 'absorbed_histories': losses,
            'right_censored_histories': [{'prefix': h, 'probability_mass': str(m), 'memory': str(r)} for h,m,r in live],
            'median': median, 'finite_law': moment, 'node_count': len(nodes),
            'history_merge_count': 0, 'physical_half_life_seconds': None}


def predict(root):
    root = Path(root)
    contract = read_json(root/DATA/'model_contract.json')
    validate_contract(root, contract)
    runs = {name: simulate(root, contract, name) for name in VARIANTS}
    baseline = runs['baseline']
    crossing = baseline['median']['interval_reference_returns']
    return {'schema_version': 3, 'profile': PROFILE, 'statuses': dict(STATUS),
            'contract_sha256': digest(contract), 'runs': runs,
            'isotope_candidates': [{'id': case['id'], 'grouping': {k:case[k] for k in ('Z','A','N','q','r_p','r_n')},
                                   'construction': 'same_identity_insensitive_surrogate', 'finite_run_sha256': digest(baseline),
                                   'conditional_median_reference_returns': baseline['median'],
                                   'physical_half_life_seconds': None, 'prediction_status': 'atomic_prediction_incomplete'} for case in contract['cases']],
            'conditional_test': {'premises': ['same_surrogate_configuration', 'same_native_to_reference_observation_map',
                                               'same_reference_to_SI_map_for_compared_species'],
                                 'consequence': 'identical_survival_distributions_and_equal_medians', 'half_life_ratio': '1',
                                 'scope': 'falsifiable_declared_specialization_not_native_atomic_prediction'},
            'clock_countermodels': [{'native_reference_gain': str(g), 'Cs_definition_hz': str(CS_HZ),
                                    'conditional_median_seconds_interval': [str(g*Q(c)/CS_HZ) for c in crossing],
                                    'selection': 'unselected_identifiability_witness', 'physical_uncertainty': 'unknown',
                                    'premise': 'hypothetically identify g physical Cs cycles per model reference return'} for g in (Q(1),Q(2))],
            'fitted_parameters': [], 'evaluation_inputs_read': [],
            'uncertainty': {'native_survival': 'exact_for_declared_finite_joint_law',
                            'physical_model_discrepancy': 'unknown', 'reference_realization': 'unknown',
                            'measurement_covariance': 'unknown_not_assumed_independent', 'physical_budget_status': 'incomplete'},
            'dependencies': contract['scientific_dependencies'],
            'exposure': contract['exposure'], 'unobserved_target': contract['unobserved_target']}


def validate_prediction(root, prediction):
    require(canonical(prediction) == canonical(predict(root)), 'Prediction differs from full target-independent replay')
    return prediction


def _catalog(root, catalog_path=None):
    from matter1_isotopes import load_catalog, load_inputs, build_catalog, json_bytes
    if catalog_path is None:
        return load_catalog(root), (Path(root)/CATALOG).read_bytes()
    # Reproduction can consume its freshly generated catalog; authenticate it
    # against source bytes and curation, never merely against a caller's hash.
    expected = build_catalog(load_inputs(root))
    blob = Path(catalog_path).read_bytes()
    require(blob == json_bytes(expected), 'Supplied isotope catalog differs from bound source regeneration')
    return expected, blob


def _measured(record):
    h = record['half_life']
    require(h['kind'] == 'measured' and h['quantity'] == 'total_half_life', 'Comparison requires measured total half-life')
    v = Q(h['value_seconds'])
    lo, hi = Q(h['uncertainty_minus_seconds']), Q(h['uncertainty_plus_seconds'])
    require(v > lo >= 0 and hi >= 0, 'Positive source uncertainty envelope')
    return v, (v-lo,v+hi)


def compare(root, prediction, catalog=None, catalog_path=None):
    """Validate frozen prediction first; only this stage reads measured lifetimes."""
    root = Path(root)
    validate_prediction(root, prediction)
    actual, catalog_blob = _catalog(root, catalog_path)
    if catalog is not None:
        require(catalog == actual, 'Comparison may consume only the validated source catalog')
    catalog = actual
    records = {r['id']:r for r in catalog['isotopes']}
    comparisons = []
    for left,right in (('Og-294:ground','Lv-290:ground'), ('Lv-290:ground','Fl-286:ground'), ('Lv-293:ground','Fl-289:ground')):
        a, b = records[left], records[right]
        x, xb = _measured(a)
        y, yb = _measured(b)
        bounds = mapping(root).ratio_bounds([str(v) for v in xb], [str(v) for v in yb])
        low, high = map(Q, bounds['bounds'])
        comparisons.append({'numerator': left, 'denominator': right, 'measured_ratio': str(x/y),
            'conditional_model_ratio': '1', 'source_reported_uncertainty_envelope_ratio': bounds['bounds'],
            'equality_in_reported_envelope': low <= 1 <= high,
            'outcome': 'conditional_identity_insensitive_shared_clock_specialization_disagrees_with_reported_envelopes' if not low<=1<=high else 'not_excluded_by_reported_envelopes',
            'confidence_interpretation': 'descriptive_source_envelopes_only_not_joint_confidence_or_significance',
            'dependence': 'experimental_overlap_possible_no_independence_or_covariance_assumed',
            'source_records': {left:a['selection_source'], right:b['selection_source']},
            'classification': 'retrospective_conditional_model_comparison'})
    benchmark = []
    for key in ('Og-294:ground','Lv-290:ground','Fl-286:ground','Lv-293:ground','Fl-289:ground'):
        rec = records[key]
        value, envelope = _measured(rec)
        with localcontext() as ctx:
            ctx.prec = 40
            v = Decimal(value.numerator)/Decimal(value.denominator)
            lam = Decimal(2).ln()/v
            mean = v/Decimal(2).ln()
            lower, upper = [Decimal(x.numerator)/Decimal(x.denominator) for x in envelope]
            hazard_interval = [str(Decimal(2).ln()/upper),str(Decimal(2).ln()/lower)]
            mean_interval = [str(lower/Decimal(2).ln()),str(upper/Decimal(2).ln())]
        benchmark.append({'isotope':key, 'calibrating_half_life_seconds':str(value),
            'constant_hazard_per_second_display': str(lam), 'mean_lifetime_seconds_display': str(mean),
            'display_precision_decimal_digits':40, 'display_rounding':'decimal_context_half_even',
            'law':'S(t)=exp(-lambda*t), lambda=ln(2)/T_half',
            'half_life_source_envelope_seconds':[str(x) for x in envelope],
            'hazard_interval_exact_expression':'[ln(2)/T_upper, ln(2)/T_lower]',
            'mean_lifetime_interval_exact_expression':'[T_lower/ln(2), T_upper/ln(2)]',
            'hazard_interval_per_second_display':hazard_interval,
            'mean_lifetime_interval_seconds_display':mean_interval,
            'interval_interpretation':'monotonic_image_of_source_reported_envelopes_not_joint_confidence',
            'samples':[{'time_seconds':str(k*value), 'survival':str(Q(1,2**k))} for k in (0,1,2,4)],
            'classification':'conventional_exponential_benchmark_calibrated_to_each_measurement',
            'native_AOD_prediction':False, 'uncertainty':'source_uncertainty_not_reduced_or_refitted', 'source':rec['selection_source']})
    require(records['Fl-298:ground']['half_life']['kind']=='unknown', 'Unobserved Fl-298 must not acquire a measured target')
    return {'schema_version':3, 'profile':PROFILE, 'prediction_sha256':digest(prediction),
            'catalog_sha256':hashlib.sha256(catalog_blob).hexdigest(),
            'classification':'retrospective_conditional_model_comparison', 'comparisons':comparisons,
            'conventional_benchmark':benchmark, 'unscored':[{'id':'Fl-298:ground','reason':'unobserved_model_target_no_measurement'}],
            'native_atomic_agreement':'not_tested_atomic_map_unestablished',
            'interpretation':'The equal-state/shared-clock specialization fails the reported half-life envelopes. The isotope-dependent construction or observation premises must change; the data do not select a replacement law.',
            'physical_uncertainty_status':'incomplete_no_combined_significance_or_sigma_score'}


def report(root, prediction, comparison):
    runs = prediction['runs']
    base, off = runs['baseline'], runs['feedback_off']
    require(base['rows'][:3] == off['rows'][:3], 'Feedback intervention cannot change earlier survival')
    require(base['rows'][3]['survival'] != off['rows'][3]['survival'], 'Feedback must change strictly later survival')
    require(base['median'] != runs['loss_gain_2']['median'], 'Loss-gain countermodel must demonstrate different survival')
    return {'schema_version':3, 'profile':PROFILE, 'statuses':dict(STATUS),
            'prediction_sha256':digest(prediction), 'comparison_sha256':digest(comparison),
            'case_count':len(CASES), 'executed_variants':list(VARIANTS),
            'native_medians':{k:v['median'] for k,v in runs.items()},
            'causal_control':{'intervention_at_reference_count':2, 'common_survival_through_count':2,
                              'first_later_difference_count':3, 'baseline_survival_at_3':base['rows'][3]['survival'],
                              'feedback_off_survival_at_3':off['rows'][3]['survival']},
            'exact_assertions':['H1 traversal and injective Q4 coordinates', 'normalized admissible kernels including zero-weight admitted exit',
                                'probability mass conservation at every reference return', 'monotone survival and absorbing competing outcomes',
                                'antisymmetric responses affect subsequent kernels', 'unmerged history identities and retained inner lineage',
                                'M3 full finite joint law reproduces survival and spread', 'target-free replay precedes source-bound comparison'],
            'source_envelope_disagreements':sum(not x['equality_in_reported_envelope'] for x in comparison['comparisons']),
            'fitted_parameters':[], 'physical_prediction_executed':False,
            'geometry_or_test_success_is_native_admission':False}


def generate(root, catalog_path=None):
    root = Path(root)
    contract = default_contract(root)
    require(read_json(root/DATA/'model_contract.json') == contract, 'Explicit contract initialization/rebinding required before generation')
    prediction = predict(root)
    comparison = compare(root, prediction, catalog_path=catalog_path)
    return {'prediction.json':prediction, 'comparison.json':comparison, 'survival_report.json':report(root,prediction,comparison)}


def verify(root):
    root = Path(root)
    products = generate(root)
    for name,value in products.items():
        require((root/DATA/name).read_bytes() == canonical(value), f'Stale or forged survival artifact: {name}')
    return products['survival_report.json']
