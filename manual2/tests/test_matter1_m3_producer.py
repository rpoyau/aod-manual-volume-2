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



class CurrentConsumerAcceptanceTests(unittest.TestCase):
    """Synthetic execution receipts exercise acceptance guards, not scientific evidence."""
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import record_matter1_isotope_acceptance as recorder
        import matter1_m3 as historical
        import matter1_coupled_preparations as coupled
        import matter1_preparation_workflow as workflow
        from publication_support import verify_foundation
        cls.recorder = recorder
        read = lambda name: json.loads((ROOT / name).read_text())
        current = p.verify(ROOT)
        foundation = verify_foundation(ROOT)
        old = read('manual2/data/m1/m3_observation/observation_report.json')
        cls.observation = {'status': 'PASS_M3_OBSERVATION',
            'profile': 'matter1:r03:m3-observation:v1', 'cases': 5,
            'report_sha256': hashlib.sha256((ROOT / 'manual2/data/m1/m3_observation/observation_report.json').read_bytes()).hexdigest(),
            'physical_calibration': 'not established'}
        cls.metrology = {'status': 'PASS_M3_METROLOGY_APPLICATIONS',
            'profile': 'matter1:m3-metrology:applications:v1',
            'outputs': {name: hashlib.sha256((ROOT / 'manual2/data/m1/m3_metrology' / name).read_bytes()).hexdigest()
                        for name in ('comparison.json', 'metrology_report.json', 'prediction.json')},
            'native_cases': 5, 'atomic_diagnostics': 4,
            'physical_calibration': 'not established', 'independent_physical_prediction': False}
        typed = {}
        for name, item in old['cases'].items():
            record = item['prediction']['complete_temporal_record']
            typed[name] = {'original_input_sha256': item['original_input_sha256'],
                'counts': record['counts'], 'context_sha256': record['observation_context']['input_sha256']}
        pilots = recorder.replay_current_coupled(ROOT)
        cls.coupled_results = pilots
        uncertainty = read('manual2/data/m1/preparation_workflow/uncertainty.json')['cases']['H-1-neutral']
        frozen = read('manual2/data/m1/preparation_workflow/frozen_diagnostic.json')
        cls.receipt = {'status': 'PASS_REQUIRED_M3_CONSUMER',
            'upstream_head': current['upstream_head'], 'upstream_tree': current['upstream_tree'],
            'api_contract_sha256': current['files']['contracts/scientific/TEMPORAL_OBSERVATION.json']['sha256'],
            'foundation_upstream_head': foundation['upstream_head'],
            'foundation_source_digest': foundation['source_digest'],
            'historical_observation_metrology_head': historical.verify_vendor(ROOT)['upstream_head'],
            'historical_survival_executor_head': historical.verify_legacy_vendor(ROOT)['upstream_head'],
            'metrology': {'persisted_historical_verification': cls.metrology},
            'typed_observation': {**cls.observation, 'current_actual_upstream_equals_vendored': True,
                                  'cases': typed},
            'quantity_comparison_dependency': {'actual_upstream_equals_vendored': True,
                'routes': ['bounds', 'conversion', 'finite_joint_law', 'metadata', 'multi_output',
                           'nonlinear_moments', 'published', 'published_moments', 'shared_cancel', 'shared_reinforce']},
            'coupled_preparations': {name: {'actual_upstream_equals_vendored': True,
                'result_sha256': coupled.digest(value)} for name, value in pilots.items()},
            'application_joint_propagation': {'actual_upstream_equals_vendored': True,
                'result_sha256': workflow.digest(uncertainty)},
            'complete_application_freeze': {'actual_upstream_equals_vendored': True,
                'result_sha256': workflow.digest(frozen), 'output': frozen['prediction']['output']},
            'executed': {'common_prefix_through_cut': 39,
                'feedback_disabled_original_validator_rejected': True,
                'cases': {'baseline': {'counts': {'outer_plus': 6, 'outer_minus': 5}},
                          'intervention': {'counts': {'outer_plus': 2, 'outer_minus': 5}}},
                'atomic_point_prediction': {'frequency_hz': None}}}

    def validate(self, receipt):
        self.recorder.validate_m3_consumer(ROOT, receipt, self.metrology, self.observation,
                                           self.coupled_results)

    def test_complete_current_receipt_preserves_historical_authority(self):
        self.validate(deepcopy(self.receipt))
        self.assertNotEqual(self.receipt['upstream_head'],
                            self.receipt['historical_observation_metrology_head'])

    def test_stale_current_authority_rejected(self):
        for key in ('upstream_head', 'upstream_tree', 'api_contract_sha256',
                    'foundation_upstream_head', 'foundation_source_digest'):
            with self.subTest(field=key):
                receipt = deepcopy(self.receipt)
                receipt[key] = '0' * len(receipt[key])
                with self.assertRaises(ValueError):
                    self.validate(receipt)

    def test_historical_identity_or_report_cannot_be_relabelled(self):
        for key in ('historical_observation_metrology_head', 'historical_survival_executor_head'):
            with self.subTest(field=key):
                receipt = deepcopy(self.receipt)
                receipt[key] = receipt['upstream_head']
                with self.assertRaises(ValueError):
                    self.validate(receipt)
        receipt = deepcopy(self.receipt)
        receipt['metrology']['persisted_historical_verification']['native_cases'] = 0
        with self.assertRaises(ValueError):
            self.validate(receipt)
        receipt = deepcopy(self.receipt)
        receipt['typed_observation']['report_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.validate(receipt)

    def test_every_current_quantity_route_required_once(self):
        for name in self.receipt['quantity_comparison_dependency']['routes']:
            with self.subTest(route=name):
                receipt = deepcopy(self.receipt)
                receipt['quantity_comparison_dependency']['routes'].remove(name)
                with self.assertRaises(ValueError):
                    self.validate(receipt)
        receipt = deepcopy(self.receipt)
        receipt['quantity_comparison_dependency']['routes'].append('bounds')
        with self.assertRaises(ValueError):
            self.validate(receipt)

    def test_all_six_coupled_cases_and_exact_results_required(self):
        for name in self.receipt['coupled_preparations']:
            with self.subTest(case=name):
                receipt = deepcopy(self.receipt)
                del receipt['coupled_preparations'][name]
                with self.assertRaises(ValueError):
                    self.validate(receipt)
                receipt = deepcopy(self.receipt)
                receipt['coupled_preparations'][name]['result_sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    self.validate(receipt)

    def test_one_round_pilots_cannot_replace_two_round_consumer(self):
        import matter1_coupled_preparations as coupled
        pilots = json.loads((ROOT / 'manual2/data/m1/coupled_preparations/pilots.json').read_text())
        receipt = deepcopy(self.receipt)
        for name, value in pilots.items():
            receipt['coupled_preparations'][name]['result_sha256'] = coupled.digest(value)
        with self.assertRaises(ValueError):
            self.validate(receipt)

    def test_actual_execution_flags_require_true_boolean(self):
        routes = [('typed_observation', 'current_actual_upstream_equals_vendored'),
                  ('quantity_comparison_dependency', 'actual_upstream_equals_vendored'),
                  ('application_joint_propagation', 'actual_upstream_equals_vendored'),
                  ('complete_application_freeze', 'actual_upstream_equals_vendored')]
        for name, key in routes:
            for bad in (False, 1, 'true'):
                with self.subTest(route=name, flag=bad):
                    receipt = deepcopy(self.receipt)
                    receipt[name][key] = bad
                    with self.assertRaises(ValueError):
                        self.validate(receipt)
        for name in self.receipt['coupled_preparations']:
            receipt = deepcopy(self.receipt)
            receipt['coupled_preparations'][name]['actual_upstream_equals_vendored'] = False
            with self.assertRaises(ValueError):
                self.validate(receipt)

    def test_joint_and_frozen_outputs_are_bound_to_application(self):
        for name in ('application_joint_propagation', 'complete_application_freeze'):
            receipt = deepcopy(self.receipt)
            receipt[name]['result_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                self.validate(receipt)
        receipt = deepcopy(self.receipt)
        receipt['complete_application_freeze']['output']['unit'] = 'Hz'
        with self.assertRaises(ValueError):
            self.validate(receipt)

    def test_typed_observation_and_feedback_cannot_be_partial(self):
        receipt = deepcopy(self.receipt)
        del receipt['typed_observation']['cases']['burden']
        with self.assertRaises(ValueError):
            self.validate(receipt)
        receipt = deepcopy(self.receipt)
        receipt['typed_observation']['cases']['burden']['original_input_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.validate(receipt)
        for key, value in (('common_prefix_through_cut', 38),
                           ('feedback_disabled_original_validator_rejected', False)):
            receipt = deepcopy(self.receipt)
            receipt['executed'][key] = value
            with self.assertRaises(ValueError):
                self.validate(receipt)
        receipt = deepcopy(self.receipt)
        receipt['executed']['atomic_point_prediction']['frequency_hz'] = 1
        with self.assertRaises(ValueError):
            self.validate(receipt)

    def test_evidence_hashes_exclude_changing_runner_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            checks = Path(tmp)
            for name in self.recorder.EVIDENCE_INPUTS:
                (checks / name).write_bytes(b'completed scientific input')
            output = checks / 'isotope-acceptance.json'
            expected = self.recorder.evidence_input_hashes(checks, output)
            self.assertEqual(len(expected), 23)
            for name in ('isotope-acceptance-console.json', 'acceptance-commands.json',
                         'property-acceptance.json'):
                (checks / name).write_bytes(b'now being written')
            self.assertEqual(self.recorder.evidence_input_hashes(checks, output), expected)
            (checks / 'm3-consumer.json').write_bytes(b'changed scientific input')
            with self.assertRaises(ValueError):
                self.recorder.evidence.check_equal(
                    self.recorder.evidence_input_hashes(checks, output), expected,
                    'acceptance inputs changed during replay')

    def test_missing_evidence_or_output_alias_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            checks = Path(tmp)
            for name in self.recorder.EVIDENCE_INPUTS:
                (checks / name).write_bytes(b'complete')
            with self.assertRaises(ValueError):
                self.recorder.evidence_input_hashes(checks, checks / 'm3-consumer.json')
            (checks / 'm3-consumer.json').unlink()
            with self.assertRaises(ValueError):
                self.recorder.evidence_input_hashes(checks, checks / 'acceptance.json')


if __name__ == '__main__':
    unittest.main()
