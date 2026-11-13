"""Independent AME matrix and adoption boundary checks."""
import copy
from fractions import Fraction
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

from manual2.scripts import matter1_mass_covariance as c
from manual2.scripts import matter1_properties as p
from manual2.scripts import matter1_m3_producer as producer


class MassCovarianceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[2]
        cls.baseline = p.build(cls.root)['mass_derivations.json']
        cls.result = c.build(cls.root, cls.baseline, producer.load(cls.root).mapping)

    @staticmethod
    def tiny(rows):
        return ('\n'.join([c.HEADER, '       nuclides coded as AAAZZZi i=isomeric state',
                           '      e.g. 1H=10010', '', 'nuclide 1 nuclide 2 Covariance', *rows]) + '\n').encode()

    def test_complete_selected_archive_block_includes_cesium_daughters(self):
        self.assertEqual(self.result['source_matrix']['order'],
                         [10000,10010,20010,30010,30020,40020,1290530,1320540,1320550,1330550])
        self.assertEqual(self.result['source_matrix']['exact_psd_rank'],10)
        self.assertEqual(len(self.result['source_matrix']['entries']),55)
        self.assertEqual(self.result['source_matrix']['unit'],'(nano-u)^2')
        self.assertFalse(self.result['typed_m3_acceptance'])
        self.assertFalse(self.result['physical_budget_complete'])
        method=self.result['method']
        self.assertEqual(method['sigma_convention']['kind'],'one_standard_deviation')
        self.assertEqual(method['sigma_convention']['status'],'source_confirmed')
        self.assertEqual(method['energy_conversion']['status'],'not_applied')
        self.assertEqual(method['energy_conversion']['value'],'931494.10242')
        self.assertEqual(method['energy_conversion']['standard_uncertainty'],'0.00028')
        self.assertEqual({x['id'] for x in self.result['sources']},
                         {'ame2020-covariance','ame2020-atomic-masses','ame2020-part-i','ame2020-part-ii'})

    def test_source_diagonal_is_preserved_not_replaced_by_rounded_sigma(self):
        rows={q['code']:q for q in self.result['atomic_mass_inputs']}
        self.assertEqual(Fraction(rows[10010]['covariance_variance_nano_u2']),Fraction('0.00019583639'))
        self.assertNotEqual(Fraction(rows[10010]['covariance_variance_nano_u2']),Fraction('0.014')**2)
        self.assertTrue(rows[10010]['diagonal_compatible'])
        self.assertFalse(rows[1330550]['diagonal_compatible'])
        precise={10000:'1008664915.904',10010:'1007825031.898',20010:'2014101777.844',
                 30010:'3016049281.320',30020:'3016029321.967',40020:'4002603254.130'}
        for code,mean in precise.items():
            self.assertEqual(Fraction(rows[code]['mean_nano_u']),Fraction(mean))
            self.assertEqual(rows[code]['source_id'],'ame2020-part-ii')
            self.assertTrue(rows[code]['diagonal_compatible'])
        self.assertEqual(Fraction(rows[10000]['mean_nano_u'])-Fraction(rows[10000]['electronic_table_record']['mean_nano_u']),Fraction('0.004'))
        self.assertEqual(Fraction(rows[30020]['mean_nano_u'])-Fraction(rows[30020]['electronic_table_record']['mean_nano_u']),Fraction('-0.003'))

    def test_cesium_coverage_is_distinct_from_compatible_adoption(self):
        self.assertEqual(self.result['status'],'partial')
        self.assertEqual(self.result['coverage']['adopted_rows'],6)
        self.assertEqual(self.result['coverage']['held_rows'],3)
        self.assertTrue(all(x['incompatible_codes']==[1330550] for x in self.result['held']))
        self.assertTrue(all('Cs-133' in x['record_id'] for x in self.result['held']))

    def test_published_h3_he3_variance_counterexample_to_independence(self):
        order=self.result['source_matrix']['order'];matrix=self.result['source_matrix']['matrix']
        i,j=order.index(30010),order.index(30020)
        variance=Fraction(matrix[i][i])+Fraction(matrix[j][j])-2*Fraction(matrix[i][j])
        self.assertEqual(variance,Fraction('0.0040384698'))
        self.assertNotEqual(variance,Fraction(matrix[i][i])+Fraction(matrix[j][j]))

    def test_cross_output_covariance_preserves_deuterium_duplicate(self):
        names=self.result['output_order'];cov=self.result['output_covariance_nano_u2']
        i=names.index('neutron_separation_energy:isotope:H-2:ground')
        j=names.index('proton_separation_energy:isotope:H-2:ground')
        self.assertEqual(cov[i],cov[j])
        self.assertEqual(cov[i][j],cov[i][i])

    def test_shared_mass_path_has_zero_joint_variance(self):
        names=self.result['output_order'];cov=self.result['output_covariance_nano_u2']
        relation={'neutron_separation_energy:isotope:He-4:ground':1,
                  'proton_separation_energy:isotope:He-4:ground':-1,
                  'neutron_separation_energy:isotope:H-3:ground':-1,
                  'proton_separation_energy:isotope:He-3:ground':1}
        coeff=[relation.get(name,0) for name in names]
        value=sum(coeff[i]*Fraction(cov[i][j])*coeff[j] for i in range(len(names)) for j in range(len(names)))
        self.assertEqual(value,0)

    def test_unknown_scale_is_rejected(self):
        raw=self.tiny(['10000 10000 1']).replace(b'nano-amu**2',b'amu**2')
        with self.assertRaisesRegex(ValueError,'scale or unit'):c.parse_matrix(raw,[10000])

    def test_missing_correlation_is_not_zero(self):
        with self.assertRaisesRegex(ValueError,'missing covariance'):
            c.parse_matrix(self.tiny(['10000 10000 1','10010 10010 1']),[10000,10010])

    def test_mirrored_entry_is_not_silently_merged(self):
        raw=self.tiny(['10000 10000 1','10010 10000 0','10000 10010 0','10010 10010 1'])
        with self.assertRaisesRegex(ValueError,'duplicate or mirrored'):c.parse_matrix(raw,[10000,10010])

    def test_unknown_state_does_not_alias_ground_state(self):
        with self.assertRaisesRegex(ValueError,'missing covariance'):
            c.parse_matrix(self.tiny(['10010 10010 1']),[10011])

    def test_duplicate_order_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'nuclide order'):
            c.parse_matrix(self.tiny(['10010 10010 1']),[10010,10010])

    def test_nonfinite_entry_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'nonfinite'):
            c.parse_matrix(self.tiny(['10010 10010 NaN']),[10010])

    def test_non_psd_matrix_is_not_repaired(self):
        with self.assertRaisesRegex(ValueError,'positive semidefinite'):
            c.validate_matrix([[1,2],[2,1]],[10000,10010])
        with self.assertRaisesRegex(ValueError,'zero covariance pivot'):
            c.validate_matrix([[0,1],[1,1]],[10000,10010])

    def test_asymmetry_and_missing_matrix_dimension_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'asymmetric'):c.validate_matrix([[1,0],[1,1]],[10000,10010])
        with self.assertRaisesRegex(ValueError,'incomplete'):c.validate_matrix([[1]],[10000,10010])

    def test_singular_legitimate_covariance_is_allowed(self):
        _,rank=c.validate_matrix([[1,1],[1,1]],[10000,10010]);self.assertEqual(rank,1)

    def test_changed_adoption_manifest_is_not_resealable(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/c.INPUTS;target.parent.mkdir(parents=True)
            target.write_bytes((self.root/c.INPUTS).read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'manifest changed'):c.input_paths(td)

    def test_changed_raw_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            for name in c.input_paths(self.root):
                target=Path(td)/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(self.root/name,target)
            source=next(s for s in self.result['sources'] if s['id']=='ame2020-covariance')
            with (Path(td)/source['path']).open('ab') as handle:handle.write(b'changed')
            with self.assertRaisesRegex(ValueError,'source bytes changed'):
                c.build(td,self.baseline,producer.load(self.root).mapping)

    def test_changed_coefficients_are_rejected(self):
        report=copy.deepcopy(self.baseline)
        row=next(r for r in report['rows'] if r['property']=='neutron_separation_energy' and r['value'] is not None)
        row['coefficients'][0]['coefficient']+=1
        with self.assertRaisesRegex(ValueError,'coefficients differ'):
            c.build(self.root,report,producer.load(self.root).mapping)


    def test_equal_value_source_alias_is_rejected(self):
        report=copy.deepcopy(self.baseline)
        row=next(r for r in report['rows'] if r['property']=='neutron_separation_energy' and r['value'] is not None)
        term=row['coefficients'][0]; original=term['source_quantity_id']
        report['source_quantities']['alias']=copy.deepcopy(report['source_quantities'][original])
        term['source_quantity_id']='alias'
        with self.assertRaisesRegex(ValueError,'source quantity alias'):
            c.build(self.root,report,producer.load(self.root).mapping)

    def test_moved_source_locator_is_rejected(self):
        report=copy.deepcopy(self.baseline)
        key=next(k for k,q in report['source_quantities'].items() if q['quantity']=='mass_excess')
        report['source_quantities'][key]['locator']['line']+=1
        with self.assertRaisesRegex(ValueError,'locator or value differs'):
            c.build(self.root,report,producer.load(self.root).mapping)

    def test_negative_or_missing_magnitude_does_not_authenticate_diagonal(self):
        with self.assertRaises(ValueError):c.diagonal_compatible('1','-1','1')
        with self.assertRaises(ValueError):c.diagonal_compatible('1','1','0')
        self.assertFalse(c.diagonal_compatible('73.914558','8','1'))

    def test_published_fraction_square_root_is_only_rounded_for_display(self):
        for row in self.result['adopted']:
            variance=row['atomic_mass_reduction']['output_variance']
            self.assertEqual(row['standard_deviation']['expression'],'sqrt('+variance+')')
            self.assertEqual(row['standard_deviation']['display_rule'],'10 significant digits, round half even')
            self.assertEqual(row['unit'],'nano-u')


if __name__=='__main__':unittest.main()
