"""Executed causal interventions and real persisted v2 mutations.

These checks concern a declared finite evolution, not native atomic admission.
Every persisted corruption is tested through the read-only CLI with -B and -O.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'manual2/scripts'))
import matter1_stateful as s

VERIFIER = Path('manual2/scripts/verify_matter1_stateful.py')


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


class StatefulTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = s.prepare(ROOT)
        cls.base = cls.products['baseline_trace']
        cls.loss = cls.products['early_loss_trace']
        cls.fixture = s.t.read_json(ROOT / s.GEOMETRY)

    def disposable(self, parent):
        root = Path(parent) / 'repo'
        paths = [VERIFIER, Path('manual2/scripts/matter1_stateful.py'),
                 Path('manual2/scripts/matter1_temporal.py'), Path('manual2/scripts/matter1_folding.py'),
                 s.GEOMETRY, *(Path(x) for x in s.t.SOURCE_LABELS), *(s.DATA / x for x in s.FILES)]
        for relative in paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return root

    def rejected(self, name, action, filename='early_loss_trace.json'):
        for optimized in (False, True):
            with self.subTest(mutation=name, optimized=optimized), tempfile.TemporaryDirectory() as tmp:
                root = self.disposable(tmp)
                path = root / s.DATA / filename
                value = json.loads(path.read_text())
                action(value)
                path.write_bytes(s.canonical_bytes(value))
                before = snapshot(root)
                args = [sys.executable, '-B'] + (['-O'] if optimized else []) + [str(root / VERIFIER), '--root', str(root), '--check-data']
                result = subprocess.run(args, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0, name)
                self.assertIn('ERROR:', result.stderr)
                self.assertEqual(before, snapshot(root), 'Verifier mutated persisted files')

    def test_sequential_baseline_counts(self):
        self.assertEqual(self.base['summary']['completed_return_cuts'], {
            'outer_plus':[26,33,40,47,54,61,68], 'outer_minus':[27,35,43,51,59,67]})
        self.assertEqual(self.base['summary']['observed_reclosure_counts'], {'outer_plus':6,'outer_minus':5})
        self.assertEqual(self.base['summary']['model_count_ratio'], '6/5')
        self.assertIsNone(self.base['summary']['physical_frequency_ratio'])

    def test_controlled_early_loss_changes_later_returns_and_contacts(self):
        self.assertEqual(self.loss['summary']['loss_cuts']['outer_plus'], 41)
        self.assertEqual(self.loss['summary']['completed_return_cuts']['outer_plus'], [26,33,40])
        self.assertEqual([x['cut'] for x in self.loss['contacts']], [36,40])
        self.assertEqual(self.loss['summary']['model_count_ratio'], '2/5')
        self.assertEqual(self.base['summary']['contact_count'], 8)
        self.assertTrue(all(not any(e['event_id'].startswith('outer_plus:') for e in r['events'])
                            for r in self.loss['cut_records'] if r['cut'] >= 41))
        self.assertTrue(all(not r['coupling_available'] for r in self.loss['cut_records'] if r['cut'] >= 41))

    def test_response_is_consumed_strictly_next_cut(self):
        response = self.loss['responses'][0]
        self.assertEqual((response['input_cut'], response['committed_cut']), (40,41))
        records = {x['cut']:x for x in self.loss['cut_records']}
        self.assertEqual(records[41]['applied_response_ids'], [response['response_id']])
        self.assertTrue(records[40]['states'][0]['retained'])
        self.assertFalse(records[41]['states'][0]['retained'])

    def test_preintervention_prefix_is_immutable(self):
        self.assertEqual([r for r in self.base['cut_records'] if r['cut'] < 40],
                         [r for r in self.loss['cut_records'] if r['cut'] < 40])
        model = deepcopy(self.products['baseline_scenario'])
        model['parameters']['capacity_schedule'].append({'from_cut':52,'capacity':'0'})
        altered = s.simulate(model, self.fixture, ROOT)
        self.assertEqual([r for r in self.base['cut_records'] if r['cut'] < 52],
                         [r for r in altered['cut_records'] if r['cut'] < 52])

    def test_exposure_preserves_inner_maps_and_histories(self):
        expected = self.loss['outer_waves'][0]['returns'][0]['fold']['inner_maps']
        self.assertEqual(self.loss['exposures']['outer_plus'], expected)
        self.assertEqual(self.base['initial_inner_waves'], self.loss['initial_inner_waves'])
        self.assertTrue(all(x['inner_scope'] != x['outer_scope'] for x in expected))
        self.assertEqual(self.base['outer_waves'][0]['returns'][:3], self.loss['outer_waves'][0]['returns'])

    def test_loss_during_incomplete_cycle_retains_partial_events(self):
        model = deepcopy(self.products['early_loss_scenario'])
        model['parameters']['contact_completion_cuts'] = [36,41,45,49,53,57,61,65]
        altered = s.simulate(model, self.fixture, ROOT)
        aborted = altered['aborted_cycles']['outer_plus']
        self.assertEqual(aborted[0]['cut'],42)
        self.assertEqual(aborted[0]['committed_events'][0]['cut'],41)
        committed = {e['event_id']:e for r in altered['cut_records'] for e in r['events']}
        self.assertTrue(all(e == committed[e['event_id']] for e in aborted[0]['committed_events']))
        self.assertEqual(altered['summary']['completed_return_cuts']['outer_plus'],[26,33,40])

    def test_last_queued_response_is_not_falsely_applied(self):
        model = deepcopy(self.products['early_loss_scenario'])
        model['parameters']['end_cut'] = 40
        model['parameters']['contact_completion_cuts'] = [36,40]
        trace = s.simulate(model, self.fixture, ROOT)
        self.assertEqual(trace['pending_response']['committed_cut'],41)
        self.assertTrue(trace['summary']['final_retention']['outer_plus'])

    def test_parameterized_dwell_and_capacity_are_valid_inputs(self):
        model = deepcopy(self.products['baseline_scenario'])
        model['parameters']['outer_dwell_samples']['outer_plus'] = 1
        altered = s.simulate(model, self.fixture, ROOT)
        self.assertEqual(altered['summary']['completed_return_cuts']['outer_plus'],[27,35,43,51,59,67])
        self.assertEqual(altered['summary']['model_count_ratio'],'1')
        self.assertEqual(altered['statuses']['native_admission_status'],'pending')

    def test_zero_reference_increment_is_unknown_ratio(self):
        model = deepcopy(self.products['baseline_scenario'])
        model['parameters']['outer_dwell_samples'] = {'outer_plus':4,'outer_minus':4}
        model['parameters']['end_cut'] = 40
        model['parameters']['contact_completion_cuts'] = [36,40]
        trace = s.simulate(model, self.fixture, ROOT)
        self.assertIsNone(trace['summary']['model_count_ratio'])
        self.assertEqual(trace['summary']['ratio_status'],'undefined_zero_reference_increment')

    def test_contact_support_comes_from_committed_contact_events(self):
        events = {e['event_id']:e for r in self.base['cut_records'] for e in r['contact_events']}
        for contact in self.base['contacts']:
            self.assertTrue(all(e == events[e['event_id']] for e in contact['support']['events']))
            self.assertTrue(all(len(m['return_prefix']) >= 2 for m in contact['maps']))
        for result in self.base['responses']:
            a,b = result['boundary_pair']['forward'], result['boundary_pair']['reverse']
            self.assertEqual(Fraction(a['value']), -Fraction(b['value']))

    def test_persisted_trace_mutations_rejected(self):
        cases = [
            ('postloss phantom return', lambda d:d['outer_waves'][0]['returns'].append(deepcopy(self.base['outer_waves'][0]['returns'][3]))),
            ('postloss phantom contact', lambda d:d['contacts'].append(deepcopy(self.base['contacts'][2]))),
            ('loss state changed', lambda d:d['cut_records'][21]['states'][0].__setitem__('retained',True)),
            ('response not applied', lambda d:d['cut_records'][21].__setitem__('applied_response_ids',[])),
            ('earlier event erased', lambda d:d['cut_records'][5]['events'].pop()),
            ('prefix chain forged', lambda d:d['cut_records'][3].__setitem__('previous_record_sha256','0'*64)),
            ('inner map dropped', lambda d:d['exposures']['outer_plus'].pop()),
            ('scope alias', lambda d:d['exposures']['outer_plus'][0].__setitem__('inner_scope',d['exposures']['outer_plus'][0]['outer_scope'])),
            ('ratio fabricated', lambda d:d['summary'].__setitem__('model_count_ratio','1')),
            ('physical result invented', lambda d:d['summary'].__setitem__('physical_frequency_ratio','1')),
            ('missing status', lambda d:d['statuses'].pop('native_admission_status')),
            ('promoted admission', lambda d:d['statuses'].__setitem__('native_admission_status','admitted')),
            ('response status absent', lambda d:d['responses'][0].pop('status')),
            ('forged certificate', lambda d:d['outer_waves'][0]['returns'][0].__setitem__('certificate','certified')),
            ('mandatory hinge dropped', lambda d:d['outer_waves'][0]['returns'][0].__setitem__('roles',[1,-1])),
            ('contact event rewound', lambda d:d['contacts'][0]['support']['events'][0].__setitem__('cut',0)),
            ('finite horizon missing pending field', lambda d:d.pop('pending_response')),
        ]
        for name, action in cases:
            self.rejected(name,action)

    def test_persisted_scenario_and_report_mutations_rejected(self):
        cases = [
            ('negative capacity',lambda d:d['parameters']['capacity_schedule'][0].__setitem__('capacity','-1')),
            ('unknown frequency input',lambda d:d['parameters'].__setitem__('hydrogen_hz','1420405751.768')),
            ('bad dwell',lambda d:d['parameters']['outer_dwell_samples'].__setitem__('outer_plus',True)),
            ('missing source binding',lambda d:d['source_bindings'].pop()),
            ('automatic readmission',lambda d:d['rule'].__setitem__('readmission','automatic')),
            ('status removed',lambda d:d.pop('statuses')),
            ('unknown rule status',lambda d:d['rule'].__setitem__('radiation_identification','photon')),
            ('valid input with stale trace',lambda d:d['parameters']['capacity_schedule'][-1].__setitem__('capacity','1')),
        ]
        for name,action in cases:
            self.rejected(name,action,'early_loss_scenario.json')
        self.rejected('report claims atomic prediction',lambda d:d['statuses'].__setitem__('native_atomic_mapping_status','complete'),'stateful_report.json')

    def test_valid_verification_is_read_only_and_unknown_flags_fail(self):
        for optimized in (False, True):
            with tempfile.TemporaryDirectory() as tmp:
                root=self.disposable(tmp); before=snapshot(root)
                args=[sys.executable,'-B']+(['-O'] if optimized else [])+[str(root/VERIFIER),'--root',str(root)]
                result=subprocess.run(args,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(before,snapshot(root))
                bad=subprocess.run(args+['--repair'],capture_output=True,text=True)
                self.assertNotEqual(bad.returncode,0)
                self.assertEqual(before,snapshot(root))

    def test_generation_is_explicit_and_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            s.generate(ROOT,tmp)
            for name in s.FILES:
                self.assertEqual((ROOT/s.DATA/name).read_bytes(),(Path(tmp)/s.DATA/name).read_bytes())


if __name__ == '__main__':
    unittest.main()
