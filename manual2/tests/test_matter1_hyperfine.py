"""Persisted hostile probes of the external pilot and pending atomic map.

These tests establish data/claim guard behavior, not a native atomic prediction.
Every mutation is written to disk before the real verifier runs, normally and
under -O, and the complete disposable input tree is checked for side effects.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / 'manual2/scripts'
sys.path.insert(0, str(SCRIPTS))
from matter1_hyperfine import CS_ID, H_ID, INPUTS, OUTPUT, SUBDIR, ValidationError, evaluate


def snapshot(root):
    return {str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size, p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


def set_path(obj, path, value):
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


class HyperfineTests(unittest.TestCase):
    def fixture(self, parent):
        root = Path(parent) / 'repo'
        shutil.copytree(REPO / SUBDIR, root / SUBDIR)
        source = REPO / 'manual2/data/m1/matter1_elements_1_118_ledger.csv'
        shutil.copy2(source, root / 'manual2/data/m1' / source.name)
        return root

    def run_cli(self, root, optimized=False, generate=False, extra=()):
        script = 'generate_matter1_hyperfine.py' if generate else 'verify_matter1_hyperfine.py'
        return subprocess.run([sys.executable, '-B'] + (['-O'] if optimized else []) +
                              [str(SCRIPTS / script), '--root', str(root), *extra], capture_output=True, text=True)

    def test_P4_01_source_inventory_preserves_atomic_identity(self):
        report = evaluate(REPO)
        self.assertEqual((report['isotope_count'], report['state_count'], report['transition_count']), (2, 4, 2))
        self.assertEqual(report['required_stages'], ['P4a', 'P2', 'P3'])
        self.assertEqual(report['P4a_status'], 'inventory_verified')
        self.assertEqual(report['atomic_native_admission_status'], 'pending')
        self.assertEqual(report['atomic_native_execution_status'], 'not_executed')
        self.assertEqual(report['empirical_status'], 'not_compared')
        self.assertIsNone(report['predicted_frequency_ratio'])
        self.assertIsNone(report['empirical_score'])

    def test_P5_03_ratio_is_published_measurement_transcription(self):
        report = evaluate(REPO)
        ratio = report['measured_ratio']
        self.assertEqual(ratio['transcribed_input_fraction'], '177550718971/1149078971250')
        self.assertEqual(ratio['decimal_display'], '0.1545156803086000')
        self.assertEqual(ratio['reported_standard_uncertainty_display'], '2.1757E-13')
        self.assertEqual(report['classification'], 'external_retrospective_reference_arithmetic')

    def test_P5_04_success_verifier_read_only_normal_and_optimized(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            before = snapshot(root)
            for optimized in (False, True):
                result = self.run_cli(root, optimized)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(snapshot(root), before)

    def test_P4_P5_F_hostile_persisted_mutations(self):
        # IDs state the acceptance scope. A rejection never proves native dynamics.
        probes = [
            ('P4-01 isotope changed', 'target_inventory.json', ['states', 1, 'isotope_id'], 'atom:Z055:A133:q0'),
            ('P4-01 same state twice', 'target_inventory.json', ['transitions', 0, 'state_ids'], ['atom:Z001:A001:q0:ground:F0:mF0'] * 2),
            ('P4-01 element alias', 'target_inventory.json', ['isotopes', 0, 'element_reference_id'], 'matter1:reference:Z055:A133'),
            ('P4-01 invalid charge', 'target_inventory.json', ['isotopes', 0, 'charge'], 1),
            ('P4-01 invalid quantum state', 'target_inventory.json', ['states', 0, 'm_F'], '2'),
            ('P4-01 missing P2', 'observation_map.json', ['required_stages'], ['P4a', 'P3']),
            ('P4-01 missing P3', 'observation_map.json', ['required_stages'], ['P4a', 'P2']),
            ('P4-01 missing inventory', 'observation_map.json', ['required_stages'], ['P2', 'P3']),
            ('P4-02 sigma is mF', 'observation_map.json', ['spin_role_identification'], 'sigma_equals_mF'),
            ('P4-03 detection is cycles', 'target_inventory.json', ['clock_operation', 'counted_observable'], 'detected_state_populations'),
            ('P4-03 wrong frequency observable', 'target_inventory.json', ['transitions', 0, 'observable'], 'population_detection_count'),
            ('P4-03 wrong native recurrence map', 'observation_map.json', ['recurrence_observable_map', 'external_observable'], 'population_detection_count'),
            ('P5-01 retroactive freeze', 'target_exposure.json', ['classification'], 'blind_prediction'),
            ('P5-01 erased exposure', 'target_exposure.json', ['decision_history', 0, 'target_visible'], False),
            ('P5-01 target selection access', 'target_exposure.json', ['native_target_access_policy'], 'allowed'),
            ('P5-01 invented independence', 'target_exposure.json', ['independence_evidence_status'], 'established'),
            ('P5-02 calibrant reused', 'target_exposure.json', ['calibrant_is_held_out'], True),
            ('P5-03 OCR uncertainty', 'target_inventory.json', ['transitions', 0, 'standard_uncertainty_hz'], '0.02'),
            ('P5-03 omitted corrections', 'target_inventory.json', ['transitions', 0, 'corrections'], []),
            ('P5-03 ignored covariance', 'target_inventory.json', ['transitions', 0, 'covariance_status'], 'independent'),
            ('P5-03 unknown covariance zero', 'target_inventory.json', ['transitions', 0, 'covariance_hz2'], '0'),
            ('P5-03 realization zero', 'target_inventory.json', ['transitions', 1, 'realization_uncertainty_hz'], '0'),
            ('P5-03 reference replaced', 'target_inventory.json', ['transitions', 0, 'reference_transition_id'], H_ID),
            ('P5-06 source status promotion', 'target_inventory.json', ['sources', 0, 'status'], 'native_admission'),
            ('P5-06 state status promotion', 'target_inventory.json', ['states', 0, 'quantum_number_status'], 'native_admitted'),
            ('P5-06 admission promotion', 'observation_map.json', ['native_admission_status'], 'admitted'),
            ('P5-06 execution promotion', 'observation_map.json', ['native_execution_status'], 'executed'),
            ('P5-06 empirical promotion', 'observation_map.json', ['empirical_status'], 'agrees'),
            ('P5-06 phase promotion', 'observation_map.json', ['phase_map_status'], 'complete'),
            ('F-05 unbound before state', 'observation_map.json', ['configuration_bindings', 0, 'native_before_id'], 'invented:before'),
            ('F-05 mismatched frozen model', 'observation_map.json', ['configuration_bindings', 1, 'native_model_id'], 'other-model'),
            ('F-06 per-line fit', 'target_exposure.json', ['per_line_fitting'], True),
            ('F-06 per-line policy', 'observation_map.json', ['model_policy'], 'fit_each_line'),
            ('F-07 detection promoted shedding', 'observation_map.json', ['transferred_radiation_map', 'sheddic_output_id'], 'detected-photon'),
            ('F-07 fake transfer', 'observation_map.json', ['transferred_radiation_map', 'status'], 'executed'),
            ('P5-06 fake predicted ratio', 'observation_map.json', ['predicted_frequency_ratio'], '0.1545156803086000'),
            ('P5-06 fake score', 'observation_map.json', ['empirical_score'], '0'),
        ]
        for label, filename, path, value in probes:
            for optimized in (False, True):
                with self.subTest(probe=label, optimized=optimized), tempfile.TemporaryDirectory() as temp:
                    root = self.fixture(temp)
                    target = root / SUBDIR / filename
                    obj = json.loads(target.read_bytes())
                    set_path(obj, path, value)
                    target.write_text(json.dumps(obj) + '\n')
                    before = snapshot(root)
                    result = self.run_cli(root, optimized)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn('verification failed:', result.stderr)
                    self.assertEqual(snapshot(root), before)
                    # Regenerating a report must not launder an invalid input.
                    generation = self.run_cli(root, optimized, generate=True)
                    self.assertNotEqual(generation.returncode, 0, generation.stdout)
                    self.assertEqual(snapshot(root), before)

    def test_P5_06_missing_consumed_status_rejected(self):
        targets = [
            ('target_inventory.json', [], 'inventory_status'),
            ('target_inventory.json', ['sources', 0], 'transcription_status'),
            ('target_inventory.json', ['transitions', 0], 'covariance_status'),
            ('target_inventory.json', ['transitions', 1], 'realization_uncertainty_status'),
            ('target_inventory.json', ['clock_operation'], 'native_closure_identification'),
            ('target_exposure.json', [], 'exposure_status'),
            ('target_exposure.json', [], 'model_selection_status'),
            ('observation_map.json', [], 'map_status'),
            ('observation_map.json', [], 'native_admission_status'),
            ('observation_map.json', [], 'native_execution_status'),
            ('observation_map.json', [], 'empirical_status'),
            ('observation_map.json', ['recurrence_observable_map'], 'binding_status'),
            ('observation_map.json', ['transferred_radiation_map'], 'status'),
        ]
        for filename, path, field in targets:
            for optimized in (False, True):
                with self.subTest(file=filename, field=field, optimized=optimized), tempfile.TemporaryDirectory() as temp:
                    root = self.fixture(temp)
                    target = root / SUBDIR / filename
                    obj = json.loads(target.read_bytes())
                    cursor = obj
                    for key in path:
                        cursor = cursor[key]
                    del cursor[field]
                    target.write_text(json.dumps(obj) + '\n')
                    before = snapshot(root)
                    result = self.run_cli(root, optimized)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertEqual(snapshot(root), before)

    def test_P5_04_report_evidence_and_cli_corruption_rejected(self):
        for name in (OUTPUT, 'sources/hellwig1970-page200.png'):
            for optimized in (False, True):
                with self.subTest(file=name, optimized=optimized), tempfile.TemporaryDirectory() as temp:
                    root = self.fixture(temp)
                    target = root / SUBDIR / name
                    target.write_bytes(target.read_bytes() + b'corruption')
                    before = snapshot(root)
                    result = self.run_cli(root, optimized)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(snapshot(root), before)
        result = self.run_cli(REPO, extra=['--unknown-flag'])
        self.assertNotEqual(result.returncode, 0)

    def test_explicit_generation_into_disposable_output_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            before = snapshot(root)
            output = Path(temp) / 'generated'
            result = self.run_cli(root, generate=True, extra=['--output-root', str(output)])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(snapshot(root), before)
            self.assertEqual((output / SUBDIR / OUTPUT).read_bytes(), (root / SUBDIR / OUTPUT).read_bytes())
            self.assertEqual(list(p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()), [(SUBDIR / OUTPUT).as_posix()])


if __name__ == '__main__':
    unittest.main()
