"""Finite coupled histories, causal controls and source-authorized replay."""
from copy import deepcopy
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'manual2/scripts'))
import matter1_coupled_preparations as m


class CoupledPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = m.default_config(1, 1, 1, rounds=2)
        cls.result = m.run_case(cls.config, ROOT)
        cls.exact = m.enumerate_paths(cls.config, ROOT)

    def test_current_producer_with_unchanged_historical_helpers(self):
        binding = self.result['source_binding']
        self.assertEqual(binding['producer_commit'], m.PRODUCER)
        self.assertEqual(binding['historical_helper_sha256'], m.LEGACY_SHA)
        self.assertEqual(binding['producer_loader_sha256'], hashlib.sha256(
            (ROOT/'manual2/scripts/matter1_m3_producer.py').read_bytes()).hexdigest())
        session = m.initialize(self.config, ROOT)
        self.assertIs(session.construction.module.n, m.producer.load(ROOT).native)

    def test_pure_validation_cache_preserves_the_complete_result(self):
        uncached = m.run_case(self.config, ROOT, cached=False)
        self.assertEqual(m.canonical(uncached), m.canonical(self.result))

    def test_strict_config_and_forced_path_arity(self):
        for key in ('z', 'a', 'electron_count', 'rounds', 'seed'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.run_case(dict(self.config, **{key: True}), ROOT)
        for path in [(1,), (1,)*5, (True, 1, 1, 1), (0, 1, 1, 1)]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                m.run_case(self.config, ROOT, forced=path)

    def test_six_distinct_inventory_preparations(self):
        for name, a, e in m.PILOTS:
            with self.subTest(name=name):
                result = m.run_case(m.default_config(1, a, e, rounds=1), ROOT)
                c = result['construction']
                self.assertEqual((c['z'], c['a'], c['electron_count'], c['charge']), (1, a, e, 1-e))
                self.assertEqual(len(c['constituents']), a+e)
                self.assertEqual(len(set(x['wave_identity'] for x in c['constituents'])), a+e)
                self.assertTrue(all(x['certificate_sha256'] for x in c['constituents']))

    def test_bare_single_constituent_has_no_self_contact_or_zero_hyperfine(self):
        result = m.run_case(m.default_config(1, 1, 0, rounds=1), ROOT)
        self.assertEqual(result['trajectory']['contacts'], [])
        self.assertIsNone(result['observation'])
        self.assertEqual(result['attempts']['atomic_transition']['status'], 'not_applicable')
        self.assertIsNone(result['physical_frequency_hz'])
        self.assertEqual(result['readouts']['accumulated_burden'], 0)

    def test_complete_full_state_checkpoint_continuation(self):
        resumed = m.run_case(self.config, ROOT, checkpoint_after=1)
        self.assertEqual(m.canonical(resumed), m.canonical(self.result))
        session = m.initialize(self.config, ROOT); m.advance(session)
        record = m.checkpoint(session)
        for name in ('waves', 'channels', 'responses', 'rcds', 'response_cuts', 'pending', 'cursor', 'round'):
            self.assertIn(name, record['state'])
        self.assertIn('rng_state', record)
        restored = m.restore_checkpoint(record, self.config, ROOT)
        self.assertEqual(m.checkpoint(restored), record)

    def test_checkpoint_rejects_resealed_current_history_rng_or_population(self):
        session = m.initialize(self.config, ROOT); m.advance(session)
        record = m.checkpoint(session)
        for key in ('current', 'history', 'rng', 'population'):
            bad = deepcopy(record)
            if key == 'current': bad['state']['responses'][0] += 1
            if key == 'history': bad['state']['returns'][0]['committed'] += 1
            if key == 'rng': bad['rng_state'][1][0] += 1
            if key == 'population': bad['state']['waves'].pop()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'full-state replay'):
                m.restore_checkpoint(bad, self.config, ROOT)

    def test_forced_checkpoint_needs_independently_bound_prefix(self):
        session = m.initialize(self.config, ROOT); m.advance(session, (1, 1))
        record = m.checkpoint(session)
        self.assertEqual(m.checkpoint(m.restore_checkpoint(record, self.config, ROOT,
            forced_prefix=(1, 1))), record)
        with self.assertRaises(ValueError):
            m.restore_checkpoint(record, self.config, ROOT, forced_prefix=(-1, -1))

    def test_final_observation_does_not_mutate_complete_state(self):
        session = m.initialize(self.config, ROOT)
        m.advance(session); m.advance(session)
        before = m.checkpoint(session)
        self.assertEqual(m.finish(session), m.finish(session))
        self.assertEqual(m.checkpoint(session), before)

    def test_exact_same_history_readouts_and_joint_covariance(self):
        exact = self.exact
        self.assertEqual(len(exact['paths']), 16)
        self.assertEqual(sum(Q(x['probability']) for x in exact['paths']), 1)
        self.assertEqual(exact['means']['accumulated_burden'], '18')
        self.assertEqual(exact['means']['outer_commit'], '20593/2')
        self.assertGreater(Q(exact['covariance'][2][2]), 0)
        self.assertEqual(m.readouts(self.result), self.result['readouts'])
        for i in range(4):
            for j in range(4):
                self.assertEqual(exact['covariance'][i][j], exact['covariance'][j][i])

    def test_enumeration_budget_is_explicit(self):
        with self.assertRaisesRegex(ValueError, 'six binary'):
            m.enumerate_paths(m.default_config(1, 3, 1, rounds=2), ROOT)

    def test_sampled_paths_share_exact_law_and_all_runs_are_kept(self):
        sampled = m.sampling_comparison(self.exact, ROOT)
        self.assertEqual([x['seed'] for x in sampled['runs']], list(m.SAMPLE_SEEDS))
        self.assertEqual(sum(x['count'] for x in sampled['counts']), len(m.SAMPLE_SEEDS))
        self.assertTrue(sampled['criterion_passed'])
        self.assertEqual(sampled['discarded_runs'], [])
        for row in sampled['runs']:
            self.assertEqual(m.digest(row['trajectory']), row['trajectory_sha256'])

    def test_passive_projection_preserves_trajectory_and_rng(self):
        passive = m.run_case(self.config, ROOT, observer=False)
        self.assertEqual(passive['trajectory'], self.result['trajectory'])
        self.assertEqual(passive['execution'], self.result['execution'])
        self.assertIsNone(passive['observation'])

    def test_actual_name_permutation_preserves_timed_correspondence(self):
        renamed = m.run_case(self.config, ROOT, names=('node-beta', 'node-alpha'))
        self.assertEqual(renamed['readouts'], self.result['readouts'])
        self.assertNotEqual(renamed['trajectory_sha256'], self.result['trajectory_sha256'])
        key = lambda x: [(r['constituent'], r['committed'], r['pacing'], r['orientation'])
            for r in x['trajectory']['inner_returns']]
        self.assertEqual(key(renamed), key(self.result))

    def test_all_region_boundary_identity(self):
        rows = m.boundary_rows(self.result, ROOT)
        self.assertEqual(len(rows['regions']), 4)
        for row in rows['regions']:
            self.assertEqual(row['internal'], '0')
            self.assertEqual(row['divergence'], row['boundary'])

    def test_finite_reduction_checks_joint_next_state_and_observable(self):
        check = m.finite_reduction_control(ROOT)
        self.assertEqual(check['groups'], [2, 2])
        self.assertTrue(check['joint_next_state_and_observable_laws_equal'])
        self.assertTrue(check['burden_only_counterexamples'])

    def test_cancellation_availability_debit_and_actual_next_return(self):
        check = m.shedding_availability_control(ROOT)
        self.assertEqual(check['net_only_before'], 0)
        self.assertEqual(check['retained_after_export'], '9')
        self.assertEqual(check['bridge']['load'], 18)
        self.assertEqual(check['shedding']['surplus'], '9')
        self.assertNotEqual(check['next_kernel_before'], check['next_kernel_after'])
        nexts = check['matched_continuations']
        self.assertNotEqual(nexts['export_disabled']['return']['committed'],
                            nexts['export_enabled']['return']['committed'])
        self.assertFalse(set(check['retained_contact_ids']) & set(check['exported_contact_ids']))

    def test_retained_pressure_is_needed_for_native_next_response(self):
        check = m.pressure_memory_control(ROOT)
        self.assertTrue(check['same_admitted_history'])
        self.assertTrue(check['same_present_current'])
        self.assertEqual([x['current'] for x in check['next_states']], ['1', '1/2'])

    def test_stale_cache_window_current_and_population_are_rejected(self):
        window = self.result['execution']['reference_window']
        cached = m.readout_cache(self.config, window, ROOT)
        self.assertTrue(m.replay_readout_cache(cached, self.config, window, ROOT))
        for key in ('window', 'current', 'population'):
            bad = deepcopy(cached)
            if key == 'window': bad['window'][0] += 1
            if key == 'current': bad['readouts']['signed_current'] += 1
            if key == 'population': bad['population'].pop()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'stale'):
                m.replay_readout_cache(bad, self.config, window, ROOT)

    def test_resealed_output_is_not_original_execution(self):
        bad = deepcopy(self.result)
        bad['trajectory']['contacts'][-1]['signed_response'] += 1
        bad['trajectory_sha256'] = m.digest(bad['trajectory'])
        bad['readouts'] = m.readouts(bad)
        with self.assertRaisesRegex(ValueError, 'original-input replay'):
            m.verify_case(self.config, bad, ROOT)

    def test_native_admissibility_zero_weight_and_hinge_distinctions(self):
        n = m.producer.load(ROOT).native
        allowed = (0, 1, 1, 0); absent = (0, 3, 1, 0)
        self.assertEqual(n.kernel([allowed], {allowed: 0})['status'], 'EMPTY_POSITIVE_WEIGHT_SUPPORT')
        self.assertEqual(n.kernel([absent], {absent: 1})['status'], 'EMPTY_ADMISSIBLE_SUPPORT')
        self.assertEqual(n.kernel([allowed, absent], {allowed: 1, absent: 9})['probabilities'][absent], 0)
        self.assertTrue(all(x['hinge_count'] == 1 for x in self.result['trajectory']['inner_returns']))
        with self.assertRaises(Exception): n.fibre_step(1, -1, 'leave_hinge')

    def test_missing_physical_maps_are_preserved_as_specific_attempts(self):
        self.assertEqual(self.result['empirical_inputs_read'], [])
        self.assertIsNone(self.result['physical_frequency_hz'])
        self.assertIsNone(self.result['physical_half_life_seconds'])
        for key in ('physical_preparation', 'frg', 'retention_loss', 'atomic_transition', 'physical_clock'):
            row = self.result['attempts'][key]
            self.assertEqual(row['status'], 'incomplete_dependent_output')
            self.assertTrue(row['attempt']); self.assertTrue(row['missing'])


if __name__ == '__main__':
    unittest.main()
