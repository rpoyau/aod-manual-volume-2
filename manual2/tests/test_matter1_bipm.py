"""Published data consistency and persisted mutations, independently of atomic claims."""
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'manual2/scripts'))
import matter1_bipm as b


class BIPMTests(unittest.TestCase):
    def test_full_covariance_and_input_output_rounding(self):
        report = b.verify(ROOT)
        self.assertEqual(report['checked_ratios'], 105)
        self.assertTrue(all(r['input_output_rounding_overlap'] for r in report['ratio_checks']))
        self.assertEqual(report['effective_measurements'], 146)
        self.assertEqual(report['correlation_coefficients'], 1168)
        self.assertEqual(report['atomic_prediction'], 'not_asserted')

    def test_rounding_includes_covariance_input_precision(self):
        report = b.evaluate(ROOT)
        row = next(r for r in report['ratio_checks'] if r['ratio'] == '5/14')
        point = Q(row['sigma_from_printed_covariance'])
        output_cell = b.cell(row['reported_sigma'])
        self.assertGreater(point, output_cell[1])
        self.assertTrue(row['input_output_rounding_overlap'])

    def test_exact_psd_rejects_positive_diagonal_indefinite_matrix(self):
        with self.assertRaisesRegex(ValueError, 'PSD'):
            b.check_psd([[Q(1), Q(2)], [Q(2), Q(1)]])
        with self.assertRaisesRegex(ValueError, 'Zero covariance pivot'):
            b.check_psd([[Q(0), Q(1)], [Q(1), Q(1)]])
        b.check_psd([[Q(1), Q(1)], [Q(1), Q(1)]])

    def test_correlation_and_measurement_identity_mutations(self):
        text = next((ROOT/b.REL/'raw').glob('ClockInputData*')).read_text()
        changes = [('r(q3,q7)\t0.001', 'r(q3,q7)\t1.01'),
                   ('r(q3,q7)', 'r(q3,q999)'), ('q2\tnu1', 'q1\tnu1'),
                   ('Uncertx10000Exclude', 'Uncertx10000Unspecified')]
        for old, new in changes:
            with self.subTest(new=new):
                self.assertIn(old, text)
                with self.assertRaises(ValueError):
                    b.parse_input(text.replace(old, new, 1))

    def test_ratio_sigma_mutation_rejects_at_numerical_layer(self):
        data = ROOT/b.REL/'raw'
        cov = next(data.glob('ClockOutputCovData*')).read_text()
        out = next(data.glob('ClockOutputData*')).read_text()
        self.assertIn('1.057e-11', out)
        with self.assertRaisesRegex(ValueError, 'rounding cells'):
            b.covariance_checks(cov, out.replace('1.057e-11', '2.057e-11', 1))

    def test_covariance_scaling_is_squared_once(self):
        value, multiplier = Q(7, 3), Q(47, 20)
        self.assertEqual(multiplier**2 * value, Q(2209, 400)*value)
        report = b.verify(ROOT)
        self.assertTrue(report['random_effect_already_in_outputs'])
        self.assertFalse(report['additional_random_effect_applied'])
        self.assertEqual(report['recommendation_covariance_multiplier'], '2209/400')

    def test_persisted_hostile_mutations_rejected_without_repair(self):
        cases = ['raw', 'manifest', 'status', 'unit', 'ratio', 'omitted_status']
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                shutil.copytree(ROOT/b.REL, root/b.REL)
                scripts = root/'manual2/scripts'; scripts.mkdir(parents=True)
                for name in ['matter1_bipm.py', 'verify_matter1_bipm.py']:
                    shutil.copy2(ROOT/'manual2/scripts'/name, scripts/name)
                if case == 'raw':
                    p = next((root/b.REL/'raw').glob('ClockInputData*'))
                    p.write_bytes(p.read_bytes() + b'\nCORRUPTION\n')
                elif case == 'manifest':
                    p = root/b.REL/'source_manifest.json'
                    value = json.loads(p.read_bytes()); value['target_exposure_status'] = 'blind'
                    p.write_bytes(b.canonical(value))
                else:
                    p = root/b.REL/'bipm_report.json'; value = json.loads(p.read_bytes())
                    if case == 'status': value['atomic_prediction'] = 'verified'
                    if case == 'unit': value['covariance_interpretation'] = 'dimensionless'
                    if case == 'ratio': value['ratio_checks'][0]['reported_sigma'] = '1'
                    if case == 'omitted_status': del value['least_squares_adjustment']
                    p.write_bytes(b.canonical(value))
                def snapshot():
                    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in root.rglob('*') if p.is_file()}
                before = snapshot()
                for optimized in (False, True):
                    cmd = [sys.executable, '-B'] + (['-O'] if optimized else []) + [str(scripts/'verify_matter1_bipm.py'), '--root', str(root)]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(before, snapshot())

    def test_readonly_verifier_rejects_unknown_option(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT/'manual2/scripts/verify_matter1_bipm.py'), '--repair'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__': unittest.main()
