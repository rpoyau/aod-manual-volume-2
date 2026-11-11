"""Paired preparation inventory, trusted uncertainty and target separation."""
from copy import deepcopy
from fractions import Fraction as Q
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'manual2/scripts'))
import matter1_preparation_workflow as w
import matter1_coupled_preparations as c
import matter1_m3_producer as p


class PreparationWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modules = p.load(ROOT)
        cls.matrix = w.reference_preparations(ROOT)
        cls.ensemble = c.enumerate_paths(c.default_config(1, 1, 1, rounds=1, seed=20261111), ROOT)

    def test_all_reference_pairs_preserve_bare_charge(self):
        self.assertTrue(w.validate_reference_matrix(self.matrix))
        self.assertEqual(len(self.matrix), 236)
        he = [r for r in self.matrix if r['z'] == 2]
        self.assertEqual([r['charge'] for r in he], [2, 0])
        self.assertEqual([r['electron_count'] for r in he], [0, 2])
        self.assertTrue(all(r['physical_prediction'] is None for r in self.matrix))

    def test_missing_duplicate_substituted_and_boolean_inventory_rejected(self):
        mutants = [self.matrix[:-1], self.matrix[:-1]+[self.matrix[0]]]
        wrong = deepcopy(self.matrix); wrong[2]['electron_count'] = 1; mutants.append(wrong)
        wrong = deepcopy(self.matrix); wrong[0]['z'] = True; mutants.append(wrong)
        wrong = deepcopy(self.matrix); wrong[0]['status'] = 'physical_prediction'; mutants.append(wrong)
        wrong = deepcopy(self.matrix); wrong[0]['configuration']['electron_count'] = 1; mutants.append(wrong)
        wrong = deepcopy(self.matrix); wrong[0]['configuration']['z'] = True; mutants.append(wrong)
        for rows in mutants:
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                w.validate_reference_matrix(rows)

    def test_real_joint_paths_propagate_covariance(self):
        propagated = w.propagate_ensemble(self.ensemble, self.modules)
        result = propagated['result']
        self.assertEqual(result['method'], 'finite_joint_law')
        self.assertEqual(result['status'], 'conditional')
        self.assertTrue(result['output_covariance'])
        self.assertEqual(result['outputs']['inner_reclosures']['unit'], 'count')
        self.assertEqual(result['outputs']['outer_commit']['kind'], 'native_cut_index')
        self.assertEqual(sum(Q(row['probability']) for row in self.ensemble['paths']), 1)
        self.assertEqual(propagated['physical_input_budget']['physical_model_discrepancy'], 'unknown')

    def test_trusted_joint_law_cannot_be_mutated_or_given_evaluation_role(self):
        product = w.propagate_ensemble(self.ensemble, self.modules)
        request, trusted = product['request'], product['trusted_sources']
        bad = deepcopy(request); bad['model']['support'][0][0] = '0'
        with self.assertRaises(ValueError):
            self.modules.metrology.propagate_quantities(bad, trusted)
        bad = deepcopy(request)
        first = next(iter(bad['inputs']))
        bad['inputs'][first]['quantity']['role'] = 'evaluation'
        with self.assertRaises(ValueError):
            self.modules.metrology.propagate_quantities(bad, trusted)

    def test_reported_magnitudes_are_not_automatically_sigmas(self):
        source, bindings = w.target_quantities(ROOT, self.modules)
        records = {r['id']: r for r in source['payload']['records']}
        for name, binding in bindings.items():
            category = binding['quantity']['uncertainty']['category']
            expected = 'standard_uncertainty' if records[name]['uncertainty']['kind'] == 'reported_standard_uncertainty' else 'unknown'
            self.assertEqual(category, expected)
            self.assertEqual(Q(binding['quantity']['value']), Q(records[name]['value']))

    def test_comparison_separates_not_applicable_unresolved_and_zero(self):
        result = w.comparisons(ROOT, {'native': 'frozen'}, self.modules)
        for row in result['rows']:
            atomic = row['atomic_transition']
            self.assertEqual(atomic['status'], 'not_applicable' if row['id'].endswith('bare') else 'missing_observation_map')
            self.assertIsNone(atomic['prediction_hz'])
            self.assertIsNone(atomic['residual_variance'])
            self.assertIsNone(row['retention']['half_life_seconds'])
        self.assertEqual(len(result['retained_isotope_measurements']), 3)

    def test_target_mutation_changes_only_comparison(self):
        native = {'native': 'frozen'}
        before = w.comparisons(ROOT, native, self.modules)
        original_read = w.read
        def changed(path):
            result = original_read(path)
            if str(path).endswith(w.TARGET_PATHS[0]):
                result = deepcopy(result)
                for row in result['properties']:
                    if row['id'] == 'hyperfine:H-1':
                        row['value'] = '7'
                        row['uncertainty'] = {'kind': 'not_supplied', 'value': None}
            return result
        with patch.object(w, 'read', side_effect=changed), self.assertRaisesRegex(ValueError, 'independently reconstructed'):
            w.comparisons(ROOT, native, self.modules)
        self.assertEqual(before['native_prediction_sha256'], w.digest(native))
        self.assertEqual(native, {'native': 'frozen'})

    def test_no_target_access_when_preparing_inventory(self):
        with patch.object(w, 'read', side_effect=RuntimeError('target access')):
            self.assertEqual(w.reference_preparations(ROOT), self.matrix)

    def test_reference_presentation_row_permutation_preserves_actual_execution(self):
        original = w.execute_reference(1, 'neutral', ROOT)
        reordered = list(reversed(deepcopy(self.matrix)))
        self.assertTrue(w.validate_reference_matrix(reordered))
        with patch.object(w, 'reference_preparations', return_value=reordered):
            permuted = w.execute_reference(1, 'neutral', ROOT)
        self.assertEqual(original, permuted)

    def test_full_native_prediction_executes_with_targets_unavailable(self):
        original_open = Path.open
        prohibited = {(ROOT/name).resolve() for name in w.TARGET_PATHS}
        def without_targets(path, *args, **kwargs):
            if path.resolve() in prohibited:
                raise RuntimeError('Evaluation target accessed during prediction')
            return original_open(path, *args, **kwargs)
        with patch.object(Path, 'open', without_targets):
            result = w.build_predictions(ROOT)
        self.assertEqual(result['reference_preparations.json']['counts']['construction_executions'], 6)
        self.assertEqual(len(result['uncertainty.json']['cases']), 7)
        frozen = result['frozen_diagnostic.json']
        self.assertEqual(frozen['prediction']['output']['unit'], 'count')
        self.assertTrue(frozen['replayed'])


if __name__ == '__main__':
    unittest.main()
