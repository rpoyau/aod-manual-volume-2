"""Actual persisted isotope mutations; checks are invariant under python -O."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import matter1_isotopes as iso


def snapshot(root):
    return {str(p.relative_to(root)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class Matter1IsotopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=iso.load_catalog(ROOT)
        cls.by={r['id']:r for r in cls.catalog['isotopes']}

    def fixture(self):
        temp=tempfile.TemporaryDirectory(prefix='matter1-isotope-test-');self.addCleanup(temp.cleanup)
        root=Path(temp.name)/'manual2';root.mkdir()
        shutil.copytree(ROOT/iso.BASE,root/iso.BASE)
        for relative in iso.expected_artifacts(ROOT):
            target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,target)
        (root/'scripts').mkdir()
        for f in ('matter1_isotopes.py','verify_matter1_isotopes.py','generate_matter1_isotopes.py'):
            shutil.copy2(ROOT/'scripts'/f,root/'scripts'/f)
        return root

    def run_verify(self,root,optimized=False,flags=()):
        return subprocess.run([sys.executable,'-B']+(['-O'] if optimized else [])+
                              [str(root/'scripts/verify_matter1_isotopes.py'),'--root',str(root),*flags],capture_output=True,text=True)

    def test_exact_grouping_all_records(self):
        for r in self.catalog['isotopes']:
            s=r['support_coordinates'];self.assertEqual(4*s['q']+s['r_p']+s['r_n'],r['A'])
            self.assertEqual((2*s['q']+s['r_p'],2*s['q']+s['r_n']),(r['Z'],r['N']))
        self.assertEqual({k:self.by['Cs-133:ground']['support_coordinates'][k] for k in ['q','r_p','r_n']},{'q':27,'r_p':1,'r_n':24})

    def test_reference_defaults_preserved(self):
        self.assertEqual({k:self.catalog['default_isotopes'][k] for k in ['Og','Lv','Fl']},
                         {'Og':'Og-294:ground','Lv':'Lv-293:ground','Fl':'Fl-289:ground'})

    def test_ensdf_adopted_values_and_newer_updates_are_separate(self):
        r=self.by['Fl-286:ground'];self.assertEqual(Decimal(r['half_life']['value_seconds']),Decimal('.166'))
        self.assertEqual(Decimal(r['updates'][0]['half_life']['value_seconds']),Decimal('.106'))
        self.assertIn('not independent',r['updates'][0]['overlap'])
        self.assertEqual(Decimal(self.by['Og-294:ground']['half_life']['value_seconds']),Decimal('.00058'))

    def test_new_2025_livermorium_data_are_unevaluated_experimental(self):
        for id,value in [('Lv-288:ground','.0020'),('Lv-289:ground','.0024')]:
            r=self.by[id];self.assertEqual(r['empirical_status'],'reported_observed')
            self.assertEqual(r['selection_source'],'xundl2025')
            self.assertEqual(Decimal(r['half_life']['value_seconds']),Decimal(value))
        self.assertEqual(self.by['Lv-289:ground']['half_life']['uncertainty_plus_seconds'],'0.0044')

    def test_tentative_isomers_and_rejected_candidates_not_promoted(self):
        self.assertEqual(self.by['Fl-290:ground']['empirical_status'],'tentative_assignment')
        self.assertEqual(self.by['Lv-294:ground']['half_life']['kind'],'unknown')
        self.assertEqual(self.by['Og-295:ground']['empirical_status'],'unobserved_rejected_candidate')
        self.assertIsNone(self.by['Og-295:ground']['half_life']['value_seconds'])
        self.assertEqual(self.by['Fl-289:m_candidate']['empirical_status'],'tentative_isomer')
        self.assertNotEqual(self.by['Fl-289:m_candidate']['id'],self.by['Fl-289:ground']['id'])

    def test_target_has_no_fabricated_half_life(self):
        r=self.by['Fl-298:ground'];self.assertEqual(r['N'],184)
        self.assertEqual(r['empirical_status'],'unobserved_model_target');self.assertIsNone(r['half_life']['value_seconds'])

    def test_pb_channel_limit_is_not_total_or_infinity(self):
        r=self.by['Pb-208:ground'];self.assertEqual(r['half_life']['kind'],'observationally_stable')
        self.assertIsNone(r['half_life']['value_seconds']);limit=r['limits'][0]
        self.assertEqual(limit['measurement']['quantity'],'channel_partial_half_life')
        self.assertEqual(limit['confidence'],'90% confidence level')
        self.assertEqual(Decimal(limit['measurement']['value_seconds']),Decimal('2.6e21')*31557600)

    def test_single_event_time_is_not_half_life(self):
        r=self.by['Lv-290:ground'];e=r['event_times'][0]
        self.assertEqual(e['quantity'],'event_waiting_time')
        self.assertNotEqual(Decimal(e['value_seconds']),Decimal(r['half_life']['value_seconds']))

    def test_alpha_edges_conserve_nucleons_and_fission_has_no_fake_daughter(self):
        for edge in self.catalog['decay_edges']:
            p=self.by[edge['parent']];d=edge['daughter']
            if edge['mode']=='alpha':self.assertEqual((p['Z']-d['Z'],p['A']-d['A']),(2,4))
            if edge['mode']=='spontaneous_fission':self.assertIsNone(d)

    def test_nickel_binding_control_exceeds_iron(self):
        fe=self.by['Fe-56:ground']['binding_energy_per_nucleon'];ni=self.by['Ni-62:ground']['binding_energy_per_nucleon']
        self.assertGreater(Decimal(ni['value_keV'])-Decimal(ni['uncertainty_keV']),Decimal(fe['value_keV'])+Decimal(fe['uncertainty_keV']))

    def test_partial_channel_uncertainty_is_not_promoted_to_total(self):
        r=self.by['Fl-286:ground'];u=r['updates'][0];partials=u['channel_partial_half_lives']
        self.assertEqual(len(partials),3)
        for p in partials:
            self.assertEqual(p['measurement']['quantity'],'channel_partial_half_life')
            self.assertEqual(p['uncertainty_status'],'incomplete_branching_uncertainty')
        self.assertEqual(Decimal(partials[0]['measurement']['value_seconds']),Decimal('.191'))
        self.assertEqual(Decimal(u['half_life']['value_seconds']),Decimal('.106'))

    def test_generation_to_separate_output_does_not_consume_delivered_catalog(self):
        root=self.fixture();(root/iso.BASE/'catalog.json').write_text('deliberately stale output')
        before=snapshot(root)
        temp=tempfile.TemporaryDirectory(prefix='isotope-output-');self.addCleanup(temp.cleanup)
        output=Path(temp.name)
        result=subprocess.run([sys.executable,'-B',str(root/'scripts/generate_matter1_isotopes.py'),
                               '--root',str(root),'--output-root',str(output)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(snapshot(root),before)
        for p,b in iso.expected_artifacts(ROOT).items():self.assertEqual((output/p).read_bytes(),b)

    def test_catalog_known_values_are_retrospective(self):
        for r in self.catalog['isotopes']:
            if r['half_life']['kind']=='measured':self.assertEqual(r['exposure'],'retrospective_source_seen_before_model_freeze')

    def test_fresh_generation_matches_persisted_outputs(self):
        for path,data in iso.expected_artifacts(ROOT).items():self.assertEqual((ROOT/path).read_bytes(),data)

    def test_valid_verification_never_writes_normal_and_optimized(self):
        root=self.fixture();before=snapshot(root)
        for optimized in (False,True):
            result=self.run_verify(root,optimized,('--check-data',));self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(snapshot(root),before)

    def test_semantic_quantity_aliases_and_bad_status_rejected(self):
        for field,value in [('quantity','mean_lifetime'),('kind','stable_forever'),('value_seconds','Infinity')]:
            h=copy.deepcopy(self.by['Og-294:ground']['half_life']);h[field]=value
            with self.assertRaises(iso.ValidationError):iso.validate_life(h)
        data=iso.load_inputs(ROOT);data['isotopes'][0]['native_admission']='admitted'
        with self.assertRaises(iso.ValidationError):iso.validate_records(data)

    def test_hostile_persisted_mutations_are_rejected_without_repair(self):
        cases={
            'half_life':lambda c:c['isotopes'][0]['half_life'].update(kind='measured',value_seconds='1'),
            'status':lambda c:c['isotopes'][0].update(native_admission='admitted'),
            'support':lambda c:c['isotopes'][0]['support_coordinates'].update(q=99),
            'isotope_state':lambda c:c['isotopes'][0].update(state='m'),
            'decimal_bool':lambda c:c['isotopes'][0].update(A=True),
            'daughter':lambda c:next(e for e in c['decay_edges'] if e['mode']=='alpha')['daughter'].update(A=1),
            'selection':lambda c:c['default_isotopes'].update(Og='Og-295:ground'),
            'source_identity':lambda c:c['sources'][0].update(sha256='0'*64),
            'target_measurement':lambda c:next(r for r in c['isotopes'] if r['id']=='Fl-298:ground')['half_life'].update(kind='measured',value_seconds='100'),
            'interval':lambda c:next(r for r in c['isotopes'] if r['id']=='Og-294:ground')['half_life'].update(uncertainty_minus_seconds='99'),
        }
        for name,mutation in cases.items():
            with self.subTest(name=name):
                root=self.fixture();p=root/iso.BASE/'catalog.json';data=json.loads(p.read_bytes());mutation(data);p.write_bytes(iso.json_bytes(data));before=snapshot(root)
                for optimized in (False,True):
                    result=self.run_verify(root,optimized,('--check-data',));self.assertNotEqual(result.returncode,0,name);self.assertEqual(snapshot(root),before)

    def test_source_bytes_curated_inputs_and_tables_are_bound(self):
        paths=['sources/ensdf-Og-294.pdf','sources/xundl2025.txt','curation.json']
        for name in paths:
            with self.subTest(path=name):
                root=self.fixture();p=root/iso.BASE/name;p.write_bytes(p.read_bytes()+b'\ncorrupted');before=snapshot(root)
                for optimized in (False,True):self.assertNotEqual(self.run_verify(root,optimized).returncode,0);self.assertEqual(snapshot(root),before)
        root=self.fixture();p=root/'sections/generated_isotope_chains.tex';p.write_bytes(b'forged chain');before=snapshot(root)
        self.assertNotEqual(self.run_verify(root,True).returncode,0);self.assertEqual(snapshot(root),before)

    def test_unknown_flags_rejected_read_only(self):
        root=self.fixture();before=snapshot(root)
        self.assertNotEqual(self.run_verify(root,True,('--fix',)).returncode,0);self.assertEqual(snapshot(root),before)

    def test_direct_semantic_decay_mutation_fails(self):
        r=self.by['Og-294:ground'];ch=copy.deepcopy(r['decay_channels'][0]);ch['daughter']['A']=291
        with self.assertRaises(iso.ValidationError):iso.validate_channel(ch,r,{s['id'] for s in self.catalog['sources']})
        r=copy.deepcopy(self.by['H-1:ground']);r['A']=True;data=iso.load_inputs(ROOT);data['isotopes'][0]=r
        with self.assertRaises(iso.ValidationError):iso.validate_records(data)

if __name__=='__main__':unittest.main()
