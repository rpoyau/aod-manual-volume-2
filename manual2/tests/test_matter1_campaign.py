"""Campaign identity, target separation, comparison typing and hostile replay.

These checks do not identify the generic model with physical atomic states.
The expensive all-135 replay is independently sharded in CI.
"""
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'manual2/scripts'))
import matter1_campaign as c


class CampaignInputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=c.default_manifest(ROOT)

    def test_CAMP_01_complete_coverage_without_promoting_slots(self):
        m=self.manifest
        self.assertEqual(m['coverage'],{'elements':118,'reference_slots_preserved':126,
            'reference_records':118,'isotope_state_records':27,'source_records':145,'distinct_Z_A':135})
        self.assertEqual(len(m['records']),145)
        self.assertEqual(len({r['id'] for r in m['records']}),145)
        self.assertEqual({r['z'] for r in m['records']},set(range(1,119)))
        self.assertEqual(len(m['configurations']),135)
        self.assertEqual(len(c.expected_output_paths(ROOT)),139)

    def test_CAMP_02_state_records_do_not_fabricate_dynamics(self):
        by={r['id']:r for r in self.manifest['records']}
        for symbol,a in [('Fl',289),('Lv',293)]:
            ground=by[f'{symbol}-{a}:ground'];isomer=by[f'{symbol}-{a}:m_candidate']
            self.assertNotEqual(ground['id'],isomer['id'])
            self.assertNotEqual(ground['state_assignment'],isomer['state_assignment'])
            self.assertEqual(ground['configuration_id'],isomer['configuration_id'])
            self.assertIsNone(ground['state_to_configuration_map'])
            self.assertIsNone(isomer['state_to_configuration_map'])

    def test_CAMP_03_legacy_selection_is_not_an_evaluation(self):
        legacy=[r for r in self.manifest['records'] if r['provenance_kind']=='legacy_element_reference']
        self.assertEqual(len(legacy),118)
        self.assertTrue(all(r['state_assignment']=='selection_provenance_unresolved' for r in legacy))
        self.assertTrue(all(r['selection_policy']=='legacy-reference-a-unresolved' for r in legacy))
        h=next(r for r in self.manifest['configurations'] if r['id']=='Z001-A001')
        self.assertEqual(h['n'],0)
        self.assertEqual(h['electron_count'],1)
        self.assertIsNone(h['physical_loss_rule'])

    def test_CAMP_04_manifest_is_bound_to_original_inputs(self):
        for mutation in ('extra','state','inventory','status'):
            m=deepcopy(self.manifest)
            if mutation=='extra':m['unexpected']=True
            elif mutation=='state':m['records'][0]['state_to_configuration_map']={}
            elif mutation=='inventory':m['configurations'][0]['recipe']['a']=True
            else:m['physical_predictions']='complete'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):c.validate_manifest(ROOT,m)

    def test_CAMP_05_balanced_shards_partition_all_inputs(self):
        parts=[c.select_shard(self.manifest,j,4) for j in range(4)]
        self.assertEqual([len(p) for p in parts],[34,34,34,33])
        joined=[x for part in parts for x in part]
        self.assertEqual(len(joined),len(set(joined)))
        self.assertEqual(set(joined),{r['id'] for r in self.manifest['configurations']})
        for args in [(True,4),(0,False),(-1,4),(4,4),(0,0),(0,136)]:
            with self.subTest(args=args),self.assertRaises(ValueError):c.select_shard(self.manifest,*args)

    def test_CAMP_06_duplicate_keys_and_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'value.json'
            for raw in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}'):
                path.write_text(raw)
                before=path.read_bytes()
                with self.subTest(raw=raw),self.assertRaises(ValueError):c.read_json(path)
                self.assertEqual(path.read_bytes(),before)

    def test_CAMP_07_identity_input_is_target_free(self):
        inputs=c.identity_inputs(ROOT)
        for row in inputs['records']:
            self.assertEqual(set(row),set(c.IDENTITY_FIELDS))
            self.assertFalse({'half_life','frequency_hz','event_times','decay_channels'}&set(row))
        self.assertEqual(c.sha(ROOT/c.DATA/'identity_inputs.json'),c.IDENTITY_SHA256)


class CampaignReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=c.default_manifest(ROOT)
        cls.key='Z001-A001'
        cls.case=c.execute_case(ROOT,cls.manifest,cls.key)

    def test_CAMP_08_real_hydrogen_inventory_executes_without_targets(self):
        original_open=Path.open
        forbidden=('isotopes/curation.json','isotopes/catalog.json','atomic/evaluation_target.json',
                   'm3_metrology/current/hydrogen/','m3_metrology/current/cesium/')
        def guarded(path,*args,**kwargs):
            if any(part in str(path) for part in forbidden):
                raise AssertionError('Prediction opened evaluation input: '+str(path))
            return original_open(path,*args,**kwargs)
        with patch.object(Path,'open',guarded):
            replay=c.execute_case(ROOT,c.default_manifest(ROOT),self.key)
        self.assertEqual(c.canonical(replay),c.canonical(self.case))
        self.assertEqual(replay['result']['empirical_inputs_read'],[])

    def test_CAMP_09_exact_projection_preserves_scope(self):
        row=c._case_projection(self.case['result'])
        self.assertEqual(row['construction_status'],'native_generic_fold_admitted')
        self.assertEqual(row['execution_status'],'declared_finite_dynamics_executed')
        self.assertFalse(row['cross_configuration_frequency_ratio_identified'])
        self.assertIsNone(row['half_life_seconds'])
        if row['cadence_ratio'] is not None:self.assertGreaterEqual(Q(row['cadence_ratio']),0)

    def test_CAMP_10_status_and_numeric_projection_mutations_fail(self):
        good=c._case_projection(self.case['result'])
        for key,value in [('construction_status','physical_atom_admitted'),
                          ('execution_status','empirical_agreement'),
                          ('cadence_ratio',True),('cadence_ratio',0.5),('lag','nan'),
                          ('half_life_seconds','1'),('cross_configuration_frequency_ratio_identified',True),
                          ('reference_window',[False,100]),('reference_identity','')]:
            bad=deepcopy(good);bad[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):c.validate_projection(bad)

    def test_CAMP_20_consumed_engine_statuses_cannot_be_hidden_by_projection(self):
        mutations=[('construction','native_atomic_identification',True),
                   ('construction','native_construction_admitted',False),
                   ('execution','native_frg_gate_executed',True),
                   ('execution','status','complete_physical_prediction'),
                   ('physical','half_life_seconds','1')]
        for section,key,value in mutations:
            bad=deepcopy(self.case['result']);bad[section][key]=value
            with self.subTest(section=section,key=key),self.assertRaises(ValueError):c._case_projection(bad)

    def test_CAMP_11_original_case_and_alias_binding(self):
        for key,value in [('configuration_id','Z055-A133'),('manifest_sha256','0'*64),
                          ('engine_code_sha256','0'*64)]:
            bad=deepcopy(self.case);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_case_envelope(self.manifest,self.key,bad)

    def test_CAMP_12_resealed_trajectory_mutation_rejected(self):
        bad=deepcopy(self.case)
        bad['result']['trajectory']['outer_return']['committed']+=1
        bad['result']['trajectory_sha256']=c.digest(bad['result']['trajectory'])
        with self.assertRaises(ValueError):c.verify_case(ROOT,self.manifest,self.key,bad)

    def test_CAMP_13_persisted_hostile_artifact_rejected_without_repair(self):
        bad=deepcopy(self.case)
        bad['result']['physical']['half_life_seconds']='1'
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'case.json';path.write_bytes(c.json_bytes(bad));before=path.read_bytes()
            code="import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import matter1_campaign as c;r=Path(sys.argv[2]);c.verify_case(r,c.default_manifest(r),'Z001-A001',c.read_json(sys.argv[3]))"
            args=[sys.executable,'-B']+(['-O'] if not __debug__ else [])+['-c',code,str(ROOT/'manual2/scripts'),str(ROOT),str(path)]
            result=subprocess.run(args,capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn(b'differs from complete original-input replay',result.stderr)
            self.assertEqual(path.read_bytes(),before)


class CampaignProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=c.default_manifest(ROOT)
        cls.folder=ROOT/c.DATA
        cls.prediction=c.read_json(cls.folder/'prediction.json')
        cls.report=c.read_json(cls.folder/'campaign_report.json')
        cls.comparison=c.read_json(cls.folder/'comparison.json')

    def test_CAMP_14_every_result_and_input_record_is_present(self):
        self.assertEqual(set(self.prediction['cases']),{r['id'] for r in self.manifest['configurations']})
        for row in self.prediction['cases'].values():c.validate_projection(row)
        self.assertEqual(len(c.ui_projection(ROOT)['records']),145)

    def test_CAMP_23_fast_case_binding_rejects_cross_configuration_alias(self):
        h=c.read_json(self.folder/'cases/Z001-A001.json')
        cs=c.read_json(self.folder/'cases/Z055-A133.json')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'case.json'
            bad=deepcopy(cs);bad['result']=deepcopy(h['result'])
            path.write_bytes(c.json_bytes(bad));before=path.read_bytes()
            with self.assertRaisesRegex(ValueError,'different operative configuration'):
                c.validate_case_envelope(self.manifest,'Z055-A133',c.read_json(path))
            self.assertEqual(path.read_bytes(),before)
            bad['result']['original_config']=deepcopy(cs['result']['original_config'])
            bad['result']['configuration_sha256']=cs['result']['configuration_sha256']
            with self.assertRaisesRegex(ValueError,'inventory differs'):
                c.validate_case_envelope(self.manifest,'Z055-A133',bad)
            for key in ('z','a','electron_count'):
                bad['result']['construction'][key]=cs['result']['construction'][key]
            with self.assertRaisesRegex(ValueError,'constituent identities differ'):
                c.validate_case_envelope(self.manifest,'Z055-A133',bad)

    def test_CAMP_15_native_windows_do_not_become_atomic_frequency(self):
        for row in self.prediction['native_comparisons']:
            self.assertIsNone(row['atomic_frequency_ratio'])
            a,b=row['left_window'],row['right_window']
            self.assertEqual(Q(row['finite_protocol_elapsed_cut_ratio']),Q(a[1]-a[0],b[1]-b[0]))
            self.assertEqual(row['matched_window'],a==b)
            self.assertEqual(row['left_reference_id'][0],row['left_configuration'])
            self.assertEqual(row['right_reference_id'][0],row['right_configuration'])
            self.assertFalse(row['same_reference_identity'])
            self.assertTrue(row['same_reference_recipe'])
        self.assertIsNone(self.prediction['physical_atomic_prediction'])
        self.assertIsNone(self.prediction['physical_half_life_prediction'])

    def test_CAMP_16_hydrogen_reductions_and_uncertainties_remain_separate(self):
        h=self.comparison['hydrogen_source_reductions']
        self.assertEqual(Q(h['table_iv']['corrected_frequency_hz']),Q('1420405751.7691'))
        self.assertEqual(h['table_iv']['source_reported_uncertainty']['reported_value_or_bound'],'0.0024')
        self.assertEqual(h['published_mean']['source_reported_uncertainty']['reported_value_or_bound'],'0.002')
        self.assertEqual(self.comparison['hydrogen_exposure'],'retrospective_known_before_model_selection')
        self.assertIsNone(self.comparison['hydrogen_observation']['predicted_frequency_hz'])
        self.assertFalse(self.comparison['hydrogen_observation']['matched_native_and_historical_window'])

    def test_CAMP_17_catalog_quantities_and_unknown_uncertainty_preserved(self):
        self.assertEqual(len(self.comparison['rows']),27)
        for row in self.comparison['rows']:
            self.assertEqual(row['quantity'],'total_half_life')
            self.assertIsNone(row['model_seconds']);self.assertIsNone(row['normalized_residual'])
            self.assertEqual(row['uncertainty']['shared_source_covariance'],'unknown')
            self.assertFalse(row['overlapping_measurements_averaged'])
        rejected=next(r for r in self.comparison['rows'] if r['record_id']=='Og-295:ground')
        self.assertEqual(rejected['evaluation']['kind'],'unknown')
        self.assertEqual(rejected['empirical_status'],'unobserved_rejected_candidate')

    def test_CAMP_18_acceptance_scope_is_not_physical_completion(self):
        rows={r['id']:r for r in self.report['acceptance']}
        self.assertEqual(set(rows),{'FB'+str(i) for i in range(1,8)})
        self.assertEqual(rows['FB2']['matched_control_runs_recorded_here'],0)
        self.assertFalse(rows['FB3']['ensemble_distribution_claimed'])
        for key in ('FB4','FB5','FB6'):self.assertEqual(rows[key]['outcome'],'unresolved')
        self.assertFalse(self.report['independent_physical_prediction'])

    def test_CAMP_21_display_rejects_actual_changed_executor_sources(self):
        for filename in ('matter1_campaign.py','matter1_campaign_engine.py'):
            with self.subTest(filename=filename),tempfile.TemporaryDirectory() as folder:
                root=Path(folder)/'repo'
                for source in c.input_paths(ROOT):
                    destination=root/source.relative_to(ROOT)
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(source,destination)
                self.assertEqual(len(c.ui_projection(root)['records']),145)
                path=root/'manual2/scripts'/filename
                path.write_bytes(path.read_bytes()+b'\n# persisted hostile source mutation\n')
                before=path.read_bytes()
                with self.assertRaisesRegex(ValueError,'source differs'):c.ui_projection(root)
                self.assertEqual(path.read_bytes(),before)

    def test_CAMP_22_display_rejects_resealed_metadata_promotions(self):
        changes=[('prediction','application_code_sha256','0'*64),
                 ('prediction','engine_code_sha256','0'*64),
                 ('prediction','schema_version',True),('prediction','profile','unknown'),
                 ('report','manifest_sha256','0'*64),('report','schema_version',True),
                 ('report','profile','unknown')]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'repo'
            for source in c.input_paths(ROOT):
                destination=root/source.relative_to(ROOT)
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,destination)
            for owner,key,value in changes:
                prediction=deepcopy(self.prediction);report=deepcopy(self.report)
                (prediction if owner=='prediction' else report)[key]=value
                report['prediction_sha256']=c.digest(prediction)
                (root/c.DATA/'prediction.json').write_bytes(c.json_bytes(prediction))
                (root/c.DATA/'campaign_report.json').write_bytes(c.json_bytes(report))
                with self.subTest(owner=owner,key=key),self.assertRaises(ValueError):c.ui_projection(root)

    def test_CAMP_19_products_check_does_not_claim_execution_replay(self):
        result=c.verify(ROOT,products_only=True)
        self.assertEqual(result['status'],'PASS_CAMPAIGN_PRODUCTS_NO_EXECUTION_REPLAY')
        self.assertFalse(result['full_campaign_verified'])


if __name__=='__main__':unittest.main()
