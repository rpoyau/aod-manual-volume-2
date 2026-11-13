"""Property source/identity checks and persisted negative fixtures."""
import copy
from decimal import Decimal
from fractions import Fraction
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
from manual2.scripts import matter1_mass_derivations as mass


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

    def test_complete_mass_pilot_matches_independent_decimal_values_and_nulls(self):
        report=self.products['mass_derivations.json']
        self.assertEqual(report['counts'],dict(records=24,numeric=15,null=9,isotopes=6))
        expected={
            ('binding_energy','H-1'):'0', ('binding_energy','H-2'):'2224.5662',
            ('binding_energy','H-3'):'8481.7962', ('binding_energy','He-3'):'7718.04132',
            ('binding_energy','He-4'):'28295.6624', ('binding_energy','Cs-133'):'1118527.1538',
            ('neutron_separation_energy','H-2'):'2224.566229',
            ('proton_separation_energy','H-2'):'2224.566229',
            ('neutron_separation_energy','H-3'):'6257.230055',
            ('proton_separation_energy','He-3'):'5493.475079',
            ('neutron_separation_energy','He-4'):'20577.62107',
            ('proton_separation_energy','He-4'):'19813.866094',
            ('neutron_separation_energy','Cs-133'):'8989.56806',
            ('proton_separation_energy','Cs-133'):'6080.939554',
            ('alpha_decay_q','Cs-133'):'-1988.68287',
        }
        for row in report['rows']:
            key=(row['property'],row['entity_id'].split(':')[1])
            if key in expected:
                self.assertEqual(Fraction(row['value']),Fraction(expected[key]))
                self.assertEqual(Fraction(row['m3_nominal']['result']),Fraction(expected[key]))
            else:
                self.assertIsNone(row['value'])
                self.assertIsNone(row['conditional_sd_range'])
                self.assertIsNone(row['catalog_uncertainty']['value'])
                self.assertTrue(row['missing_inputs'])
                self.assertEqual(len(row['requested_inputs']),3)
                self.assertTrue(any(t['source_quantity_id'] is not None for t in row['requested_inputs']))
        self.assertFalse(report['typed_m3_acceptance'])
        self.assertFalse(report['physical_budget_complete'])

    def test_exact_A_scaling_preserves_reported_magnitude_convention(self):
        report=self.products['mass_derivations.json']
        expected={'H-1':'0','H-2':'0.0004','H-3':'0.0009','He-3':'0.00045',
                  'He-4':'0.0008','Cs-133':'0.0399'}
        for row in report['rows']:
            if row['property']!='binding_energy':continue
            isotope=row['entity_id'].split(':')[1];a=int(isotope.split('-')[1])
            quantity=report['source_quantities'][row['coefficients'][0]['source_quantity_id']]
            self.assertEqual(row['magnitude_scaling']['coefficient'],a)
            self.assertEqual(Fraction(row['magnitude_scaling']['value']),Fraction(expected[isotope]))
            self.assertEqual(Fraction(row['magnitude_scaling']['value']),a*Fraction(quantity['reported_magnitude']))
            self.assertEqual(quantity['quantity'],'binding_energy_per_nucleon')
            self.assertEqual(row['magnitude_scaling']['statistical_convention'],'source_documented_rounded_marginals')
            self.assertEqual(row['catalog_uncertainty']['kind'],'scaled_source_reported_magnitude')

    def test_covariance_adoption_is_separate_from_retained_catalog_uncertainty(self):
        report=self.products['mass_derivations.json'];adoption=report['covariance_adoption']
        self.assertEqual(adoption['status'],'partial')
        self.assertEqual(adoption['coverage']['candidate_rows'],9)
        self.assertEqual(adoption['coverage']['adopted_rows']+adoption['coverage']['held_rows'],9)
        self.assertTrue(adoption['adopted']);self.assertTrue(adoption['held'])
        rows={r['id']:r for r in report['rows']}
        for result in adoption['adopted']:
            row=rows[result['record_id']]
            self.assertEqual(result['baseline_mass_excess_value_keV'],row['value'])
            self.assertIsNone(row['catalog_uncertainty']['value'])
            self.assertEqual(row['conditional_sd_range']['premise_status'],'source_documented_rounded_marginals')
            self.assertEqual(result['unit'],'nano-u')
            self.assertEqual(result['variance_unit'],'(nano-u)^2')
        self.assertFalse(adoption['typed_m3_acceptance'])
        self.assertFalse(adoption['physical_budget_complete'])

    def test_mass_dependencies_preserve_repeated_inputs_and_two_paths(self):
        report=self.products['mass_derivations.json'];rows={r['id']:r for r in report['rows']}
        neutron=rows['neutron_separation_energy:isotope:H-2:ground']
        proton=rows['proton_separation_energy:isotope:H-2:ground']
        self.assertEqual(neutron['coefficients'],proton['coefficients'])
        self.assertEqual(report['dependencies']['coefficient_rank'],7)
        for relation in report['dependencies']['zero_output_combinations']:
            self.assertEqual(sum(t['coefficient']*Fraction(rows[t['record_id']]['value']) for t in relation),0)
            combined=[dict(source_quantity_id=q['source_quantity_id'],coefficient=t['coefficient']*q['coefficient'])
                      for t in relation for q in rows[t['record_id']]['coefficients']]
            self.assertEqual(mass.coefficients(combined),[])
        binding=rows['binding_energy:isotope:H-2:ground']
        self.assertEqual(Fraction(neutron['value'])-Fraction(binding['value']),Fraction('0.000029'))

    def test_source_identity_controls_cancellation_not_equal_values(self):
        quantities={key:dict(value='7',reported_magnitude='1',unit='keV') for key in ('x','y')}
        terms=lambda other:[dict(source_quantity_id='x',coefficient=1),dict(source_quantity_id=other,coefficient=-1)]
        self.assertEqual(mass.coefficients(terms('x')),[])
        self.assertEqual(mass.conditional_sd_range(terms('x'),quantities)['upper'],'0')
        self.assertEqual(mass.conditional_sd_range(terms('y'),quantities)['upper'],'2')
        reinforced=[dict(source_quantity_id='x',coefficient=1)]*2
        bounds=mass.conditional_sd_range(reinforced,quantities)
        self.assertEqual((bounds['lower'],bounds['upper']),('2','2'))
        with self.assertRaises(ValueError):mass.coefficients([dict(source_quantity_id='x',coefficient=True)])
        with self.assertRaises(ValueError):mass.conditional_sd_range(terms('unbound'),quantities)
        unbound=[dict(source_quantity_id='unbound',coefficient=c) for c in (1,-1)]
        with self.assertRaises(ValueError):mass.conditional_sd_range(unbound,quantities)
        quantities['x']['unit']='Hz'
        with self.assertRaises(ValueError):mass.conditional_sd_range(terms('x'),quantities)

    def test_conditional_SD_ranges_are_not_adopted_point_or_hard_bounds(self):
        rows={r['id']:r for r in self.products['mass_derivations.json']['rows']}
        expected={'neutron_separation_energy:isotope:H-2:ground':('0.000412','0.000468'),
                  'proton_separation_energy:isotope:He-3:ground':('0.000032','0.000088'),
                  'neutron_separation_energy:isotope:Cs-133:ground':('1.02756','1.04444'),
                  'proton_separation_energy:isotope:Cs-133:ground':('0.002917','0.013083'),
                  'alpha_decay_q:isotope:Cs-133:ground':('3.14485','3.16115')}
        for identity,pair in expected.items():
            row=rows[identity];bounds=row['conditional_sd_range']
            self.assertEqual(tuple(Fraction(bounds[k]) for k in ('lower','upper')),tuple(map(Fraction,pair)))
            self.assertEqual(bounds['kind'],'range_of_possible_standard_deviations')
            self.assertEqual(bounds['premise_status'],'source_documented_rounded_marginals')
            self.assertFalse(bounds['joint_covariance_adopted'])
            self.assertIsNone(bounds['coverage'])
            self.assertIsNone(row['catalog_uncertainty']['value'])

    def test_missing_and_invalid_marginal_magnitudes_cannot_be_zero_filled(self):
        terms=[dict(source_quantity_id='x',coefficient=1)]
        quantities={'x':dict(reported_magnitude=None,unit='keV')}
        bounds=mass.conditional_sd_range(terms,quantities)
        self.assertEqual(bounds['status'],'missing_marginal_magnitude')
        self.assertIsNone(bounds['lower']);self.assertIsNone(bounds['upper'])
        for value in ('-1','NaN'):
            quantities['x']['reported_magnitude']=value
            with self.assertRaises(ValueError):mass.conditional_sd_range(terms,quantities)
        quantities['x']=dict(reported_magnitude='1',unit='Hz')
        with self.assertRaises(ValueError):mass.conditional_sd_range(terms,quantities)
        quantities['x']['reported_magnitude']=None
        with self.assertRaises(ValueError):mass.conditional_sd_range(terms,quantities)

    def test_mass_source_fields_preserve_identity_and_systematics(self):
        report=self.products['mass_derivations.json'];quantities=report['source_quantities']
        for identity,row in quantities.items():
            self.assertIn(report['source']['sha256'],identity)
            self.assertIn(':'+row['quantity']+':',identity)
            self.assertEqual(row['catalog_uncertainty_kind'],'source_reported_magnitude_convention_not_reconstructed')
            self.assertEqual(row['uncertainty_convention'],'one_standard_deviation')
            self.assertEqual(row['convention_evidence'],'source_convention')
            self.assertEqual(row['source_sha256'],report['source']['sha256'])
            lo,hi=row['locator']['value_columns']
            self.assertEqual(Fraction(row['raw_row'][lo-1:hi].strip().replace('#','.')),Fraction(row['value']))
            ulo,uhi=row['locator']['magnitude_columns']
            self.assertEqual(row['estimated'],'#' in row['raw_row'][lo-1:uhi])
        evidence=report['source_convention']
        source=next(s for s in report['covariance_adoption']['sources'] if s['id']==evidence['source_id'])
        self.assertEqual(evidence['source_sha256'],source['sha256'])
        self.assertEqual(evidence['status'],'source_documented_rounded_marginals')
        self.assertEqual(evidence['manifest']['sha256'],mass.covariance.INPUTS_SHA256)

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
        binding=mass.producer.verify(self.root);vendor=mass.producer.VENDOR
        paths.add(str(vendor/'binding.json'))
        paths.add(str(vendor/binding['producer_handoff']['path']))
        paths.update(str(vendor/'current'/name) for name in binding['files'])
        paths.update(mass.covariance.input_paths(self.root))
        for name in paths:
            dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(self.root/name,dest)
        return root,paths

    def test_mass_sidecar_tampering_rejected_without_repair(self):
        with tempfile.TemporaryDirectory() as td:
            root,paths=self.fixture(td);target=root/p.BASE/'mass_derivations.json';original=target.read_bytes()
            def alias(d):
                row=next(r for r in d['rows'] if r['property']=='neutron_separation_energy' and r['coefficients'])
                key=row['coefficients'][0]['source_quantity_id'];clone=copy.deepcopy(d['source_quantities'][key]);clone['id']='invented_alias'
                d['source_quantities']['invented_alias']=clone;row['coefficients'][0]['source_quantity_id']='invented_alias'
            mutations=[lambda d:d['rows'][0]['coefficients'][0].__setitem__('coefficient',2),
                       lambda d:next(r for r in d['rows'] if r['conditional_sd_range'])['conditional_sd_range'].__setitem__('upper','0'),
                       lambda d:d.__setitem__('typed_m3_acceptance',True),
                       lambda d:d['source'].__setitem__('sha256','0'*64),alias,
                       lambda d:next(iter(d['source_quantities'].values()))['locator'].__setitem__('line',1)]
            for mutate in mutations:
                data=p.read(target);mutate(data);target.write_bytes(p.canonical(data));before=self.snapshot(root,paths)
                with self.assertRaises(ValueError):p.verify(root)
                self.assertEqual(before,self.snapshot(root,paths));target.write_bytes(original)

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
