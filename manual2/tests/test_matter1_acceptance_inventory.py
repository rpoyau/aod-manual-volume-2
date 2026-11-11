"""Runner/recorder integration and persisted incomplete-log counterexamples.

Generated log fixtures below are parser test inputs, never execution receipts.
"""
from __future__ import annotations
import hashlib
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import matter1_test_inventory as inventory
import record_matter1_acceptance as core
import record_matter1_v2_acceptance as v2
import record_matter1_property_acceptance as properties


def log_fixture(ids):
    ids = sorted(ids)
    lines = [f'{test.rsplit(".", 1)[1]} ({test}) ... ok' for test in ids]
    return '\n'.join(lines + ['', f'Ran {len(ids)} tests in 0.001s', '', 'OK', ''])


def suite_ids(suite):
    for child in suite:
        if isinstance(child, unittest.TestSuite):
            yield from suite_ids(child)
        else:
            yield child.id()


class AcceptanceInventoryTests(unittest.TestCase):
    def test_workflow_and_recorder_use_the_shared_runner_inventory(self):
        workflow = (ROOT / '.github/workflows/matter1.yml').read_text()
        main_runs = [line.strip() for line in workflow.splitlines()
                     if '| tee /tmp/matter1-checks/tests-optimized.txt' in line]
        self.assertEqual(main_runs, [
            'python -B -O scripts/matter1_test_inventory.py --run-optimized 2>&1 | tee /tmp/matter1-checks/tests-optimized.txt'])
        self.assertIs(core.OPTIMIZED_MODULES, inventory.OPTIMIZED_MODULES)
        self.assertTrue({'test_matter1_data_classes', 'test_matter1_external_transitions'} <= inventory.OPTIMIZED_MODULES)
        self.assertIn("-p 'test_matter1_campaign*.py'", workflow)
        for flags in ([], ['-O']):
            result = subprocess.run([sys.executable, '-B', *flags,
                str(ROOT / 'scripts/matter1_test_inventory.py'), '--list-optimized'],
                text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), inventory.optimized_module_names())

    def test_executable_suite_matches_recorder_method_identity(self):
        loaded = list(suite_ids(inventory.load_optimized_suite()))
        expected = {t for t in core.source_test_ids() if t.split('.')[2] in inventory.OPTIMIZED_MODULES}
        self.assertEqual(len(loaded), len(set(loaded)))
        self.assertEqual(set(loaded), expected)

    def test_persisted_missing_method_with_adjusted_count_is_rejected(self):
        ids = core.source_test_ids()
        expected = {t for t in ids if t.split('.')[2] in inventory.OPTIMIZED_MODULES}
        with tempfile.TemporaryDirectory() as folder:
            checks = Path(folder)
            (checks / 'tests.txt').write_text(log_fixture(ids))
            path = checks / 'tests-optimized.txt'
            path.write_text(log_fixture(expected))
            self.assertEqual(v2.validate_logs(checks, ids)['optimized']['method_count'], len(expected))
            for module in ('test_matter1_data_classes', 'test_matter1_external_transitions'):
                omitted = next(t for t in expected if t.split('.')[2] == module)
                path.write_text(log_fixture(expected - {omitted}))
                before = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaisesRegex(core.EvidenceError, 'validation subset'):
                    v2.validate_logs(checks, ids)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_duplicate_and_failed_methods_cannot_become_success(self):
        ids = core.source_test_ids()
        expected = {t for t in ids if t.split('.')[2] in inventory.OPTIMIZED_MODULES}
        good = log_fixture(expected)
        first = good.splitlines()[0]
        bad_logs = [first + '\n' + good,
                    good.replace(first, first[:-2] + 'FAIL', 1),
                    good.replace(first, first[:-2] + "skipped 'not executed'", 1)]
        with tempfile.TemporaryDirectory() as folder:
            checks = Path(folder)
            (checks / 'tests.txt').write_text(log_fixture(ids))
            for bad in bad_logs:
                path = checks / 'tests-optimized.txt'; path.write_text(bad)
                before = path.read_bytes()
                with self.assertRaises(core.EvidenceError):
                    v2.validate_logs(checks, ids)
                self.assertEqual(path.read_bytes(), before)

    def test_reproduction_recorders_use_the_complete_dynamic_inventory(self):
        from check_matter1_reproduction import expected_output_paths
        from manual2.scripts import matter1_property_model as model
        expected = expected_output_paths(ROOT)
        self.assertTrue({'data/m1/properties/model/' + name for name in model.OUTPUTS} <= expected)
        self.assertTrue(any(name.startswith('data/m1/campaign/cases/') for name in expected))
        for name in ('record_matter1_acceptance.py', 'record_matter1_isotope_acceptance.py'):
            text = (ROOT / 'scripts' / name).read_text()
            self.assertIn('expected_output_paths(', text)
            self.assertNotIn('import EXPECTED_OUTPUTS', text)

    def test_prior_acceptance_source_and_physical_promotions_are_rejected(self):
        # Synthetic validator fixtures; these never become acceptance artifacts.
        inventory = {'fixture.py': {'sha256': '0' * 64, 'bytes': 1}}
        logs = {'normal': {'fixture': 'normal'}, 'optimized': {'fixture': 'optimized'}}
        ids = {'manual2.tests.test_matter1_isotopes.Fixture.test_retained'}
        core_ids = [r['id'] for r in core.read_json(ROOT / core.PLAN)['records']]
        v2_ids = [f'SI-{n:02}' for n in range(1, 19)] + [f'PRED-{n:02}' for n in range(1, 6)]
        extra = ['VIS-01', 'VIS-02', 'FOUND-01', 'PUB-01', 'REPRO-01']
        docs = {
            'acceptance.json': {'document_kind': 'executed_scoped_acceptance_receipt',
                'record_count': 39, 'records': [{'id': id_, 'outcome': 'executed_scope_pass'} for id_ in core_ids],
                'native_admission_status': 'pending', 'atomic_mapping_status': 'pending', 'physical_empirical_status': 'not_compared'},
            'v2-acceptance.json': {'criteria_count': 23,
                'records': [{'id': id_, 'assertion_outcome': 'executed_scope_pass'} for id_ in v2_ids],
                'atomic_prediction_objective': 'incomplete', 'native_atomic_admission': 'pending'},
            'isotope-acceptance.json': {'record_count': 6,
                'records': [{'id': 'ISO-01', 'test_id': next(iter(ids)), 'outcome': 'executed_scope_pass'}] +
                    [{'id': id_, 'outcome': 'executed_scope_pass'} for id_ in extra],
                'physical_isotope_half_life_prediction': 'not_established', 'native_isotope_admission': 'not_established'},
        }
        for doc in docs.values():
            doc.update(source_test_model_artifact_inventory=deepcopy(inventory), test_runs=deepcopy(logs))
        properties.validate_prior_documents(docs, inventory, logs, ids)
        mutations = [
            lambda d: d['acceptance.json']['source_test_model_artifact_inventory']['fixture.py'].__setitem__('sha256', '1' * 64),
            lambda d: d['v2-acceptance.json']['test_runs'].__setitem__('optimized', {'stale': True}),
            lambda d: d['v2-acceptance.json'].__setitem__('atomic_prediction_objective', 'complete'),
            lambda d: d['isotope-acceptance.json'].__setitem__('physical_isotope_half_life_prediction', 'established'),
            lambda d: d['acceptance.json']['records'].pop(),
            lambda d: d['isotope-acceptance.json']['records'][0].__setitem__('outcome', 'not_run'),
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'synthetic-validator-input.json'
            for mutate in mutations:
                bad = deepcopy(docs); mutate(bad); path.write_bytes(core.canonical(bad))
                before = path.read_bytes()
                with self.assertRaises(core.EvidenceError):
                    properties.validate_prior_documents(core.read_json(path), inventory, logs, ids)
                self.assertEqual(path.read_bytes(), before)

    def test_property_browser_receipt_cannot_hide_missing_views_or_changed_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in properties.BROWSER_PATHS:
                path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('fixture')
            browser = {'status': 'PASS', 'inputs_unchanged': True, 'page_errors': [],
                'input_sha256': {name: core.sha((root / name).read_bytes()) for name in properties.BROWSER_PATHS},
                'property_checks': [{'width': w, 'theme': t, 'entities': 2, 'element_coverage': 118,
                    'source_state_separate_from_count': True, 'horizontal_overflow': False}
                    for w in (736, 360, 320) for t in ('light', 'dark')]}
            properties.validate_browser(root, browser, 2)
            for mutate in (lambda d: d['property_checks'].pop(),
                           lambda d: d['property_checks'][0].__setitem__('source_state_separate_from_count', 1),
                           lambda d: d['property_checks'][0].__setitem__('horizontal_overflow', True),
                           lambda d: d['property_checks'][0].__setitem__('entities', 1)):
                bad = deepcopy(browser); mutate(bad)
                with self.assertRaises(core.EvidenceError): properties.validate_browser(root, bad, 2)
            path = root / sorted(properties.BROWSER_PATHS)[0]; path.write_text('changed fixture')
            before = path.read_bytes()
            with self.assertRaisesRegex(core.EvidenceError, 'stale input'):
                properties.validate_browser(root, browser, 2)
            self.assertEqual(path.read_bytes(), before)

    def test_reproduction_receipt_binds_inputs_and_complete_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); relative = 'data/m1/properties/model/prediction.json'
            path = root / 'manual2' / relative; path.parent.mkdir(parents=True); path.write_text('{}')
            current = {'manual2/' + relative: core.sha(path.read_bytes())}
            receipt = {'status': 'PASS_REPRODUCTION', 'source_unchanged': True, 'source_sha256': current,
                       'outputs': [{'path': relative, 'comparison': 'byte equality'}]}
            properties.validate_reproduction(root, receipt, {relative}, current)
            changes = [lambda d: d.__setitem__('source_unchanged', False),
                       lambda d: d['source_sha256'].__setitem__('manual2/' + relative, '0' * 64),
                       lambda d: d.__setitem__('outputs', []),
                       lambda d: d['outputs'][0].__setitem__('comparison', 'not compared')]
            for mutate in changes:
                bad = deepcopy(receipt); mutate(bad)
                with self.assertRaises(core.EvidenceError):
                    properties.validate_reproduction(root, bad, {relative}, current)

    def test_property_acquisition_gaps_and_physical_status_cannot_be_promoted(self):
        reports = {'properties': {'status': 'PASS_ELEMENT_PROPERTY_CATALOG', 'acquisition_complete': False,
                    'missing_source_families': ['atomic_levels_lines'], 'physical_predictions_executed': 0,
                    'counts': {'element_z_coverage': 118, 'pilot_isotopes': 6}},
            'property-model': {'status': 'PASS_PROPERTY_MODEL_ORIGINAL_INPUT_REPLAY', 'native_pilots': 6,
                'comparison_checked': True, 'physical_prediction_complete': False,
                'whole_law_disposition': 'incomplete_missing_premises'}}
        self.assertEqual(properties.validate_lane_reports(reports), 'partial_source_acquisition')
        changes = [lambda d: d['properties'].__setitem__('acquisition_complete', True),
                   lambda d: d['properties'].__setitem__('physical_predictions_executed', 1),
                   lambda d: d['property-model'].__setitem__('physical_prediction_complete', True),
                   lambda d: d['property-model'].__setitem__('comparison_checked', False),
                   lambda d: d['properties'].__setitem__('status', 'PASS_FAKE_SUCCESS')]
        for mutate in changes:
            bad = deepcopy(reports); mutate(bad)
            with self.assertRaises(core.EvidenceError): properties.validate_lane_reports(bad)

    def test_preceding_evidence_hashes_reject_changed_supplied_files(self):
        with tempfile.TemporaryDirectory() as folder:
            checks = Path(folder)
            for name in ('tests.txt', 'tests-optimized.txt'):
                (checks / name).write_text('synthetic hash-validation fixture')
            bindings = {name: core.sha((checks / name).read_bytes()) for name in ('tests.txt', 'tests-optimized.txt')}
            docs = {'synthetic.json': {'evidence_sha256': bindings}}
            properties.verify_prior_file_hashes(checks, docs)
            (checks / 'tests.txt').write_text('changed supplied file')
            before = (checks / 'tests.txt').read_bytes()
            with self.assertRaisesRegex(core.EvidenceError, 'stale evidence'):
                properties.verify_prior_file_hashes(checks, docs)
            self.assertEqual((checks / 'tests.txt').read_bytes(), before)

    def test_property_recorder_cli_rejects_incomplete_logs_before_any_write(self):
        ids = core.source_test_ids()
        optimized = {t for t in ids if t.split('.')[2] in inventory.OPTIMIZED_MODULES}
        with tempfile.TemporaryDirectory() as folder:
            checks = Path(folder); output = checks / 'property-acceptance.json'
            (checks / 'tests.txt').write_text(log_fixture(ids))
            (checks / 'tests-optimized.txt').write_text(log_fixture(optimized - {sorted(optimized)[0]}))
            before = {p.name: p.read_bytes() for p in checks.iterdir()}
            for flags in ([], ['-O']):
                result = subprocess.run([sys.executable, '-B', *flags,
                    str(ROOT / 'scripts/record_matter1_property_acceptance.py'),
                    '--checks-dir', str(checks), '--output', str(output)], text=True, capture_output=True)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('validation subset', result.stderr)
                self.assertFalse(output.exists())
                self.assertEqual({p.name: p.read_bytes() for p in checks.iterdir()}, before)


if __name__ == '__main__':
    unittest.main()
