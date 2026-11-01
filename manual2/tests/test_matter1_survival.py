"""SURV-01..19: finite survival, target separation and persisted hostile probes.

These assertions establish a declared finite law and its restricted comparison.
They do not establish native nuclear admission, a physical clock or precision.
"""
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT/'manual2/scripts'
sys.path.insert(0, str(SCRIPTS))
import matter1_survival as s


def snapshot(root):
    return {str(p.relative_to(root)):(hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class SurvivalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prediction = s.predict(ROOT)
        cls.runs = cls.prediction['runs']

    def fixture(self, folder):
        root = Path(folder)/'repo'
        shutil.copytree(ROOT/'sections', root/'sections')
        shutil.copytree(ROOT/'manual2/vendor', root/'manual2/vendor')
        (root/'manual2/sections').mkdir(parents=True,exist_ok=True)
        for path in (ROOT/'manual2/sections').glob('generated_isotope_*.tex'):
            shutil.copyfile(path,root/'manual2/sections'/path.name)
        for sub in ('survival','isotopes'):
            shutil.copytree(ROOT/'manual2/data/m1'/sub, root/'manual2/data/m1'/sub)
        for name in ('reference_inputs.csv',):
            shutil.copyfile(ROOT/'manual2/data/m1'/name, root/'manual2/data/m1'/name)
        return root

    def cli(self, root, command='verify', optimized=False, extra=()):
        return subprocess.run([sys.executable,'-B']+(['-O'] if optimized else [])+
                              [str(SCRIPTS/f'{command}_matter1_survival.py'),'--root',str(root),*map(str,extra)],
                              capture_output=True)

    def test_SURV_01_exact_formal_support_accounting(self):
        for row in self.prediction['isotope_candidates']:
            g = row['grouping']
            self.assertEqual(g['A'], 4*g['q']+g['r_p']+g['r_n'])
            self.assertEqual(g['Z'], 2*g['q']+g['r_p'])
            self.assertEqual(g['N'], 2*g['q']+g['r_n'])
        cs = s.grouping(55,133)
        self.assertEqual((cs['q'],cs['r_p'],cs['r_n']), (27,1,24))
        for values in ((True,1),(1,False),(2,1),(0,1)):
            with self.assertRaises(ValueError): s.grouping(*values)

    def test_SURV_02_Q4_injective_paths_and_retained_start_witnesses(self):
        s.validate_geometry(s.GEOMETRY)
        bad = deepcopy(s.GEOMETRY)
        bad['vertices']['E'] = bad['vertices']['D']
        with self.assertRaises(ValueError): s.validate_geometry(bad)
        for run in self.runs.values():
            self.assertEqual(len(run['initial_returns']),4)
            for w in run['initial_returns']+run['reference_returns']:
                self.assertEqual(w['start'],w['end'])
                self.assertGreaterEqual(w['phase_bearing_traversals'],2)
                self.assertEqual(len(set(w['event_ids'])),4)
                self.assertEqual(w['certificate_kind'],'finite_predicate_witness_not_native_motif_admission')

    def test_SURV_03_exact_kernel_and_zero_weight_is_not_absence(self):
        for run in self.runs.values():
            for node in run['nodes']:
                k = node['kernel']
                self.assertEqual(sum(Q(r['probability']) for r in k),1)
                self.assertTrue(all(Q(r['probability'])>=0 for r in k))
                self.assertEqual(k[-1]['admissible'],False)
                self.assertEqual(k[-1]['probability'],'0')
                if node['excess']=='0':
                    self.assertTrue(k[2]['admissible'])
                    self.assertEqual(k[2]['weight'],'0')

    def test_SURV_04_conservation_competing_channels_and_survival(self):
        for run in self.runs.values():
            previous = Q(1)
            for row in run['rows']:
                retained, alpha, sf = map(Q,(row['survival'],row['loss_alpha'],row['loss_sf']))
                self.assertEqual(retained+alpha+sf,1)
                self.assertLessEqual(retained,previous)
                self.assertEqual(alpha,sf)
                previous = retained
            terminal = sum(Q(h['probability_mass']) for h in run['absorbed_histories'])
            terminal += sum(Q(h['probability_mass']) for h in run['right_censored_histories'])
            self.assertEqual(terminal,1)
            for h in run['absorbed_histories']:
                self.assertTrue(h['absorbing'])
                self.assertEqual(h['physical_channel_identification'],'not_established')

    def test_SURV_05_first_crossing_is_ensemble_median_not_one_event(self):
        expected = ['1','1','1','5/6','3/4','3/5','19/36','703/1680','211/576']
        self.assertEqual([r['survival'] for r in self.runs['baseline']['rows']],expected)
        self.assertEqual(self.runs['baseline']['median']['interval_reference_returns'],[6,7])
        self.assertEqual(self.runs['loss_gain_2']['median']['interval_reference_returns'],[4,5])
        self.assertEqual(self.runs['capacity_0']['median']['interval_reference_returns'],[2,3])
        self.assertEqual(self.runs['feedback_off']['median']['lower_bound_reference_returns'],8)
        self.assertEqual(self.runs['feedback_off']['median']['kind'],'right_censored')
        losses = self.runs['baseline']['absorbed_histories']
        self.assertLess(min(x['reference_count'] for x in losses),7)
        self.assertGreater(max(x['reference_count'] for x in losses),7)

    def test_SURV_06_returned_response_changes_strictly_later_survival(self):
        b,off = self.runs['baseline'],self.runs['feedback_off']
        self.assertEqual(b['rows'][:3],off['rows'][:3])
        self.assertEqual(b['rows'][3]['survival'],'5/6')
        self.assertEqual(off['rows'][3]['survival'],'1')
        self.assertEqual(b['nodes'][0],off['nodes'][0])
        for node in b['nodes']:
            for child in node['retained_children']:
                self.assertEqual(sum(map(Q,child['response_pair'])),0)
                self.assertEqual(Q(child['memory_next']),Q(node['memory_before'])+Q(child['response_pair'][0]))
                self.assertTrue(child['response_committed_after_contact'])

    def test_SURV_07_histories_are_not_merged_or_erased(self):
        for run in self.runs.values():
            self.assertEqual(run['history_merge_count'],0)
            self.assertEqual(run['node_count'],255)
            self.assertEqual(len({n['prefix'] for n in run['nodes']}),255)
            for h in run['absorbed_histories']:
                self.assertEqual(h['inner_lineage_sha256'],s.digest(run['retained_inner']))
                seed_ids = list(run['retained_inner']['scope_map']['return_map'].values())
                expected = seed_ids+[f"candidate:prefix:{h['prefix'][:i]}" for i in range(1,len(h['prefix'])+1)]
                self.assertEqual(h['committed_candidate_return_ids'],expected)
            mapping = run['retained_inner']['scope_map']
            self.assertNotEqual(mapping['source'],mapping['target'])
            self.assertEqual(len(mapping['event_map']),8)
            self.assertEqual(len(set(mapping['event_map'].values())),8)
            self.assertEqual(set(mapping['return_map']),set(run['retained_inner']['witness_ids']))
            # Equal numerical memory does not identify distinct event histories.
            terminal = run['right_censored_histories']
            self.assertLess(len({h['memory'] for h in terminal}),len(terminal))

    def test_SURV_08_full_finite_joint_law_not_linear_guard(self):
        for run in self.runs.values():
            m = run['finite_law']
            p = Q(run['rows'][-1]['survival'])
            self.assertEqual(Q(m['output_mean']),p)
            self.assertEqual(Q(m['output_variance']),p*(1-p))
            self.assertEqual(m['uncertainty_status'],'exact_for_declared_joint_law')
            self.assertIsNone(run['physical_half_life_seconds'])
        m = s.mapping(ROOT)
        with self.assertRaises(ValueError):
            m.propagate(['input','x'],['x'],{},support=[('1',{'x':'0'}),('1',{'x':'1'})])
        with self.assertRaises(ValueError):
            m.propagate(['input','x'],['x'],{},support=[('1/2',{'x':'0'}),('1/2',{'x':'1'})],covariance=[['0']])

    def test_SURV_09_missing_atomic_and_clock_maps_have_countermodels(self):
        p = self.prediction
        self.assertEqual(p['fitted_parameters'],[])
        self.assertEqual(p['conditional_test']['half_life_ratio'],'1')
        self.assertTrue(all(r['physical_half_life_seconds'] is None for r in p['isotope_candidates']))
        self.assertEqual(len({r['finite_run_sha256'] for r in p['isotope_candidates']}),1)
        a,b = p['clock_countermodels']
        self.assertEqual(a['Cs_definition_hz'],b['Cs_definition_hz'])
        self.assertEqual(list(map(Q,b['conditional_median_seconds_interval'])),[2*Q(x) for x in a['conditional_median_seconds_interval']])
        self.assertTrue(all(x['status']=='unresolved' for x in p['dependencies']))

    def test_SURV_10_prediction_succeeds_without_measured_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            shutil.rmtree(root/'manual2/data/m1/isotopes')
            (root/s.DATA/'comparison.json').unlink()
            expected = s.canonical(self.prediction)
            before = snapshot(root)
            for optimized in (False,True):
                run = self.cli(root,'predict',optimized)
                self.assertEqual(run.returncode,0,run.stderr.decode())
                self.assertEqual(run.stdout,expected)
                self.assertEqual(snapshot(root),before)

    def test_SURV_11_prediction_never_reads_target_or_benchmark(self):
        original = Path.read_bytes
        def audited(path):
            if any(x in str(path) for x in ('/isotopes/','comparison.json','benchmark.json','evaluation_target.json')):
                raise AssertionError('Predictor consumed external target')
            return original(path)
        with patch.object(Path,'read_bytes',audited):
            self.assertEqual(s.canonical(s.predict(ROOT)),s.canonical(self.prediction))

    def test_SURV_12_retrospective_conditional_equality_is_falsified(self):
        c = s.compare(ROOT,self.prediction)
        self.assertEqual(len(c['comparisons']),3)
        for row in c['comparisons']:
            self.assertFalse(row['equality_in_reported_envelope'])
            self.assertLess(Q(row['source_reported_uncertainty_envelope_ratio'][1]),1)
            self.assertEqual(row['classification'],'retrospective_conditional_model_comparison')
        self.assertEqual(c['native_atomic_agreement'],'not_tested_atomic_map_unestablished')
        self.assertEqual(c['unscored'],[{'id':'Fl-298:ground','reason':'unobserved_model_target_no_measurement'}])

    def test_SURV_13_conventional_exponential_is_separate_calibration(self):
        for row in s.compare(ROOT,self.prediction)['conventional_benchmark']:
            self.assertFalse(row['native_AOD_prediction'])
            self.assertEqual([x['survival'] for x in row['samples']],['1','1/2','1/4','1/16'])
            self.assertEqual(row['samples'][1]['time_seconds'],row['calibrating_half_life_seconds'])
            self.assertIn('calibrated',row['classification'])

    def test_SURV_14_mutating_catalog_cannot_change_prediction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            path = root/s.CATALOG
            catalog = s.read_json(path)
            next(x for x in catalog['isotopes'] if x['id']=='Og-294:ground')['half_life']['value_seconds']='100'
            path.write_bytes(s.canonical(catalog))
            self.assertEqual(s.canonical(s.predict(root)),s.canonical(self.prediction))
            before = snapshot(root)
            for optimized in (False,True):
                self.assertNotEqual(self.cli(root,'compare',optimized).returncode,0)
                self.assertEqual(snapshot(root),before)

    def test_SURV_15_persisted_hostile_mutations_reject_without_repair(self):
        mutations = [
            ('model_contract.json',lambda x:x['geometry']['vertices'].__setitem__('E',x['geometry']['vertices']['D'])),
            ('model_contract.json',lambda x:x['statuses'].__setitem__('native_motif_admission','admitted')),
            ('model_contract.json',lambda x:x['statuses'].pop('physical_uncertainty')),
            ('model_contract.json',lambda x:x['variants']['baseline'].__setitem__('loss_gain','2')),
            ('model_contract.json',lambda x:x['variants']['baseline'].__setitem__('capacity','0')),
            ('model_contract.json',lambda x:x['cases'][0].__setitem__('Z',True)),
            ('model_contract.json',lambda x:x.__setitem__('measured_half_life_seconds','0.00058')),
            ('model_contract.json',lambda x:x['source_bindings'][0].__setitem__('sha256','0'*64)),
            ('prediction.json',lambda x:x['runs']['baseline']['nodes'][0]['kernel'][0].__setitem__('probability','1')),
            ('prediction.json',lambda x:x['runs']['baseline']['nodes'][0]['kernel'][2].__setitem__('admissible',False)),
            ('prediction.json',lambda x:x['runs']['baseline']['nodes'][0]['retained_children'][0].__setitem__('response_pair',['1','1'])),
            ('prediction.json',lambda x:x['runs']['baseline']['nodes'][0]['retained_children'][0]['return_witness'].__setitem__('end','1111')),
            ('prediction.json',lambda x:x['runs']['baseline']['absorbed_histories'][0].__setitem__('absorbing',False)),
            ('prediction.json',lambda x:x['runs']['baseline']['absorbed_histories'][0].__setitem__('committed_candidate_return_ids',[])),
            ('prediction.json',lambda x:x['runs']['baseline']['rows'][3].__setitem__('survival','1')),
            ('prediction.json',lambda x:x['runs']['baseline']['finite_law'].__setitem__('output_variance','0')),
            ('prediction.json',lambda x:x['runs']['baseline']['median'].__setitem__('crossing',3)),
            ('prediction.json',lambda x:x['isotope_candidates'][0].__setitem__('physical_half_life_seconds','1')),
            ('prediction.json',lambda x:x['uncertainty'].__setitem__('measurement_covariance','independent')),
            ('prediction.json',lambda x:x['clock_countermodels'][0].__setitem__('selection','calibrated_physical_result')),
            ('comparison.json',lambda x:x['comparisons'][0].__setitem__('equality_in_reported_envelope',True)),
            ('comparison.json',lambda x:x.__setitem__('native_atomic_agreement','verified')),
            ('comparison.json',lambda x:x.__setitem__('catalog_sha256','0'*64)),
            ('survival_report.json',lambda x:x.__setitem__('physical_prediction_executed',True)),
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            for name, mutate in mutations:
                path = root/s.DATA/name
                original = path.read_bytes()
                value = s.read_json(path)
                mutate(value)
                path.write_bytes(s.canonical(value))
                before = snapshot(root)
                for optimized in (False,True):
                    with self.subTest(file=name, mutation=mutations.index((name,mutate)), optimized=optimized):
                        run = self.cli(root,'verify',optimized,('--check-data',))
                        self.assertNotEqual(run.returncode,0,run.stdout.decode()[:300])
                        self.assertEqual(snapshot(root),before)
                path.write_bytes(original)

    def test_SURV_16_unknown_flags_and_unsupported_status_reject(self):
        for optimized in (False,True):
            self.assertNotEqual(self.cli(ROOT,'verify',optimized,('--repair',)).returncode,0)
        contract = s.read_json(ROOT/s.DATA/'model_contract.json')
        contract['statuses']['execution']='not_executed'
        with self.assertRaises(ValueError): s.simulate(ROOT,contract)

    def test_SURV_17_replay_rejects_self_consistent_claim_hashes(self):
        p = deepcopy(self.prediction)
        p['runs']['baseline']['median']['crossing']=1
        p['isotope_candidates'][0]['finite_run_sha256']=s.digest(p['runs']['baseline'])
        with self.assertRaises(ValueError): s.validate_prediction(ROOT,p)

    def test_SURV_18_verifier_is_read_only_in_both_modes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            before = snapshot(root)
            outputs=[]
            for optimized in (False,True):
                run = self.cli(root,'verify',optimized,('--check-data',))
                self.assertEqual(run.returncode,0,run.stderr.decode())
                self.assertEqual(snapshot(root),before)
                outputs.append(run.stdout)
            self.assertEqual(outputs[0],outputs[1])

    def test_SURV_19_fresh_catalog_consumed_only_after_source_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'fresh-catalog.json'
            path.write_bytes((ROOT/s.CATALOG).read_bytes())
            actual = s.compare(ROOT,self.prediction,catalog_path=path)
            self.assertEqual(actual,s.compare(ROOT,self.prediction))
            mutated=s.read_json(path)
            mutated['isotopes'][0]['empirical_status']='verified'
            path.write_bytes(s.canonical(mutated))
            for optimized in (False,True):
                result=self.cli(ROOT,'compare',optimized,('--isotope-catalog',path))
                self.assertNotEqual(result.returncode,0)


if __name__ == '__main__':
    unittest.main()
