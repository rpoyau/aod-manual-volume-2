"""Persisted classification counterexamples; no model/campaign regeneration."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from manual2.scripts import matter1_data_classes as c


class DataClassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[2]
        cls.lock = c.read(cls.root / c.LOCK)
        cls.registry = c.read(cls.root / c.REGISTRY)
        cls.paths = sorted(set([c.REGISTRY, c.LOCK,
            'manual2/scripts/matter1_data_classes.py',
            'manual2/scripts/verify_matter1_data_classes.py',
            *cls.lock['artifacts'], *cls.lock['authority']['files']]))

    @staticmethod
    def snapshot(root, paths):
        return {p: (hashlib.sha256((root / p).read_bytes()).hexdigest(),
                    (root / p).stat().st_mtime_ns, (root / p).stat().st_size) for p in paths}

    def persisted(self, mutate):
        with tempfile.TemporaryDirectory(prefix='matter1-data-class-mutation-') as td:
            root = Path(td)
            for name in self.paths:
                dest = root / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.root / name, dest)
            registry = copy.deepcopy(self.registry)
            mutate(root, registry)
            (root / c.REGISTRY).write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n')
            before = self.snapshot(root, self.paths)
            with self.assertRaises((ValueError, KeyError, IndexError, TypeError)):
                c.verify(root)
            self.assertEqual(before, self.snapshot(root, self.paths), 'failed verifier repaired input')

    @staticmethod
    def card(registry, id_):
        return next(card for card in registry['cards'] if card['id'] == id_)

    def test_positive_read_only_and_scoped_receipt(self):
        before = self.snapshot(self.root, self.paths)
        receipt = c.verify(self.root)
        self.assertEqual(receipt['status'], 'PASS_CLASSIFICATION_BINDINGS_ONLY')
        self.assertEqual(receipt['cards'], 14)
        self.assertEqual(receipt['support_codes'], {'D0': 3, 'O0': 2})
        self.assertEqual(receipt['executed_models'], 0)
        self.assertEqual(receipt['replayed_campaign_cases'], 0)
        for name in ['native_admission_verified', 'physical_predictions_verified', 'empirical_agreement_verified']:
            self.assertIs(receipt[name], False)
        self.assertEqual(before, self.snapshot(self.root, self.paths))

    def test_d0_to_o0_swap_rejected(self):
        def mutate(root, registry):
            card = self.card(registry, 'campaign-current-audit')
            card['support_class'].update(code='O0', name=c.SUPPORT['O0'])
            card['data_card']['C_support'] = 'O0'
        self.persisted(mutate)

    def test_o0_to_d0_swap_rejected(self):
        def mutate(root, registry):
            card = self.card(registry, 'atomic-countermodel-residuals')
            card['support_class'].update(code='D0', name=c.SUPPORT['D0'])
            card['data_card']['C_support'] = 'D0'
        self.persisted(mutate)

    def test_raw_target_as_native_rejected(self):
        def mutate(root, registry):
            card = self.card(registry, 'hydrogen-measured-transition')
            card['support_class'].update(code='D0', name=c.SUPPORT['D0'])
            card['data_card']['C_support'] = 'D0'
            card['record_form'] = 'Exact fixture'
            card['claim_class'] = 'native exact fixture'
        self.persisted(mutate)

    def test_static_ledger_is_not_automatically_d0(self):
        def mutate(root, registry):
            card = self.card(registry, 'static-reference')
            card['support_class'].update(code='D0', name=c.SUPPORT['D0'])
        self.persisted(mutate)

    def test_whole_campaign_is_not_automatically_d0(self):
        def mutate(root, registry):
            card = self.card(registry, 'campaign-declared-dynamics')
            card['support_class'].update(code='D0', name=c.SUPPORT['D0'])
        self.persisted(mutate)

    def test_calibration_as_prediction_rejected(self):
        def mutate(root, registry):
            card = self.card(registry, 'cesium-defining-anchor')
            card['claim_class'] = 'empirical comparison'
            card['execution_outcome']['classifier_confers_physical_prediction'] = True
        self.persisted(mutate)

    def test_missing_class_field_rejected(self):
        self.persisted(lambda root, registry: self.card(registry, 'isotope-finite-targets').pop('claim_class'))

    def test_display_scope_promotion_rejected(self):
        def mutate(root, registry):
            self.card(registry, 'deuterium-tritium-target-supplement')['decimal_display']['scopes'] = ['internal']
        self.persisted(mutate)

    def test_execution_outcome_promotion_rejected(self):
        def mutate(root, registry):
            self.card(registry, 'atomic-observation-declaration')['execution_outcome']['source_fields']['/native_execution_status'] = 'executed'
        self.persisted(mutate)

    def test_integer_for_false_outcome_rejected(self):
        def mutate(root, registry):
            self.card(registry, 'campaign-current-audit')['execution_outcome']['classifier_confers_native_admission'] = 0
        self.persisted(mutate)

    def test_altered_source_rejected(self):
        def mutate(root, registry):
            path = root / 'manual2/data/m1/hyperfine/target_inventory.json'
            source = c.read(path)
            source['transitions'][0]['standard_uncertainty_hz'] = '0'
            path.write_text(json.dumps(source))
        self.persisted(mutate)

    def test_altered_source_and_resealed_registry_rejected(self):
        def mutate(root, registry):
            path = root / 'manual2/data/m1/hyperfine/target_inventory.json'
            source = c.read(path)
            source['transitions'][0]['standard_uncertainty_hz'] = '0'
            path.write_text(json.dumps(source))
            for card in registry['cards']:
                for binding in card['bindings']:
                    if binding['path'] == str(path.relative_to(root)):
                        binding['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.persisted(mutate)

    def test_source_lock_resealing_rejected(self):
        def mutate(root, registry):
            path = root / c.LOCK
            lock = c.read(path)
            lock['authority']['commit'] = '0' * 40
            path.write_text(json.dumps(lock))
            registry['source_lock']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.persisted(mutate)

    def test_authority_source_changed_rejected(self):
        def mutate(root, registry):
            path = root / next(p for p in self.lock['authority']['files'] if p.endswith('06_field_dynamics_applications.tex.source'))
            path.write_text(path.read_text().replace('D0 & exact internal fixture', 'D1 & exact internal fixture'))
        self.persisted(mutate)

    def test_isotope_point_and_nonpoint_partition_preserved(self):
        points = self.card(self.registry, 'isotope-finite-targets')['bindings'][0]['json_pointers']
        nonpoints = self.card(self.registry, 'isotope-nonpoint-inventory')['bindings'][0]['json_pointers']
        source = c.read(self.root / 'manual2/data/m1/isotopes/catalog.json')
        point_indices = {int(p.split('/')[-1]) for p in points if p.startswith('/isotopes/')}
        nonpoint_indices = {int(p.split('/')[-1]) for p in nonpoints if p.startswith('/isotopes/')}
        self.assertFalse(point_indices & nonpoint_indices)
        self.assertEqual(point_indices | nonpoint_indices, set(range(27)))
        for i in point_indices:
            self.assertEqual(source['isotopes'][i]['half_life']['kind'], 'measured')
            self.assertIsNotNone(source['isotopes'][i]['half_life']['value_seconds'])
        for i in nonpoint_indices:
            self.assertIsNone(source['isotopes'][i]['half_life']['value_seconds'])

    def test_cli_modes_and_unknown_flag(self):
        before = self.snapshot(self.root, self.paths)
        script = self.root / 'manual2/scripts/verify_matter1_data_classes.py'
        for optimization in [[], ['-O']]:
            result = subprocess.run([sys.executable, '-B', *optimization, str(script), '--root', str(self.root)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(json.loads(result.stdout)['status'], 'PASS_CLASSIFICATION_BINDINGS_ONLY')
        rejected = subprocess.run([sys.executable, '-B', str(script), '--repair'], capture_output=True, text=True)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(before, self.snapshot(self.root, self.paths))


if __name__ == '__main__':
    unittest.main()
