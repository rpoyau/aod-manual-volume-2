"""All-element campaign: identity inputs, complete replay and separate comparisons.

The frozen input projection contains isotope identities and source assignments,
not frequency or lifetime targets. Model execution never opens the evaluation
catalog. Generic fold admission is distinct from physical atomic admission.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import csv
import hashlib
from fractions import Fraction as Q
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path('manual2/data/m1/campaign')
PROFILE = 'matter1:all-elements-campaign:v1'
IDENTITY_SHA256 = 'fd2f46dd80fdbc87bcf1db574bae224a59370aedc159e4a72408d92cbdf23491'
REFERENCE_SHA256 = '1ab139f127467ad77b25d873522fa253e713c6cad1fad21a3589726b0450f232'
IDENTITY_FIELDS = ('id','Z','A','N','symbol','state','state_assignment','spin_parity',
                   'empirical_status','exposure','selection_source','source_records')
OUTPUTS = ('manifest.json','prediction.json','comparison.json','campaign_report.json')
DEPENDENCIES = (
    'physical_preparation_to_constructed_state',
    'native_FRG_ring_gate_for_atomic_coupling',
    'atomic_state_to_emitted_phase_observation_map',
    'isotope_state_dependent_retention_capacity_and_loss_observable',
    'decay_channel_and_daughter_identification',
    'reference_reclosures_to_realized_SI_cycles',
    'matched_apparatus_window_and_complete_joint_uncertainty',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()


def _pairs(items):
    result = {}
    for key,value in items:
        require(key not in result, 'Duplicate JSON key: '+key)
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+value)))


def _engine():
    import matter1_campaign_engine as engine
    return engine


def identity_inputs(root=ROOT):
    root=Path(root)
    path=root/DATA/'identity_inputs.json'
    require(sha(path)==IDENTITY_SHA256, 'Campaign isotope identity snapshot changed')
    data=read_json(path)
    require(type(data['schema_version']) is int and data['schema_version']==1,
            'Identity schema differs')
    require(len(data['records'])==27 and len({r['id'] for r in data['records']})==27,
            'Identity coverage differs')
    for row in data['records']:
        require(set(row)==set(IDENTITY_FIELDS), 'Identity fields differ')
        require(all(type(row[k]) is int for k in ('Z','A','N')) and
                1<=row['Z']<=118 and row['A']>=row['Z'] and row['N']==row['A']-row['Z'],
                'Invalid exact identity counts')
        require(row['state'] in ('ground','m_candidate'), 'Unknown isotope state')
        require(row['state_assignment'] in ('established_ground_state','assumed_ground_state',
                'tentative_ground_state','not_established','tentative_isomer'), 'Unknown state assignment')
        require(row['empirical_status'] in ('evaluated_observed','reported_observed','tentative_assignment',
                'tentative_isomer','unobserved_rejected_candidate','unobserved_model_target'),
                'Unknown empirical status')
        require(row['exposure'] in ('retrospective_source_seen_before_model_freeze',
                'unscored_target_no_measured_value'), 'Unknown target exposure')
    return data


def reference_inputs(root=ROOT):
    path=Path(root)/'manual2/data/m1/reference_inputs.csv'
    require(sha(path)==REFERENCE_SHA256, 'Preserved element reference input changed')
    with path.open(newline='') as handle:
        rows=list(csv.DictReader(handle))
    require(len(rows)==126 and [int(r['z']) for r in rows]==list(range(1,127)),
            'Reference slot coverage differs')
    elements=[r for r in rows if r['record_kind']=='element_reference']
    require(len(elements)==118 and [int(r['z']) for r in elements]==list(range(1,119)),
            'Element reference coverage differs')
    require(all(r['record_kind']=='unfilled_reference_slot' for r in rows[118:]),
            'Unfilled slots were promoted to elements')
    return elements


def configuration_id(z,a):
    require(type(z) is int and type(a) is int and 1<=z<=118 and a>=z,
            'Configuration requires exact Z and A')
    return f'Z{z:03d}-A{a:03d}'


def default_manifest(root=ROOT):
    """Read only target-free identities and frozen reference selections."""
    records=[]
    for row in reference_inputs(root):
        z,a=int(row['z']),int(row['mass_a'])
        records.append({'id':f"reference:{row['symbol']}-{a}", 'z':z,'a':a,
            'symbol':row['symbol'], 'state':'unspecified_reference',
            'state_assignment':'selection_provenance_unresolved',
            'configuration_id':configuration_id(z,a), 'provenance_kind':'legacy_element_reference',
            'selection_source':row['source_id'], 'selection_policy':row['selection_policy_id'],
            'physical_preparation':None, 'state_to_configuration_map':None})
    for row in identity_inputs(root)['records']:
        records.append({'id':row['id'],'z':row['Z'],'a':row['A'],'symbol':row['symbol'],
            'state':row['state'],'state_assignment':row['state_assignment'],
            'configuration_id':configuration_id(row['Z'],row['A']),
            'provenance_kind':'curated_isotope_state', 'selection_source':row['selection_source'],
            'selection_policy':'preserved_curated_record', 'physical_preparation':None,
            'state_to_configuration_map':None})
    pairs=sorted({(r['z'],r['a']) for r in records})
    require(len(records)==145 and len(pairs)==135, 'Campaign coverage differs')
    engine=_engine()
    configurations=[]
    for z,a in pairs:
        key=configuration_id(z,a)
        configurations.append({'id':key,'z':z,'a':a,'n':a-z,'electron_count':z,
            'recipe':engine.default_config(z,a),
            'record_ids':[r['id'] for r in records if r['configuration_id']==key],
            'preparation':{'kind':'generic_neutral_constituent_inventory',
                'physical_atomic_state':None,'environment':'declared_finite_coupling_only'},
            'physical_loss_rule':None,'physical_observation_map':None})
    return {'schema_version':1,'profile':PROFILE,
        'input_sha256':{'reference_inputs.csv':REFERENCE_SHA256,'identity_inputs.json':IDENTITY_SHA256},
        'records':records,'configurations':configurations,
        'coverage':{'elements':118,'reference_slots_preserved':126,'reference_records':118,
                    'isotope_state_records':27,'source_records':145,'distinct_Z_A':135},
        'state_resolution':'Separate records share a generic inventory when no state-preparation map is established.',
        'stopping_policy':{'internal_rounds':3,'new_outer_reclosures':1,
            'physical_survival_horizon':None,
            'rule':'Complete the declared internal rounds, then one outer reclosure; no physical decay stopping claim.'},
        'physical_predictions':None,'unresolved_dependencies':list(DEPENDENCIES)}


def validate_manifest(root, manifest):
    require(canonical(manifest)==canonical(default_manifest(root)),
            'Campaign manifest differs from original target-free inputs')
    return manifest


def _config(manifest,key):
    rows=[row for row in manifest['configurations'] if row['id']==key]
    require(len(rows)==1, 'Unknown or duplicate campaign configuration')
    return rows[0]


def execute_case(root,manifest,key):
    config=_config(manifest,key)
    engine=_engine()
    result=engine.run_case(config['recipe'],root=Path(root))
    return {'schema_version':1,'profile':PROFILE,'configuration_id':key,
            'manifest_sha256':digest(manifest),'original_configuration':deepcopy(config),
            'engine_code_sha256':sha(Path(engine.__file__)), 'result':result}


def validate_case_envelope(manifest,key,value):
    require(set(value)=={'schema_version','profile','configuration_id','manifest_sha256',
            'original_configuration','engine_code_sha256','result'}, 'Campaign case schema differs')
    require(type(value['schema_version']) is int and value['schema_version']==1 and value['profile']==PROFILE,
            'Campaign case profile differs')
    require(value['configuration_id']==key and value['manifest_sha256']==digest(manifest),
            'Campaign case binding differs')
    require(canonical(value['original_configuration'])==canonical(_config(manifest,key)),
            'Campaign original configuration differs')
    engine=_engine()
    require(value['engine_code_sha256']==sha(Path(engine.__file__)), 'Campaign executor differs')
    recipe=_config(manifest,key)['recipe']
    result=value['result']
    require(canonical(result['original_config'])==canonical(recipe) and
            result['configuration_sha256']==digest(recipe),
            'Campaign result is bound to a different operative configuration')
    construction=result['construction']
    require(all(type(construction[name]) is int and construction[name]==recipe[name]
                for name in ('z','a','electron_count')), 'Campaign result inventory differs')
    actual_specs=[(row['id'],row['p'],row['q']) for row in construction['constituents']]
    require(canonical(actual_specs)==canonical(engine.inventory(recipe)),
            'Campaign constituent identities differ from the operative inventory')
    return value


def verify_case(root,manifest,key,value):
    validate_case_envelope(manifest,key,value)
    require(canonical(value)==canonical(execute_case(root,manifest,key)),
            'Campaign case differs from complete original-input replay: '+key)
    return True


def native_comparisons(cases):
    """Compare finite protocol outputs without identifying an atomic frequency."""
    pairs=[('H-1/Cs-133','Z001-A001','Z055-A133'),
           ('Fl-286/Fl-289','Z114-A286','Z114-A289'),
           ('Og-294/Lv-290','Z118-A294','Z116-A290'),
           ('Lv-293/Fl-289','Z116-A293','Z114-A289')]
    rows=[]
    for name,left,right in pairs:
        a=_case_projection(cases[left]['result']);b=_case_projection(cases[right]['result'])
        aw,bw=a['reference_window'],b['reference_window']
        rows.append({'id':name,'left_configuration':left,'right_configuration':right,
            'left_bounded_cadence':a['cadence_ratio'],'right_bounded_cadence':b['cadence_ratio'],
            'left_lag':a['lag'],'right_lag':b['lag'],
            'left_window':aw,'right_window':bw,
            'left_reference_id':[left,a['reference_identity']],
            'right_reference_id':[right,b['reference_identity']],
            'same_reference_identity':(left,a['reference_identity'])==(right,b['reference_identity']),
            'same_reference_recipe':cases[left]['result']['rule']['reference']==cases[right]['result']['rule']['reference']
                and cases[left]['result']['construction']['reference_RD']==cases[right]['result']['construction']['reference_RD'],
            'reference_identity_scope':'Native identities are local to each independent configuration run; cross-run keys include configuration_id.',
            'matched_window':aw==bw,
            'finite_protocol_elapsed_cut_ratio':str(Q(aw[1]-aw[0],bw[1]-bw[0])),
            'elapsed_ratio_scope':'Durations of the same declared finite protocol in model scheduler cuts; not transition frequencies or SI time.',
            'atomic_frequency_ratio':None,
            'reason':'Configuration-specific windows and an unidentified emitted-phase map do not supply a common-window atomic frequency ratio.'})
    return rows


def _assemble_prediction(root,manifest,cases):
    expected={row['id'] for row in manifest['configurations']}
    require(set(cases)==expected, 'Incomplete or extra campaign cases')
    for key,value in cases.items():validate_case_envelope(manifest,key,value)
    return {'schema_version':1,'profile':PROFILE,'manifest_sha256':digest(manifest),
        'application_code_sha256':sha(Path(__file__)),
        'engine_code_sha256':sha(Path(_engine().__file__)),
        'target_access':'evaluation_values_not_read', 'configuration_count':len(cases),
        'case_sha256':{key:digest(cases[key]) for key in sorted(cases)},
        'native_comparisons':native_comparisons(cases),
        'cases':{key:_case_projection(cases[key]['result']) for key in sorted(cases)},
        'physical_atomic_prediction':None,'physical_half_life_prediction':None,
        'physical_gain':None,'physical_capacity':None,'physical_loss_observable':None,
        'unresolved_dependencies':list(DEPENDENCIES)}


def predict(root=ROOT,manifest=None):
    root=Path(root);manifest=default_manifest(root) if manifest is None else validate_manifest(root,manifest)
    cases={row['id']:execute_case(root,manifest,row['id']) for row in manifest['configurations']}
    return _assemble_prediction(root,manifest,cases),cases


def validate_projection(value):
    require(value['construction_status']=='native_generic_fold_admitted',
            'Unknown campaign construction status')
    require(value['execution_status']=='declared_finite_dynamics_executed',
            'Unknown campaign execution status')
    require(type(value['cross_configuration_frequency_ratio_identified']) is bool and
            value['cross_configuration_frequency_ratio_identified'] is False,
            'Campaign does not identify a cross-configuration frequency ratio')
    require(value['survival_probability'] is None and value['half_life_seconds'] is None and
            value['physical_atomic_identification'] is False, 'Physical status promotion')
    semantics={
        'window_policy':'from first internal round to one newly completed outer reclosure; configuration-specific endpoints',
        'cadence_definition':'new parent returns / new independent reference returns in (lo,hi]',
        'lag_definition':'parent-minus-reference retained-return count, zero declared phase bias',
        'phase_unit':'complete retained return',
    }
    require(all(value[key]==expected for key,expected in semantics.items()),
            'Unknown campaign observation semantics')
    window=value['reference_window']
    require(type(window) is list and len(window)==2 and all(type(x) is int for x in window)
            and window[0]<window[1], 'Invalid campaign comparison window')
    require(isinstance(value['reference_identity'],str) and bool(value['reference_identity']),
            'Missing reference identity')
    require((value['cadence_ratio'] is None)==(value['lag'] is None), 'Incomplete observation pair')
    if value['cadence_ratio'] is None:
        require(value['observation_dependency']=='Fewer than two committed cross-returns in this bounded window',
                'Undefined observation requires the declared dependency')
    else:
        require(value['observation_dependency'] is None,
                'Defined observation has an inconsistent dependency')
    for name in ('cadence_ratio','lag'):
        if value[name] is None: continue
        require(isinstance(value[name],str), 'Campaign '+name+' requires an exact rational string')
        try: number=Q(value[name])
        except (ValueError,ZeroDivisionError) as exc:
            raise ValueError('Invalid exact campaign '+name) from exc
        if name=='cadence_ratio': require(number>=0, 'Negative cadence')
    return value


def _case_projection(result):
    # Validate every consumed status before projecting. This is structural
    # validation, not a substitute for the complete native replay verifier.
    require(result['construction']['native_construction_admitted'] is True and
            result['construction']['native_atomic_identification'] is False,
            'Unknown or promoted engine construction status')
    require(result['execution']['status']=='bounded_declared_model_executed' and
            result['execution']['native_inner_and_outer_returns_admitted'] is True and
            result['execution']['native_frg_gate_executed'] is False,
            'Unknown or promoted engine execution status')
    require(result['empirical_inputs_read']==[], 'Engine consumed empirical inputs')
    require(result['inner_prefixes_extended'] is True, 'Missing evolved inner prefixes')
    physical=result['physical']
    require(all(physical[key] is None for key in ('atomic_state_identification','emitted_phase_map',
            'nuclear_loss_rule','survival_probability','half_life_seconds','frequency_hz')),
            'Unidentified physical output was promoted')
    if result['observation'] is not None:
        require(result['observation']['physical_frequency_hz'] is None,
                'Native observation promoted to physical frequency')
    return validate_projection(_engine().summary(result))


def input_paths(root=ROOT):
    root=Path(root)
    return [root/'manual2/data/m1/reference_inputs.csv',
        root/'manual2/scripts/matter1_campaign.py',root/'manual2/scripts/matter1_campaign_engine.py']+[
        root/DATA/name for name in ('identity_inputs.json','manifest.json','prediction.json','campaign_report.json')]


def _evaluation(root):
    import matter1_isotopes as isotopes
    catalog=isotopes.load_catalog(root)
    source_projection=[{k:r[k] for k in IDENTITY_FIELDS} for r in catalog['isotopes']]
    require(canonical(source_projection)==canonical(identity_inputs(root)['records']),
            'Evaluation identity/state projection differs from frozen campaign input')
    return catalog


def comparison(root,manifest,prediction,cases):
    """Called after prediction is frozen; source validation precedes target use."""
    require(canonical(prediction)==canonical(_assemble_prediction(root,manifest,cases)),
            'Comparison prediction differs from bound campaign cases')
    catalog=_evaluation(root)
    import matter1_m3_metrology_vendor as vendor
    api=vendor.metrology(root)
    hydrogen=api.load_profile('hydrogen')
    cesium=api.load_profile('cesium')
    hydrogen_reductions={name:api.reduce_hydrogen(hydrogen,name)
                         for name in ('table_iv','table_vi','published_mean')}
    cesium_reductions={name:api.reduce_cesium(cesium,name)
                      for name in ('August2013','typical_Table1')}
    rows=[]
    for record in catalog['isotopes']:
        rows.append({'record_id':record['id'],
            'configuration_id':configuration_id(record['Z'],record['A']),
            'quantity':'total_half_life', 'evaluation':deepcopy(record['half_life']),
            'empirical_status':record['empirical_status'], 'state_assignment':record['state_assignment'],
            'source_records':deepcopy(record['source_records']), 'exposure':record['exposure'],
            'updates':deepcopy(record['updates']), 'limits':deepcopy(record['limits']),
            'event_times':deepcopy(record.get('event_times',[])),
            'model_seconds':None,'residual_seconds':None,'normalized_residual':None,
            'comparison_status':'physical_loss_and_clock_maps_unestablished',
            'uncertainty':{'model':'unknown','realization':'unknown','shared_source_covariance':'unknown'},
            'overlapping_measurements_averaged':False})
    from matter1_m3_metrology import isotope_inputs
    return {'schema_version':1,'profile':PROFILE,'prediction_sha256':digest(prediction),
        'evaluation_catalog_sha256':sha(Path(root)/'manual2/data/m1/isotopes/catalog.json'),
        'rows':rows,'hydrogen_source_reductions':hydrogen_reductions,
        'cesium_realization_records':cesium_reductions,'selected_event_reductions':isotope_inputs(root),
        'hydrogen_exposure':'retrospective_known_before_model_selection',
        'hydrogen_observation':{'method':'continuous_active_maser_heterodyne',
            'beat_definition':'nu_B = nu_M - 284 nu_R - nu_S',
            'phase_definition_turns':'DeltaPhi_B = DeltaPhi_M - 284 DeltaPhi_R - DeltaPhi_S',
            'matched_native_and_historical_window':False,
            'physical_H_Cs_ratio':None,'predicted_frequency_hz':None,'predicted_period_seconds':None,
            'reason':'Generic recurrence does not identify state-resolved maser emission or apparatus preparation.'},
        'fitted_parameters':[], 'empirical_agreement':None,
        'uncertainty_status':'incomplete_no_zero_substitution_or_independence_assumption',
        'correction_policy':'Use each historical reduction once; keep Table IV, Table VI and published mean separate.'}


def _report(manifest,prediction,comp):
    projections=[validate_projection(row) for row in prediction['cases'].values()]
    construction_count=sum(row['construction_status']=='native_generic_fold_admitted' for row in projections)
    execution_count=sum(row['execution_status']=='declared_finite_dynamics_executed' for row in projections)
    observation_count=sum(row['cadence_ratio'] is not None for row in projections)
    return {'schema_version':1,'profile':PROFILE,'manifest_sha256':digest(manifest),
        'prediction_sha256':digest(prediction),'comparison_sha256':digest(comp),
        'coverage':deepcopy(manifest['coverage']),
        'configuration_results':len(prediction['cases']),
        'execution_counts':{'generic_constructed':construction_count,'baseline_executed':execution_count,
            'bounded_native_observations':observation_count,'matched_controls_in_this_artifact':0},
        'stopping_policy':deepcopy(manifest['stopping_policy']),
        'physical_prediction_objective':'unresolved_observation_and_state_identification',
        'unresolved_dependencies':list(DEPENDENCIES),
        'acceptance':[
            {'id':'FB1','scope':'Generic inventory construction and scoped native folding',
             'outcome':'executed_for_campaign_configurations','count':construction_count},
            {'id':'FB2','scope':'Declared finite internal baseline dynamics',
             'outcome':'baseline_executed_controls_require_separate_test_evidence',
             'count':execution_count,'matched_control_runs_recorded_here':0},
            {'id':'FB3','scope':'Exact conditional kernels sampled with complete histories retained',
             'outcome':'no_state_reduction_claim','ensemble_distribution_claimed':False},
            {'id':'FB4','scope':'State-resolved physical observation', 'outcome':'unresolved',
             'dependencies':list(DEPENDENCIES[:5])},
            {'id':'FB5','scope':'Realized SI mapping', 'outcome':'unresolved',
             'dependencies':[DEPENDENCIES[5]]},
            {'id':'FB6','scope':'Complete physical uncertainty and comparison', 'outcome':'unresolved',
             'dependencies':[DEPENDENCIES[6]]},
            {'id':'FB7','scope':'Reproduction', 'outcome':'requires_separate_fresh_verification',
             'assertion':'Generation is not verification; run the read-only campaign verifier.'}],
        'frozen_models_preserved':['R02','R03','legacy_survival','static_reference'],
        'independent_physical_prediction':False}


def expected_output_paths(root=ROOT):
    manifest=default_manifest(root)
    return [str(DATA/name) for name in OUTPUTS]+[
        str(DATA/'cases'/(row['id']+'.json')) for row in manifest['configurations']]


def select_shard(manifest,index,count):
    require(type(index) is int and type(count) is int and 0<=index<count<=135,
            'Shard must satisfy 0 <= index < count <= 135')
    return [row['id'] for position,row in enumerate(manifest['configurations']) if position%count==index]


def generate(root=ROOT,output_root=None,case_ids=None,finalize=False):
    root=Path(root);destination=Path(root if output_root is None else output_root)
    require(not (finalize and case_ids is not None), 'Finalize and case generation are separate modes')
    manifest=default_manifest(root)
    folder=destination/DATA;folder.mkdir(parents=True,exist_ok=True)
    (folder/'manifest.json').write_bytes(json_bytes(manifest))
    case_folder=folder/'cases';case_folder.mkdir(exist_ok=True)
    selected=[r['id'] for r in manifest['configurations']] if case_ids is None else list(case_ids)
    require(len(selected)==len(set(selected)), 'Duplicate selected configuration')
    if not finalize:
        for key in selected:
            value=execute_case(root,manifest,key)
            (case_folder/(key+'.json')).write_bytes(json_bytes(value))
    if case_ids is not None and not finalize:
        return {'status':'generated_case_shards','cases':selected,'full_campaign_verified':False}
    cases={r['id']:read_json(case_folder/(r['id']+'.json')) for r in manifest['configurations']}
    require({p.name for p in case_folder.iterdir()}=={key+'.json' for key in cases},
            'Case output inventory differs')
    prediction=_assemble_prediction(root,manifest,cases)
    # All prediction bytes are fixed before any target is opened.
    (folder/'prediction.json').write_bytes(json_bytes(prediction))
    comp=comparison(root,manifest,prediction,cases)
    report=_report(manifest,prediction,comp)
    for name,value in [('comparison.json',comp),('campaign_report.json',report)]:
        (folder/name).write_bytes(json_bytes(value))
    return {'status':'generated','cases':len(cases),'outputs':list(OUTPUTS),
            'physical_atomic_prediction':None,'physical_half_life_prediction':None,
            'full_campaign_verified':False}


def verify(root=ROOT,case_ids=None,products_only=False):
    root=Path(root);folder=root/DATA
    manifest=validate_manifest(root,read_json(folder/'manifest.json'))
    require(not (products_only and case_ids is not None), 'Products-only and selected replay are separate modes')
    selected=[r['id'] for r in manifest['configurations']] if case_ids is None else list(case_ids)
    require(len(selected)==len(set(selected)), 'Duplicate selected configuration')
    known={r['id'] for r in manifest['configurations']}
    require(set(selected)<=known, 'Unknown selected campaign configuration')
    inventory={p.name for p in (folder/'cases').iterdir()}
    require(inventory<={key+'.json' for key in known}, 'Extra campaign case file')
    cases={key:read_json(folder/'cases'/(key+'.json')) for key in selected}
    if not products_only:
        for key in selected:verify_case(root,manifest,key,cases[key])
    if case_ids is not None:
        return {'status':'PASS_SELECTED_CAMPAIGN_CASES','cases':selected,'full_campaign_verified':False}
    require(inventory=={key+'.json' for key in known}, 'Incomplete campaign case inventory')
    prediction=_assemble_prediction(root,manifest,cases)
    comp=comparison(root,manifest,prediction,cases)
    report=_report(manifest,prediction,comp)
    for name,value in [('prediction.json',prediction),('comparison.json',comp),('campaign_report.json',report)]:
        require(canonical(read_json(folder/name))==canonical(value),'Stored campaign artifact differs: '+name)
    require({p.name for p in folder.iterdir()}==set(OUTPUTS)|{'identity_inputs.json','cases'},
            'Campaign output inventory differs')
    return {'status':'PASS_CAMPAIGN_PRODUCTS_NO_EXECUTION_REPLAY' if products_only else 'PASS_CAMPAIGN_ORIGINAL_INPUT_REPLAY',
            'configuration_count':len(cases),
            'source_records':145,'elements':118,'physical_atomic_prediction':None,
            'physical_half_life_prediction':None,'full_campaign_verified':not products_only,
            'prediction_sha256':digest(prediction)}


def ui_projection(root=ROOT):
    """Fast display projection; the scientific verifier separately re-executes."""
    root=Path(root);folder=root/DATA
    manifest=validate_manifest(root,read_json(folder/'manifest.json'))
    prediction=read_json(folder/'prediction.json');report=read_json(folder/'campaign_report.json')
    for value in (prediction,report):
        require(type(value['schema_version']) is int and value['schema_version']==1 and
                value['profile']==PROFILE, 'Campaign display schema/profile differs')
    application_sha=sha(Path(__file__))
    engine_sha=sha(Path(_engine().__file__))
    require(sha(root/'manual2/scripts/matter1_campaign.py')==application_sha and
            sha(root/'manual2/scripts/matter1_campaign_engine.py')==engine_sha,
            'Campaign display source differs from executing modules')
    require(prediction['application_code_sha256']==application_sha and
            prediction['engine_code_sha256']==engine_sha,
            'Campaign display executor binding is stale')
    require(prediction['manifest_sha256']==digest(manifest) and report['manifest_sha256']==digest(manifest)
            and report['prediction_sha256']==digest(prediction), 'Campaign display binding differs')
    require(prediction['physical_atomic_prediction'] is None and prediction['physical_half_life_prediction'] is None,
            'Campaign display cannot promote a physical prediction')
    require(set(prediction['cases'])=={r['id'] for r in manifest['configurations']},
            'Campaign display coverage differs')
    records=[]
    for row in manifest['records']:
        projected=validate_projection(prediction['cases'][row['configuration_id']])
        records.append({**deepcopy(row),
            'construction_status':projected['construction_status'],
            'execution_status':projected['execution_status'],
            'cadence_ratio':projected['cadence_ratio'],'lag':projected['lag'],
            'reference_identity':projected['reference_identity'],
            'reference_window':deepcopy(projected['reference_window']),
            'window_policy':projected['window_policy'],
            'cross_configuration_frequency_ratio_identified':False,
            'observation_dependency':projected['observation_dependency'],
            'survival':None,'survival_status':'physical_loss_observable_unestablished',
            'physical_prediction_status':'unresolved', 'dependencies':list(DEPENDENCIES)})
    return {'schema':1,'profile':PROFILE,'records':records,'prediction_sha256':digest(prediction),
            'verification_scope':'Bound display projection; full scientific replay is a separate verifier.',
            'model_scope':'Generic declared recurrence model; no physical isotope half-life or atomic frequency.'}
