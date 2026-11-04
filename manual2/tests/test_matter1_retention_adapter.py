from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'manual2/scripts'))
import matter1_retention_adapter as app


class RetentionAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = deepcopy(app.original_contexts(ROOT)['configurations/Fl-286'])
        cls.context['contract'].update(Z=1, N=1, engine_start_cut=250000,
            intervention_cut=400000, horizon_cut=1100000,
            window_endpoints=[400000,750000,1100000], selected_label='small declared construction')
        cls.context['preparation'].update(id='small:ground', symbol='constructed', Z=1, N=1, A=2)
        cls.record = app.case_assessment(ROOT, original_context=cls.context)

    def reseal(self, record):
        record.pop('record_sha256', None)
        record['record_sha256'] = app.digest(record)
        return record

    def test_RA_01_common_rule_and_three_actual_inventories(self):
        contexts = app.original_contexts(ROOT)
        self.assertEqual(tuple(contexts), app.SELECTION)
        contracts = []
        for key, z, n in [('configurations/Fl-286',114,172),
                          ('configurations/Fl-289',114,175), ('r02/baseline',118,176)]:
            context = app.validate_context(ROOT, contexts[key])
            self.assertEqual((context['contract']['Z'],context['contract']['N']), (z,n))
            contract = deepcopy(context['contract'])
            for field in ('Z','N','selected_label'):
                contract.pop(field)
            contracts.append(contract)
        self.assertTrue(all(contract == contracts[0] for contract in contracts))

    def test_RA_02_actual_admission_and_complete_history_are_recorded(self):
        value = self.record
        self.assertEqual(value['actual_construction']['distinct_constituents'], 2)
        self.assertEqual(value['native_admission']['admitted_distinct_parent_constituents'], 2)
        self.assertEqual(value['actual_construction']['structural_RD'], 197)
        self.assertEqual(value['actual_construction']['evolving_aggregate_fields'], 5)
        self.assertTrue(value['actual_construction']['frozen_inner_formation_histories'])
        self.assertGreater(value['complete_history']['actions']['records'], 0)
        self.assertGreater(value['complete_history']['returned_currents']['records'], 0)
        self.assertEqual(value['actual_construction']['constituent_histories']['records'], 2)

    def test_RA_03_square_normalization_and_capacity_are_not_transferred(self):
        square = app.square_domain(ROOT)
        self.assertEqual((square['reference_structural_RD'], square['raw_normalization_unit'], square['raw_capacity']), (5,5,'5'))
        self.assertEqual((square['raw_signed_response'], square['raw_burden'], square['decision_exit_probability']), ('0','10','1/3'))
        self.assertFalse(square['transferred_to_aggregate'])
        self.assertEqual(self.record['reference']['structural_RD'], 61)
        self.assertIsNone(self.record['retention_mapping']['normalization'])
        self.assertIsNone(self.record['retention_mapping']['capacity'])

    def test_RA_04_actual_cadence_causality_does_not_supply_retention_schedule(self):
        witness = self.record['existing_cadence_law_causal_witness']
        cut = witness['affected_action']['cut']
        self.assertLess(witness['response_cut'], cut)
        self.assertTrue(all(committed < cut for committed in witness['contact_commit_cuts']))
        self.assertTrue(witness['contact_ids'])
        self.assertIsNone(self.record['retention_mapping']['decision_schedule'])

    def test_RA_05_signed_and_nonnegative_history_is_not_erased(self):
        burden = self.record['burden']
        self.assertGreaterEqual(Fraction(burden['nonnegative_sum']), abs(Fraction(burden['signed_response'])))
        self.assertEqual(burden['contributing_contacts'], self.record['complete_history']['burden_operands']['records'])
        self.assertTrue(burden['contributions_retained'])
        self.assertGreater(int(burden['nonnegative_sum']), 0)

    def test_RA_06_missing_loss_does_not_become_survival_or_censoring(self):
        for key in ('survival_probability','loss_reference_count','ensemble_median','physical_seconds'):
            self.assertIsNone(self.record[key])
        for key in ('kernel_state','decision_schedule','normalization','capacity','loss_predicate','exposure_operation'):
            self.assertIsNone(self.record['retention_mapping'][key])
        self.assertIn('no defined loss observable', self.record['horizon_status'])
        self.assertFalse(self.record['physical_isotope_admission'])

    def test_RA_07_real_json_roundtrip_replays_from_independent_context(self):
        value = json.loads(app.canonical(self.record))
        original = deepcopy(self.context)
        self.assertTrue(app.verify_case_assessment(value, original_context=original, root=ROOT))
        self.assertEqual(original, self.context)

    def test_RA_08_resealed_count_lineage_and_history_mutations_fail(self):
        for target, key, value in [('counts','new_parent_closures',99),
                                   ('actual_construction','parent_identity','substituted'),
                                   ('complete_history','actions',{'records':0,'sha256':'0'*64})]:
            changed = deepcopy(self.record); changed[target][key] = value
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, 'original-context replay'):
                app.verify_case_assessment(self.reseal(changed), original_context=self.context, root=ROOT)

    def test_RA_09_resealed_capacity_or_loss_claim_is_not_accepted(self):
        changed = deepcopy(self.record)
        changed['retention_mapping']['capacity'] = '5'
        changed['survival_probability'] = '2/3'
        with self.assertRaisesRegex(ValueError, 'original-context replay'):
            app.verify_case_assessment(self.reseal(changed), original_context=self.context, root=ROOT)

    def test_RA_10_incomplete_case_or_embedded_original_replacement_fails(self):
        with self.assertRaisesRegex(ValueError, 'original-context replay'):
            app.verify_case_assessment({'record_sha256':self.record['record_sha256']}, original_context=self.context, root=ROOT)
        changed = deepcopy(self.record)
        changed['original_context']['contract']['N'] = 2
        changed['original_context_sha256'] = app.digest(changed['original_context'])
        with self.assertRaisesRegex(ValueError, 'original-context replay'):
            app.verify_case_assessment(self.reseal(changed), original_context=self.context, root=ROOT)

    def test_RA_11_preparation_cannot_disagree_with_actual_inventory(self):
        changed = deepcopy(self.context); changed['preparation']['N'] = 2
        with self.assertRaisesRegex(ValueError, 'inventory differ'):
            app.case_assessment(ROOT, original_context=changed)

    def test_RA_12_boolean_float_and_extra_target_inputs_fail(self):
        for key, value in [('Z',True),('N',1.0),('horizon_cut',False),('window_endpoints',[400000,1100000.0])]:
            changed = deepcopy(self.context); changed['contract'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'Exact'):
                app.case_assessment(ROOT, original_context=changed)
        changed = deepcopy(self.context); changed['evaluation_targets'] = {'half_life':'1'}
        with self.assertRaisesRegex(ValueError, 'Complete original'):
            app.case_assessment(ROOT, original_context=changed)

    def test_RA_13_isotope_specific_capacity_and_hazard_cannot_enter_common_law(self):
        for key, value in [('parent_capacity',5),('parent_loss_rule','fitted hazard'),('physical_seconds','1')]:
            changed = deepcopy(self.context); changed['contract'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'common construction law'):
                app.case_assessment(ROOT, original_context=changed)

    def test_RA_14_label_only_change_preserves_actual_state_and_histories(self):
        context = deepcopy(self.context)
        context['contract']['selected_label'] = 'arbitrary isotope label'
        context['preparation']['id'] = 'renamed:ground'
        record = app.case_assessment(ROOT, original_context=context)
        for key in ('actual_construction','complete_history','burden','counts','reference','native_admission'):
            self.assertEqual(record[key], self.record[key])
        self.assertNotEqual(record['original_context_sha256'], self.record['original_context_sha256'])

    def test_RA_15_real_constituent_change_changes_witnesses_without_forced_survival(self):
        context = deepcopy(self.context)
        context['contract']['N'] = 2; context['preparation'].update(N=2,A=3)
        record = app.case_assessment(ROOT, original_context=context)
        self.assertEqual(record['actual_construction']['distinct_constituents'],3)
        self.assertNotEqual(record['actual_construction']['parent_identity'],self.record['actual_construction']['parent_identity'])
        self.assertNotEqual(record['actual_construction']['scope_map_sha256'],self.record['actual_construction']['scope_map_sha256'])
        self.assertIsNone(record['survival_probability'])

    def fixture(self, folder):
        root = Path(folder)/'repo'
        packet = app.constructed.DATA/'source_packet'
        shutil.copytree(ROOT/packet, root/packet)
        sources = app.read_json(ROOT/packet/'source_bindings.json')['sha256']
        names = [name.removeprefix('upstream/') for name in sources
                 if name.startswith(('upstream/sections/','upstream/appendices/'))]
        names += ['manual2/scripts/'+name for name in ('matter1_model.py','matter1_constructed_coupling.py',
            'generate_matter1_constructed_coupling.py','verify_matter1_constructed_coupling.py','matter1_retention_adapter.py')]
        for name in names:
            path = root/name; path.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/name,path)
        return root

    def test_RA_16_actual_evaluation_file_changes_leave_assessment_bytes_identical(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.fixture(folder)
            target = root/'manual2/data/m1/isotopes/curation.json'
            target.parent.mkdir(parents=True)
            target.write_bytes((ROOT/'manual2/data/m1/isotopes/curation.json').read_bytes())
            before = app.case_assessment(root, original_context=self.context)
            target.write_text('{"replacement_targets":{"Fl-286":{"half_life":"999999"}}}\n')
            after = app.case_assessment(root, original_context=self.context)
            self.assertEqual(app.canonical(before), app.canonical(after))

    def test_RA_17_native_and_application_source_substitution_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.fixture(folder)
            path = root/'manual2/scripts/matter1_retention_adapter.py'
            path.write_bytes(path.read_bytes()+b'\n# substituted\n')
            with self.assertRaisesRegex(ValueError, 'assessment implementation'):
                app.case_assessment(root, original_context=self.context)
            shutil.copyfile(ROOT/'manual2/scripts/matter1_retention_adapter.py',path)
            native = root/app.constructed.DATA/'source_packet/upstream/manual/scripts/aod_native_closure_wave.py'
            native.write_bytes(native.read_bytes()+b'\n# substituted\n')
            with self.assertRaisesRegex(ValueError, 'original member changed'):
                app.case_assessment(root, original_context=self.context)

    def test_RA_18_unselected_contexts_cannot_replace_full_investigation(self):
        contexts = app.original_contexts(ROOT)
        contexts['configurations/Fl-286'] = deepcopy(self.context)
        with self.assertRaisesRegex(ValueError, 'three bound investigation contexts'):
            app.assess(ROOT, originals=contexts)


if __name__ == '__main__':
    unittest.main(verbosity=2)
