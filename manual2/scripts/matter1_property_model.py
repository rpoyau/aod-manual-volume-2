"""Six-pilot native execution and explicitly unselected property-map witnesses.

Prediction does not import the property catalog or read evaluation values.
The maps below are downstream countermodels to identifiability, not atomic laws.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

import matter1_campaign_engine as native

ROOT = Path(__file__).resolve().parents[2]
DATA = Path('manual2/data/m1/properties/model')
PROFILE = 'matter1:element-properties:pilot-obstruction:v1'
UPSTREAM = '71cbcf7e637ababcde3b2e073fb4ceec4b1681b9'
CS_HZ = Q(9192631770)
PILOTS = (('H-1',1,1),('H-2',1,2),('H-3',1,3),('He-3',2,3),('He-4',2,4),('Cs-133',55,133))
PREDICTION_OUTPUTS = ('protocol.json','state_map.json','prediction.json','controls.json','obligations.json') + tuple(
    'raw/'+p[0]+'.json' for p in PILOTS) + tuple('controls/'+name+'.json' for name in ('fixed_path','feedback_off','passive'))
OUTPUTS = PREDICTION_OUTPUTS + ('comparison.json',)
MAIN = {
    'sections/05_curl_closure_duon_current.tex': ['eq:key-proposed-admitted-trace'],
    'sections/06_wave_state_relational_time.tex': ['eq:wave-update-trace','eq:cadence-ratio'],
    'sections/07_cell_measures_mappings.tex': ['def:m3-map','prop:m3-atomic-gain','eq:m3-finite-law'],
}
UNRESOLVED = (
    ('STATE','physical preparation to native state','A state-specific construction must distinguish the measured electronic and nuclear states.'),
    ('PHASE','native return to emitted phase','A justified emitted-phase law must fix relative gains before target comparison.'),
    ('ENERGY','native history to energy','An energy observable and its dimensional normalization must be justified independently of evaluated energies.'),
    ('MASS','native construction to neutral atomic mass','A rest-mass observable must account for the specified whole atomic state; transition energy is not atomic rest mass.'),
    ('SI','realized clock and uncertainty','An applicable realization, compatible observation window and joint uncertainty must be supplied.'),
    ('JOINT','one law across independent properties','One fixed model must predict independently measured quantities without per-property retuning.'),
)


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path):
    def pairs(items):
        result={}
        for k,v in items:
            require(k not in result,'Duplicate key: '+k)
            result[k]=v
        return result
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+x)))


def source_bindings(root):
    root=Path(root)
    foundation=read_json(root/'manual2/evidence/foundation-source.json')
    require(foundation['upstream_head']==UPSTREAM,'Property model foundation changed')
    rows=[]
    for name,labels in MAIN.items():
        blob=(root/name).read_bytes()
        sha=hashlib.sha256(blob).hexdigest()
        require(sha==foundation['files'][name],'Bound Main source differs: '+name)
        text=blob.decode()
        require(all('\\label{'+label+'}' in text for label in labels),'Missing exact Main label')
        rows.append({'path':name,'sha256':sha,'labels':labels})
    for name in ('manual2/scripts/matter1_campaign_engine.py',
                 'manual2/vendor/aod_m3/current/aod_native_closure_wave.py',
                 'manual2/scripts/matter1_property_model.py'):
        rows.append({'path':name,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()})
    require((root/'manual2/scripts/matter1_property_model.py').read_bytes()==Path(__file__).read_bytes(),
            'Executing property model differs from requested source')
    return {'upstream_head':UPSTREAM,'files':rows,'role':'Main definitions consumed by a downstream application; no Main change'}


def default_protocol(root=ROOT):
    return {'schema_version':1,'profile':PROFILE,'source_bindings':source_bindings(root),
        'pilot_order':[p[0] for p in PILOTS],
        'native_rule':'unchanged matter1:inner-recurrence-campaign:v1',
        'native_configs':{name:native.default_config(z,a) for name,z,a in PILOTS},
        'stopping_rule':'three inner rounds and one new outer reclosure for every pilot',
        'reference_policy':'configuration-specific generic reference; comparison to Cs below is a stipulated diagnostic bridge, not an identified atomic frequency ratio',
        'global_map_family':{
            'formula':'g_lambda(Z)=1+lambda*(55-Z)/54; r_i=q_i/q_Cs; nu_i=nu_Cs*r_i*g_lambda(Z)',
            'domain':'pilot Z in {1,2,55}; lambda >= 0; q_i and q_Cs positive bounded cadences',
            'witnesses':[{'id':'W0','lambda':'0','energy_scale_J':'1','mass_scale_kg':'1'},
                         {'id':'W1','lambda':'1','energy_scale_J':'2','mass_scale_kg':'2'}],
            'selection':'none; all witnesses are unselected countermodels',
            'energy_formula':'E_i=energy_scale_J*r_i*g_lambda(Z)',
            'mass_formula':'m_i=mass_scale_kg*B_i/B_Cs',
            'dimensional_status':'typed positive maps only; no energy operator, rest-mass law or physical identification is established',
            'per_property_or_isotope_retuning':False},
        'reference':{'frequency_hz':str(CS_HZ),'role':'retained exact Cs SI definition only; not a realized clock',
                     'source':'https://www.bipm.org/en/si-base-units/second'},
        'requested_observables':['hyperfine_frequency','excitation_energy','atomic_mass','ionization_energy','ground_configuration','spin_parity'],
        'evaluation':{'exposure':'retrospective; known targets predate this protocol',
            'adopted_target_ids':{name:'hyperfine:'+name for name,z,a in PILOTS},
            'target_transition':'ground_state_hyperfine_separation',
            'target_conditions':{'electronic_state':'ground','magnetic_field':'unperturbed_zero_field'},
            'calibration_inputs':['Cs defining frequency only'],
            'fitted_parameters':[],'target_access_in_prediction':'forbidden',
            'countermodel_residual_role':'descriptive diagnostic only; no selected law or empirical AOD score',
            'family_ratio_criterion':'Under identification of the stipulated bridge with the selected H/D/T targets, every common-gain isotope ratio must lie in the ratio envelope formed from reported values plus/minus their quoted uncertainty magnitudes. One failed ratio excludes the whole common-Z gain family from that diagnostic criterion.',
            'criterion_origin':'retrospective; targets already exposed, not a preregistered or independent test',
            'envelope_semantics':'descriptive rectangular source envelopes; not joint confidence intervals; no Gaussian law, independence or coverage probability assumed',
            'whole_law_gate':'incomplete if any requested physical observable lacks its state/observation law; never substitute a derived duplicate for an independent observable',
            'failure_policy':'A valid out-of-domain witness or violated claimed invariant rejects the declared candidate; a future calibrated empirical rejection applies to the frozen model-and-observation conjunction, not all AOD.',
            'revision_policy':'Record a new protocol and preserve the failed version before changing laws, targets, exclusions or criteria.'},
        'controls':{'pilot':'H-1','feedback_intervention':'feedback off after common first round, with the same forced admissible orientation path',
            'passive_observation':'observer=False must preserve complete trajectory and RNG state',
            'state_label_control':'two declared spectroscopy-state requests share one generic config because the state-to-native map is absent'},
        'claim':'executable missing-premise diagnosis; no atomic physical prediction'}


def validate_protocol(root,protocol):
    require(canonical(protocol)==canonical(default_protocol(root)),
            'Frozen property model protocol differs: source, state, law, target policy or retuning')
    return protocol


def _dimensions():
    # Dimension order is mass, length, time. Native counts/ratios are dimensionless.
    return {'dimension_order':['M','L','T'],'native_ratio':[0,0,0],
        'frequency_scale':[0,0,-1],'energy_scale':[1,2,-2],'mass_scale':[1,0,0],
        'frequency_output':[0,0,-1],'energy_output':[1,2,-2],'mass_output':[1,0,0],
        'identifiability':'Multiplying a dimensionless trace statistic by any positive correctly dimensioned scale preserves dimensions; dimensions do not select the scale.',
        'transition_energy_vs_rest_mass':'Even importing E=h*nu and a mass-equivalent E/c^2 would describe the selected transition; it does not identify the neutral atom rest mass.',
        'external_physical_relations_executed':False}


def state_map():
    rows=[]
    for name,z,a in PILOTS:
        rows.append({'entity_id':f'atomic-isotope:{name}:q0:ground','isotope_entity_id':f'isotope:{name}:ground',
            'native_config':native.default_config(z,a),'operative_distinctions':['Z','A','electron_count','rounds','seed','feedback'],
            'unrepresented_physical_distinctions':['electronic wavefunction/configuration','nuclear spin','hyperfine sublevel','apparatus/environment'],
            'generic_inventory_identified':True,'physical_state_correspondence':'unestablished',
            'charge_scope':'neutral inventory count; no electronic state identified'})
    generic=native.default_config(1,1)
    return {'schema_version':1,'profile':PROFILE,'rows':rows,
        'state_separation_obstruction':{'requests':['H-1:requested-lower-spectroscopy-state','H-1:requested-upper-spectroscopy-state'],
            'request_status':'distinct requested roles; no quantum labels or physical admission invented',
            'operative_configurations':[generic,deepcopy(generic)],'same_configuration':True,
            'consequence':'This adapter cannot infer a state splitting from distinctions that have not entered a justified native preparation map.'}}


def map_witnesses(protocol,runs):
    qc=Q(runs['Cs-133']['observation']['cadence_ratio'])
    bc=runs['Cs-133']['construction']['outward_occurrences']
    require(qc>0 and bc>0,'Positive declared reference required')
    rows=[]
    for witness in protocol['global_map_family']['witnesses']:
        lam=Q(witness['lambda']);epsilon=Q(witness['energy_scale_J']);mu=Q(witness['mass_scale_kg'])
        require(lam>=0 and epsilon>0 and mu>0,'Invalid common positive map parameters')
        for name,z,a in PILOTS:
            r=Q(runs[name]['observation']['cadence_ratio'])/qc
            gain=1+lam*Q(55-z,54)
            b=runs[name]['construction']['outward_occurrences']
            require(gain>0,'Gain outside positive family')
            rows.append({'witness':witness['id'],'entity_id':f'atomic-isotope:{name}:q0:ground',
                'pilot':name,'common_parameter_vector':deepcopy(witness),'native_cadence_quotient':str(r),
                'gain':str(gain),'diagnostic_frequency_hz':str(CS_HZ*r*gain),
                'arbitrary_energy_witness_J':str(epsilon*r*gain),
                'arbitrary_mass_witness_kg':str(mu*Q(b,bc)),
                'classification':'unselected_typed_map_counterexample_not_physical_prediction',
                'physical_standard_uncertainty':None,'trajectory_sha256':runs[name]['trajectory_sha256']})
    for name,z,a in PILOTS:
        pair=[r for r in rows if r['pilot']==name]
        require(pair[0]['arbitrary_energy_witness_J']!=pair[1]['arbitrary_energy_witness_J'] and
                pair[0]['arbitrary_mass_witness_kg']!=pair[1]['arbitrary_mass_witness_kg'],
                'Dimensional witnesses do not separate outputs')
        if name=='Cs-133':
            require(all(Q(r['diagnostic_frequency_hz'])==CS_HZ for r in pair),'Cs normalization broken')
        else:
            require(pair[0]['diagnostic_frequency_hz']!=pair[1]['diagnostic_frequency_hz'],
                    'Relative-phase witnesses fail to separate outputs')
    return rows


def causal_controls(root,baseline):
    config=native.default_config(1,1)
    signs=tuple(r['orientation'] for r in baseline['trajectory']['decisions'])
    fixed=native.run_case(config,root,_forced=signs)
    off=native.run_case(dict(config,feedback=False),root,_forced=signs)
    passive=native.run_case(config,root,observer=False)
    first=lambda r:[x for x in r['trajectory']['inner_returns'] if x['round']==0]
    require(fixed['trajectory']==baseline['trajectory'],'Forced baseline is not the original admissible path')
    require(first(fixed)==first(off),'Intervention lost common first-round prefix')
    require([d['orientation'] for d in fixed['trajectory']['decisions']]==
            [d['orientation'] for d in off['trajectory']['decisions']],'Matched path differs')
    require(fixed['trajectory']['outer_return']['committed']!=off['trajectory']['outer_return']['committed'],
            'Specified feedback intervention did not change later execution')
    require(passive['trajectory']==baseline['trajectory'] and
            passive['execution']['rng_state_sha256']==baseline['execution']['rng_state_sha256'],
            'Passive observation changed the engine')
    # This control is conditional on one fixed path, not a claim that two seeded
    # samplers with different weights consume the same sequence of random draws.
    report={'profile':PROFILE,'pilot':'H-1','fixed_orientation_path':list(signs),
        'comparison_class':'matched_admissible_path_intervention_not_unconditional_sampling_test',
        'same_first_round':True,'same_orientation_path':True,'passive_trajectory_equal':True,
        'passive_rng_equal':True,'baseline_outer_cut':fixed['trajectory']['outer_return']['committed'],
        'feedback_off_outer_cut':off['trajectory']['outer_return']['committed'],
        'baseline_path_probability':fixed['execution']['conditional_path_probability'],
        'feedback_off_path_probability':off['execution']['conditional_path_probability'],
        'passive_observation':passive['observation'],'physical_causal_effect_established':False,
        'raw_sha256':{'fixed_path':digest(fixed),'feedback_off':digest(off),'passive':digest(passive)}}
    return report,{'fixed_path':fixed,'feedback_off':off,'passive':passive}


def prediction_products(root=ROOT,progress=None):
    """Execute every pilot using only frozen model/source inputs; never targets."""
    root=Path(root)
    protocol=default_protocol(root)
    runs={}
    for name,z,a in PILOTS:
        if progress:progress('Executing native pilot '+name)
        runs[name]=native.run_case(protocol['native_configs'][name],root)
        require(runs[name]['observation'] is not None,'Pilot lacks defined generic observation')
    controls,raw_controls=causal_controls(root,runs['H-1'])
    witnesses=map_witnesses(protocol,runs)
    states=state_map()
    rows=[]
    for name,z,a in PILOTS:
        r=runs[name]
        rows.append({'pilot':name,'entity_id':f'atomic-isotope:{name}:q0:ground',
            'config':protocol['native_configs'][name],'native_construction':r['construction'],
            'native_execution':r['execution'],'native_observation':r['observation'],
            'trajectory_sha256':r['trajectory_sha256'],'raw_sha256':digest(r),
            'physical_prediction':False,'physical_properties':{p:None for p in protocol['requested_observables']}})
    collisions=[]
    for i,left in enumerate(rows):
        for right in rows[i+1:]:
            if left['native_observation']['cadence_ratio']==right['native_observation']['cadence_ratio']:
                require(left['trajectory_sha256']!=right['trajectory_sha256'],'Distinct pilot traces unexpectedly identical')
                collisions.append({'left':left['entity_id'],'right':right['entity_id'],
                    'common_bounded_cadence':left['native_observation']['cadence_ratio'],
                    'left_trajectory_sha256':left['trajectory_sha256'],'right_trajectory_sha256':right['trajectory_sha256'],
                    'scope':'Equal scalar cadence does not reconstruct distinct retained preparations or histories; no physical degeneracy is asserted.'})
    prediction={'schema_version':1,'profile':PROFILE,'status':'native_pilot_executed_physical_property_laws_unresolved',
        'protocol_sha256':digest(protocol),'state_map_sha256':digest(states),'source_bindings':protocol['source_bindings'],
        'target_access':'not_read','exposure':'retrospective_targets_previously_known; no independent prediction claim',
        'rows':rows,'countermodels':witnesses,'dimensions':_dimensions(),'controls_sha256':digest(controls),
        'cadence_projection_collisions':collisions,
        'fitted_parameters':[],'selected_physical_law':None,'physical_prediction_complete':False,
        'obstruction':{'fixed':['all six native histories','Cs frequency normalization','one common parameter vector per witness','quantity dimensions'],
            'free':['relative emitted-phase gain','energy scale and observable','atomic rest-mass scale and observable'],
            'result':'Two explicit global map witnesses preserve every listed constraint but give different nonreference frequency, energy and mass outputs.',
            'scope':'Non-identifiability within these declared map families; not proof that every future AOD application must remain underdetermined.'}}
    obligations={'schema_version':1,'profile':PROFILE,'prediction_sha256':digest(prediction),
        'items':[{'id':'EP-'+key,'premise':title,'status':'unresolved','required_evidence':detail} for key,title,detail in UNRESOLVED],
        'model_work_completed':'six generic executions, causal controls and explicit map non-identifiability witnesses',
        'physical_model_completed':False,'source_bindings':protocol['source_bindings']}
    products={'protocol.json':protocol,'state_map.json':states,'prediction.json':prediction,
              'controls.json':controls,'obligations.json':obligations}
    products.update({'raw/'+name+'.json':r for name,r in runs.items()})
    products.update({'controls/'+name+'.json':r for name,r in raw_controls.items()})
    return products


def generate_predictions(root=ROOT,output_root=None,progress=None):
    products=prediction_products(root,progress)
    destination=Path(root if output_root is None else output_root)/DATA
    for name,value in products.items():
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(canonical(value))
    return {'status':'generated_target_free_property_diagnostics','outputs':sorted(products),
            'physical_prediction_complete':False,'prediction_sha256':digest(products['prediction.json'])}


def verify_predictions(root=ROOT,progress=None,prediction_root=None):
    products=prediction_products(root,progress)
    destination=Path(root if prediction_root is None else prediction_root)/DATA
    for name,value in products.items():
        path=destination/name
        require(path.read_bytes()==canonical(value),'Stored property model differs; verifier does not repair: '+name)
    return products


def validate_prediction_envelope(root,prediction,protocol):
    """Structural preflight only; public comparison CLI performs native replay first."""
    validate_protocol(root,protocol)
    require(prediction['profile']==PROFILE and prediction['protocol_sha256']==digest(protocol),
            'Prediction protocol binding differs')
    require(prediction['status']=='native_pilot_executed_physical_property_laws_unresolved' and
            prediction['source_bindings']==protocol['source_bindings'] and
            prediction['state_map_sha256']==digest(state_map()),'Prediction source, state or status differs')
    require(prediction['target_access']=='not_read' and prediction['fitted_parameters']==[] and
            prediction['selected_physical_law'] is None and prediction['physical_prediction_complete'] is False,
            'Unsupported physical prediction, target access or fitted law')
    require([r['pilot'] for r in prediction['rows']]==[p[0] for p in PILOTS], 'Pilot coverage differs')
    require(all(r['physical_prediction'] is False and
                set(r['physical_properties'])==set(protocol['requested_observables']) and
                all(v is None for v in r['physical_properties'].values())
                for r in prediction['rows']),'Unidentified physical property was promoted or omitted')
    for row,(name,z,a) in zip(prediction['rows'],PILOTS):
        require(row['entity_id']==f'atomic-isotope:{name}:q0:ground' and
                row['config']==protocol['native_configs'][name],'Pilot state or operative configuration differs')
    projected={row['pilot']:{'observation':row['native_observation'],'construction':row['native_construction'],
                           'trajectory_sha256':row['trajectory_sha256']} for row in prediction['rows']}
    require(prediction['countermodels']==map_witnesses(protocol,projected),
            'Common observation/energy/mass witness changed or retuned')
    return prediction


def _family_ratio_diagnostic(rows):
    """Test a whole common-Z gain family without selecting or refitting lambda."""
    by={r['pilot']:r for r in rows};checks=[]
    for numerator in ('H-2','H-3'):
        a,b=by[numerator],by['H-1'];ta,tb=a['target'],b['target']
        item={'numerator':numerator,'denominator':'H-1','status':'not_checked_missing_numeric_target_or_quoted_magnitude'}
        if ta and tb and ta['value_kind']==tb['value_kind']=='numeric' and all(
                t['uncertainty'].get('value') is not None for t in (ta,tb)):
            av,bv=Q(ta['value']),Q(tb['value']);au,bu=Q(ta['uncertainty']['value']),Q(tb['uncertainty']['value'])
            require(au>=0 and bu>=0,'Negative quoted uncertainty magnitude')
            if av-au>0 and bv-bu>0:
                ratios=[Q(x['diagnostic_frequency_hz'])/Q(y['diagnostic_frequency_hz'])
                    for x,y in zip(a['diagnostics'],b['diagnostics'])]
                require(len(ratios)==2 and ratios[0]==ratios[1], 'Common-Z gain did not cancel')
                lower,upper=(av-au)/(bv+bu),(av+au)/(bv-bu)
                passes=lower<=ratios[0]<=upper
                item.update(status='within_reported_envelope' if passes else 'outside_reported_envelope',
                    entire_common_gain_family_ratio=str(ratios[0]),reported_point_ratio=str(av/bv),
                    descriptive_ratio_envelope=[str(lower),str(upper)],all_lambda_values_covered=True,
                    reason='g_lambda(1) cancels algebraically for every positive member; the two witnesses also agree exactly.',
                    uncertainty_semantics=[deepcopy(ta['uncertainty']),deepcopy(tb['uncertainty'])],
                    covariance='unknown; shared H dependence retained; rectangle is not a joint-confidence region')
        checks.append(item)
    failed=any(r['status']=='outside_reported_envelope' for r in checks)
    complete=all(r['status'] in ('within_reported_envelope','outside_reported_envelope') for r in checks)
    return {'classification':'retrospective_whole_countermodel_family_diagnostic',
        'hypothesis':'Identify the stipulated bridge outputs with the selected zero-field H/D/T hyperfine targets and use the explicitly declared descriptive-envelope criterion.',
        'disposition':'incompatible_with_retained_source_envelopes' if failed else ('compatible_on_checked_ratios' if complete else 'not_checked_missing_source_input'),
        'checks':checks,'parameter_fit_performed':False,'physical_AOD_theory_refuted':False,
        'observable_types_in_diagnostic':1 if complete else 0,
        'scope':'One frequency observable across isotopes; does not satisfy the independent multi-property gate and does not provide a physical state/observation map.'}


def _compare_catalog_values(root,prediction,protocol,catalog):
    """Pure diagnostic reduction. Production callers use compare_catalog's source validation.

    The test suite uses explicitly synthetic records here to check arithmetic
    and non-mutation. This private helper does not certify catalog provenance.
    """
    validate_prediction_envelope(root,prediction,protocol)
    require(type(catalog) is dict and type(catalog.get('properties')) is list,'Property target catalog required')
    rows=[]
    for name,z,a in PILOTS:
        entity=f'atomic-isotope:{name}:q0:ground'
        requested_id=protocol['evaluation']['adopted_target_ids'][name]
        matches=[r for r in catalog['properties'] if r['id']==requested_id]
        require(len(matches)<=1,'Duplicate adopted target ID: '+requested_id)
        target=matches[0] if matches else None
        candidates=[r for r in prediction['countermodels'] if r['entity_id']==entity]
        if target is not None and target['value_kind']=='numeric':
            require(target['entity_id']==entity and target['property']=='hyperfine_frequency' and
                    target.get('selection_status')=='adopted' and
                    target.get('transition')==protocol['evaluation']['target_transition'],
                    'Adopted target state/property/transition differs')
            require(type(target.get('conditions')) is dict and all(target['conditions'].get(k)==v
                    for k,v in protocol['evaluation']['target_conditions'].items()) and
                    'experimental_window' in target['conditions'] and 'magnetic_sublevels' in target['conditions'],
                    'Target field regime, state or acquisition conditions missing/different')
            require(all(type(target.get(k)) is str and bool(target[k]) for k in
                    ('source_id','locator','exposure','method','qualification')) and
                    type(target.get('uncertainty')) is dict and target.get('physical_prediction') is False,
                    'Target provenance, uncertainty, exposure or claim scope missing')
            competing=[r for r in catalog['properties'] if r.get('entity_id')==entity and
                r.get('property')=='hyperfine_frequency' and r.get('transition')==target['transition'] and
                r.get('selection_status')=='adopted']
            require(len(competing)==1,'Ambiguous adopted target for requested state/transition')
            require(target['unit']=='Hz' and type(target['value']) is str and Q(target['value'])>0,
                    'Hyperfine comparison requires positive exact Hz target')
            observed=Q(target['value'])
            if name=='Cs-133':require(observed==CS_HZ,'Cs defining target differs from frozen reference')
            diagnostic=[{'witness':r['witness'],'diagnostic_frequency_hz':r['diagnostic_frequency_hz'],
                'residual_hz':str(Q(r['diagnostic_frequency_hz'])-observed),
                'relative_residual':str((Q(r['diagnostic_frequency_hz'])-observed)/observed),
                'standardized_residual':None} for r in candidates]
            status='calibrant_reproduction_not_prediction' if name=='Cs-133' else 'unselected_countermodel_residual_only'
        else:
            diagnostic=[];status='no_numeric_target_for_requested_external_state'
        rows.append({'pilot':name,'entity_id':entity,'property':'hyperfine_frequency',
            'target':deepcopy(target),'comparison_status':status,'diagnostics':diagnostic,
            'target_selection':{'requested_record_id':requested_id,'policy':'explicit adopted source/transition record; alternate records retained'},
            'matching':{'external_state_identity':entity,'external_transition':protocol['evaluation']['target_transition'],
                'native_to_external_state':'unestablished','native_to_experimental_window':'unestablished',
                'native_field_regime':'not represented; recorded zero-field target conditions are not native admission',
                'external_conditions':deepcopy(target.get('conditions')) if target else None,
                'conditional_scope':'descriptive residual for an unselected bridge; no state/field/window-matched physical score'},
            'physical_prediction_test':'not_executed_missing_selected_state_and_observation_law',
            'shared_reference_covariance':None,'complete_joint_uncertainty':None})
    matrix=[{'property':p,'law_status':'missing_premise','independent_empirical_score':None,
        'reason':'No selected physical state/observable law; derived re-expression is not an independent observation.'}
        for p in protocol['requested_observables']]
    return {'schema_version':1,'profile':PROFILE,'prediction_sha256':digest(prediction),
        'protocol_sha256':digest(protocol),'evaluation_catalog_sha256':digest(catalog),
        'exposure':'retrospective','fitted_parameters':[],'per_property_retuning':False,
        'rows':rows,'multiobservable_matrix':matrix,'whole_law_disposition':'incomplete_missing_premises',
        'joint_family_diagnostic':_family_ratio_diagnostic(rows),
        'physical_model_empirical_score':None,'independent_property_tests_completed':0,
        'derived_frequency_period_energy_tests_count_as_independent':False,
        'interpretation':'Residuals describe unselected dimensional/phase countermodels. They neither select a map nor constitute a test of a completed AOD atomic law.'}


def compare_catalog(root,prediction,protocol,catalog):
    """Validate the adopted source catalog after target-free replay, then compare.

    An alternate target file must be a byte-equivalent parsed copy of this
    source-bound catalog. New acquisition/selection requires a data rebind.
    """
    from matter1_properties import verify, validate_catalog
    root=Path(root)
    verify(root)
    folder=root/'manual2/data/m1/properties'
    validate_catalog(catalog,read_json(folder/'states.json'),read_json(folder/'definitions.json'))
    require(canonical(catalog)==canonical(read_json(folder/'catalog.json')),
            'Comparison target differs from adopted source-bound catalog')
    return _compare_catalog_values(root,prediction,protocol,catalog)
