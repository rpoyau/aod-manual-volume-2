"""The all-element campaign must preserve prior scientific data and placements."""
import importlib.util
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'campaign_preservation', ROOT/'scripts/check_matter1_campaign_preservation.py')
preservation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preservation)


class CampaignPreservationTests(unittest.TestCase):
    def test_scientific_data_and_chart_keep_their_bound_identities(self):
        report = preservation.verify(ROOT)
        self.assertEqual(report['status'], 'PASS_CAMPAIGN_PRESERVATION')
        self.assertEqual(report['checked_files'], 278)
        self.assertEqual(report['byte_preserved_files'] + report['source_metadata_successors'], 278)

    def test_persisted_manifest_omission_or_rebinding_rejects(self):
        original = json.loads((ROOT / preservation.BASELINE).read_bytes())
        for mutation in ('omission', 'relocation', 'successor'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                baseline = deepcopy(original)
                name = next(iter(baseline['files']))
                if mutation == 'omission':
                    del baseline['files'][name]
                elif mutation == 'relocation':
                    baseline.setdefault('relocations', {})[name] = 'substitute.json'
                else:
                    baseline.setdefault('source_successors', {})[name] = {
                        'original_sha256': baseline['files'][name],
                        'current_sha256': '0' * 64,
                        'changed_metadata_pointers': ['/value'],
                        'scientific_payload_sha256': '0' * 64,
                    }
                target = root / preservation.BASELINE
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps(baseline))
                before = target.read_bytes()
                with self.assertRaisesRegex(ValueError, 'preservation baseline'):
                    preservation.verify(root)
                self.assertEqual(target.read_bytes(), before)


