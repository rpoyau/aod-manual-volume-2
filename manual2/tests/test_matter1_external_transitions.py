"""Acquired targets stay outside native inputs and retain source limits."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'manual2/scripts'))
import verify_matter1_external_transitions as v

def snapshot(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}

class ExternalTransitionTests(unittest.TestCase):
    def fixture(self,folder):
        root=Path(folder)
        shutil.copytree(ROOT/v.DATA,root/v.DATA)
        legacy=Path('manual2/data/m1/hyperfine/target_inventory.json')
        (root/legacy).parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/legacy,root/legacy)
        return root

    def cli(self,root,optimized=False,extra=()):
        return subprocess.run([sys.executable,'-B']+(['-O'] if optimized else [])+
            [str(ROOT/'manual2/scripts/verify_matter1_external_transitions.py'),'--root',str(root),*extra],
            capture_output=True,text=True)

    def test_source_inventory_is_read_only_in_both_modes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);before=snapshot(root)
            for opt in (False,True):
                result=self.cli(root,opt);self.assertEqual(result.returncode,0,result.stderr)
                receipt=json.loads(result.stdout)
                self.assertEqual(receipt['reported_frequency_records'],2)
                self.assertEqual(receipt['O0_scores_executed'],0)
                self.assertFalse(receipt['native_calculation_inputs_supplied'])
                self.assertEqual(snapshot(root),before)

    def test_persisted_class_and_status_promotions_reject_without_repair(self):
        changes=[lambda d:d['records'][0].__setitem__('data_support_class','D0'),
                 lambda d:d['records'][0].__setitem__('data_support_class','O0'),
                 lambda d:d['records'][0].__setitem__('native_calculation_input',True),
                 lambda d:d['records'][0].__setitem__('scientific_claim_class','native_exact_fixture'),
                 lambda d:d['records'][0].__setitem__('physical_comparison_status','agrees'),
                 lambda d:d['records'][0].pop('uncertainty_coverage'),
                 lambda d:d['records'][1].__setitem__('value_hz','1516701470.775'),
                 lambda d:d['source_rows'][2].__setitem__('acquisition_status','full_pdf_downloaded')]
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);p=root/v.DATA/'catalog.json';original=p.read_bytes()
            for mutate in changes:
                data=json.loads(original);mutate(data);p.write_text(json.dumps(data))
                before=snapshot(root)
                for opt in (False,True):
                    self.assertNotEqual(self.cli(root,opt).returncode,0)
                    self.assertEqual(snapshot(root),before)
                p.write_bytes(original)
            self.assertEqual(self.cli(root).returncode,0)

    def test_numeric_types_and_unknown_dependence_are_not_promoted(self):
        base=json.loads((ROOT/v.DATA/'catalog.json').read_text())
        for field,value in [('value_hz',327384352.5222),('uncertainty_hz',True),
                            ('joint_covariance','independent'),('uncertainty_coverage','one_sigma'),
                            ('magnetic_sublevels',[0,0])]:
            changed=deepcopy(base);changed['records'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):v.validate_metadata(changed)
        changed=deepcopy(base);changed['records'][0]['calibration_anchor'].pop('zero_uncertainty_scope')
        with self.assertRaises((KeyError,ValueError)):v.validate_metadata(changed)

    def test_actual_source_bytes_and_original_hydrogen_binding_are_checked(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder)
            for rel in [v.DATA/'wineland1972-publisher.html',Path('manual2/data/m1/hyperfine/target_inventory.json')]:
                p=root/rel;old=p.read_bytes()
                if p.suffix=='.json':
                    d=json.loads(old);d['sources'][0]['pdf_sha256']='0'*64;p.write_text(json.dumps(d))
                else:p.write_bytes(old+b'\nchanged source\n')
                before=snapshot(root)
                for opt in (False,True):self.assertNotEqual(self.cli(root,opt).returncode,0)
                self.assertEqual(snapshot(root),before);p.write_bytes(old)

    def test_evaluator_standard_uncertainty_keeps_its_source_and_limits(self):
        base=json.loads((ROOT/v.DATA/'catalog.json').read_text())
        t=base['records'][2]
        self.assertEqual(t['standard_uncertainty_hz'],'0.007')
        self.assertEqual(t['uncertainty_convention']['kind'],'one_standard_deviation_in_evaluation')
        self.assertEqual(t['uncertainty_convention']['source_id'],'kramida2010-hdt')
        self.assertEqual(t['uncertainty_convention']['locators'],v.UNCERTAINTY_LOCATORS)
        self.assertIsNone(t['uncertainty_distribution'])
        self.assertIsNone(t['uncertainty_coverage'])
        self.assertIsNone(t['joint_covariance'])
        self.assertIsNone(base['records'][1]['value_hz'])
        self.assertNotIn('standard_uncertainty_hz',base['records'][0])
        for field,value in [('standard_uncertainty_hz','0'),('uncertainty_distribution','Gaussian'),
                            ('uncertainty_coverage','0.6827'),('joint_covariance',{'independent':True})]:
            changed=deepcopy(base);changed['records'][2][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):v.validate_metadata(changed)
        for field,value in [('caveat',''),('source_id','mathur1967'),('locators',[])]:
            changed=deepcopy(base);changed['records'][2]['uncertainty_convention'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):v.validate_metadata(changed)

    def test_persisted_uncertainty_promotion_and_lost_caveat_reject_read_only(self):
        changes=[lambda d:d['records'][2].__setitem__('uncertainty_distribution','Gaussian'),
                 lambda d:d['records'][2].__setitem__('uncertainty_coverage','0.6827'),
                 lambda d:d['records'][2]['uncertainty_convention'].__setitem__('caveat',''),
                 lambda d:d['records'][0].__setitem__('standard_uncertainty_hz','0.0017')]
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);p=root/v.DATA/'catalog.json';original=p.read_bytes()
            for mutate in changes:
                data=json.loads(original);mutate(data);p.write_text(json.dumps(data))
                before=snapshot(root)
                for opt in (False,True):
                    self.assertNotEqual(self.cli(root,opt).returncode,0)
                    self.assertEqual(snapshot(root),before)
                p.write_bytes(original)
            self.assertEqual(self.cli(root).returncode,0)

    def test_current_native_run_cannot_open_the_acquired_targets(self):
        import matter1_campaign_engine as engine
        config=engine.default_config(1,1);expected=engine.run_case(config,ROOT)
        original=Path.open
        def guarded(path,*args,**kwargs):
            if 'external_transitions' in path.parts:
                raise AssertionError('Native calculation attempted to read an external target')
            return original(path,*args,**kwargs)
        with mock.patch.object(Path,'open',guarded):
            self.assertEqual(engine.run_case(config,ROOT),expected)

    def test_unknown_cli_flag_does_not_generate_or_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);before=snapshot(root)
            for opt in (False,True):self.assertNotEqual(self.cli(root,opt,('--repair',)).returncode,0)
            self.assertEqual(snapshot(root),before)

if __name__=='__main__':unittest.main()
