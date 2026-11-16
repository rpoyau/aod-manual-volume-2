"""Current-native construction and executable finite campaign controls."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as Q
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'manual2/scripts'))
import matter1_campaign_engine as e


class CampaignEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = e.default_config(1, 1)
        cls.result = e.run_case(cls.config, ROOT)
        off = dict(cls.config, feedback=False)
        cls.control = e.run_case(off, ROOT)

    def test_exact_inventory_and_hydrogen_zero_neutrons(self):
        self.assertEqual(e.inventory(self.config), (('p000',3,3),('e000',1,2)))
        self.assertEqual(e.inventory(e.default_config(2,4)),
                         (('p000',3,3),('p001',3,3),('n000',3,4),('n001',3,4),('e000',1,2),('e001',1,2)))
        with self.assertRaisesRegex(ValueError, 'inapplicable'):
            e.remove_neutron(self.config)
        self.assertEqual(e.remove_neutron(e.default_config(1,2))['a'], 1)

    def test_strict_integer_and_declared_schema(self):
        for key in ('z','a','electron_count','rounds','seed'):
            for invalid in (True,False,1.0,'1'):
                bad = dict(self.config); bad[key] = invalid
                with self.assertRaises(ValueError): e.validate_config(bad)
        for extra in ('physical_frequency_hz','capacity','half_life','state_label'):
            with self.assertRaises(ValueError): e.validate_config(dict(self.config, **{extra:1}))
        for bad in (dict(self.config,a=0),dict(self.config,rounds=0),dict(self.config,rounds=9),
                    dict(self.config,electron_count=2),dict(self.config,feedback=1)):
            with self.assertRaises(ValueError): e.validate_config(bad)

    def test_current_native_and_separate_constructor_authorities(self):
        b = self.result['source_bindings']
        self.assertEqual(b['native_head'], e.CURRENT_HEAD)
        self.assertEqual(b['native_sha256'], e.CURRENT_NATIVE_SHA)
        self.assertIn('constructor_recipe', b)
        constructed = e.construct(self.config, ROOT)
        self.assertEqual(constructed.module.n.__file__,
                         str(ROOT/'manual2/vendor/aod_m3/current/aod_native_closure_wave.py'))
        for wave in constructed.field.inner:
            constructed.module.n.validate_wave(wave)

    def test_distinct_constituents_and_scope_maps(self):
        c = self.result['construction']
        identities = [r['wave_identity'] for r in c['constituents']]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertEqual(c['outward_occurrences'],34)
        self.assertEqual(c['structural_RD'],69)
        for row in c['inner_to_outer_maps']:
            self.assertLess(row[2],row[4])
            self.assertNotEqual(row[1],row[3])

    def test_inner_histories_actually_extend_then_bind_outer(self):
        t = self.result['trajectory']
        self.assertEqual(len(t['inner_returns']),6)
        self.assertTrue(self.result['inner_prefixes_extended'])
        self.assertEqual(len({r['return_id'] for r in t['inner_returns']}),6)
        self.assertGreater(t['outer_return']['start'],max(r['committed'] for r in t['inner_returns']))
        self.assertNotEqual(self.result['updated_fold_proposal_sha256'],
                            self.result['construction']['fold_proposal_sha256'])
        for row in t['inner_returns']:
            self.assertGreaterEqual(row['atomic_traversals'],2)
            self.assertEqual(row['hinge_count'],1)

    def test_exact_conditional_kernels_and_seeded_choices(self):
        rng = random.Random(self.config['seed'])
        for d in self.result['trajectory']['decisions']:
            weights, probs = e.kernel(d['response'])
            self.assertEqual(d['weights'],list(weights))
            self.assertEqual(list(map(Q,d['probabilities'])),list(probs))
            self.assertEqual(sum(probs),1)
            draw = rng.randrange(sum(weights))
            self.assertEqual(d['draw'],draw)
            self.assertEqual(d['orientation'],1 if draw<weights[0] else -1)
            self.assertEqual(Q(d['selected_probability']),probs[0 if d['orientation']==1 else 1])
        with self.assertRaises(ValueError): e.kernel(1.0)

    def test_committed_feedback_drives_only_later_transition(self):
        contacts = {r['id']:r for r in self.result['trajectory']['contacts']}
        affected = []
        for d in self.result['trajectory']['decisions']:
            self.assertLess(d['response_cut'],d['start'])
            for identity in d['consumed_contact_ids']:
                self.assertLess(contacts[identity]['committed'],d['start'])
            if d['round'] and d['response']:
                affected.append(d)
        self.assertTrue(affected)

    def test_matched_prefix_and_real_later_feedback_change(self):
        baseline = self.result['trajectory']; control = self.control['trajectory']
        self.assertEqual([r for r in baseline['inner_returns'] if r['round']==0],
                         [r for r in control['inner_returns'] if r['round']==0])
        self.assertNotEqual([r for r in baseline['inner_returns'] if r['round']==1],
                            [r for r in control['inner_returns'] if r['round']==1])
        self.assertNotEqual(baseline['outer_return']['committed'],control['outer_return']['committed'])
        cut = min(baseline['outer_return']['committed'],control['outer_return']['committed'])
        self.assertEqual(sum(r['committed']<=cut for r in baseline['reference_returns']),
                         sum(r['committed']<=cut for r in control['reference_returns']))
        self.assertEqual(int(baseline['outer_return']['committed']<=cut),0)
        self.assertEqual(int(control['outer_return']['committed']<=cut),1)

    def test_returned_current_uses_real_emission_and_paired_response(self):
        returns = {r['return_id']:r for r in self.result['trajectory']['inner_returns']}
        signed, burden = 0,0
        for row in self.result['trajectory']['contacts']:
            self.assertLess(row['emitted'],row['committed'])
            self.assertEqual(row['signed_response']+row['opposite_response'],0)
            if not row['formation']:
                self.assertEqual(returns[row['source_return_id']]['committed'],row['emitted'])
                self.assertEqual(row['signed_response'],row['orientation']*row['rcd']*row['lag_at_emission'])
                signed += row['signed_response']; burden += row['nonnegative_burden']
        self.assertGreater(burden,0)
        self.assertGreaterEqual(burden,abs(signed))

    def test_observer_is_passive(self):
        passive = e.run_case(self.config,ROOT,observer=False)
        self.assertEqual(passive['trajectory_sha256'],self.result['trajectory_sha256'])
        self.assertEqual(passive['trajectory'],self.result['trajectory'])
        self.assertIsNone(passive['observation'])

    def test_native_observation_counts_actual_reference_returns(self):
        o = self.result['observation']; self.assertIsNotNone(o)
        lo,hi = o['window']
        refs = [r for r in self.result['trajectory']['reference_returns'] if lo<r['committed']<=hi]
        self.assertEqual(o['reference_new_returns'],len(refs))
        self.assertEqual(Q(o['cadence_ratio']),Q(1,len(refs)))
        self.assertEqual(Q(o['lag']),1-len(refs))
        self.assertEqual(e.summary(self.result)['phase_unit'],'complete retained return')
        self.assertFalse(e.summary(self.result)['cross_configuration_frequency_ratio_identified'])

    def test_no_physical_loss_or_identification_is_invented(self):
        self.assertEqual(self.result['empirical_inputs_read'],[])
        self.assertFalse(self.result['construction']['native_atomic_identification'])
        self.assertFalse(self.result['execution']['native_frg_gate_executed'])
        for name in ('atomic_state_identification','emitted_phase_map','nuclear_loss_rule',
                     'survival_probability','half_life_seconds','frequency_hz'):
            self.assertIsNone(self.result['physical'][name])

    def test_original_context_rejects_resealed_changed_trace(self):
        bad = deepcopy(self.result)
        bad['trajectory']['inner_returns'][0]['committed'] += 1
        bad['trajectory_sha256'] = e.digest(bad['trajectory'])
        with self.assertRaisesRegex(ValueError,'original-input'):
            e.verify_case(self.config,bad,ROOT)


    def test_cache_complete_output_equivalence(self):
        uncached = e.run_case(self.config, ROOT, _cached=False)
        self.assertEqual(e.canonical(uncached), e.canonical(self.result))
        deuterium = e.default_config(1,2)
        cached_neutron = e.run_case(deuterium,ROOT)
        uncached_neutron = e.run_case(deuterium,ROOT,_cached=False)
        self.assertEqual(e.canonical(cached_neutron),e.canonical(uncached_neutron))

    def test_cached_positive_does_not_admit_replaced_forgeries(self):
        built = e.construct(self.config, ROOT)
        n = built.module.n
        w = built.field.inner[0]
        n.validate_wave(w)
        with self.assertRaises(Exception): n.validate_wave(replace(w,identity='forged'))
        cert = replace(w.certificates[0],certificate_digest='forged')
        with self.assertRaises(Exception):
            n.validate_wave(replace(w,certificates=(cert,*w.certificates[1:])))
        t = w.returns[0]
        n.certify(t)
        with self.assertRaises(Exception): n.certify(t,'not-a-motif')
        outer_t = built.field.records[0][0]
        n.certify(outer_t,'outer',inner=built.field.inner)
        with self.assertRaises(Exception): n.certify(outer_t,'outer',inner=(w,))
        with self.assertRaises(Exception):
            n.admitted(t,w.certificates[0],{})

    def test_rcd_rejects_wrong_contact_binding(self):
        built = e.construct(self.config, ROOT)
        left,right = built.field.inner
        contacts = [e._contact(built.module,left,right,('e000',1,2),2000+100*j,
                                'negative-control:'+str(j),0,1) for j in range(2)]
        self.assertEqual(e._rcd(built.module,left,right,contacts,9).duration(),9)
        bad = [contacts[0],replace(contacts[1],left_prefix='forged')]
        with self.assertRaises(Exception): e._rcd(built.module,left,right,bad,9)
        with self.assertRaises(Exception): e._rcd(built.module,left,right,list(reversed(contacts)),9)
        with self.assertRaises(Exception): e._rcd(built.module,left,right,contacts,61)


    def test_projection_rejects_false_and_unknown_statuses(self):
        mutations = [
            ('construction','native_construction_admitted',False),
            ('construction','native_construction_admitted',1),
            ('construction','native_atomic_identification',True),
            ('execution','status','not_executed'),
            ('execution','native_inner_and_outer_returns_admitted',False),
            ('execution','native_frg_gate_executed',True),
            ('execution','new_outer_reclosures',True),
            ('execution','inner_reclosures',0),
            ('physical','half_life_seconds',0),
            ('observation','cadence_ratio','1'),
            ('observation','lag',-2),
            ('observation','reference_new_returns',3.0),
            ('observation','window',[0,1]),
        ]
        for section,key,value in mutations:
            with self.subTest(section=section,key=key,value=value):
                bad = deepcopy(self.result);bad[section][key] = value
                with self.assertRaises(ValueError):e.summary(bad)
        bad = deepcopy(self.result);bad['observation'] = None;bad['observation_dependency'] = None
        with self.assertRaises(ValueError):e.summary(bad)

    def test_independent_exact_small_ensemble(self):
        config = dict(self.config,rounds=2)
        ensemble = e.exact_small_ensemble(config,ROOT)
        self.assertEqual(len(ensemble['paths']),16)
        self.assertEqual(sum(Q(p['probability']) for p in ensemble['paths']),1)
        self.assertGreater(len({p['outer_commit'] for p in ensemble['paths']}),1)


if __name__ == '__main__':
    unittest.main()
