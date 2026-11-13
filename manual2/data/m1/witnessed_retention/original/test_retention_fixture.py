from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as Q
import json
import unittest

import retention_fixture as r


class RetentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=r.default_contract()
        cls.result=r.generate()

    def frame(self,case='burden',prefix='+-',observer=True):
        frame,mass,earlier=r.prepare_prefix(self.contract,case,prefix,observer)
        frame.prepare_next()
        return frame

    def test_source_binding(self):
        self.assertEqual(len(r.verify_sources()['sha256']),9)

    def test_exact_third_return_survival(self):
        cases=self.result['cases']
        self.assertEqual(cases['net_memory']['S3'],'5/6')
        self.assertEqual(cases['burden']['S3'],'2/3')
        self.assertEqual(cases['burden_feedback_off']['S3'],'1')
        self.assertEqual(cases['burden_latest_response_window']['S3'],'1')
        # Delayed background has one witnessed unit of lag at response two.
        self.assertEqual(cases['burden_background_pending']['S3'],'5/76')

    def test_exact_normalization_and_total_mass(self):
        for case in self.result['cases'].values():
            self.assertEqual(sum(Q(t['probability_mass']) for t in case['terminals']),1)
            self.assertEqual(Q(case['S3'])+Q(case['absorbed_probability']),1)
            for prefix in case['prefixes']:
                for decision in prefix['earlier_decisions']+[prefix['third_decision']]:
                    self.assertEqual(sum(Q(x) for x in decision['probabilities'].values()),1)
                    self.assertTrue(all(Q(x)>=0 for x in decision['probabilities'].values()))

    def test_raw_and_normalized_operands_remain_distinct(self):
        row=next(p for p in self.result['cases']['burden']['prefixes'] if p['prefix']=='+-')
        self.assertEqual((row['unit'],row['raw_signed'],row['raw_burden']),(5,'0','10'))
        self.assertEqual((row['normalized_signed'],row['normalized_burden']),('0','2'))
        self.assertEqual(row['raw_capacity'],'5')
        self.assertEqual(row['third_decision']['probabilities']['exit'],'1/3')

    def test_cancellation_preserves_contributions(self):
        frame=self.frame()
        self.assertEqual(frame.raw_signed(),0);self.assertEqual(frame.raw_burden(),10)
        self.assertEqual(len(frame.responses),2)
        self.assertEqual([Q(x['raw_burden']) for x in frame.responses],[5,5])
        self.assertEqual([Q(x['raw_signed']) for x in frame.responses],[5,-5])
        self.assertNotEqual(frame.responses[0]['candidate_return_id'],frame.responses[1]['candidate_return_id'])

    def test_orientation_is_not_lag_or_negative_closure(self):
        rows={p['prefix']:p for p in self.result['cases']['burden']['prefixes']}
        for a,b in [('++','--'),('+-','-+')]:
            self.assertEqual(Q(rows[a]['raw_signed']),-Q(rows[b]['raw_signed']))
            self.assertEqual(rows[a]['raw_burden'],rows[b]['raw_burden'])
            self.assertEqual(rows[a]['reference_lags'],['1','1'])
            self.assertEqual(rows[b]['reference_lags'],['1','1'])
            self.assertEqual(rows[a]['third_decision']['probabilities'],rows[b]['third_decision']['probabilities'])

    def test_changed_preparation_changes_measured_lag(self):
        frame=r.Fixture(self.contract,'burden',candidate_seed_override=3)
        frame.prepare_next()
        self.assertEqual(frame.pending_inputs['reference']['lag'],'0')
        self.assertEqual(frame.pending_inputs['reference']['candidate_bip'],frame.pending_inputs['reference']['sender_bip'])

    def test_reference_decision_requires_actual_return(self):
        frame=r.Fixture(self.contract,'burden')
        before=frame.measured_reference();frame.prepare_next()
        self.assertEqual(frame.measured_reference(),before+1)
        trace,cert,registry=frame.reference.records[-1]
        r.n.admitted(trace,cert,registry)
        self.assertEqual(trace.vertices[0],trace.vertices[-1])
        self.assertGreater(frame.pending_decision['cut'],trace.indices[-1])

    def test_no_response_alias_can_be_counted_twice(self):
        frame=self.frame();frame.responses.append(deepcopy(frame.responses[0]))
        with self.assertRaisesRegex(ValueError,'more than one response'):frame.validate()

    def test_changed_lag_and_recomputed_totals_rejected(self):
        frame=self.frame()
        response=frame.responses[0]
        term=next(t for t in response['terms'] if t['sender']=='reference')
        term['lag']='2';term['raw_signed']='10';term['raw_burden']='10'
        response['raw_signed']='10';response['raw_burden']='10'
        with self.assertRaisesRegex(ValueError,'regenerate'):frame.validate()

    def test_changed_response_orientation_rejected(self):
        frame=self.frame();frame.responses[0]['terms'][0]['orientation']=-1
        with self.assertRaisesRegex(ValueError,'orientation'):frame.validate()

    def test_changed_contact_prefix_rejected(self):
        frame=self.frame();ch=frame.channels['reference'];old=ch.events[-2]
        ch.events[-2]=replace(old,left_prefix='0'*64)
        with self.assertRaises((ValueError,r.n.AdmissionError)):frame.validate()

    def test_unconsumed_formation_contact_is_still_bound(self):
        frame=self.frame();ch=frame.channels['background']
        ch.events[0]=replace(ch.events[0],left_prefix='0'*64)
        with self.assertRaisesRegex(ValueError,'actual committed pair prefixes'):frame.validate()

    def test_future_operands_rejected(self):
        frame=self.frame();frame.responses[0]['terms'][0]['comparison_cut']=frame.clock.cut+1
        with self.assertRaises((ValueError,r.n.AdmissionError)):frame.validate()

    def test_feedback_is_strictly_later(self):
        for case in self.result['cases'].values():
            for row in case['prefixes']:
                decision=row['third_decision']
                self.assertLess(decision['consumed_through'],decision['cut'])
                response_ids=decision['active_response_ids']
                self.assertTrue(all(len(identity.split(':')[-1])<=2 for identity in response_ids))
        # Fresh third-contact reflection can affect a later response, not the
        # already committed two-response load consumed by decision three.
        a,_,_=r.prepare_prefix(self.contract,'burden','+-')
        b=deepcopy(a)
        self.assertEqual(a.prepare_next()['probabilities'],b.prepare_next(reverse_extra=1)['probabilities'])

    def test_matched_prefix_and_feedback_disabled(self):
        cases=self.result['cases']
        for index in range(4):
            signatures=[cases[name]['prefixes'][index]['committed_prefix_sha256'] for name in
                        ('net_memory','burden','burden_feedback_off','burden_latest_response_window')]
            self.assertEqual(len(set(signatures)),1)
        disabled=cases['burden_feedback_off']['prefixes'][1]
        self.assertEqual(disabled['raw_burden'],'10')
        self.assertEqual(disabled['third_decision']['selected_raw_load'],'0')
        self.assertEqual(len(disabled['third_decision']['exclusions']),2)

    def test_window_expiry_retains_history(self):
        frame=self.frame('burden_latest_response_window')
        self.assertEqual(frame.raw_burden(),10)
        self.assertEqual(frame.pending_decision['selected_raw_load'],'5')
        self.assertEqual(len(frame.responses),2)
        self.assertEqual(len(frame.pending_decision['exclusions']),1)

    def test_population_lag_enters_retention(self):
        base=self.frame();changed=self.frame('burden_background_pending')
        self.assertEqual(base.background.wave().motif,'3:4')
        self.assertEqual(changed.background.wave().motif,'3:4')
        self.assertTrue(all(m.enclosure==6 for m in changed.background.motifs))
        self.assertIsNotNone(changed.background.pending)
        self.assertEqual(changed.background.pending['atomic_steps'],1)
        self.assertEqual(changed.raw_burden(),147)
        self.assertEqual(changed.pending_decision['probabilities']['exit'],'71/76')
        self.assertEqual(changed.responses[1]['terms'][0]['lag'],'1')

    def test_directional_rcd_recomputed(self):
        frame=r.Fixture(self.contract,'burden');frame.prepare_next(reverse_extra=1);frame.retain('+')
        frame.prepare_next(reverse_extra=1)
        ch=frame.channels['reference']
        forward=ch.comparison(frame.clock.cut,frame.window_length)
        reverse=ch.comparison(frame.clock.cut,frame.window_length,reverse=True)
        self.assertEqual(forward['duration'],5);self.assertEqual(reverse['duration'],7)
        self.assertEqual(forward['lag'],-reverse['lag'])
        ch.validate()

    def test_drift_uses_previous_committed_comparison(self):
        base=self.frame();changed=self.frame('burden_background_pending')
        reference=[next(t for t in x['terms'] if t['sender']=='reference') for x in base.responses]
        self.assertEqual([(x['lag'],x['prior_lag'],x['drift']) for x in reference],
                         [('1','2','-1'),('1','1','0')])
        bg=next(t for t in changed.responses[1]['terms'] if t['sender']=='background')
        self.assertEqual((bg['lag'],bg['prior_lag'],bg['drift']),('1','0','1'))

    def test_passive_observer_cannot_change_execution(self):
        a=self.frame(observer=True);b=self.frame(observer=False)
        self.assertTrue(a.observations);self.assertFalse(b.observations)
        self.assertEqual(a.clock.events,b.clock.events)
        self.assertEqual(a.responses,b.responses)
        self.assertEqual(a.pending_decision,b.pending_decision)

    def test_exposure_preserves_inner_lineage_and_counts(self):
        frame=self.frame();before=frame.candidate.wave();parent_returns=len(frame.parent_records)
        exited=frame.lose()
        self.assertEqual(frame.candidate.wave(),before)
        self.assertEqual(len(frame.parent_records),parent_returns)
        self.assertEqual(exited['exposed_certificate_digests'],[c.certificate_digest for c in before.certificates])
        self.assertEqual(exited['shedding']['surplus'],5)
        counts=r.terminal_counts(frame,'absorbed')
        self.assertEqual((counts['candidate_reclosures'],counts['parent_reclosures'],counts['reference_bips']),(2,2,3))
        self.assertEqual((counts['candidate_atomic_traversals'],counts['outer_atomic_traversals']),(8,10))

    def test_open_exit_is_not_a_closure(self):
        frame=self.frame();exited=frame.lose();raw=exited['open_path']
        self.assertNotEqual(raw['vertices'][0],raw['vertices'][-1])
        self.assertIsNone(exited['physical_decay']);self.assertIsNone(exited['daughter_identity'])

    def test_zero_weight_loss_cannot_be_installed(self):
        frame=self.frame('net_memory')
        with self.assertRaisesRegex(ValueError,'positive computed weight'):frame.lose()

    def test_json_roundtrip_and_changed_artifact(self):
        serialized=json.loads(r.canonical(self.result))
        self.assertTrue(r.verify_report(serialized,original_contract=self.contract))
        changed=deepcopy(serialized)
        changed['cases']['burden']['S3']='5/6'
        changed.pop('report_sha256');changed['report_sha256']=r.digest(changed)
        with self.assertRaisesRegex(ValueError,'original-context replay'):
            r.verify_report(changed,original_contract=self.contract)

    def test_no_measured_or_fitted_operand_can_be_added(self):
        for key,value in [('experimental_inputs',['half_life']),('fit_parameters',[1]),
                          ('physical_seconds','1'),('isotope_state_assignment','Og-294')]:
            changed=deepcopy(self.contract);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.generate(changed)

    def test_boolean_and_float_cannot_substitute_for_integer_cut(self):
        for value in (False,0.0):
            changed=deepcopy(self.contract);changed['horizon']['allowed_cut_window'][0]=value
            with self.subTest(value=value),self.assertRaises(ValueError):r.generate(changed)


if __name__=='__main__':unittest.main(verbosity=2)
