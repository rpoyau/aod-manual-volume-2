"""Exact imported dependency, historical authority and nonlinear hostile checks."""
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
sys.path.insert(0, str(ROOT / 'manual2/scripts'))
sys.path.insert(0, str(ROOT / 'scripts'))
from matter1_m3 import mapping, verify_vendor
from matter1_foundation import binding, legacy_source_bytes, legacy_engine_digest, PRIOR_ARCHIVE
from publication_support import verify_foundation
from manual2.tests.foundation_fixture import copy_foundation_receipts


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


class M3MigrationTests(unittest.TestCase):
    def fixture(self, temp):
        root = Path(temp)
        active = json.loads((ROOT / 'manual2/evidence/foundation-source.json').read_bytes())
        for name in active['files']:
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, p)
        copy_foundation_receipts(ROOT, root)
        return root

    def test_full_m3_binding_and_reviewed_source_inventory(self):
        active = verify_foundation(ROOT)
        self.assertEqual(active['upstream_head'], '71cbcf7e637ababcde3b2e073fb4ceec4b1681b9')
        self.assertEqual(active['upstream_tree'], '3ab04df3793beda481b4fb7ed0d628ba6765da70')
        self.assertEqual(active['active_main_pages'], 70)
        self.assertEqual(active['authority_status'], 'reviewed_local_PR_43_candidate_at_binding')
        migration = json.loads((ROOT / active['reviewed_rebind']).read_bytes())
        self.assertEqual(len(migration['files']), 7)
        self.assertTrue(all(row['before_sha256'] is not None for row in migration['files']))
        self.assertEqual(active['active_text_sha256'], migration['reviewed_main_render']['text_sha256'])
        migration = json.loads((ROOT / migration['previous_rebind']).read_bytes())
        self.assertEqual(len(migration['files']), 12)
        self.assertEqual(sum(row['before_sha256'] is not None for row in migration['files']), 11)

    def test_newly_changed_sources_retain_original_authority(self):
        for name in ('appendices/B_curling_curls.tex', 'sections/04_cut_running_fractal_tesseract.tex'):
            with self.subTest(name=name):
                active, historic = binding(ROOT)
                self.assertNotEqual(active['files'][name], historic['files'][name])
                self.assertEqual(hashlib.sha256(legacy_source_bytes(ROOT, name)).hexdigest(),
                                 historic['files'][name])
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.fixture(tmp)
                    p = root / PRIOR_ARCHIVE / name
                    p.write_bytes(p.read_bytes() + b'\n% hostile prior source\n')
                    before = snapshot(root)
                    with self.assertRaisesRegex(ValueError, 'archived Main source changed'):
                        legacy_source_bytes(root, name)
                    self.assertEqual(snapshot(root), before)

    def test_each_successor_receipt_and_prior_manifest_is_pinned(self):
        for name in ('manual2/evidence/m3-source-rebind.json',
                     'manual2/evidence/m3-source-rebind-2026-11-08.json',
                     str(PRIOR_ARCHIVE / 'manual2/evidence/foundation-source.json')):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = self.fixture(tmp)
                p = root / name
                p.write_bytes(p.read_bytes() + b'\n')
                before = snapshot(root)
                with self.assertRaisesRegex(ValueError, 'Preservation:'):
                    binding(root)
                self.assertEqual(snapshot(root), before)

    def test_archived_authority_and_current_source_are_both_required(self):
        name = 'sections/06_wave_state_relational_time.tex'
        old = legacy_source_bytes(ROOT, name)
        self.assertEqual(hashlib.sha256(old).hexdigest(), 'bbe6e0b7917940a6320b79be467ffbe8591ca1ec7b8aa0ffe1626cee320de2bb')
        for prefix in ('', 'manual2/evidence/pre-m3-main/'):
            with self.subTest(prefix=prefix), tempfile.TemporaryDirectory() as tmp:
                root = self.fixture(tmp)
                p = root / (prefix + name)
                p.write_bytes(p.read_bytes() + b'\n% hostile edit\n')
                before = snapshot(root)
                with self.assertRaisesRegex(ValueError, 'source changed'):
                    legacy_source_bytes(root, name)
                self.assertEqual(snapshot(root), before)

    def test_resealed_successor_allowlist_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            p = root / 'manual2/evidence/m3-source-rebind-2026-11-08.json'
            record = json.loads(p.read_bytes())
            record['files'][0]['after_sha256'] = '0' * 64
            p.write_text(json.dumps(record))
            manifest = root / 'manual2/evidence/foundation-source.json'
            active = json.loads(manifest.read_bytes())
            active['reviewed_rebind_sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(active))
            before = snapshot(root)
            with self.assertRaisesRegex(ValueError, 'unreviewed active foundation'):
                binding(root)
            self.assertEqual(snapshot(root), before)

    def test_resealed_source_and_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            name = 'sections/07_cell_measures_mappings.tex'
            p = root / name
            p.write_bytes(p.read_bytes() + b'\n% hostile ontology\n')
            p = root / 'manual2/evidence/foundation-source.json'
            record = json.loads(p.read_bytes())
            record['files'][name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
            record['source_digest'] = hashlib.sha256(json.dumps(record['files'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            p.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'unreviewed active foundation'):
                verify_foundation(root)

    def test_actual_adapter_and_original_engine_both_verified(self):
        self.assertEqual(legacy_engine_digest(ROOT, 'manual2/scripts/matter1_atomic.py'),
                         '00fc9ee7d37e39f67a60dcc93398d0b7a7511ef9e66c4f3d0ab9ede144ce3a12')
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            p = root / 'manual2/scripts/matter1_atomic.py'
            shutil.copy2(ROOT / 'manual2/scripts/matter1_atomic.py', p)
            p.write_bytes(p.read_bytes() + b'\n# altered executor\n')
            with self.assertRaisesRegex(ValueError, 'current adapter changed'):
                legacy_engine_digest(root, 'manual2/scripts/matter1_atomic.py')

    def test_vendor_edited_source_and_resealed_binding_rejected(self):
        self.assertEqual(verify_vendor(ROOT)['upstream_head'], '71cbcf7e637ababcde3b2e073fb4ceec4b1681b9')
        for reseal in (False, True):
            with self.subTest(reseal=reseal), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                dest = root / 'manual2/vendor/aod_m3'
                shutil.copytree(ROOT / 'manual2/vendor/aod_m3', dest)
                code = dest / 'current/aod_mapping_error.py'
                code.write_bytes(code.read_bytes() + b'\n# hostile modification\n')
                if reseal:
                    p = dest / 'binding.json'
                    record = json.loads(p.read_bytes())
                    record['files']['current/aod_mapping_error.py']['sha256'] = hashlib.sha256(code.read_bytes()).hexdigest()
                    p.write_text(json.dumps(record))
                before = snapshot(root)
                with self.assertRaisesRegex(ValueError, 'M3 vendor'):
                    mapping(root)
                self.assertEqual(snapshot(root), before)

    def test_prior_vendor_binding_and_sources_remain_required(self):
        for name in ('binding.json', 'current/M3_MATHEMATICAL_BINDINGS.json'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = self.fixture(tmp)
                shutil.copytree(ROOT / 'manual2/vendor/aod_m3', root / 'manual2/vendor/aod_m3')
                p = root / PRIOR_ARCHIVE / 'manual2/vendor/aod_m3' / name
                p.write_bytes(p.read_bytes() + b'\n')
                before = snapshot(root)
                with self.assertRaisesRegex(ValueError, 'M3 prior vendor'):
                    verify_vendor(root)
                self.assertEqual(snapshot(root), before)

    def test_required_upstream_absence_cannot_become_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            for optimized in (False, True):
                command = [sys.executable, '-B'] + (['-O'] if optimized else [])
                command += [str(ROOT / 'scripts/check_matter1_m3_consumer.py'), '--upstream-root', tmp]
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('M3 consumer integration failed', result.stderr)
                self.assertNotIn('PASS_REQUIRED_M3_CONSUMER', result.stdout)


class M3FiniteLawTests(unittest.TestCase):
    def setUp(self):
        self.m = mapping(ROOT)

    def test_anticorrelated_product_retains_nonlinear_variance(self):
        expr = ['mul', ['add', ['parameter', 'one'], ['input', 'd']],
                ['sub', ['parameter', 'one'], ['mul', ['parameter', 'a'], ['input', 'd']]]]
        result = self.m.propagate(expr, ['d'], {'one': {'value': '1'}, 'a': {'value': '999/1000'}},
                                  support=[('1/4', {'d': '-1/100'}), ('1/2', {'d': '0'}), ('1/4', {'d': '1/100'})])
        self.assertEqual(Q(result['output_variance']), Q(1018001, 400000000000000))
        self.assertEqual(Q(result['output_variance']) / Q(result['linearized_variance_diagnostic']), Q('50.90005'))
        self.assertNotEqual(result['mean_shift'], '0')
        self.assertEqual(result['uncertainty_status'], 'exact_for_declared_joint_law')

    def test_interval_zero_derivative_is_not_zero_exact_variance(self):
        expr = ['add', ['div', ['parameter', 'one'], ['add', ['parameter', 'one'], ['input', 'd']]], ['input', 'd']]
        result = self.m.propagate(expr, ['d'], {'one': {'value': '1'}},
                                  support=[('1/2', {'d': '-1/1000'}), ('1/2', {'d': '1/1000'})])
        self.assertEqual(result['linearized_variance_diagnostic'], '0')
        self.assertEqual(Q(result['output_variance']), Q(1, 999998000001000000))

    def test_covariance_only_nonlinear_remains_partial(self):
        result = self.m.propagate(['mul', ['input', 'x'], ['input', 'x']], ['x'], {},
                                  means={'x': '1'}, covariance=[['1/100000000']])
        self.assertEqual(result['uncertainty_status'], 'partial')
        self.assertIsNone(result['output_variance'])

    def test_exact_affine_and_invalid_probability_controls(self):
        result = self.m.propagate(['input', 'x'], ['x'], {}, means={'x': '1'}, covariance=[['2']])
        self.assertEqual(result['output_variance'], '2')
        for support in ([('1/3', {'x': '0'}), ('1/3', {'x': '1'})], [('2', {'x': '0'}), ('-1', {'x': '1'})]):
            with self.assertRaises(ValueError):
                self.m.propagate(['input', 'x'], ['x'], {}, support=support)


if __name__ == '__main__':
    unittest.main()
