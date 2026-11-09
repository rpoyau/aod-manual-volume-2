"""Application replay, target separation, dependency and missing-input controls."""
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'manual2/scripts'))
import matter1_atomic as atomic
import matter1_m3 as dependency
import matter1_m3_metrology as application
import matter1_m3_metrology_vendor as vendor


class MetrologyApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = vendor.metrology(ROOT)
        cls.products = application.report(ROOT, metrology_api=cls.api)
        cls.prediction = cls.products['prediction.json']
        cls.comparison = cls.products['comparison.json']
        cls.report = cls.products['metrology_report.json']

    def test_all_five_native_cases_replay_with_original_scope(self):
        cases = self.prediction['native_r03']
        self.assertEqual(len(cases), 5)
        for case in cases.values():
            self.assertEqual(case['population_size'], 4)
            self.assertEqual(case['native_observations']['compared']['count'], 2)
            self.assertEqual(case['native_observations']['reference']['count'], 3)
            self.assertEqual(case['conditional_outputs']['elapsed_seconds'], '1/3064210590')
            self.assertEqual(case['native_binding']['physical_correspondence'], 'unestablished')
            self.assertIsNone(case['physical_half_life'])
        self.assertEqual(cases['burden']['pending_count'], 0)
        self.assertEqual(cases['burden_background_pending']['pending_count'], 1)
        self.assertNotEqual(cases['burden']['context_sha256'], cases['burden_background_pending']['context_sha256'])

    def test_four_diagnostics_preserve_old_residuals_and_intervention(self):
        old = atomic.compare(self.prediction['atomic_diagnostics'], atomic.default_target())
        self.assertEqual([(r['scenario'], r['lambda']) for r in self.comparison['rows']],
                         [(r['scenario'], r['lambda']) for r in old['rows']])
        for new, prior in zip(self.comparison['rows'], old['rows']):
            self.assertEqual(new['assessment']['residual'], prior['residual_hz'])
            self.assertEqual(new['historical_window_match'], 'unestablished')
            self.assertFalse(new['assessment']['independent_physical_validation'])
            self.assertFalse(new['assessment']['corrections_applied_by_assessment'])
            self.assertEqual(new['assessment']['complete_physical_uncertainty']['kind'], 'unknown')
            definition = next(s for s in new['record']['sources'] if s['id'] == 'SI:Cs133-definition')
            self.assertEqual(new['record']['comparison']['dependency_ids'], [definition['id']])
            self.assertEqual(new['assessment']['shared_source_payload_sha256'], [definition['sha256']])
            self.assertEqual(new['record']['reference_role'], 'reference_dependent_evaluation')
        values = [r['record']['prediction']['value'] for r in self.comparison['rows']]
        self.assertNotEqual(values[0], values[1])
        self.assertNotEqual(values[0], values[2])
        self.assertIsNone(self.comparison['physical_atomic_prediction'])

    def test_prediction_never_loads_evaluation_target(self):
        original = atomic.read_json
        def read(path):
            if Path(path).name == 'evaluation_target.json':
                raise AssertionError('Evaluation target read during prediction')
            return original(path)
        with patch.object(atomic, 'read_json', side_effect=read):
            result = application.predict(ROOT, metrology_api=self.api)
        self.assertEqual(application.canonical(result), application.canonical(self.prediction))

    def test_changed_evaluation_changes_only_scoring(self):
        target = atomic.default_target()
        target['classification'] = 'synthetic_evaluation_mutation'
        target['frequency_hz'] = str(Q(target['frequency_hz'])+1)
        before = application.canonical(self.prediction)
        changed = application.compare(ROOT, self.prediction, metrology_api=self.api, evaluation_target=target)
        self.assertEqual(changed['prediction_sha256'], self.comparison['prediction_sha256'])
        self.assertEqual(application.canonical(self.prediction), before)
        for a, b in zip(changed['rows'], self.comparison['rows']):
            self.assertEqual(Q(a['assessment']['residual']), Q(b['assessment']['residual'])-1)
        self.assertFalse(changed['independent_physical_validation'])

    def test_resealed_prediction_mutation_cannot_be_scored(self):
        changed = deepcopy(self.prediction)
        changed['atomic_diagnostics']['countermodels'][0]['mapped_ratio'] = '1'
        changed['atomic_diagnostics']['calibration_sha256'] = application.digest(changed['atomic_diagnostics']['calibration'])
        with self.assertRaisesRegex(ValueError, 'original-input replay'):
            application.compare(ROOT, changed, metrology_api=self.api)

    def test_type_changed_target_metadata_cannot_claim_historical_identity(self):
        target = atomic.default_target()
        target['schema_version'] = True
        with self.assertRaisesRegex(ValueError, 'typed target'):
            application._comparison(ROOT, self.prediction, self.api, target)

    def test_historical_reductions_and_uncertainties_stay_separate(self):
        hydrogen = self.report['hydrogen']
        self.assertEqual(hydrogen['table_iv']['corrected_frequency_hz'], '14204057517691/10000')
        self.assertEqual(hydrogen['table_vi']['corrected_frequency_hz'], '14204057517667/10000')
        self.assertEqual(hydrogen['published_mean']['corrected_frequency_hz'], '14204057517679/10000')
        self.assertEqual(hydrogen['published_mean']['published_rounded_frequency_hz'], '1420405751.768')
        self.assertEqual(hydrogen['table_vi']['correction_ownership']['already_in_input'], ['NP3', 'wall'])
        self.assertEqual(set(self.report['cesium']), {'August2013', 'typical_Table1'})
        for case in self.report['cesium'].values():
            self.assertEqual(case['Cs_SI_frequency_role'], 'calibration_identity')
            self.assertEqual(case['complete_covariance']['kind'], 'unknown')

    def test_isotope_missing_inputs_do_not_become_physical_predictions(self):
        records = self.report['isotope_applications']
        self.assertEqual(set(records['deuterium_tritium']), {'H-2', 'H-3'})
        for row in records['deuterium_tritium'].values():
            self.assertEqual(row['status'], 'missing_input')
            self.assertIsNone(row['frequency_hz'])
        rows = records['livermorium']['events']
        self.assertEqual([r['interval_seconds'] for r in rows], ['283/50000', '173/10000'])
        for row in rows:
            self.assertEqual(row['origin'], 'implantation')
            self.assertEqual(row['m3_event_timing_status'], 'missing_input')
            self.assertIsNone(row['resolution'])
            self.assertIsNone(row['lifetime_prediction'])
        self.assertFalse(records['livermorium']['formation_timestamp_inferred'])
        self.assertFalse(records['livermorium']['half_life_inferred_from_two_intervals'])

    def test_injected_api_cannot_substitute_unbound_companion(self):
        with patch.object(self.api, '__file__', atomic.__file__):
            with self.assertRaisesRegex(ValueError, 'runtime source differs'):
                application.report(ROOT, metrology_api=self.api)

    def test_loader_isolates_and_restores_ambient_aliases(self):
        first, second = object(), object()
        with patch.dict(sys.modules, {'aod_m3_temporal': first, 'aod_mapping_error': second}):
            api = vendor.metrology(ROOT)
            self.assertIs(api.m, api.t.m)
            self.assertIs(sys.modules['aod_m3_temporal'], first)
            self.assertIs(sys.modules['aod_mapping_error'], second)

    def test_companion_contract_and_profiles_cannot_be_resealed(self):
        for name in ('current/aod_m3_metrology.py', 'current/TEMPORAL_METROLOGY.json',
                     'current/hydrogen/protocol.json', 'current/hydrogen/reported_uncertainty.json',
                     'current/cesium/protocol.json'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                shutil.copytree(ROOT/vendor.VENDOR, root/vendor.VENDOR)
                shutil.copytree(ROOT/dependency.VENDOR, root/dependency.VENDOR)
                previous = Path(dependency.verify_vendor(ROOT)['previous_binding']['path']).parent
                shutil.copytree(ROOT/previous, root/previous)
                path = root/vendor.VENDOR/name
                path.write_bytes(path.read_bytes()+b'\n')
                with self.assertRaisesRegex(ValueError, 'vendor source changed'):
                    vendor.verify_vendor(root)
                binding_path = root/vendor.VENDOR/'binding.json'
                binding = json.loads(binding_path.read_text())
                binding['files'][name]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                binding_path.write_text(json.dumps(binding))
                with self.assertRaisesRegex(ValueError, 'vendor binding changed'):
                    vendor.verify_vendor(root)

    def test_unknown_correction_or_evaluation_dependency_cannot_be_promoted(self):
        row = self.prediction['atomic_diagnostics']['countermodels'][0]
        for mutation in ('unknown_zero', 'evaluation_dependency', 'altered_endpoint'):
            record, trusted = application.assessment_record(self.prediction, row, atomic.default_target(), self.api)
            if mutation == 'unknown_zero':
                record['influences'][0]['residual_uncertainty']['value'] = '0'
            elif mutation == 'evaluation_dependency':
                record['prediction']['dependency_ids'].append(record['comparison']['source_id'])
            else:
                record['prediction']['value'] = '1'
            declaration = {k: deepcopy(v) for k, v in record.items() if k not in ('source_id', 'sources')}
            updated = self.api.m.source(record['source_id'], 'model', {'comparison_assessment': declaration})
            record['sources'][-1] = updated
            trusted[updated['id']] = updated
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.api.assess_comparison(record, trusted)

    def test_lv_input_changes_are_rejected_before_reduction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root/application.DATA
            folder.mkdir(parents=True)
            data = json.loads((ROOT/application.DATA/'application_inputs.json').read_text())
            data['livermorium']['timestamp_resolution'] = '1/125000000'
            (folder/'application_inputs.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'application inputs changed'):
                application.isotope_inputs(root)

    def test_persisted_artifact_mutation_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT/application.DATA, root/application.DATA)
            path = root/application.DATA/'metrology_report.json'
            changed = json.loads(path.read_text())
            changed['independent_physical_prediction'] = True
            path.write_text(json.dumps(changed))
            before = {p.name: p.read_bytes() for p in (root/application.DATA).iterdir()}
            # Use independently executed products to isolate the persisted-artifact boundary.
            with patch.object(application, 'report', return_value=self.products):
                with self.assertRaisesRegex(ValueError, 'Stored metrology artifact differs'):
                    application.verify(root)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root/application.DATA).iterdir()})


if __name__ == '__main__':
    unittest.main()
