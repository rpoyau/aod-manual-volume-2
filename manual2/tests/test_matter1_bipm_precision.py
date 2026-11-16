"""The precision successor preserves point results and rejects zero-format slack."""
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'manual2/scripts'))
import matter1_bipm as old
import matter1_bipm_precision as current


class BIPMPrecisionTests(unittest.TestCase):
    def test_105_point_results_unchanged_and_zero_precision_unresolved(self):
        result = current.verify(ROOT)
        self.assertEqual(result['ratio_checks'], old.verify(ROOT)['ratio_checks'])
        self.assertEqual(result['checked_ratios'], 105)
        self.assertIn('unknown', result['printed_zero_source_status'])
        self.assertEqual(result['rounding_claim_status'], 'conditional_consistency_not_source_precision_certification')

    def test_zero_exponent_never_supplies_precision(self):
        for zero in ('0', '0.00000e+00', '0.00000e-40'):
            with self.subTest(zero=zero), self.assertRaisesRegex(ValueError, 'explicit source/format policy'):
                current.cell(zero)
        self.assertEqual(current.cell('1.234e-4'), (Q('0.00012335'), Q('0.00012345')))

    def test_plus_one_percent_sigma_rejected_at_numerical_layer(self):
        raw = ROOT / current.REL / 'raw'
        covariance = next(raw.glob('ClockOutputCovData*')).read_text()
        text = next(raw.glob('ClockOutputData*')).read_text()
        changed, n = re.subn(r'(^nu9/nu14\s+[\d.]+ \+/- )([\d.eE+-]+)',
                            lambda m: m[1] + str(current.decimal(Q(m[2]) * Q(101, 100))), text, flags=re.M)
        self.assertEqual(n, 1)
        self.assertEqual(len(old.covariance_checks(covariance, changed)), 105)
        with self.assertRaisesRegex(ValueError, 'rounding cells'):
            current.covariance_checks(covariance, changed)

    def test_persisted_status_mutation_rejected_read_only_in_both_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / current.REL, root / current.REL)
            p = root / current.REL / 'bipm_precision_report.json'
            data = json.loads(p.read_bytes())
            data['printed_zero_source_status'] = 'physical_zero_certified'
            p.write_text(json.dumps(data))
            def snapshot():
                return {str(x.relative_to(root)): hashlib.sha256(x.read_bytes()).hexdigest()
                        for x in root.rglob('*') if x.is_file()}
            before = snapshot()
            for optimized in (False, True):
                command = [sys.executable, '-B'] + (['-O'] if optimized else [])
                command += [str(ROOT / 'manual2/scripts/verify_matter1_bipm_precision.py'), '--root', str(root)]
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('persisted report differs', result.stderr)
                self.assertEqual(snapshot(), before)


if __name__ == '__main__':
    unittest.main()
