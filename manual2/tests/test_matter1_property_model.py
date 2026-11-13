"""Executable pilot obligations, target separation and whole-law scope guards."""
from copy import deepcopy
from fractions import Fraction as Q
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'manual2/scripts'))
import matter1_property_model as m


class PropertyModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_open=Path.open
        cls.opened=[]
        def guard(path,*args,**kwargs):
            name=str(path)
            cls.opened.append(name)
            forbidden=('properties/catalog.json','properties/states.json','external_transitions/',
                       'isotopes/catalog.json','isotopes/curation.json','atomic/evaluation_target.json',
                       'atomic/benchmark_inputs.json')
            if any(x in name for x in forbidden):
                raise AssertionError('Prediction opened evaluation/state target: '+name)
            return original_open(path,*args,**kwargs)
        with patch.object(Path,'open',guard):
            cls.products=m.prediction_products(ROOT)
        cls.prediction=cls.products['prediction.json'];cls.protocol=cls.products['protocol.json']
        cls.catalog={'schema':'synthetic-test-targets','properties':[
            {'id':'hyperfine:H-1','entity_id':'atomic-isotope:H-1:q0:ground','property':'hyperfine_frequency',
             'value':'1000','unit':'Hz','value_kind':'numeric','uncertainty':{'value':None,'kind':'unknown'},
             'method':'synthetic','exposure':'synthetic_test_only','source_id':'synthetic','locator':'test',
             'qualification':'not a physical measurement','physical_prediction':False,'selection_status':'adopted','transition':'ground_state_hyperfine_separation',
             'conditions':{'electronic_state':'ground','magnetic_field':'unperturbed_zero_field','experimental_window':None,'magnetic_sublevels':None}},
            {'id':'hyperfine:Cs-133','entity_id':'atomic-isotope:Cs-133:q0:ground','property':'hyperfine_frequency',
             'value':str(m.CS_HZ),'unit':'Hz','value_kind':'numeric','uncertainty':{'value':'0','kind':'definition'},
             'method':'synthetic','exposure':'synthetic_test_only','source_id':'synthetic','locator':'test',
             'qualification':'test defining-reference check','physical_prediction':False,'selection_status':'adopted','transition':'ground_state_hyperfine_separation',
             'conditions':{'electronic_state':'ground','magnetic_field':'unperturbed_zero_field','experimental_window':None,'magnetic_sublevels':None}}]}

    def test_prediction_executes_without_targets_or_catalog_state_labels(self):
        self.assertTrue(self.opened)
        self.assertEqual(self.prediction['target_access'],'not_read')
        self.assertEqual(self.prediction['fitted_parameters'],[])
        self.assertEqual(set(self.products),set(m.PREDICTION_OUTPUTS))

    def test_all_six_original_configs_execute_with_actual_bound_witnesses(self):
        self.assertEqual([r['pilot'] for r in self.prediction['rows']],[p[0] for p in m.PILOTS])
        for row in self.prediction['rows']:
            raw=self.products['raw/'+row['pilot']+'.json']
            self.assertEqual(raw['original_config'],self.protocol['native_configs'][row['pilot']])
            self.assertEqual(row['raw_sha256'],m.digest(raw))
            self.assertEqual(row['trajectory_sha256'],m.native.digest(raw['trajectory']))
            self.assertTrue(raw['execution']['native_inner_and_outer_returns_admitted'])
            self.assertFalse(raw['execution']['native_frg_gate_executed'])
            self.assertTrue(raw['inner_prefixes_extended'])
            self.assertEqual(len(raw['trajectory']['inner_returns']),3*(row['config']['a']+row['config']['z']))
            self.assertTrue(all(r['certificate_sha256'] for r in raw['trajectory']['inner_returns']))

    def test_state_distinction_obstruction_is_explicit_and_not_atomic_admission(self):
        states=self.products['state_map.json'];pair=states['state_separation_obstruction']
        self.assertNotEqual(*pair['requests'])
        self.assertEqual(*pair['operative_configurations'])
        for row in states['rows']:
            self.assertEqual(row['physical_state_correspondence'],'unestablished')
            self.assertIn('nuclear spin',row['unrepresented_physical_distinctions'])

    def test_two_global_maps_preserve_reference_but_separate_unidentified_properties(self):
        rows=self.prediction['countermodels']
        for name,z,a in m.PILOTS:
            a,b=[r for r in rows if r['pilot']==name]
            self.assertEqual(a['trajectory_sha256'],b['trajectory_sha256'])
            self.assertNotEqual(a['arbitrary_energy_witness_J'],b['arbitrary_energy_witness_J'])
            self.assertNotEqual(a['arbitrary_mass_witness_kg'],b['arbitrary_mass_witness_kg'])
            if name=='Cs-133':
                self.assertEqual(Q(a['diagnostic_frequency_hz']),m.CS_HZ)
                self.assertEqual(Q(b['diagnostic_frequency_hz']),m.CS_HZ)
            else:self.assertNotEqual(a['diagnostic_frequency_hz'],b['diagnostic_frequency_hz'])
        for witness in self.protocol['global_map_family']['witnesses']:
            self.assertTrue(all(r['common_parameter_vector']==witness for r in rows if r['witness']==witness['id']))

    def test_dimension_check_does_not_identify_photon_or_rest_mass_law(self):
        d=self.prediction['dimensions']
        for name in ('frequency','energy','mass'):
            self.assertEqual([x+y for x,y in zip(d['native_ratio'],d[name+'_scale'])],d[name+'_output'])
        self.assertFalse(d['external_physical_relations_executed'])
        self.assertIsNone(self.prediction['selected_physical_law'])
        self.assertTrue(all(all(v is None for v in r['physical_properties'].values()) for r in self.prediction['rows']))

    def test_equal_cadence_does_not_erase_distinct_retained_histories(self):
        collisions=self.prediction['cadence_projection_collisions']
        pair=next(r for r in collisions if r['left']=='atomic-isotope:H-3:q0:ground' and
                  r['right']=='atomic-isotope:He-4:q0:ground')
        self.assertEqual(pair['common_bounded_cadence'],'1/35')
        self.assertNotEqual(pair['left_trajectory_sha256'],pair['right_trajectory_sha256'])

    def test_matched_fixed_path_control_changes_later_execution(self):
        c=self.products['controls.json']
        self.assertTrue(c['same_first_round']);self.assertTrue(c['same_orientation_path'])
        self.assertNotEqual(c['baseline_outer_cut'],c['feedback_off_outer_cut'])
        self.assertFalse(c['physical_causal_effect_established'])
        a=self.products['controls/fixed_path.json'];b=self.products['controls/feedback_off.json']
        first=lambda r:[x for x in r['trajectory']['inner_returns'] if x['round']==0]
        self.assertEqual(first(a),first(b))
        self.assertEqual([d['orientation'] for d in a['trajectory']['decisions']],
                         [d['orientation'] for d in b['trajectory']['decisions']])

    def test_passive_projection_preserves_actual_trajectory(self):
        a=self.products['raw/H-1.json'];b=self.products['controls/passive.json']
        self.assertEqual(a['trajectory'],b['trajectory'])
        self.assertEqual(a['execution']['rng_state_sha256'],b['execution']['rng_state_sha256'])
        self.assertIsNone(b['observation'])

    def test_common_protocol_rejects_per_property_retuning(self):
        bad=deepcopy(self.protocol)
        bad['global_map_family']['per_property_or_isotope_retuning']={'H-1':{'frequency':'best-fit'}}
        with self.assertRaisesRegex(ValueError,'Frozen property model protocol differs'):
            m.validate_protocol(ROOT,bad)
        bad=deepcopy(self.prediction)
        bad['countermodels'][0]['diagnostic_frequency_hz']='1000'
        with self.assertRaisesRegex(ValueError,'retuned'):
            m._compare_catalog_values(ROOT,bad,self.protocol,self.catalog)

    def test_physical_promotions_and_omitted_obligations_are_rejected(self):
        for change in ('claim','target','state','mass','omission'):
            bad=deepcopy(self.prediction)
            if change=='claim':bad['physical_prediction_complete']=True
            elif change=='target':bad['target_access']='read'
            elif change=='state':bad['rows'][0]['entity_id']='atomic-isotope:Cs-133:q0:ground'
            elif change=='mass':bad['rows'][0]['physical_properties']['atomic_mass']='1'
            else:bad['rows'][0]['physical_properties'].pop('spin_parity')
            with self.subTest(change=change),self.assertRaises(ValueError):
                m._compare_catalog_values(ROOT,bad,self.protocol,self.catalog)

    def test_target_mutation_changes_only_comparison_and_not_frozen_outputs(self):
        before=m.canonical(self.products)
        a=m._compare_catalog_values(ROOT,self.prediction,self.protocol,self.catalog)
        target=deepcopy(self.catalog);target['properties'][0]['value']='2000'
        b=m._compare_catalog_values(ROOT,self.prediction,self.protocol,target)
        self.assertNotEqual(a['rows'][0]['diagnostics'],b['rows'][0]['diagnostics'])
        self.assertEqual(a['prediction_sha256'],b['prediction_sha256'])
        self.assertEqual(before,m.canonical(self.products))
        self.assertEqual(a['rows'][-1]['comparison_status'],'calibrant_reproduction_not_prediction')

    def test_state_unit_and_numeric_target_scope(self):
        for change in ('unit','duplicate','zero'):
            bad=deepcopy(self.catalog)
            if change=='unit':bad['properties'][0]['unit']='MHz'
            elif change=='duplicate':bad['properties'].append(deepcopy(bad['properties'][0]))
            else:bad['properties'][0]['value']='0'
            with self.subTest(change=change),self.assertRaises(ValueError):
                m._compare_catalog_values(ROOT,self.prediction,self.protocol,bad)
        absent=m._compare_catalog_values(ROOT,self.prediction,self.protocol,{'properties':[]})
        self.assertTrue(all(r['comparison_status']=='no_numeric_target_for_requested_external_state' for r in absent['rows']))

    def test_unrelated_source_records_survive_but_adopted_ambiguity_fails(self):
        alternative=deepcopy(self.catalog['properties'][0])
        alternative.update(id='hyperfine:H-1:alternative',selection_status='alternative',value='999')
        catalog=deepcopy(self.catalog);catalog['properties'].append(alternative)
        result=m._compare_catalog_values(ROOT,self.prediction,self.protocol,catalog)
        self.assertEqual(result['rows'][0]['target']['id'],'hyperfine:H-1')
        catalog['properties'][-1]['selection_status']='adopted'
        with self.assertRaisesRegex(ValueError,'Ambiguous adopted'):
            m._compare_catalog_values(ROOT,self.prediction,self.protocol,catalog)

    def test_source_state_exposure_and_field_regime_cannot_be_dropped(self):
        for field in ('source_id','locator','exposure','conditions','selection_status','transition'):
            bad=deepcopy(self.catalog);bad['properties'][0].pop(field)
            with self.subTest(field=field),self.assertRaises(ValueError):
                m._compare_catalog_values(ROOT,self.prediction,self.protocol,bad)
        bad=deepcopy(self.catalog);bad['properties'][0]['conditions']['magnetic_field']='finite_field'
        with self.assertRaises(ValueError):m._compare_catalog_values(ROOT,self.prediction,self.protocol,bad)
        result=m._compare_catalog_values(ROOT,self.prediction,self.protocol,self.catalog)
        self.assertEqual(result['rows'][0]['matching']['native_to_external_state'],'unestablished')
        self.assertEqual(result['rows'][0]['matching']['native_to_experimental_window'],'unestablished')

    def test_public_comparison_validates_adopted_source_catalog(self):
        catalog=m.read_json(ROOT/'manual2/data/m1/properties/catalog.json')
        result=m.compare_catalog(ROOT,self.prediction,self.protocol,catalog)
        self.assertEqual(result['evaluation_catalog_sha256'],m.digest(catalog))
        bad=deepcopy(catalog)
        selected=next(r for r in bad['properties'] if r['id']=='hyperfine:H-1')
        selected['value']=str(Q(selected['value'])+1)
        with self.assertRaises(ValueError):m.compare_catalog(ROOT,self.prediction,self.protocol,bad)

    def test_entire_common_gain_family_is_tested_without_member_selection(self):
        catalog=deepcopy(self.catalog)
        base=catalog['properties'][0];base['value']='77000';base['uncertainty']['value']='1'
        for isotope,value in [('H-2','10500'),('H-3','6600')]:
            row=deepcopy(base);row.update(id='hyperfine:'+isotope,
                entity_id=f'atomic-isotope:{isotope}:q0:ground',value=value)
            catalog['properties'].append(row)
        positive=m._compare_catalog_values(ROOT,self.prediction,self.protocol,catalog)
        self.assertEqual(positive['joint_family_diagnostic']['disposition'],'compatible_on_checked_ratios')
        catalog['properties'][2]['value']='5000'
        negative=m._compare_catalog_values(ROOT,self.prediction,self.protocol,catalog)
        family=negative['joint_family_diagnostic']
        self.assertEqual(family['disposition'],'incompatible_with_retained_source_envelopes')
        self.assertEqual([r['entire_common_gain_family_ratio'] for r in family['checks']],['3/22','3/35'])
        self.assertFalse(family['parameter_fit_performed'])
        self.assertFalse(family['physical_AOD_theory_refuted'])
        self.assertEqual(negative['whole_law_disposition'],'incomplete_missing_premises')

    def test_multiobservable_gate_cannot_pass_from_reexpressed_frequency(self):
        r=m._compare_catalog_values(ROOT,self.prediction,self.protocol,self.catalog)
        self.assertEqual(r['whole_law_disposition'],'incomplete_missing_premises')
        self.assertEqual(r['independent_property_tests_completed'],0)
        self.assertIsNone(r['physical_model_empirical_score'])
        self.assertFalse(r['derived_frequency_period_energy_tests_count_as_independent'])
        self.assertEqual({r['property'] for r in r['multiobservable_matrix']},set(self.protocol['requested_observables']))
        self.assertTrue(all(row['law_status']=='missing_premise' for row in r['multiobservable_matrix']))

    def test_persisted_resealed_trajectory_is_rejected_without_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            bad=deepcopy(self.products)
            raw=bad['raw/H-1.json']
            raw['trajectory']['inner_returns'][0]['committed']+=1
            raw['trajectory_sha256']=m.native.digest(raw['trajectory'])
            bad['prediction.json']['rows'][0]['raw_sha256']=m.digest(raw)
            bad['prediction.json']['rows'][0]['trajectory_sha256']=raw['trajectory_sha256']
            bad['obligations.json']['prediction_sha256']=m.digest(bad['prediction.json'])
            for name,value in bad.items():
                p=root/m.DATA/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(m.canonical(value))
            files={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError,'verifier does not repair'):
                m.verify_predictions(ROOT,prediction_root=root)
            self.assertEqual(files,{str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_duplicate_and_nonfinite_json_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.json'
            for raw in ('{"a":1,"a":2}','{"a":NaN}'):
                path.write_text(raw)
                with self.assertRaises(ValueError):m.read_json(path)


if __name__=='__main__':unittest.main()