class CampaignSuccessorBoundaryTests(unittest.TestCase):
    """Synthetic authority fixtures isolate the successor's inner checks.

    Patching the independent baseline digest admits a declared test authority;
    it does not simulate editing or resealing the real scientific manifest.
    The expected scientific payload is written directly, not projected by the
    implementation under test.
    """

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.old_name = 'manual2/data/old_observation.json'
        self.current_name = 'manual2/data/observation/result.json'
        self.current = {
            'source_sha256': '1' * 64,
            'records': [{'source/with~escape': '2' * 64, 'value': '2/3'}],
            'covariance': [[1, 0], [0, 2]],
            'physical_status': 'unresolved',
        }
        original = deepcopy(self.current)
        original['source_sha256'] = '0' * 64
        original['records'][0]['source/with~escape'] = '0' * 64
        invariant = {
            'source_sha256': None,
            'records': [{'source/with~escape': None, 'value': '2/3'}],
            'covariance': [[1, 0], [0, 2]],
            'physical_status': 'unresolved',
        }
        self.baseline = {
            'schema_version': 1,
            'head': 'synthetic-scientific-source',
            'tree': 'synthetic-tree',
            'scope': 'Synthetic successor boundary test; no physical claim.',
            'files': {self.old_name: self.digest(original)},
            'relocations': {self.old_name: self.current_name},
            'source_successors': {self.old_name: {
                'original_sha256': self.digest(original),
                'current_sha256': self.digest(self.current),
                'changed_metadata_pointers': [
                    '/source_sha256', '/records/0/source~1with~0escape'],
                'scientific_payload_sha256': self.digest(invariant),
            }},
        }
        self.write_current()
        self.bind_fixture()

    @staticmethod
    def encode(value):
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(',', ':'), allow_nan=False).encode()

    @classmethod
    def digest(cls, value):
        return hashlib.sha256(cls.encode(value)).hexdigest()

    def write_current(self):
        path = self.root / self.current_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.encode(self.current))

    def bind_fixture(self):
        path = self.root / preservation.BASELINE
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = self.encode(self.baseline)
        path.write_bytes(raw)
        self.authority = hashlib.sha256(raw).hexdigest()

    def verify_fixture(self):
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob('*') if p.is_file()}
        try:
            with patch.object(preservation, 'BASELINE_SHA256', self.authority):
                return preservation.verify(self.root)
        finally:
            after = {p.relative_to(self.root): p.read_bytes()
                     for p in self.root.rglob('*') if p.is_file()}
            self.assertEqual(after, before, 'Preservation verifier repaired its inputs')

    def test_exact_successor_relocation_and_escaped_leaf_are_admitted(self):
        self.assertFalse((self.root / self.old_name).exists())
        report = self.verify_fixture()
        self.assertEqual(report['checked_files'], 1)
        self.assertEqual(report['byte_preserved_files'], 0)
        self.assertEqual(report['source_metadata_successors'], 1)

    def test_unapproved_metadata_change_still_rejects_exact_current_bytes(self):
        self.current['source_sha256'] = '3' * 64
        self.write_current()
        with self.assertRaisesRegex(ValueError, 'frozen pre-campaign input'):
            self.verify_fixture()

    def test_scientific_changes_reject_after_current_digest_rebinding(self):
        original = deepcopy(self.current)
        for mutation in ('number', 'dimension', 'new_field', 'status'):
            with self.subTest(mutation=mutation):
                self.current = deepcopy(original)
                if mutation == 'number':
                    self.current['covariance'][1][1] = 3
                elif mutation == 'dimension':
                    self.current['covariance'].append([0, 0])
                elif mutation == 'new_field':
                    self.current['uncertainty'] = 0
                else:
                    self.current['physical_status'] = 'established'
                self.write_current()
                self.baseline['source_successors'][self.old_name]['current_sha256'] = self.digest(self.current)
                self.bind_fixture()
                with self.assertRaisesRegex(ValueError, 'scientific successor payload'):
                    self.verify_fixture()

    def test_metadata_mask_cannot_supply_a_missing_leaf(self):
        del self.current['source_sha256']
        self.write_current()
        self.baseline['source_successors'][self.old_name]['current_sha256'] = self.digest(self.current)
        self.bind_fixture()
        with self.assertRaises(ValueError):
            self.verify_fixture()

    def test_metadata_mask_rejects_non_sha256_values_and_subtrees(self):
        original = deepcopy(self.current)
        for replacement in (7, None, {'physical_value': 7}, ['2' * 64], 'F' * 64, 'short'):
            with self.subTest(replacement=replacement):
                self.current = deepcopy(original)
                self.current['source_sha256'] = replacement
                self.write_current()
                self.baseline['source_successors'][self.old_name]['current_sha256'] = self.digest(self.current)
                self.bind_fixture()
                with self.assertRaises(ValueError):
                    self.verify_fixture()

    def test_metadata_mask_requires_unique_canonical_pointers(self):
        original = deepcopy(self.baseline['source_successors'][self.old_name])
        for pointers in (
                ['source_sha256'],
                original['changed_metadata_pointers'] + ['/source_sha256'],
                ['/source_sha256', '/records/-1/source~1with~0escape'],
                ['/source_sha256', '/records/00/source~1with~0escape']):
            with self.subTest(pointers=pointers):
                successor = deepcopy(original)
                successor['changed_metadata_pointers'] = pointers
                self.baseline['source_successors'][self.old_name] = successor
                self.bind_fixture()
                with self.assertRaises(ValueError):
                    self.verify_fixture()

    def test_historical_identity_and_successor_membership_remain_bound(self):
        original = deepcopy(self.baseline)
        for mutation in ('historical_identity', 'unbound_successor', 'unbound_relocation'):
            with self.subTest(mutation=mutation):
                self.baseline = deepcopy(original)
                if mutation == 'historical_identity':
                    self.baseline['source_successors'][self.old_name]['original_sha256'] = '9' * 64
                elif mutation == 'unbound_successor':
                    self.baseline['source_successors']['not-bound.json'] = deepcopy(
                        self.baseline['source_successors'][self.old_name])
                else:
                    self.baseline['relocations']['not-bound.json'] = self.current_name
                self.bind_fixture()
                with self.assertRaises(ValueError):
                    self.verify_fixture()


if __name__ == '__main__':
    unittest.main()
