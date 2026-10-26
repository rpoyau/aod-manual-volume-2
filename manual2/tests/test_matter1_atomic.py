"""Atomic-map obstruction, external benchmark and persisted hostile mutations.

Passing tests establishes the stated diagnostics and data separation, not an
atomic prediction. Both optimized and normal verifier processes inspect the
actual mutated files without writing repairs.
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
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO/'manual2/scripts'
sys.path.insert(0, str(SCRIPTS))
import matter1_atomic as a


def snapshot(root):
    return {str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class AtomicTests(unittest.TestCase):
    def fixture(self, temp):
        root = Path(temp)/'repo'
        shutil.copytree(REPO/'sections', root/'sections')
        for folder in ('folding', 'atomic'):
            shutil.copytree(REPO/'manual2/data/m1'/folder, root/'manual2/data/m1'/folder)
        return root

    def cli(self, root, command='verify', optimized=False, extra=()):
        return subprocess.run([sys.executable, '-B']+(['-O'] if optimized else [])+
                              [str(SCRIPTS/f'{command}_matter1_atomic.py'), '--root', str(root), *map(str, extra)],
                              capture_output=True, text=True)

    def test_PRED_01_atomic_point_is_underdetermined_with_executable_witness(self):
        result = a.predict(REPO)
        self.assertEqual(result['status'], 'prediction_objective_incomplete_observation_map_underdetermined')
        self.assertTrue(all(result['atomic_prediction'][k] is None for k in ('ratio', 'frequency_hz', 'transition_period_seconds', 'standard_uncertainty_hz')))
        rows = result['countermodels']
        self.assertEqual([r['mapped_ratio'] for r in rows], ['6/5', '12/5', '2/5', '4/5'])
        self.assertEqual(rows[0]['trace_sha256'], rows[1]['trace_sha256'])
        self.assertTrue(all(r['Cs_gain'] == '1' for r in rows))
        self.assertEqual(rows[0]['conditional_unit_conversion']['frequency_hz'], '11031158124')
        # Symbolic family: an arbitrary positive desired ratio has a free lambda.
        # This explicitly demonstrates missing determination, not candidate selection.
        r = Q(rows[0]['finite_cadence_ratio'])
        for desired in (Q(1, 7), Q(2), Q(7, 3)):
            lam = desired/r-1
            self.assertGreater(lam, -1)
            self.assertEqual(r*(1+lam), desired)

    def test_PRED_02_Cs_scale_and_no_isotope_specific_fit(self):
        p = a.predict(REPO)
        self.assertEqual(p['calibration']['reference_hz'], '9192631770')
        self.assertEqual(p['calibration']['fitted_parameters'], [])
        contract = a.read_json(REPO/a.SUBDIR/'model_contract.json')
        self.assertEqual(contract['map_family']['selection_status'], 'no_member_selected_as_atomic_model')
        for row in p['countermodels']:
            conversion = row['conditional_unit_conversion']
            self.assertEqual(Q(conversion['frequency_hz']), Q(row['mapped_ratio'])*a.CS_HZ)
            self.assertEqual(Q(conversion['frequency_hz'])*Q(conversion['transition_period_seconds']), 1)
            self.assertEqual(conversion['uncertainty_status'], 'partial')

    def test_PRED_03_prediction_succeeds_without_any_target_or_benchmark_file(self):
        expected = a.canonical(a.predict(REPO))
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            for name in ('evaluation_target.json', 'benchmark_inputs.json'):
                (root/a.SUBDIR/name).unlink()
            before = snapshot(root)
            for opt in (False, True):
                run = self.cli(root, 'predict', opt)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(run.stdout.encode(), expected)
                self.assertEqual(snapshot(root), before)

    def test_PRED_03_predictor_does_not_read_external_target_paths(self):
        read = Path.read_bytes
        seen = []
        def audited(path):
            seen.append(str(path))
            if any(token in str(path) for token in ('evaluation_target', 'benchmark_inputs', '/hyperfine/')):
                raise AssertionError('Predictor read evaluation/benchmark data')
            return read(path)
        with patch.object(Path, 'read_bytes', audited):
            a.predict(REPO)
        self.assertTrue(any('model_contract' in path for path in seen))

    def test_PRED_04_target_intervention_changes_only_bound_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            predicted = self.cli(root, 'predict')
            self.assertEqual(predicted.returncode, 0, predicted.stderr)
            p = json.loads(predicted.stdout)
            first = self.cli(root, 'compare')
            self.assertEqual(first.returncode, 0, first.stderr)
            target = a.default_target()
            target.update(classification='synthetic_evaluation_mutation', frequency_hz=str(Q(target['frequency_hz'])+1))
            altered = Path(temp)/'altered_target.json'
            altered.write_bytes(a.canonical(target))
            second = self.cli(root, 'compare', extra=('--target', altered))
            self.assertEqual(second.returncode, 0, second.stderr)
            c1, c2 = map(json.loads, (first.stdout, second.stdout))
            self.assertEqual(c1['prediction_sha256'], c2['prediction_sha256'])
            self.assertNotEqual(c1['evaluation_sha256'], c2['evaluation_sha256'])
            self.assertEqual(Q(c1['rows'][0]['residual_hz'])-Q(c2['rows'][0]['residual_hz']), 1)
            self.assertEqual(json.loads(self.cli(root, 'predict').stdout), p)
            self.assertIsNone(c1['atomic_empirical_score'])
            self.assertIsNone(c1['prediction_measurement_covariance_hz2'])
            self.assertTrue(all(r['standardized_residual'] is None for r in c1['rows']))

    def test_PRED_05_sequential_intervention_changes_diagnostic_observable(self):
        from matter1_stateful import prepare
        dynamics = prepare(REPO)
        left, right = dynamics['baseline_trace'], dynamics['early_loss_trace']
        self.assertEqual([r for r in left['cut_records'] if r['cut']<40],
                         [r for r in right['cut_records'] if r['cut']<40])
        rows = a.predict(REPO)['countermodels']
        self.assertEqual(Q(rows[0]['mapped_ratio']), 3*Q(rows[2]['mapped_ratio']))
        self.assertEqual(rows[0]['lambda'], rows[2]['lambda'])
        self.assertNotEqual(rows[0]['trace_sha256'], rows[2]['trace_sha256'])

    def test_conventional_hamiltonian_matches_independent_eigensolver(self):
        import numpy as np
        result = a.benchmark(a.default_benchmark())
        self.assertEqual(len(result['rows']), 10)
        for row in result['rows']:
            matrix = np.array([[float(Q(x)) for x in line] for line in row['matrix_hz']])
            eigen = np.linalg.eigvalsh(matrix)
            self.assertAlmostEqual(eigen[1]-eigen[0], float(row['frequency_hz']), delta=4e-6)
            self.assertIsNone(row['complete_standard_uncertainty_hz'])
        for isotope in ('H-1', 'Cs-133'):
            rows = [r for r in result['rows'] if r['isotope']==isotope]
            self.assertEqual(rows[0]['frequency_hz'], rows[4]['frequency_hz'])
            self.assertEqual(rows[1]['frequency_hz'], rows[3]['frequency_hz'])
            self.assertEqual(Q(rows[2]['shift_hz']), 0)
            self.assertGreater(Q(rows[4]['shift_hz']), 0)

    def test_conventional_weak_field_limit_is_quadratic(self):
        model = a.default_benchmark()
        beta = 2*Q(model['mu_B_over_h_hz_per_tesla'])
        for atom in model['species']:
            delta = Q(atom['splitting_hz'])
            b = Q(1, 10**6)
            matrix = a.clock_block(delta, atom['I'], beta, b)
            square = (matrix[0][0]-matrix[1][1])**2+4*matrix[0][1]**2
            self.assertEqual(square-delta**2, beta**2*b**2)
            self.assertGreater(beta**2/(2*delta), 0)

    def test_verifier_and_explicit_generation_are_read_only_or_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            before = snapshot(root)
            for opt in (False, True):
                r = self.cli(root, optimized=opt, extra=('--check-data',))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(snapshot(root), before)
            output = Path(temp)/'generated'
            run = self.cli(root, 'generate', extra=('--output-root', output))
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(snapshot(root), before)
            self.assertEqual(set(str(p.relative_to(output/a.SUBDIR)) for p in (output/a.SUBDIR).iterdir()), set(a.OUTPUTS))
            for name in a.OUTPUTS:
                self.assertEqual((root/a.SUBDIR/name).read_bytes(), (output/a.SUBDIR/name).read_bytes())

    def test_persisted_hostile_mutations_rejected_in_both_modes(self):
        probes = [
            ('model_contract.json', ['admission_status'], 'admitted'),
            ('model_contract.json', ['native_configuration_status'], 'complete'),
            ('model_contract.json', ['state_assignment_status'], 'physical_atomic_states'),
            ('model_contract.json', ['target_policy'], 'read_target'),
            ('model_contract.json', ['map_family', 'selection_status'], 'selected_by_H_fit'),
            ('model_contract.json', ['map_family', 'witness_values'], ['0', '0']),
            ('model_contract.json', ['external_states', 0, 'z'], 55),
            ('model_contract.json', ['reference', 'frequency_hz'], '9192631771'),
            ('model_contract.json', ['source_bindings', 0, 'sha256'], 'forged'),
            ('model_contract.json', ['exposure'], 'blind'),
            ('model_contract.json', ['dependency_gates', 'P4a'], 'native_admitted'),
            ('model_contract.json', ['dependency_gates', 'P2'], 'complete'),
            ('model_contract.json', ['dependency_gates', 'P3'], 'complete'),
            ('evaluation_target.json', ['standard_uncertainty_hz'], '0.02'),
            ('evaluation_target.json', ['prediction_measurement_covariance_hz2'], '0'),
            ('evaluation_target.json', ['classification'], 'independent_test'),
            ('benchmark_inputs.json', ['classification'], 'AOD_prediction'),
            ('benchmark_inputs.json', ['species', 0, 'splitting_role'], 'derived'),
            ('benchmark_inputs.json', ['uncertainty_status'], 'complete'),
            ('benchmark_inputs.json', ['mu_B_over_h_standard_uncertainty'], '0'),
            ('prediction.json', ['atomic_prediction', 'ratio'], '1/7'),
            ('prediction.json', ['atomic_prediction', 'admission_status'], 'admitted'),
            ('prediction.json', ['countermodels', 0, 'classification'], 'atomic_prediction'),
            ('prediction.json', ['countermodels', 0, 'conditional_unit_conversion', 'frequency_hz'], '1420405751.768'),
            ('prediction.json', ['target_access'], 'read'),
            ('prediction.json', ['calibration_sha256'], 'forged'),
            ('prediction.json', ['engine_bindings', 0, 'sha256'], 'forged'),
            ('comparison.json', ['atomic_empirical_score'], '0'),
            ('comparison.json', ['prediction_sha256'], 'forged'),
            ('comparison.json', ['rows', 0, 'residual_hz'], '0'),
            ('comparison.json', ['frequency_period_tests_independent'], True),
            ('benchmark.json', ['rows', 0, 'frequency_hz'], '0'),
            ('obligations.json', ['objective_status'], 'complete'),
            ('atomic_report.json', ['PRED_01'], 'passed_atomic_prediction'),
        ]
        for name, path, value in probes:
            for opt in (False, True):
                with self.subTest(name=name, path=path, optimized=opt), tempfile.TemporaryDirectory() as temp:
                    root = self.fixture(temp)
                    target = root/a.SUBDIR/name
                    obj = json.loads(target.read_bytes()); cur = obj
                    for key in path[:-1]: cur = cur[key]
                    cur[path[-1]] = value
                    target.write_bytes(a.canonical(obj))
                    before = snapshot(root)
                    run = self.cli(root, optimized=opt)
                    self.assertNotEqual(run.returncode, 0)
                    self.assertIn('atomic verification failed:', run.stderr)
                    self.assertEqual(snapshot(root), before)
                    if name in a.INPUTS:
                        gen = self.cli(root, 'generate', optimized=opt)
                        self.assertNotEqual(gen.returncode, 0)
                        self.assertEqual(snapshot(root), before)

    def test_missing_consumed_status_and_unknown_flags_fail(self):
        for name, field in [('model_contract.json', 'status'), ('model_contract.json', 'admission_status'),
                            ('evaluation_target.json', 'covariance_status'), ('benchmark_inputs.json', 'field_status'),
                            ('prediction.json', 'status'), ('comparison.json', 'classification')]:
            for opt in (False, True):
                with self.subTest(name=name, field=field, optimized=opt), tempfile.TemporaryDirectory() as temp:
                    root = self.fixture(temp); file = root/a.SUBDIR/name
                    obj = a.read_json(file); del obj[field]; file.write_bytes(a.canonical(obj))
                    before = snapshot(root)
                    self.assertNotEqual(self.cli(root, optimized=opt).returncode, 0)
                    self.assertEqual(snapshot(root), before)
        self.assertNotEqual(self.cli(REPO, extra=('--unknown-flag',)).returncode, 0)


if __name__ == '__main__':
    unittest.main()
