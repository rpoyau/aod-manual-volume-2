"""Current producer migration, historical identity and hostile source changes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'manual2/scripts'))
import matter1_m3_producer as p
import matter1_foundation as f
import matter1_property_model as properties
import matter1_preparation_freeze as freeze


class ProducerMigrationTests(unittest.TestCase):
    def test_current_namespaces_have_one_dependency_identity(self):
        api = p.load(ROOT)
        self.assertEqual(api.binding['upstream_head'], p.HEAD)
        self.assertIs(api.temporal.n, api.native)
        self.assertIs(api.temporal.m, api.mapping)
        self.assertIs(api.metrology.t, api.temporal)
        self.assertIs(api.experimental.mt, api.metrology)
        self.assertIs(api.experimental.m, api.mapping)
        self.assertIs(p.load(ROOT), api)

    def test_alias_context_restores_existing_imports(self):
        before = {n: sys.modules.get(n) for n in p.MODULES.values()}
        api = p.load(ROOT)
        with api.activate():
            self.assertIs(sys.modules['aod_cell_measures'], api.cells)
            self.assertIs(sys.modules['aod_m3_temporal'], api.temporal)
            self.assertTrue(api.temporal.reduction_fixtures())
        self.assertEqual(before, {n: sys.modules.get(n) for n in p.MODULES.values()})

    def test_relative_code_bindings_match_export(self):
        api = p.load(ROOT)
        for name, sha in api.experimental.code_bindings().items():
            self.assertEqual(sha, api.binding['files'][name]['sha256'])

    def test_published_moment_uncertainty_reaches_output(self):
        api = p.load(ROOT)
        request, trusted = api.metrology.quantity_input_fixture('published_moments')
        result = api.metrology.propagate_quantities(request, trusted)
        output = next(iter(result['outputs'].values()))
        self.assertEqual(output['result']['output_variance'], '1/250000')
        self.assertEqual(output['unit'], 'Hz')

    def test_new_main_identity_keeps_old_main_bytes(self):
        active, _ = f.binding(ROOT)
        historical = f.historical_m3_binding(ROOT)
        self.assertEqual(active['upstream_head'], p.HEAD)
        self.assertEqual(historical['upstream_head'], properties.UPSTREAM)
        self.assertEqual(active['files'], historical['files'])
        self.assertNotEqual(active['upstream_head'], historical['upstream_head'])

    def test_historical_property_receipt_retains_original_recipe(self):
        protocol = json.loads((ROOT/properties.DATA/'protocol.json').read_text())
        self.assertEqual(properties.source_bindings(ROOT), protocol['source_bindings'])
        self.assertNotEqual(f.historical_property_digest(ROOT),
                            hashlib.sha256(Path(properties.__file__).read_bytes()).hexdigest())

    def test_missing_actual_producer_cannot_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(Exception):
                p.verify(ROOT, tmp)

    def _copy_vendor(self, tmp):
        dest = Path(tmp)
        shutil.copytree(ROOT/p.VENDOR, dest/p.VENDOR)
        return dest

    def test_modified_binding_cannot_self_reseal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._copy_vendor(tmp)
            path = root/p.VENDOR/'binding.json'
            binding = json.loads(path.read_text())
            binding['upstream_head'] = '0'*40
            path.write_text(json.dumps(binding))
            with self.assertRaisesRegex(ValueError, 'unreviewed dependency binding'):
                p.verify(root)

    def test_request_only_handoff_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._copy_vendor(tmp)
            (root/p.VENDOR/'M3_PRODUCER_HANDOFF.json').write_text('{"readiness":"request_only"}')
            with self.assertRaisesRegex(ValueError, 'handoff changed'):
                p.load(root)

    def test_primary_pdf_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._copy_vendor(tmp)
            path = root/p.VENDOR/'current/manual/data/m3/temporal_metrology/hydrogen/source/hellwig1970.pdf'
            path.write_bytes(path.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError, 'export changed'):
                p.load(root)

    def test_cache_cannot_hide_code_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._copy_vendor(tmp)
            p.load(root)
            path = root/p.VENDOR/'current/manual/scripts/aod_mapping_error.py'
            path.write_bytes(path.read_bytes()+b'\n# changed\n')
            with self.assertRaisesRegex(ValueError, 'export changed'):
                p.load(root)

    def test_cached_binding_mutation_cannot_relabel_producer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._copy_vendor(tmp)
            api = p.load(root)
            api.binding['upstream_head'] = '0'*40
            with self.assertRaisesRegex(ValueError, 'cached dependency identity changed'):
                p.load(root)

    def test_metadata_unknown_does_not_become_zero_uncertainty(self):
        api = p.load(ROOT)
        request, trusted = api.metrology.quantity_input_fixture('metadata')
        result = api.metrology.propagate_quantities(request, trusted)
        for output in result['outputs'].values():
            self.assertIsNone(output['result']['output_variance'])
        request = deepcopy(request)
        key = next(iter(request['inputs']))
        request['inputs'][key]['quantity']['unit'] = 's'
        with self.assertRaises(ValueError):
            api.metrology.propagate_quantities(request, trusted)


class PreparationFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = p.load(ROOT)
        cls.plan, cls.trusted, cls.context = freeze.original(ROOT, cls.api)
        cls.product = cls.api.experimental.predict(cls.plan, cls.trusted, original_context=cls.context)

    def target(self, value):
        q = {'kind': 'native_reclosure_count', 'unit': 'count', 'dimension': [0, 0, 1],
            'domain': ['0', '100'], 'window': None, 'locator': 'Explicit hostile-test endpoint',
            'role': 'evaluation', 'meaning': 'Declared diagnostic endpoint; not experimental evidence',
            'value': value, 'uncertainty': {'category': 'unknown', 'reason': 'No measurement model'},
            'components': [], 'corrections': {}}
        source = self.api.mapping.source('test:separate-count-endpoint', 'evaluation', {'quantities': {'target': q}})
        binding = {'schema': self.api.metrology.QUANTITY_SCHEMA, 'source_id': source['id'],
            'source_sha256': source['sha256'], 'quantity_id': 'target', 'quantity': deepcopy(q)}
        return {'quantity_binding': binding, 'joint_evidence': None}, {**self.trusted, source['id']: source}

    def test_original_application_population_and_directed_history_are_retained(self):
        self.assertEqual(len(self.context.population), 4)
        self.assertEqual(len(self.context.couplings), 6)
        self.assertEqual(self.context.preparation['parameters']['original_config']['electron_count'], 1)
        self.assertEqual(self.product['output']['value'], '2')
        self.assertEqual(self.product['output']['dimension'], [0, 0, 1])
        self.assertEqual(self.product['output']['variance'], '0')
        self.assertEqual(self.product['propagation']['outputs']['count']['budget']['model_discrepancy']['kind'], 'unknown')

    def test_every_plan_component_is_independently_bound(self):
        for key in ('readout_definitions', 'readout_parameter_links', 'reduction_window',
                    'selection', 'stopping', 'output_definition', 'comparison_criterion',
                    'code_bindings', 'calibration_source_ids', 'original_context_sha256'):
            with self.subTest(component=key):
                plan = deepcopy(self.plan)
                plan['plan'][key] = None
                with self.assertRaises(ValueError):
                    self.api.experimental.predict(plan, self.trusted, original_context=self.context)

    def test_source_quantity_mutation_cannot_rebind_original_plan(self):
        plan = deepcopy(self.plan)
        plan['plan']['uncertainty_request']['parameters']['count']['quantity']['value'] = '3'
        with self.assertRaises(ValueError):
            self.api.experimental.predict(plan, self.trusted, original_context=self.context)

    def test_changed_target_does_not_change_prediction(self):
        comparisons = []
        for value in ('2', '3'):
            target, trusted = self.target(value)
            comparisons.append(self.api.experimental.evaluate(self.product, target,
                original_plan=self.plan, trusted_sources=trusted, original_context=self.context))
        self.assertEqual(comparisons[0]['prediction_sha256'], comparisons[1]['prediction_sha256'])
        self.assertNotEqual(comparisons[0]['residual'], comparisons[1]['residual'])
        self.assertFalse(comparisons[0]['independent_validation'])

    def test_changed_prediction_is_rejected_before_target_comparison(self):
        target, trusted = self.target('2')
        product = deepcopy(self.product)
        product['output']['value'] = '3'
        with self.assertRaisesRegex(ValueError, 'complete prediction differs'):
            self.api.experimental.evaluate(product, target, original_plan=self.plan,
                trusted_sources=trusted, original_context=self.context)


if __name__ == '__main__':
    unittest.main()
