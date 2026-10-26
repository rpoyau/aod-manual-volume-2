"""Exact SI arithmetic, domain guards, and real read-only persisted mutations.

These tests instantiate the synthetic metrology lane. They do not calibrate a
device or establish native atomic admission. BIPM source parsing has its own tests.
"""
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'manual2/scripts'))
import matter1_metrology as m
import matter1_temporal as temporal

DATA = m.DATA
VERIFIER = Path('manual2/scripts/verify_matter1_metrology.py')


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


class MetrologyTests(unittest.TestCase):
    def setUp(self):
        self.base = m.default_input(ROOT)

    def test_si_01_committed_identity_window_and_reference_count(self):
        self.assertEqual(m.interval(self.base)['reference_increment'], 4)
        # Five completions include the first anchor: only four are reclosures.
        self.assertEqual(len(self.base['binding']['lineages'][0]['returns']), 5)
        for field, value in [('reference_lineage', 'unknown'), ('reference_increment', 3), ('comparison_cut', 13)]:
            d = deepcopy(self.base); d['binding'][field] = value
            with self.subTest(field=field), self.assertRaises(m.ValidationError): m.interval(d)
        d = deepcopy(self.base); d['binding']['lineages'][0]['returns'][0]['id'] = 'changed'
        with self.assertRaisesRegex(m.ValidationError, 'prefix'): m.interval(d)

    def test_si_02_explicit_observation_map(self):
        self.assertEqual(m.interval(self.base)['elapsed_seconds'], '1')
        d = deepcopy(self.base); d['observation']['kind'] = 'native_ticks_are_seconds'
        with self.assertRaises(m.ValidationError): m.interval(d)
        d = deepcopy(self.base); d['observation']['cycles_per_return'] = '1'
        with self.assertRaises(m.ValidationError): m.interval(d)

    def test_si_03_exact_definition_and_uncertain_realization(self):
        value = m.frequency_from_ratio('1/7', '1/100000000000000000000')
        self.assertEqual(Q(value['frequency_hz']), m.CS_HZ/7)
        self.assertEqual(Q(value['transition_period_seconds']), 7/m.CS_HZ)
        self.assertEqual(value['covariance']['matrix'][1][1], '0')
        realized = m.frequency_from_ratio('1/7', '1/100000000000000000000', reference_kind='realized_reference')
        self.assertEqual(realized['uncertainty_status'], 'partial')
        self.assertIsNone(realized['frequency_variance_hz2'])
        with self.assertRaises(m.ValidationError): m.frequency_from_ratio('1/7', '0', reference_variance='1')

    def test_ratio_reference_cross_covariance(self):
        result=m.frequency_from_ratio('2','1/100000000',reference_hz='3',reference_variance='1/100000000',
                                      ratio_reference_covariance='1/200000000',reference_kind='realized_reference')
        self.assertEqual(Q(result['frequency_variance_hz2']),Q(19,100000000))
        self.assertEqual(Q(result['transition_period_variance_s2']),Q(19,100000000)/6**4)
        missing=m.frequency_from_ratio('2','1/100000000',reference_hz='3',reference_variance='1/100000000',reference_kind='realized_reference')
        self.assertIsNone(missing['frequency_variance_hz2'])

    def test_cancelled_product_gradient_does_not_certify_zero_uncertainty(self):
        # Positive finite support: R=1+delta, f=1-delta. First-order
        # cancellation is exact, but R*f=1-delta^2 is not constant.
        support = [(Q(-1,2),Q(1,4)), (Q(0),Q(1,2)), (Q(1,2),Q(1,4))]
        average = sum(p*(1-d*d) for d,p in support)
        variance = sum(p*((1-d*d)-average)**2 for d,p in support)
        self.assertEqual(average, Q(7,8))
        self.assertEqual(variance, Q(1,64))
        result = m.frequency_from_ratio('1','1/8',reference_hz='1',reference_variance='1/8',
                                        ratio_reference_covariance='-1/8',reference_kind='realized_reference')
        self.assertEqual(result['first_order_frequency_variance_hz2'], '0')
        self.assertEqual(result['uncertainty_status'], 'partial')
        self.assertIsNone(result['frequency_variance_hz2'])
        self.assertIsNone(result['standard_uncertainty_hz_display'])
        self.assertIsNone(result['transition_period_variance_s2'])
        self.assertIn('product_input_nonlinearity_requires_joint_distribution', result['unresolved_uncertainty'])
        # Small marginal variance alone also cannot validate a zero gradient.
        small = m.frequency_from_ratio('1','1/1000000',reference_hz='1',reference_variance='1/1000000',
                                       ratio_reference_covariance='-1/1000000',reference_kind='realized_reference')
        self.assertIn('cancelled_product_gradient_requires_joint_distribution', small['unresolved_uncertainty'])
        self.assertIsNone(small['frequency_variance_hz2'])

    def test_standalone_interval_rejects_false_source_and_inapplicable_transfer(self):
        for source in ({'status':'invented'}, {**self.base['source_binding'], 'sha256':'0'*64}):
            d=deepcopy(self.base);d['source_binding']=source
            with self.subTest(source=source), self.assertRaisesRegex(m.ValidationError,'Source binding'):
                m.interval(d)
        d=deepcopy(self.base);d['measurand']['transfer_model']={'status':'invented'}
        with self.assertRaisesRegex(m.ValidationError,'scale-transfer'):m.interval(d)
        d=deepcopy(self.base);d['measurand'].update(time_coordinate='coordinated_scale',
            transfer_model={'status':'synthetic_included','included_in':'endpoint_correction','source':'synthetic_link'},
            global_gravitational_correction_seconds='1')
        with self.assertRaisesRegex(m.ValidationError,'endpoint transfer'):m.interval(d)

    def test_si_04_divider_and_epoch_invariance(self):
        before = m.interval(self.base)
        d = deepcopy(self.base)
        for field in ['cycles_per_return', 'observed_cycles']:
            d['observation'][field] = str(Q(d['observation'][field])/10)
        d['reference']['nominal_ratio'] = '1/10'
        d['reference']['nominal_hz'] = str(m.CS_HZ/10)
        scale = [Q(1,10), Q(1), Q(1)]
        c = d['covariance']['matrix']
        for i in range(3):
            for j in range(3): c[i][j] = str(Q(c[i][j])*scale[i]*scale[j])
        d['budget'][0]['standard_uncertainty'] = str(Q(d['budget'][0]['standard_uncertainty'])/10)
        d['measurand']['epoch_seconds'] = '1000000'
        after = m.interval(d)
        for field in ['elapsed_seconds', 'variance_seconds2', 'standard_uncertainty_seconds_display']:
            self.assertEqual(before[field], after[field])

    def test_si_05_signed_frequency_and_endpoint_corrections(self):
        d = deepcopy(self.base); d['reference']['fractional_offset'] = '1/1000000'
        d['endpoint_correction_seconds'] = '1/1000'
        self.assertEqual(Q(m.interval(d)['elapsed_seconds']), Q(1000000,1000001)+Q(1,1000))
        d['endpoint_correction_seconds'] = '-1/1000'
        self.assertEqual(Q(m.interval(d)['elapsed_seconds']), Q(1000000,1000001)-Q(1,1000))

    def test_si_06_exact_psd_order_units_and_full_covariance(self):
        result = m.interval(self.base)
        self.assertEqual(Q(result['variance_seconds2']), Q(4904,10**24))
        d = deepcopy(self.base)
        d['covariance']['matrix'][0][2] = d['covariance']['matrix'][2][0] = '0'
        self.assertEqual(Q(m.interval(d)['variance_seconds2']), Q(3404,10**24))
        for matrix in [[[1,2],[2,1]], [[0,1],[1,1]], [[1,0],[1,1]]]:
            with self.assertRaises(m.ValidationError): m.validate_psd(matrix)
        self.assertEqual(m.quadratic([1,-1], [[1,1],[1,1]]), 0)
        for field,value in [('units',['s','1','s']), ('variables',['endpoint_correction','fractional_offset','physical_cycles'])]:
            d=deepcopy(self.base);d['covariance'][field]=value
            with self.assertRaises(m.ValidationError):m.interval(d)

    def test_si_07_inclusion_paths_prevent_double_counting(self):
        d = deepcopy(self.base); d['budget'][0]['covers'].append('already_included')
        child = deepcopy(d['budget'][0]); child.update(id='child',covers=['already_included'],included=False,included_in_aggregate='physical_cycles')
        d['budget'].append(child); m.interval(d)
        child['included'] = True
        with self.assertRaisesRegex(m.ValidationError, 'twice'): m.interval(d)

    def test_si_08_correlated_noise_deadtime_and_drift(self):
        sigma = Q(1,10**12)
        self.assertEqual(m.quadratic([100], [[sigma**2]]), 10000*sigma**2)
        self.assertNotEqual(m.quadratic([100], [[sigma**2]]), 100*sigma**2)
        d = deepcopy(self.base);d['acquisition'].update(dead_time_status='unmodeled',dead_time_seconds='1/10')
        r = m.interval(d)
        self.assertEqual(r['uncertainty_status'],'partial');self.assertIsNone(r['elapsed_seconds'])
        self.assertIn('dead_time_extrapolation_not_modeled',r['unresolved_uncertainty'])
        d['acquisition']['extrapolation_model'] = 'interpolate silently'
        with self.assertRaises(m.ValidationError):m.interval(d)

    def test_si_09_shared_endpoints_and_transfer_covariance(self):
        ps=Q(1,10**12); common,noise=80*ps,20*ps
        self.assertEqual(m.quadratic([-1,1], [[common**2+noise**2,common**2],[common**2,common**2+noise**2]]),800*ps**2)
        # Signed transfer terms are ordinary correlated endpoint inputs, not independent duplicates.
        self.assertEqual(m.quadratic([1,-1], [[4,1],[1,9]]),11)

    def test_si_10_local_and_coordinated_time(self):
        d=deepcopy(self.base);d['measurand']['global_gravitational_correction_seconds']='1'
        with self.assertRaises(m.ValidationError):m.interval(d)
        d=deepcopy(self.base);d['measurand']['time_coordinate']='coordinated_scale'
        with self.assertRaises(m.ValidationError):m.interval(d)
        d['measurand']['transfer_model']={'status':'synthetic_included','included_in':'endpoint_correction','source':'synthetic_link'}
        self.assertEqual(m.interval(d)['time_coordinate'],'coordinated_scale')

    def test_si_11_causal_calibration_and_immutable_input(self):
        before=deepcopy(self.base);m.interval(self.base);self.assertEqual(before,self.base)
        d=deepcopy(self.base);d['calibration']['available_at_cut']=13
        with self.assertRaisesRegex(m.ValidationError,'Future'):m.interval(d)
        d['calibration']['mode']='retrospective';m.interval(d)
        d=deepcopy(self.base);d['calibration']['validity_cuts']=[1,12]
        with self.assertRaises(m.ValidationError):m.interval(d)

    def test_si_12_nonlinearity_and_discrete_ambiguity(self):
        self.assertEqual(m.gaussian_quadratic_shift(1,0,'1/10')['mean_shift'],'1/100')
        self.assertEqual(m.gaussian_quadratic_shift(1,0,'1/10')['variance'],'1/5000')
        d=deepcopy(self.base);d['acquisition'].update(cycle_slip_status='ambiguous',cycle_slip_alternatives=[-1,0,1])
        r=m.interval(d);self.assertIsNone(r['elapsed_seconds']);self.assertIsNone(r['variance_seconds2'])
        self.assertEqual(len(r['conditional_interval_alternatives_seconds']),3)
        result=m.frequency_from_ratio('1','1')
        self.assertIsNone(result['transition_period_variance_s2']);self.assertEqual(result['uncertainty_status'],'partial')

    def test_si_14_covariance_multiplier_squared(self):
        g=Q(235,100);cov=[[4,1],[1,9]]
        scaled=[[g*g*x for x in row] for row in cov]
        self.assertEqual(m.quadratic([1,-1],scaled),g*g*m.quadratic([1,-1],cov))

    def test_si_15_unknown_covariance_does_not_become_zero(self):
        d=deepcopy(self.base);d['covariance']['status']='partial'
        d['covariance']['matrix'][0][1]=d['covariance']['matrix'][1][0]=None
        r=m.interval(d);self.assertEqual(r['elapsed_seconds'],'1');self.assertIsNone(r['variance_seconds2'])
        self.assertEqual(r['uncertainty_status'],'partial')
        d['covariance']['status']='complete'
        with self.assertRaises(m.ValidationError):m.interval(d)

    def test_si_16_standard_and_expanded_uncertainty(self):
        d=deepcopy(self.base);d['coverage'].update(expanded_factor='2',coverage_basis='synthetic_coverage_assumption_not_inferred')
        r=m.interval(d);self.assertEqual(r['unit'],'s');self.assertEqual(r['coverage_factor'],'2')
        self.assertIsNotNone(r['expanded_uncertainty_seconds_display'])
        d['coverage']['coverage_basis']=None
        with self.assertRaises(m.ValidationError):m.interval(d)

    def test_si_17_target_exposure_and_native_claims(self):
        for change in [lambda d:d['calibration'].__setitem__('fitted_targets',['H-1']),
                       lambda d:d['calibration'].__setitem__('exposed_targets',[]),
                       lambda d:d['statuses'].__setitem__('native_admission','complete')]:
            d=deepcopy(self.base);change(d)
            with self.assertRaises(m.ValidationError):m.interval(d)

    def test_transition_period_is_not_window_interval(self):
        self.assertEqual(m.interval(self.base)['quantity_kind'],'elapsed_interval')
        self.assertEqual(m.frequency_from_ratio('1/7')['quantity_kind'],'transition_period')
        self.assertNotEqual(m.interval(self.base)['elapsed_seconds'],m.frequency_from_ratio('1/7')['transition_period_seconds'])

    def test_si_18_stateful_history_synthetic_observation_integration(self):
        result=m.stateful_integration(ROOT)
        left,right=result['cases']['baseline'],result['cases']['early_loss']
        self.assertEqual(left['compared_return_count'],6);self.assertEqual(right['compared_return_count'],2)
        self.assertEqual(left['interval_result']['elapsed_seconds'],'1')
        self.assertEqual(right['interval_result']['elapsed_seconds'],'1')
        self.assertEqual(Q(left['synthetic_finite_window_cycle_average_rate_hz']),6*m.CS_HZ/5)
        self.assertEqual(Q(right['synthetic_finite_window_cycle_average_rate_hz']),2*m.CS_HZ/5)
        self.assertIsNone(left['atomic_transition_frequency_hz']);self.assertIsNone(right['atomic_transition_frequency_hz'])
        self.assertEqual(result['native_admission'],'not_claimed')
        self.assertEqual(result['atomic_prediction'],'not_performed')
        self.assertEqual(len(left['mapped_input']['binding']['lineages'][1]['returns']),6)
        self.assertEqual(left['mapped_input']['binding']['reference_increment'],5)

    def disposable(self, directory):
        root=Path(directory)/'repo'
        paths=[VERIFIER,Path('manual2/scripts/matter1_metrology.py'),Path(m.SOURCE_PATH),
               DATA/'metrology_inputs.json',DATA/'metrology_report.json',
               Path('manual2/scripts/matter1_stateful.py'),Path('manual2/scripts/matter1_temporal.py'),
               Path('manual2/scripts/matter1_folding.py'),Path('manual2/data/m1/folding/two_square_fold.json'),
               *(Path(path) for path in temporal.SOURCE_LABELS)]
        for relative in paths:
            target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target)
        return root

    def test_persisted_hostile_mutations_read_only_both_modes(self):
        changes={
            'invented source binding': lambda d:d.__setitem__('source_binding',{'status':'invented'}),
            'local unknown transfer': lambda d:d['measurand'].__setitem__('transfer_model',{'status':'invented'}),
            'reference identity': lambda d:d['binding'].__setitem__('reference_lineage','unknown'),
            'reference count': lambda d:d['binding'].__setitem__('reference_increment',5),
            'map promotion': lambda d:d['observation'].__setitem__('map_status','native_admitted'),
            'window mismatch': lambda d:d['observation'].__setitem__('window',[1,12]),
            'clock declaration': lambda d:d['reference'].__setitem__('realization_status','exact_device'),
            'missing calibration': lambda d:d['calibration'].pop('evidence_id'),
            'future calibration': lambda d:d['calibration'].__setitem__('available_at_cut',13),
            'changed prefix': lambda d:d['binding']['lineages'][0].__setitem__('prefix_sha256','0'*64),
            'wrong unit': lambda d:d['covariance']['units'].__setitem__(0,'s'),
            'omitted covariance': lambda d:d['covariance']['matrix'][0].__setitem__(2,None),
            'unsupported covariance status': lambda d:d['covariance'].__setitem__('status','accepted'),
            'negative variance': lambda d:d['covariance']['matrix'][0].__setitem__(0,'-1'),
            'budget mismatch': lambda d:d['budget'][0].__setitem__('standard_uncertainty','0'),
            'aggregate duplication': lambda d:d['budget'][0].__setitem__('included_in_aggregate','fractional_offset'),
            'local gravity correction': lambda d:d['measurand'].__setitem__('global_gravitational_correction_seconds','1'),
            'false independent target': lambda d:d['calibration'].__setitem__('prediction_class','independent'),
            'hidden H fit': lambda d:d['calibration'].__setitem__('fitted_targets',['H-1']),
            'missing realization status': lambda d:d['reference'].pop('realization_status'),
            'missing slip status': lambda d:d['acquisition'].pop('cycle_slip_status'),
            'unsupported noise': lambda d:d['acquisition'].__setitem__('noise_model','assume_independent'),
            'coverage without basis': lambda d:d['coverage'].__setitem__('expanded_factor','2'),
            'native admission': lambda d:d['statuses'].__setitem__('native_admission','admitted'),
            'missing native status': lambda d:d['statuses'].pop('native_admission'),
        }
        for optimized in (False,True):
            for name,change in changes.items():
                with self.subTest(name=name,optimized=optimized),tempfile.TemporaryDirectory() as directory:
                    root=self.disposable(directory);path=root/DATA/'metrology_inputs.json'
                    data=json.loads(path.read_text());change(data['examples']['complete_synthetic']);path.write_bytes(m.canonical_bytes(data))
                    before=snapshot(root)
                    command=[sys.executable,'-B']+(['-O'] if optimized else [])+[str(root/VERIFIER),'--root',str(root),'--check-data']
                    result=subprocess.run(command,capture_output=True,text=True)
                    self.assertNotEqual(result.returncode,0,name);self.assertIn('ERROR:',result.stderr)
                    self.assertEqual(before,snapshot(root),name)

    def test_public_verification_read_only_and_unknown_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            root=self.disposable(directory);before=snapshot(root)
            result=subprocess.run([sys.executable,'-B',str(root/VERIFIER),'--root',str(root)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(before,snapshot(root))
            result=subprocess.run([sys.executable,'-B',str(root/VERIFIER),'--repair'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertEqual(before,snapshot(root))


if __name__ == '__main__':
    unittest.main()
