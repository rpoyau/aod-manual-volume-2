"""Property source/identity checks and persisted negative fixtures."""
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
from manual2.scripts import matter1_properties as p
from manual2.scripts import matter1_property_adoption as a


class PropertyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(__file__).resolve().parents[2]
        cls.products=p.build(cls.root)
        cls.inputs=p.read(cls.root/p.INPUTS)

    def validate(self,mutate):
        data=copy.deepcopy(self.products)
        mutate(data)
        with self.assertRaises((ValueError,KeyError,TypeError)):
            p.validate_catalog(data['catalog.json'],data['states.json'],data['definitions.json'])

    def test_all_elements_are_identities_not_filled_reference_slots(self):
        entities=self.products['states.json']['entities']
        self.assertEqual({e['z'] for e in entities if e['kind']=='element'},set(range(1,119)))
        self.assertEqual(len([e for e in entities if e['kind']=='atom']),236)
        self.assertTrue(all(e['a'] is None for e in entities if e['kind'] in ('atom','element')))
        self.assertEqual(sum(e['pilot'] for e in entities if e['kind']=='isotope'),6)

    def test_independent_ame_known_mass_and_deuteron_binding(self):
        rows={r['id']:r for r in self.products['catalog.json']['properties']}
        self.assertEqual(rows['atomic_mass:isotope:H-1:ground']['value'],'1.007825031898')
        self.assertEqual(rows['atomic_mass:isotope:H-2:ground']['value'],'2.014101777844')
        self.assertEqual(Decimal(rows['binding_energy:isotope:H-2:ground']['value']),Decimal('2224.5662'))
        self.assertEqual(Decimal(rows['neutron_separation_energy:isotope:H-2:ground']['value']),Decimal('2224.566229'))
        self.assertIsNone(rows['neutron_separation_energy:isotope:H-2:ground']['uncertainty']['value'])

    def test_estimated_mass_not_promoted_to_measured(self):
        rows=self.products['catalog.json']['properties']
        estimated=[r for r in rows if r['property']=='atomic_mass' and r['method']=='estimated']
        self.assertGreater(len(estimated),0)
        self.assertTrue(all(r['physical_prediction'] is False for r in rows))

    def test_isomer_not_substituted_by_ground_mass(self):
        ids={e['id'] for e in self.products['states.json']['entities'] if e['nuclear_state'] not in (None,'ground')}
        rows=[r for r in self.products['catalog.json']['properties'] if r['entity_id'] in ids and r['property']=='atomic_mass']
        self.assertGreater(len(rows),0)
        self.assertTrue(all(r['value'] is None for r in rows))

    def test_source_acquisition_gap_is_material(self):
        c=self.products['coverage.json']
        self.assertFalse(c['acquisition_complete'])
        self.assertIn('atomic_ground_states_ionization',c['missing_source_families'])
        self.assertEqual(c['summary']['per_property']['ionization_energy']['numeric'],0)

    def test_hyperfine_selection_is_explicit_and_retrospective(self):
        rows=[r for r in self.products['catalog.json']['properties'] if r['property']=='hyperfine_frequency' and r['value_kind']=='numeric']
        self.assertEqual({r['id'] for r in rows},{'hyperfine:H-1','hyperfine:H-2','hyperfine:H-3','hyperfine:Cs-133'})
        self.assertTrue(all(r['selection_status']=='adopted' and r['exposure']=='retrospective' for r in rows))

    def test_boolean_z_and_wrong_symbol_rejected(self):
        self.validate(lambda d:d['states.json']['entities'][0].__setitem__('z',True))
        self.validate(lambda d:next(e for e in d['states.json']['entities'] if e['id']=='atomic-isotope:H-1:q0:ground').__setitem__('z',55))

    def test_unknown_cannot_have_numeric_uncertainty(self):
        self.validate(lambda d:next(r for r in d['catalog.json']['properties'] if r['value_kind']=='unknown')['uncertainty'].__setitem__('value','0'))

    def test_negative_mass_and_float_value_rejected(self):
        for value in ('-1',1.007825):
            self.validate(lambda d:next(r for r in d['catalog.json']['properties'] if r['property']=='atomic_mass' and r['value_kind']=='numeric').__setitem__('value',value))

    def test_unknown_uncertainty_and_unbound_source_rejected(self):
        self.validate(lambda d:d['catalog.json']['properties'][0]['uncertainty'].__setitem__('kind','fabricated_exact'))
        self.validate(lambda d:next(r for r in d['catalog.json']['properties'] if r['value_kind']=='numeric').__setitem__('source_id','not_a_source'))

    def test_hyperfine_conditions_and_units_rejected(self):
        for mutate in (lambda r:r.__setitem__('unit','s'),lambda r:r['conditions'].pop('magnetic_sublevels'),lambda r:r.__setitem__('exposure','held_out')):
            self.validate(lambda d:mutate(next(r for r in d['catalog.json']['properties'] if r['id']=='hyperfine:H-1')))

    def test_multiple_levels_are_distinct_but_duplicates_reject(self):
        d=copy.deepcopy(self.products);rows=d['catalog.json']['properties']
        for label in ('L1','L2'):
            rows.append(p.record('synthetic:'+label,'atom:Z001:q0:ground','excitation_energy','100','numeric','ame2020','synthetic parser identity test only','evaluated',level_id=label,reference_level_id='ground'))
        p.validate_catalog(d['catalog.json'],d['states.json'],d['definitions.json'])
        rows[-1]['level_id']='L1'
        with self.assertRaises(ValueError):p.validate_catalog(d['catalog.json'],d['states.json'],d['definitions.json'])

    def test_interval_is_not_a_standard_deviation(self):
        d=copy.deepcopy(self.products);row=d['catalog.json']['properties'][0]
        row.update(value_kind='interval',value=None,interval={'lower':'1.00784','upper':'1.00811'},source_id='ame2020',locator='synthetic validation fixture only',method='evaluated',uncertainty=p.uncertainty(kind='interval_not_standard_uncertainty'))
        p.validate_catalog(d['catalog.json'],d['states.json'],d['definitions.json'])
        row['interval']['upper']='1'
        with self.assertRaises(ValueError):p.validate_catalog(d['catalog.json'],d['states.json'],d['definitions.json'])
        row['interval']={'lower':'-1','upper':'2'}
        with self.assertRaises(ValueError):p.validate_catalog(d['catalog.json'],d['states.json'],d['definitions.json'])

    def fixture(self,folder):
        root=Path(folder);paths={str(p.INPUTS),*(str(p.BASE/n) for n in p.OUTPUTS)}
        for source in self.inputs['sources']:
            paths.add(source['path'])
            if source.get('pdf_path'):paths.add(source['pdf_path'])
        for name in paths:
            dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(self.root/name,dest)
        return root,paths

    def snapshot(self,root,paths):
        return {n:(hashlib.sha256((root/n).read_bytes()).hexdigest(),(root/n).stat().st_mtime_ns) for n in paths}

    def test_persisted_hostile_catalog_and_resealed_input_rejected_without_repair(self):
        with tempfile.TemporaryDirectory() as td:
            root,paths=self.fixture(td)
            cases=[p.BASE/'catalog.json',p.INPUTS]
            for name in cases:
                original=(root/name).read_bytes();d=json.loads(original)
                if name==p.INPUTS:d['sources'][0]['sha256']='0'*64
                else:d['properties'][0]['physical_prediction']=True
                (root/name).write_bytes(p.canonical(d));before=self.snapshot(root,paths)
                for opt in ([],['-O']):
                    r=subprocess.run([sys.executable,'-B',*opt,str(self.root/'manual2/scripts/verify_matter1_properties.py'),'--root',str(root)],capture_output=True,text=True)
                    self.assertNotEqual(r.returncode,0,r.stdout+r.stderr)
                    self.assertEqual(before,self.snapshot(root,paths))
                (root/name).write_bytes(original)

    def test_missing_raw_source_and_duplicate_json_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root,paths=self.fixture(td);source=root/self.inputs['sources'][0]['path'];source.write_text('damaged source')
            with self.assertRaises(ValueError):p.build(root)
            bad=root/'duplicate.json';bad.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):p.read(bad)

    def test_explicit_generation_reproduces_both_modes(self):
        for opt in ([],['-O']):
            with tempfile.TemporaryDirectory() as td:
                r=subprocess.run([sys.executable,'-B',*opt,str(self.root/'manual2/scripts/generate_matter1_properties.py'),'--output-root',td],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                for name in p.OUTPUTS:self.assertEqual((Path(td)/p.BASE/name).read_bytes(),(self.root/p.BASE/name).read_bytes())

    def test_asd_adapter_preserves_theoretical_and_uncertainty_scope(self):
        text='Z,Q,Config,Term,IE,U\n1,0,1s,2S1/2,(13.6),0.1\n2,1,1s,2S1/2,[54.4],0.2\n'
        columns=dict(z='Z',charge='Q',configuration='Config',term='Term',energy='IE',uncertainty='U')
        rows=a.asd_ionization(text,columns,'synthetic-source')
        energies=[r for r in rows if r['property']=='ionization_energy']
        self.assertEqual([r['method'] for r in energies],['theoretical','semiempirical'])
        self.assertTrue(all(r['uncertainty']['distribution'] is None for r in rows))
        with self.assertRaises(ValueError):a.asd_ionization(text+text.splitlines()[1]+'\n',columns,'synthetic-source')

    def test_curated_adapter_requires_retained_passage(self):
        with self.assertRaises(ValueError):a.curated_records('no match',{'records':[{'source_match':'not here','record':{}}]},'x')

    def test_future_response_adoptions_require_actual_conditions(self):
        for prop,entity in [('isotope_shift','atomic-isotope:H-2:q0:ground'),('zeeman_coefficient','atom:Z001:q0:ground'),('stark_coefficient','atom:Z001:q0:ground'),('polarizability','atom:Z001:q0:ground')]:
            def mutate(d):
                d['catalog.json']['properties'].append(p.record('incomplete:'+prop,entity,prop,'1','numeric','ame2020','synthetic schema challenge','evaluated',transition='T1',condition_id='C1',conditions={'label':'insufficient'}))
            self.validate(mutate)


if __name__=='__main__':unittest.main()
