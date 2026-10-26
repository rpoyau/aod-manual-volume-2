"""Exact finite model tests plus real persisted mutations, normal and optimized.

Every rejection invokes the public read-only verifier against mutated JSON in a
fresh disposable repository. Before/after snapshots include every file and path.
These assertions do not establish complete native motif admission or spectroscopy.
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
sys.path.insert(0, str(ROOT / 'manual2' / 'scripts'))
import matter1_temporal as temporal

DATA = Path('manual2/data/m1/folding')
VERIFIER = Path('manual2/scripts/verify_matter1_temporal.py')


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def trace_at(document, wave=0, occurrence=0):
    return document['outer_waves'][wave]['returns'][occurrence]


def recertify(trace):
    trace['certificate'] = temporal.certificate_for(trace)


class TemporalModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = temporal.read_json(ROOT / DATA / 'two_square_fold.json')
        cls.model = temporal.read_json(ROOT / DATA / 'temporal_model.json')
        cls.bundle = temporal.read_json(ROOT / DATA / 'temporal_trace.json')
        cls.report = temporal.read_json(ROOT / DATA / 'temporal_report.json')

    def disposable(self, parent):
        root = Path(parent) / 'repo'
        for relative in [VERIFIER, Path('manual2/scripts/matter1_temporal.py'),
                         Path('manual2/scripts/matter1_folding.py'),
                         Path('manual2/scripts/generate_matter1_temporal.py'),
                         *(Path(name) for name in temporal.SOURCE_LABELS),
                         *(DATA / name for name in ('two_square_fold.json', 'temporal_model.json',
                                                    'temporal_trace.json', 'temporal_report.json'))]:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return root

    def rejected(self, name, change, filename='temporal_trace.json', diagnostic=None):
        for optimized in (False, True):
            with self.subTest(mutation=name, optimized=optimized), tempfile.TemporaryDirectory() as temporary:
                root = self.disposable(temporary)
                path = root / DATA / filename
                value = json.loads(path.read_text())
                change(value)
                path.write_bytes(temporal.canonical_bytes(value))
                before = snapshot(root)
                command = [sys.executable, '-B'] + (['-O'] if optimized else []) + [str(root / VERIFIER), '--root', str(root), '--check-data']
                result = subprocess.run(command, capture_output=True, text=True, check=False)
                self.assertNotEqual(result.returncode, 0, f'Mutation accepted: {name}\n{result.stdout}')
                self.assertIn('ERROR:', result.stderr, result.stderr)
                if diagnostic:
                    self.assertIn(diagnostic, result.stderr)
                self.assertEqual(before, snapshot(root), f'Verification wrote or created files: {name}')

    def test_p2_01_structural_certificates(self):
        self.rejected('forged certificate label', lambda d: trace_at(d).__setitem__('certificate', 'certified'))
        self.rejected('wrong certificate scope', lambda d: trace_at(d)['certificate'].__setitem__('scope', 'another-scope'))
        def wrong_witness(d):
            t = trace_at(d)
            t['retained_return']['retained_start_id'] = t['events'][-1]['event_id']
            recertify(t)
        self.rejected('rehashed wrong retained start', wrong_witness, diagnostic='Retained start identity')
        def wrong_scope(d):
            t = trace_at(d)
            t['retained_return']['scope'] = 'another-scope'
            recertify(t)
        self.rejected('rehashed wrong witness scope', wrong_scope, diagnostic='own scope/lineage')

    def test_p2_02_hinge_is_mandatory(self):
        def drop(d):
            t = trace_at(d, 1)
            t['roles'] = [-1, 1]
            recertify(t)
        self.rejected('drop structural hinge and dwell', drop, diagnostic='Mandatory structural hinge')
        def missing(d):
            t = trace_at(d)
            t['retained_return']['hinge_event_id'] = t['events'][0]['event_id']
            recertify(t)
        self.rejected('hinge replaced by origin', missing, diagnostic='Mandatory witnessed structural hinge')
        # Removing the optional dwell leaves the mandatory structural hinge.
        trace = temporal.make_trace('no-dwell', 'scope', 1, 'lineage', self.fixture['outer_walk'],
                                     self.fixture['vertices'], 0, 1)
        result = temporal.validate_trace(trace, self.fixture)
        self.assertEqual((result['traversals'], result['dwell_samples']), (6, 0))
        self.assertEqual(trace['roles'], [1, 0, -1])

    def test_p2_03_explicit_cross_scale_maps(self):
        def mutate_map(d, action):
            t = trace_at(d)
            action(t['fold'])
            recertify(t)
        self.rejected('missing inner map', lambda d: mutate_map(d, lambda f: f['inner_maps'].pop()))
        self.rejected('substituted map', lambda d: mutate_map(d, lambda f: f['inner_maps'][1]['vertex_map'].__setitem__('w', 'D')),
                      diagnostic='Inner-to-outer incidence map')
        self.rejected('forced cross-scale equality', lambda d: mutate_map(d, lambda f: f['inner_maps'][0].__setitem__('inner_scope', trace_at(d)['scope'])))
        self.rejected('inner return reused as outer', lambda d: trace_at(d).__setitem__('certificate', deepcopy(d['inner_waves'][0]['returns'][0]['certificate'])))
        mapping = trace_at(self.bundle)['fold']['inner_maps']
        self.assertNotEqual(mapping[0]['inner_scope'], mapping[1]['inner_scope'])
        self.assertTrue(all(m['inner_scope'] != m['outer_scope'] for m in mapping))

    def test_p2_04_f04_exposure_preserves_provenance(self):
        result = self.bundle['responses'][-1]
        self.assertEqual(result['outer_retention'], 'lost_by_declared_capacity_rule')
        self.assertEqual(result['exposure'], result['preserved_inner_maps'])
        self.assertEqual(result['exposure'], trace_at(self.bundle)['fold']['inner_maps'])
        self.rejected('lost exposure certificate', lambda d: d['responses'][-1]['exposure'][0]['inner_certificates'].pop())
        self.rejected('lost inner orientation', lambda d: d['responses'][-1]['exposure'][0].__setitem__('inner_chirality', -1))
        self.rejected('substituted inner lineage', lambda d: d['responses'][-1]['exposure'][0].__setitem__('inner_lineage', 'substitute'))

    def test_p2_05_replay_cannot_add_beat(self):
        self.rejected('replayed complete return', lambda d: d['outer_waves'][0]['returns'].__setitem__(1, deepcopy(trace_at(d))))
        def reuse(d):
            t = trace_at(d)
            t['events'][2]['event_id'] = t['events'][1]['event_id']
            recertify(t)
        self.rejected('reused event with new certificate', reuse, diagnostic='Immutable event identity')
        self.assertEqual(temporal.beat_count(self.bundle['outer_waves'][0], 33, 47), 2)
        self.assertEqual(self.report['wave_summaries']['outer_plus']['beats_from_origin'], 4)

    def test_p2_06_target_input_rejected(self):
        self.rejected('desired period input', lambda d: d['update_rule'].__setitem__('desired_period', 9192631770), 'temporal_model.json')
        self.rejected('measured target input', lambda d: d.__setitem__('measured_hydrogen_hz', '1420405751.768'), 'temporal_model.json')
        self.rejected('predictive promotion', lambda d: d['update_rule'].__setitem__('predictive_status', 'independent_prediction'), 'temporal_model.json')

    def test_p3_01_reciprocal_comparison(self):
        for comparison in self.bundle['comparisons']:
            self.assertEqual(Fraction(comparison['forward']['ratio']) * Fraction(comparison['reverse']['ratio']), 1)
            self.assertEqual(Fraction(comparison['forward']['bias']), -Fraction(comparison['reverse']['bias']))
            self.assertEqual(Fraction(comparison['forward']['unwrapped_lag']), -Fraction(comparison['reverse']['unwrapped_lag']))
        self.rejected('wrong reversed ratio', lambda d: d['comparisons'][1]['reverse'].__setitem__('ratio', '3/2'))

    def test_p3_02_bias_unwrapped_lag_and_later_window(self):
        waves, contacts = self.bundle['outer_waves'], self.bundle['contacts']
        original = self.bundle['comparisons'][0]
        unbiased = temporal.compare(waves, contacts, 20, 43,
                                     {'outer_plus': '0', 'outer_minus': '0'}, self.model['comparison']['duration_map'])
        self.assertEqual(original['forward']['ratio'], unbiased['forward']['ratio'])
        self.assertNotEqual(original['forward']['unwrapped_lag'], unbiased['forward']['unwrapped_lag'])
        later = temporal.compare(waves, contacts, 34, 47, self.model['comparison']['biases'], self.model['comparison']['duration_map'])
        self.assertEqual(later['beat_counts'], [2, 2])
        self.assertEqual(later['cumulative_reclosure_counts'], [3, 2])
        self.assertEqual(later['forward']['unwrapped_lag'], '3/2')
        self.rejected('wrapped lag loses whole closure', lambda d: d['comparisons'][1]['forward'].__setitem__('unwrapped_lag', '1/2'))
        self.rejected('wrong drift', lambda d: d['comparisons'][1].__setitem__('lag_drift', '0'))

    def test_p3_03_repeated_bound_contacts(self):
        with self.assertRaisesRegex(temporal.ValidationError, 'Repeated independent bound contacts'):
            temporal.compare(self.bundle['outer_waves'], self.bundle['contacts'][:1], 20, 43,
                             self.model['comparison']['biases'], self.model['comparison']['duration_map'])
        self.rejected('only one contact', lambda d: d.__setitem__('contacts', d['contacts'][:1]))
        self.rejected('uncoupled identities', lambda d: d['contacts'][0]['direction'].__setitem__(1, d['contacts'][0]['direction'][0]))
        self.rejected('contact certificate replay', lambda d: d['contacts'][1].__setitem__('support', deepcopy(d['contacts'][0]['support'])))

    def test_p3_04_directional_duration_map(self):
        self.assertTrue(all(c['forward']['duration'] == 5 and c['reverse']['duration'] == 7 for c in self.bundle['comparisons']))
        self.assertTrue(all(c['forward']['declared_contact_support'] == 3 for c in self.bundle['comparisons']))
        self.rejected('absent duration map', lambda d: d['comparison'].pop('duration_map'), 'temporal_model.json')
        self.rejected('forced symmetric reflected input', lambda d: d['comparison']['duration_map'].__setitem__('reverse_reflections', [1, 1]), 'temporal_model.json')
        self.rejected('forced symmetric directional duration', lambda d: d['comparisons'][0]['reverse'].__setitem__('duration', 5))

    def test_p3_05_next_step_causality(self):
        self.assertTrue(all(r['committed_cut'] == r['input_cut'] + 1 for r in self.bundle['responses']))
        self.rejected('same-step self input', lambda d: d['responses'][0].__setitem__('committed_cut', d['responses'][0]['input_cut']), diagnostic='Causal response')
        self.rejected('response as own input', lambda d: d['responses'][0].__setitem__('input_comparison_id', d['responses'][0]['response_id']))

    def test_f01_opposite_handedness_equal_support(self):
        results = [temporal.validate_trace(trace_at(self.bundle, i), self.fixture) for i in (0, 1)]
        self.assertEqual([r['support_sum'] for r in results], [7, 7])
        self.assertEqual([trace_at(self.bundle, i)['chirality'] for i in (0, 1)], [1, -1])
        self.assertNotEqual(self.bundle['outer_waves'][0]['identity'], self.bundle['outer_waves'][1]['identity'])
        def flip(d):
            t = trace_at(d)
            t['chirality'] = -1
            t['roles'] = [-1, 0, 1]
            recertify(t)
        self.rejected('orientation flip without oriented trace', flip, diagnostic='Oriented outer trace')

    def test_f02_common_history_and_boundary_pair(self):
        self.rejected('future contact prefix', lambda d: d['contacts'][0]['maps'][0]['return_prefix'].append(d['outer_waves'][0]['returns'][-1]['certificate']['return_id']))
        self.rejected('substituted response prefix', lambda d: d['responses'][0]['input_history_maps'][0]['return_prefix'].pop())
        self.rejected('same orientation masquerades as pair', lambda d: d['responses'][0]['boundary_pair']['reverse'].__setitem__('orientation', 1), diagnostic='Opposite boundary orientations')
        self.rejected('wrong boundary paired by negation', lambda d: d['responses'][0]['boundary_pair']['reverse'].__setitem__('boundary_id', 'unrelated'), diagnostic='Same boundary pairing preserves boundary_id')
        self.rejected('edge not actually reversed', lambda d: d['responses'][0]['boundary_pair']['reverse'].__setitem__('oriented_edge', ['0000', '1000']), diagnostic='Actual reversed H1 boundary incidence')
        for result in self.bundle['responses']:
            temporal.validate_boundary_pair(result['boundary_pair'])
            self.assertEqual(Fraction(result['sadar']), -Fraction(result['same_boundary_reversed_sadar']))

    def test_f03_lag_alone_does_not_shed(self):
        for result in self.bundle['responses'][:2]:
            self.assertNotEqual(Fraction(result['signed_lag']), 0)
            self.assertLess(Fraction(result['residual']), 0)
            self.assertEqual(result['excess'], '0')
            self.assertIsNone(result['route'])
        self.rejected('nonzero lag promoted to shedding', lambda d: d['responses'][0].__setitem__('excess', '1/2'))
        self.rejected('wrong capacity domain', lambda d: d['responses'][0].__setitem__('capacity_domain', 'hertz'))

    def test_f08_orientation_is_not_fusion(self):
        def remove_fold(d):
            t = trace_at(d)
            t['fold'] = None
            recertify(t)
        self.rejected('handedness without fold evidence', remove_fold, diagnostic='Orientation alone does not certify')

    def test_p5_04_positive_readonly_and_reproduction(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.disposable(temporary)
            before = snapshot(root)
            for optimized in (False, True):
                command = [sys.executable, '-B'] + (['-O'] if optimized else []) + [str(root / VERIFIER), '--root', str(root)]
                result = subprocess.run(command, capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(before, snapshot(root))
            target = Path(temporary) / 'outputs'
            temporal.generate(root, target)
            self.assertEqual(before, snapshot(root))
            self.assertEqual(set(snapshot(target)), {str(DATA / 'temporal_trace.json'), str(DATA / 'temporal_report.json')})
            for name in ('temporal_trace.json', 'temporal_report.json'):
                self.assertEqual((target / DATA / name).read_bytes(), (root / DATA / name).read_bytes())
            result = subprocess.run([sys.executable, '-B', str(root / VERIFIER), '--unknown'], capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(before, snapshot(root))

    def test_p5_06_all_statuses_and_exact_types(self):
        for field in temporal.STATUSES:
            self.rejected('promote trace status ' + field, lambda d, f=field: d['statuses'].__setitem__(f, 'completed'))
            self.rejected('omit model status ' + field, lambda d, f=field: d['statuses'].pop(f), 'temporal_model.json')
        self.rejected('certificate native promotion', lambda d: trace_at(d)['certificate'].__setitem__('native_admission_status', 'admitted'))
        self.rejected('comparison native promotion', lambda d: d['comparisons'][0].__setitem__('status', 'native_executed'))
        self.rejected('route reclosure promotion', lambda d: d['responses'][-1]['route'].__setitem__('next_scope_reclosure', 'completed'))
        self.rejected('report native promotion', lambda d: d['statuses'].__setitem__('native_admission_status', 'admitted'), 'temporal_report.json')
        self.rejected('float report count', lambda d: d.__setitem__('outer_traversals_per_closure', 6.0), 'temporal_report.json')
        self.rejected('boolean sequencer count', lambda d: d['update_rule'].__setitem__('initialization_samples_per_cycle', True), 'temporal_model.json')
        self.rejected('float cycle count', lambda d: d['update_rule'].__setitem__('inner_cycles', 4.0), 'temporal_model.json')


if __name__ == '__main__':
    unittest.main()
