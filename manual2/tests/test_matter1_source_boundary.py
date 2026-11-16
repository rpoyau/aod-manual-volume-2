"""Scientific admission excludes detached authoring and task history."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'manual2/scripts'))
import matter1_constructed_coupling as coupling
from manual2.tests.foundation_fixture import copy_foundation_receipts


class ScientificSourceBoundaryTests(unittest.TestCase):
    def clone_inputs(self, destination):
        for directory in ('manual2/scripts',
                          'manual2/data/m1/constructed_coupling/source_packet'):
            shutil.copytree(ROOT / directory, destination / directory)
        copy_foundation_receipts(ROOT, destination)
        foundation = json.loads((ROOT / 'manual2/evidence/foundation-source.json').read_text())
        for name in foundation['files']:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)

    def test_normal_admission_needs_no_task_logs_or_authoring_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.clone_inputs(root)
            self.assertFalse((root / '.agents/skills').exists())
            packet = root / coupling.DATA / 'source_packet'
            self.assertFalse((packet / 'historical_checks/checks_test_normal.log').exists())
            self.assertFalse((packet / 'review/validation_summary.json').exists())
            self.assertFalse((packet / 'review/replay_check.json').exists())
            original_identity = coupling.check_sources(root)
            self.assertEqual(original_identity['selected_original_members'], 39)
            selected = json.loads((packet / 'SCIENTIFIC_MEMBER_BINDINGS.json').read_text())
            self.assertEqual(len(selected['members']), 32)
            # Changing detached history outside the source root has no effect.
            detached = root.parent / (root.name + '-history.txt')
            try:
                detached.write_text('old test log')
                self.assertEqual(coupling.check_sources(root), original_identity)
                detached.write_text('editorial correction to old test log')
                self.assertEqual(coupling.check_sources(root), original_identity)
            finally:
                detached.unlink(missing_ok=True)

    def test_scientific_tampering_and_manifest_resealing_still_reject(self):
        for name in ('constructed_coupling.py', 'contract.json', 'SCIENTIFIC_MEMBER_BINDINGS.json'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.clone_inputs(root)
                packet = root / coupling.DATA / 'source_packet'
                target = packet / name
                if name == 'SCIENTIFIC_MEMBER_BINDINGS.json':
                    value = json.loads(target.read_text())
                    value['members'].pop('contract.json')
                    target.write_text(json.dumps(value))
                else:
                    target.write_bytes(target.read_bytes() + b'\n')
                before = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in root.rglob('*') if p.is_file()}
                with self.assertRaises(ValueError):
                    coupling.check_sources(root)
                after = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in root.rglob('*') if p.is_file()}
                self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
