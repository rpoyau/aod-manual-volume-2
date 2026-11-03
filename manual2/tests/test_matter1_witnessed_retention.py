from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as Q
import json
import unittest
import hashlib
import shutil
import subprocess
import tempfile

from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'manual2/scripts'))
import matter1_witnessed_retention as r


class RetentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=r.default_contract()
        cls.result=r.predict(ROOT)

    def frame(self,case='burden',prefix='+-',observer=True):
        frame,mass,earlier=r.prepare_prefix(self.contract,case,prefix,observer)
        frame.prepare_next()
        return frame

    def test_WR_01_source_binding(self):
        self.assertEqual(len(r.verify_sources()['sha256']),9)

    def test_WR_02_exact_third_return_survival(self):
        cases=self.result['cases']
        self.assertEqual(cases['net_memory']['S3'],'5/6')
        self.assertEqual(cases['burden']['S3'],'2/3')
        self.assertEqual(cases['burden_feedback_off']['S3'],'1')
        self.assertEqual(cases['burden_latest_response_window']['S3'],'1')
        # Delayed background has one witnessed unit of lag at response two.
        self.assertEqual(cases['burden_background_pending']['S3'],'5/76')

    def test_WR_03_exact_normalization_and_total_mass(self):
        for case in self.result['cases'].values():
            self.assertEqual(sum(Q(t['probability_mass']) for t in case['terminals']),1)
            self.assertEqual(Q(case['S3'])+Q(case['absorbed_probability']),1)
            for prefix in case['prefixes']:
                for decision in prefix['earlier_decisions']+[prefix['third_decision']]:
                    self.assertEqual(sum(Q(x) for x in decision['probabilities'].values()),1)
                    self.assertTrue(all(Q(x)>=0 for x in decision['probabilities'].values()))

    def test_WR_04_raw_and_normalized_operands_remain_distinct(self):
        row=next(p for p in self.result['cases']['burden']['prefixes'] if p['prefix']=='+-')
        self.assertEqual((row['unit'],row['raw_signed'],row['raw_burden']),(5,'0','10'))
        self.assertEqual((row['normalized_signed'],row['normalized_burden']),('0','2'))
        self.assertEqual(row['raw_capacity'],'5')
        self.assertEqual(row['third_decision']['probabilities']['exit'],'1/3')

    def test_WR_05_cancellation_preserves_contributions(self):
        frame=self.frame()
        self.assertEqual(frame.raw_signed(),0);self.assertEqual(frame.raw_burden(),10)
        self.assertEqual(len(frame.responses),2)
        self.assertEqual([Q(x['raw_burden']) for x in frame.responses],[5,5])
        self.assertEqual([Q(x['raw_signed']) for x in frame.responses],[5,-5])
        self.assertNotEqual(frame.responses[0]['candidate_return_id'],frame.responses[1]['candidate_return_id'])

    def test_WR_06_orientation_is_not_lag_or_negative_closure(self):
        rows={p['prefix']:p for p in self.result['cases']['burden']['prefixes']}
        for a,b in [('++','--'),('+-','-+')]:
            self.assertEqual(Q(rows[a]['raw_signed']),-Q(rows[b]['raw_signed']))
            self.assertEqual(rows[a]['raw_burden'],rows[b]['raw_burden'])
            self.assertEqual(rows[a]['reference_lags'],['1','1'])
            self.assertEqual(rows[b]['reference_lags'],['1','1'])
            self.assertEqual(rows[a]['third_decision']['probabilities'],rows[b]['third_decision']['probabilities'])

    def test_WR_07_changed_preparation_changes_measured_lag(self):
        frame=r.Fixture(self.contract,'burden',candidate_seed_override=3)
        frame.prepare_next()
        self.assertEqual(frame.pending_inputs['reference']['lag'],'0')
        self.assertEqual(frame.pending_inputs['reference']['candidate_bip'],frame.pending_inputs['reference']['sender_bip'])

    def test_WR_08_reference_decision_requires_actual_return(self):
        frame=r.Fixture(self.contract,'burden')
        before=frame.measured_reference();frame.prepare_next()
        self.assertEqual(frame.measured_reference(),before+1)
        trace,cert,registry=frame.reference.records[-1]
        r.n.admitted(trace,cert,registry)
        self.assertEqual(trace.vertices[0],trace.vertices[-1])
        self.assertGreater(frame.pending_decision['cut'],trace.indices[-1])

    def test_WR_09_no_response_alias_can_be_counted_twice(self):
        frame=self.frame();frame.responses.append(deepcopy(frame.responses[0]))
        with self.assertRaisesRegex(ValueError,'more than one response'):frame.validate()

    def test_WR_10_changed_lag_and_recomputed_totals_rejected(self):
        frame=self.frame()
        response=frame.responses[0]
        term=next(t for t in response['terms'] if t['sender']=='reference')
        term['lag']='2';term['raw_signed']='10';term['raw_burden']='10'
        response['raw_signed']='10';response['raw_burden']='10'
        with self.assertRaisesRegex(ValueError,'regenerate'):frame.validate()

    def test_WR_11_changed_response_orientation_rejected(self):
        frame=self.frame();frame.responses[0]['terms'][0]['orientation']=-1
        with self.assertRaisesRegex(ValueError,'orientation'):frame.validate()

    def test_WR_12_changed_contact_prefix_rejected(self):
        frame=self.frame();ch=frame.channels['reference'];old=ch.events[-2]
        ch.events[-2]=replace(old,left_prefix='0'*64)
        with self.assertRaises((ValueError,r.n.AdmissionError)):frame.validate()

    def test_WR_13_unconsumed_formation_contact_is_still_bound(self):
        frame=self.frame();ch=frame.channels['background']
        ch.events[0]=replace(ch.events[0],left_prefix='0'*64)
        with self.assertRaisesRegex(ValueError,'actual committed pair prefixes'):frame.validate()

    def test_WR_14_future_operands_rejected(self):
        frame=self.frame();frame.responses[0]['terms'][0]['comparison_cut']=frame.clock.cut+1
        with self.assertRaises((ValueError,r.n.AdmissionError)):frame.validate()

    def test_WR_15_feedback_is_strictly_later(self):
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

    def test_WR_16_matched_prefix_and_feedback_disabled(self):
        cases=self.result['cases']
        for index in range(4):
            signatures=[cases[name]['prefixes'][index]['committed_prefix_sha256'] for name in
                        ('net_memory','burden','burden_feedback_off','burden_latest_response_window')]
            self.assertEqual(len(set(signatures)),1)
        disabled=cases['burden_feedback_off']['prefixes'][1]
        self.assertEqual(disabled['raw_burden'],'10')
        self.assertEqual(disabled['third_decision']['selected_raw_load'],'0')
        self.assertEqual(len(disabled['third_decision']['exclusions']),2)

    def test_WR_17_window_expiry_retains_history(self):
        frame=self.frame('burden_latest_response_window')
        self.assertEqual(frame.raw_burden(),10)
        self.assertEqual(frame.pending_decision['selected_raw_load'],'5')
        self.assertEqual(len(frame.responses),2)
        self.assertEqual(len(frame.pending_decision['exclusions']),1)

    def test_WR_18_population_lag_enters_retention(self):
        base=self.frame();changed=self.frame('burden_background_pending')
        self.assertEqual(base.background.wave().motif,'3:4')
        self.assertEqual(changed.background.wave().motif,'3:4')
        self.assertTrue(all(m.enclosure==6 for m in changed.background.motifs))
        self.assertIsNotNone(changed.background.pending)
        self.assertEqual(changed.background.pending['atomic_steps'],1)
        self.assertEqual(changed.raw_burden(),147)
        self.assertEqual(changed.pending_decision['probabilities']['exit'],'71/76')
        self.assertEqual(changed.responses[1]['terms'][0]['lag'],'1')

    def test_WR_19_directional_rcd_recomputed(self):
        frame=r.Fixture(self.contract,'burden');frame.prepare_next(reverse_extra=1);frame.retain('+')
        frame.prepare_next(reverse_extra=1)
        ch=frame.channels['reference']
        forward=ch.comparison(frame.clock.cut,frame.window_length)
        reverse=ch.comparison(frame.clock.cut,frame.window_length,reverse=True)
        self.assertEqual(forward['duration'],5);self.assertEqual(reverse['duration'],7)
        self.assertEqual(forward['lag'],-reverse['lag'])
        ch.validate()

    def test_WR_20_drift_uses_previous_committed_comparison(self):
        base=self.frame();changed=self.frame('burden_background_pending')
        reference=[next(t for t in x['terms'] if t['sender']=='reference') for x in base.responses]
        self.assertEqual([(x['lag'],x['prior_lag'],x['drift']) for x in reference],
                         [('1','2','-1'),('1','1','0')])
        bg=next(t for t in changed.responses[1]['terms'] if t['sender']=='background')
        self.assertEqual((bg['lag'],bg['prior_lag'],bg['drift']),('1','0','1'))

    def test_WR_21_passive_observer_cannot_change_execution(self):
        a=self.frame(observer=True);b=self.frame(observer=False)
        self.assertTrue(a.observations);self.assertFalse(b.observations)
        self.assertEqual(a.clock.events,b.clock.events)
        self.assertEqual(a.responses,b.responses)
        self.assertEqual(a.pending_decision,b.pending_decision)

    def test_WR_22_exposure_preserves_inner_lineage_and_counts(self):
        frame=self.frame();before=frame.candidate.wave();parent_returns=len(frame.parent_records)
        exited=frame.lose()
        self.assertEqual(frame.candidate.wave(),before)
        self.assertEqual(len(frame.parent_records),parent_returns)
        self.assertEqual(exited['exposed_certificate_digests'],[c.certificate_digest for c in before.certificates])
        self.assertEqual(exited['shedding']['surplus'],5)
        counts=r.terminal_counts(frame,'absorbed')
        self.assertEqual((counts['candidate_reclosures'],counts['parent_reclosures'],counts['reference_bips']),(2,2,3))
        self.assertEqual((counts['candidate_atomic_traversals'],counts['outer_atomic_traversals']),(8,10))

    def test_WR_23_open_exit_is_not_a_closure(self):
        frame=self.frame();exited=frame.lose();raw=exited['open_path']
        self.assertNotEqual(raw['vertices'][0],raw['vertices'][-1])
        self.assertIsNone(exited['physical_decay']);self.assertIsNone(exited['daughter_identity'])

    def test_WR_24_zero_weight_loss_cannot_be_installed(self):
        frame=self.frame('net_memory')
        with self.assertRaisesRegex(ValueError,'positive computed weight'):frame.lose()

    def test_WR_25_json_roundtrip_and_changed_artifact(self):
        serialized=json.loads(r.canonical(self.result))
        self.assertTrue(r.verify_report(serialized,original_contract=self.contract))
        changed=deepcopy(serialized)
        changed['cases']['burden']['S3']='5/6'
        changed.pop('report_sha256');changed['report_sha256']=r.digest(changed)
        with self.assertRaisesRegex(ValueError,'original-context replay'):
            r.verify_report(changed,original_contract=self.contract)

    def test_WR_26_no_measured_or_fitted_operand_can_be_added(self):
        for key,value in [('experimental_inputs',['half_life']),('fit_parameters',[1]),
                          ('physical_seconds','1'),('isotope_state_assignment','Og-294')]:
            changed=deepcopy(self.contract);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.predict(ROOT,changed)

    def test_WR_27_boolean_and_float_cannot_substitute_for_integer_cut(self):
        for value in (False,0.0):
            changed=deepcopy(self.contract);changed['horizon']['allowed_cut_window'][0]=value
            with self.subTest(value=value),self.assertRaises(ValueError):r.predict(ROOT,changed)


    def test_WR_28_independent_kernels_moments_and_censoring(self):
        checked=r.finite_kernel_checks(self.result,ROOT)
        self.assertEqual(checked['kernels'],20)
        self.assertTrue(all(row['result']['regions_checked']==16 for row in checked['checks']))
        for name,run in self.result['cases'].items():
            p=Q(run['S3']);summary=run['ensemble_summary']
            self.assertEqual(Q(summary['retained_indicator_variance']),p*(1-p))
            self.assertEqual(summary['median_reference_return'],3 if name=='burden_background_pending' else None)
            self.assertIsNone(summary['seconds'])

    def test_WR_29_all_four_prefixes_conserve_raw_signed_and_burden(self):
        expected={'++':('10','10','1/3'),'+-':('0','10','0'),
                  '-+':('0','10','0'),'--':('-10','10','1/3')}
        for row in self.result['cases']['net_memory']['prefixes']:
            self.assertEqual((row['raw_signed'],row['raw_burden'],row['third_decision']['probabilities']['exit']),expected[row['prefix']])
        self.assertTrue(all(row['third_decision']['probabilities']['exit']=='1/3'
                            for row in self.result['cases']['burden']['prefixes']))

    def test_WR_30_future_response_cannot_drive_next_kernel(self):
        frame,_,_=r.prepare_prefix(self.contract,'burden','+-')
        frame.responses[-1]['committed']=frame.clock.cut+100000
        with self.assertRaisesRegex(ValueError,'future response'):frame.prepare_next()

    def test_WR_31_pending_background_cannot_become_completed_return(self):
        frame=self.frame('burden_background_pending')
        before=len(frame.background.records)
        with self.assertRaisesRegex(ValueError,'pending path'):
            frame.background.advance(frame.clock,'fabricated-completion')
        self.assertEqual(len(frame.background.records),before)
        self.assertEqual(frame.background.pending['atomic_steps'],1)

    def test_WR_32_admission_rejects_changed_candidate_certificate(self):
        frame=self.frame();trace,cert,registry=frame.candidate.records[-1]
        changed=replace(cert,certificate_digest='0'*64)
        frame.candidate.records[-1]=(trace,changed,{changed.certificate_digest:changed})
        with self.assertRaises((ValueError,r.n.AdmissionError)):frame.validate()

    def test_WR_33_partial_exit_hinges_and_channels_are_distinct(self):
        terminal=next(row for row in self.result['cases']['burden']['terminals'] if row['outcome']=='exit')
        counts=terminal['event_counts']
        self.assertEqual((terminal['parent_reclosures'],terminal['reference_bips']),(2,3))
        self.assertEqual((counts['candidate_hinges'],counts['outer_hinges']),(2,3))
        self.assertEqual((counts['channel_ticks'],counts['channel_clicks']),(6,6))
        self.assertEqual(counts['outer_partial_atomic_traversals'],2)
        self.assertEqual(counts['reference_atomic_traversals'],12)
        self.assertEqual(counts['dwell_events'],0)
        self.assertEqual(counts['candidate_reflections'],0)

    def test_WR_34_rehashed_lineage_and_contact_artifact_fails_original_replay(self):
        changed=json.loads(r.canonical(self.result))
        run=changed['cases']['burden']
        context=run['traces']['+-']
        context['channels']['reference']['events'][0]['contact']['left_prefix']='0'*64
        context['response_history'][0]['candidate_certificate_digest']='1'*64
        row=next(row for row in run['prefixes'] if row['prefix']=='+-')
        row['context_sha256']=r.digest(context)
        terminal=next(row for row in run['terminals'] if row['outcome']=='exit')
        terminal['exposed_inner']['identity']='substituted-inner'
        terminal['source_context_sha256']=r.digest(context)
        changed.pop('report_sha256');changed['report_sha256']=r.digest(changed)
        with self.assertRaisesRegex(ValueError,'original-context replay'):
            r.verify_report(changed,original_contract=self.contract,root=ROOT)

    def test_WR_35_incomplete_artifact_and_altered_original_contract_rejected(self):
        with self.assertRaisesRegex(ValueError,'original-context replay'):
            r.verify_report({'cases':{'burden':{'S3':'2/3'}}},original_contract=self.contract,root=ROOT)
        changed=deepcopy(self.contract);changed['capacity']['diagnostic_units']='2'
        with self.assertRaisesRegex(ValueError,'frozen fixture contract'):
            r.verify_report(self.result,original_contract=changed,root=ROOT)

    def fixture(self,folder):
        root=Path(folder)/'repo'
        shutil.copytree(ROOT/r.DATA,root/r.DATA)
        (root/'manual2/scripts').mkdir(parents=True)
        shutil.copyfile(ROOT/'manual2/scripts/matter1_witnessed_retention.py',root/'manual2/scripts/matter1_witnessed_retention.py')
        return root

    def test_WR_36_persisted_rehashed_mutation_is_rejected_without_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);base=root/r.DATA
            changed=json.loads((base/'prediction.json').read_bytes())
            changed['cases']['burden']['S3']='1'
            changed.pop('report_sha256');changed['report_sha256']=r.digest(changed)
            (base/'prediction.json').write_bytes(r.json_bytes(changed))
            binding=json.loads((base/'sha256.json').read_bytes())
            binding['prediction.json']=hashlib.sha256((base/'prediction.json').read_bytes()).hexdigest()
            (base/'sha256.json').write_bytes(r.json_bytes(binding))
            before={p.relative_to(root):(p.read_bytes(),p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError,'Persisted retention artifact differs'):r.verify(root)
            after={p.relative_to(root):(p.read_bytes(),p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
            self.assertEqual(before,after)

    def test_WR_37_resealed_source_manifest_cannot_replace_trusted_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);base=root/r.DATA
            native=base/'upstream/manual/scripts/aod_native_closure_wave.py'
            native.write_bytes(native.read_bytes()+b'\n# changed\n')
            binding=json.loads((base/'source_bindings.json').read_bytes())
            binding['sha256']['upstream/manual/scripts/aod_native_closure_wave.py']=hashlib.sha256(native.read_bytes()).hexdigest()
            (base/'source_bindings.json').write_bytes(r.json_bytes(binding))
            with self.assertRaisesRegex(ValueError,'source-binding manifest'):r.verify_sources(root)

    def test_WR_38_external_generation_is_byte_identical_and_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            before={p:(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns)
                    for p in (ROOT/r.DATA).rglob('*') if p.is_file()}
            process=subprocess.run([sys.executable,'-B',str(ROOT/'manual2/scripts/generate_matter1_witnessed_retention.py'),
                '--root',str(ROOT),'--output-root',folder],capture_output=True,text=True)
            self.assertEqual(process.returncode,0,process.stderr)
            destination=Path(folder)/r.DATA
            self.assertEqual({p.name for p in destination.iterdir()},set(r.PRODUCTS))
            for name in r.PRODUCTS:self.assertEqual((destination/name).read_bytes(),(ROOT/r.DATA/name).read_bytes())
            self.assertEqual(before,{p:(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns)
                    for p in (ROOT/r.DATA).rglob('*') if p.is_file()})


if __name__=='__main__':unittest.main(verbosity=2)
