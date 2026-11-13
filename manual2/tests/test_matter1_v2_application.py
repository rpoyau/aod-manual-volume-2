"""Persisted request integrity and incomplete evidence cannot become success."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_matter1_v2_application as binding
import record_matter1_acceptance as old
import record_matter1_v2_acceptance as receipt


class V2ApplicationTests(unittest.TestCase):
    def test_v1_and_available_request_preserved(self):
        result = binding.verify(ROOT)
        self.assertEqual(result['status'], 'PASS_V2_CONSERVATION')
        self.assertEqual(result['mentioned_latest_archive']['integrity'], 'not_verified')

    def test_persisted_omission_and_v1_edit_reject_both_modes_without_repair(self):
        request = json.loads((ROOT / binding.REQUEST).read_bytes())
        for omit in (False, True):
            with self.subTest(omit=omit), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for group in ('v1_sha256', 'request_sha256'):
                    for name in request[group]:
                        target = root / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(ROOT / name, target)
                target = root / binding.REQUEST
                target.parent.mkdir(parents=True, exist_ok=True)
                edited = json.loads(json.dumps(request))
                path = next(iter(edited['v1_sha256']))
                if omit:
                    edited['v1_sha256'].pop(path)
                    target.write_text(json.dumps(edited))
                else:
                    target.write_bytes((ROOT / binding.REQUEST).read_bytes())
                    (root / path).write_bytes((root / path).read_bytes() + b'\n')
                def snapshot():
                    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in root.rglob('*') if p.is_file()}
                before = snapshot()
                for optimized in (False, True):
                    command = [sys.executable, '-B'] + (['-O'] if optimized else [])
                    command += [str(ROOT / 'scripts/check_matter1_v2_application.py'), '--root', str(root)]
                    proc = subprocess.run(command, text=True, capture_output=True)
                    self.assertNotEqual(proc.returncode, 0)
                    self.assertIn('v2 conservation failed', proc.stderr)
                    self.assertEqual(snapshot(), before)

    def test_23_criteria_do_not_promote_atomic_objective(self):
        rows = receipt.criteria(ROOT, old.source_test_ids())
        self.assertEqual(len(rows), 23)
        self.assertEqual(len({r['id'] for r in rows}), 23)
        self.assertTrue(all(r['objective_status'] == 'incomplete_atomic_map_unresolved'
                            for r in rows if r['id'].startswith('PRED')))

    def test_truncated_or_incomplete_success_log_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('tests.txt', 'tests-optimized.txt'):
                (root / name).write_text('Ran 1 test in 0.1s\n\nOK\n')
            with self.assertRaises(old.EvidenceError):
                receipt.validate_logs(root, old.source_test_ids())

    def test_atomic_status_promotion_in_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sys.path.insert(0, str(ROOT / 'manual2/scripts'))
            import matter1_stateful, matter1_metrology, matter1_bipm, matter1_atomic
            for lane, module in zip(receipt.LANES, (matter1_stateful, matter1_metrology, matter1_bipm, matter1_atomic)):
                value = module.verify(ROOT)
                if lane == 'atomic':
                    value['atomic_prediction_objective'] = 'complete'
                for suffix in ('', '-optimized'):
                    (root / (lane + suffix + '.json')).write_bytes(old.canonical(value))
            (root / 'v2-conservation.json').write_bytes(old.canonical(binding.verify(ROOT)))
            with self.assertRaisesRegex(old.EvidenceError, 'atomic: current verified receipt differs'):
                receipt.validate_lane_receipts(ROOT, root)


if __name__ == '__main__':
    unittest.main()
