"""Actual R03-to-M3 context, source isolation and independent replay controls."""
from copy import deepcopy
from dataclasses import replace
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
import matter1_m3 as dependency
import matter1_m3_observation as o
import matter1_witnessed_retention as r


class ObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = dependency.temporal(ROOT)
        cls.original = o.default_input(ROOT)
        cls.artifact = o.predict(ROOT, cls.original, cls.api)

    def test_actual_native_records_and_full_context_are_consumed(self):
        p = self.artifact['prediction']; record = p['complete_temporal_record']
        self.assertEqual(record['counts'], {'compared':2, 'reference':3})
        self.assertEqual((record['forward']['ratio'], record['reverse']['ratio']), ('2/3','3/2'))
        self.assertEqual((record['forward']['lag'], record['forward']['drift']), ('1','-1'))
        self.assertEqual((record['reverse']['lag'], record['reverse']['drift']), ('-1','1'))
        self.assertEqual(record['forward']['rcd']['support'], 5)
        self.assertEqual(len(record['observation_context']['population']), 4)
        self.assertEqual(record['observation_context']['duration_participation']['status'], 'unknown')
        self.assertEqual(p['mapped']['outputs']['elapsed_seconds']['value'], '1/3064210590')
        self.assertEqual(self.artifact['scope']['physical_elapsed_seconds'], None)

    def test_native_class_transport_preserves_every_field(self):
        fixture = r.Fixture(r.default_contract(ROOT), 'burden')
        native = fixture.background.wave(); moved = o._transport(native, self.api.n)
        self.assertIsInstance(moved, self.api.n.Wave)
        self.assertNotIsInstance(native, self.api.n.Wave)
        self.assertEqual(o.canonical(r.asdict(native)), o.canonical(r.asdict(moved)))
        self.api.n.validate_wave(moved)

    def test_pending_background_retains_history_and_does_not_create_return(self):
        baseline = o.predict(ROOT, o.default_input(ROOT, 'burden'), self.api)
        pending = o.predict(ROOT, o.default_input(ROOT, 'burden_background_pending'), self.api)
        a = baseline['complete_observation_context']; b = pending['complete_observation_context']
        self.assertEqual(len(a['pending']), 0); self.assertEqual(len(b['pending']), 1)
        self.assertEqual(len(a['population'][2]['returns'])-len(b['population'][2]['returns']), 2)
        self.assertEqual(b['pending'][0]['payload']['status'], 'pending; no return certificate')
        self.assertEqual(pending['prediction']['complete_temporal_record']['counts'], {'compared':2,'reference':3})

    def test_whole_artifact_replay_rejects_resealed_embedded_changes(self):
        for part in ('count','preparation','source','event','pending_decision'):
            with self.subTest(part=part):
                forged = deepcopy(self.artifact)
                if part == 'count': forged['prediction']['complete_temporal_record']['counts']['compared'] = 3
                elif part == 'preparation': forged['complete_observation_context']['preparation']['parameters']['case']='net_memory'
                elif part == 'source': forged['complete_observation_context']['source_dependencies'][0]['payload']['case']='net_memory'
                elif part == 'event': forged['execution']['clock_events'][0]['kind']='forged'
                else: forged['execution']['pending_decision']['probabilities']['exit']='0'
                forged['original_input_sha256'] = o.digest(forged.get('complete_observation_context'))
                with self.assertRaisesRegex(ValueError, 'Whole observation artifact differs'):
                    o.replay(ROOT, forged, original_context=self.original, temporal_api=self.api)

    def test_independent_original_cannot_be_replaced_by_self_consistent_embedded_context(self):
        other = o.default_input(ROOT, 'net_memory', '+-')
        other_artifact = o.predict(ROOT, other, self.api)
        with self.assertRaisesRegex(ValueError, 'Whole observation artifact differs'):
            o.replay(ROOT, other_artifact, original_context=self.original, temporal_api=self.api)
        self.assertEqual(o.replay(ROOT, self.artifact, original_context=self.original, temporal_api=self.api), self.artifact)

    def test_original_protocol_capacity_and_sources_cannot_be_resealed(self):
        for path in ('capacity','source','extra','target'):
            forged = deepcopy(self.original)
            if path == 'capacity': forged['contract']['capacity']['diagnostic_units']='2'
            elif path == 'source': forged['sources']['native_code_sha256']='0'*64
            elif path == 'extra': forged['reverse_extra']=True
            else: forged['measured_half_life']='1'
            with self.subTest(path=path), self.assertRaises(ValueError):
                o.predict(ROOT, forged, self.api)

    def test_opposite_orientation_preserves_cadence_but_not_signed_response(self):
        plus = self.artifact
        minus = o.predict(ROOT, o.default_input(ROOT, 'burden', '--'), self.api)
        self.assertEqual(plus['prediction']['complete_temporal_record']['counts'], minus['prediction']['complete_temporal_record']['counts'])
        self.assertEqual(plus['execution']['pending_decision']['raw_burden'], minus['execution']['pending_decision']['raw_burden'])
        self.assertEqual(int(plus['execution']['pending_decision']['raw_signed']), -int(minus['execution']['pending_decision']['raw_signed']))

    def test_actual_reverse_reflection_changes_only_directional_duration(self):
        other = o.predict(ROOT, o.default_input(ROOT, 'burden', '++', 1), self.api)
        base = self.artifact['prediction']['complete_temporal_record']
        changed = other['prediction']['complete_temporal_record']
        self.assertEqual(base['forward']['duration'], changed['forward']['duration'])
        self.assertEqual(changed['reverse']['duration']-base['reverse']['duration'], 3)
        self.assertEqual(base['counts'], changed['counts'])

    def test_frozen_domain_and_actual_source_boundaries_remain_enforced(self):
        c = o.observation_context(ROOT, self.original, self.api)
        wrong = deepcopy(c.preparation); wrong['parameters']['case']='net_memory'
        with self.assertRaisesRegex(ValueError, 'outside frozen domain'):
            self.api.predict(replace(c, preparation=wrong))
        with patch.object(self.api.n, '__file__', r.__file__), self.assertRaisesRegex(ValueError, 'native definitions differ'):
            o.observation_context(ROOT, self.original, self.api)

    def test_evaluation_mutation_is_separate_from_whole_prediction(self):
        c = o.observation_context(ROOT, self.original, self.api); p = self.api.predict(c)
        before = o.canonical(p)
        def target(cycles):
            return self.api.m.source('evaluation','evaluation',{'corrected_cycles':cycles,'window':list(c.record.window)})
        one=self.api.compare_cycles(p,target('3'),original_context=c)
        two=self.api.compare_cycles(p,target('4'),original_context=c)
        self.assertEqual(one['residual_cycles'],'0');self.assertEqual(two['residual_cycles'],'-1')
        self.assertIsNone(one['compatible']);self.assertIsNone(one['combined_standard_uncertainty'])
        self.assertEqual(before,o.canonical(p))
        self.assertEqual(self.api.reference_independence([c,c])['status'],'dependent')

    def test_historical_and_current_executors_are_distinct_and_bound(self):
        current = dependency.mapping(ROOT); old = dependency.legacy_mapping(ROOT)
        self.assertNotEqual(hashlib.sha256(Path(current.__file__).read_bytes()).hexdigest(),
                            hashlib.sha256(Path(old.__file__).read_bytes()).hexdigest())
        self.assertIn('/current/', current.__file__)
        self.assertEqual(dependency.verify_legacy_vendor(ROOT)['upstream_head'], '3ffb3c9984eef95ca4b105ac323d249f30412816')

    def test_current_temporal_import_rejects_ambient_module_aliases(self):
        with patch.dict(sys.modules, {'aod_native_closure_wave':object(), 'aod_mapping_error':object()}):
            api=dependency.temporal(ROOT)
            self.assertEqual(api.predict(o.observation_context(ROOT,self.original,api))['complete_temporal_record']['counts'], {'compared':2,'reference':3})

    def test_temporal_export_and_contract_tampering_is_rejected(self):
        for name in ('aod_m3_temporal.py','TEMPORAL_OBSERVATION.json'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root=Path(temp);folder=root/dependency.VENDOR
                shutil.copytree(ROOT/dependency.VENDOR,folder)
                path=folder/'current'/name;path.write_bytes(path.read_bytes()+b'\n')
                with self.assertRaisesRegex(ValueError,'M3 vendor source changed'):
                    dependency.temporal(root)

    def test_persisted_report_verification_is_complete_and_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            shutil.copytree(ROOT/r.DATA,root/r.DATA)
            shutil.copytree(ROOT/dependency.VENDOR,root/dependency.VENDOR)
            previous=dependency.verify_vendor(ROOT)['previous_binding']['path']
            archive=Path(previous).parent
            shutil.copytree(ROOT/archive,root/archive,dirs_exist_ok=True)
            scripts=root/'manual2/scripts';scripts.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/'manual2/scripts/matter1_witnessed_retention.py',scripts/'matter1_witnessed_retention.py')
            o.generate(root)
            self.assertEqual(o.verify(root)['status'],'PASS_M3_OBSERVATION')
            path=root/o.DATA/o.OUTPUTS[0]
            data=json.loads(path.read_text());data['cases']['burden']['execution']['pending_decision']['raw_capacity']='500'
            path.write_text(json.dumps(data));before=path.read_bytes()
            with self.assertRaisesRegex(ValueError,'Stored observation report differs'):
                o.verify(root)
            self.assertEqual(path.read_bytes(),before)


if __name__ == '__main__':
    unittest.main()
