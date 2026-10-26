"""Request/conservation guards mutate persisted copies, never the checkout."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / 'scripts/check_matter1_application.py'


class ApplicationBindingTests(unittest.TestCase):
    def test_current_conservation(self):
        result = subprocess.run([sys.executable, '-B', str(CHECK)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['baseline_numeric_comparisons'], 3024)
        self.assertEqual(report['tracked_skill_files'], 11)

    def test_persisted_manifest_omission_and_changed_source_reject_read_only(self):
        original = json.loads((ROOT / 'manual2/evidence/fusion-request.json').read_bytes())
        for omitted in (False, True):
            with self.subTest(omitted=omitted), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                for name in original['preservation_sha256']:
                    dest = root / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(ROOT / name, dest)
                shutil.copytree(ROOT / 'manual2/scripts', root / 'manual2/scripts')
                receipt = json.loads(json.dumps(original))
                name = 'sections/03_afc_basis.tex'
                (root / name).write_bytes((root / name).read_bytes() + b'\n% hostile source edit\n')
                if omitted:
                    receipt['preservation_sha256'].pop(name)
                (root / 'manual2/evidence/fusion-request.json').write_text(json.dumps(receipt))
                def snapshot():
                    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in root.rglob('*') if p.is_file()}
                before = snapshot()
                for optimized in (False, True):
                    cmd = [sys.executable, '-B'] + (['-O'] if optimized else []) + [str(CHECK), '--root', str(root)]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('Preservation', result.stderr)
                    self.assertEqual(snapshot(), before)

    def test_acceptance_inventory_retains_39_unique_request_ids(self):
        plan = json.loads((ROOT / 'manual2/evidence/fusion-acceptance-plan.json').read_bytes())
        # Entry schema is also checked by the replayable acceptance runner.
        records = plan['records']
        self.assertEqual(len(records), 39)
        self.assertEqual(len({row['id'] for row in records}), 39)


if __name__ == '__main__':
    unittest.main()
