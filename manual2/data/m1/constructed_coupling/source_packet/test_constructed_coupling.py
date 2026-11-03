import copy
from dataclasses import replace
import json
from pathlib import Path
import unittest

import constructed_coupling as c


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads((c.HERE/'contract.json').read_text())
        cls.small=copy.deepcopy(cls.contract)
        cls.small.update(Z=1,N=1,intervention_cut=400000,horizon_cut=1100000,
                         window_endpoints=[400000,750000,1100000])
        cls.runs={case:c.Engine(cls.small,case).run() for case in cls.small['cases']}

    def test_sources_bound(self):
        self.assertGreaterEqual(len(c.check_sources()['sha256']),9)

    def test_memoized_native_accessor_matches_original_and_replacement(self):
        engine=self.runs['baseline']
        for node in engine.fields.values():
            for trace,cert,registry in node.records:
                self.assertEqual(trace.trace_digest,c.n.Trace.trace_digest.fget(trace))
                c.n.admitted(trace,cert,registry)
        original=engine.fields['P'].records[0][0]
        replaced=replace(original,ancestor='altered')
        self.assertNotEqual(original.trace_digest,replaced.trace_digest)
        self.assertEqual(replaced.trace_digest,c.n.Trace.trace_digest.fget(replaced))

    def test_actual_inventory_and_alias_rejection(self):
        field=c.FoldedField('proof',c.inventory(118,176),250000)
        self.assertEqual(len(field.inner),294)
        self.assertEqual(len({w.identity for w in field.inner}),294)
        self.assertEqual(sum(w.motif=='3:3' for w in field.inner),118)
        self.assertEqual(sum(w.motif=='3:4' for w in field.inner),176)
        self.assertEqual(field.branch,15508)
        self.assertEqual(field.rd,31017)
        c.n.validate_wave(field.wave())
        with self.assertRaises(ValueError):
            c.FoldedField('bad',(('same',3,3),('same',3,3)),250000)
        with self.assertRaises(c.n.AdmissionError):
            c.n.fold_proposal((field.inner[0],field.inner[0]),c.OUTER,1)

    def test_strict_integer_and_missing_physics_inputs(self):
        for key,value in [('Z',True),('N',True),('N',1.0),('parent_capacity',66),
                          ('physical_seconds',1),('horizon_cut',True)]:
            contract=copy.deepcopy(self.small);contract[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                c.Engine(contract,'baseline')

    def test_source_native_rejects_substituted_inner(self):
        field=self.runs['baseline'].fields['P']
        t,cert,_=field.records[0]
        altered=replace(cert,inner_waves=(field.inner[0],))
        with self.assertRaises(c.n.AdmissionError):
            c.n.admitted(t,altered,{altered.certificate_digest:altered})

    def test_uncausal_fold_rejected(self):
        field=self.runs['baseline'].fields['P']
        with self.assertRaises(c.n.AdmissionError):
            c.n.outer_trace(field.inner,scope=c.OUTER,scale=1,start_index=0)

    def test_alias_return_cannot_add_a_bip(self):
        field=self.runs['baseline'].fields['P']
        with self.assertRaises(c.n.AdmissionError):
            c.n.wave([field.records[0],field.records[0]])
        self.assertEqual(field.count(-1,field.returns[0]),0)
        self.assertEqual(field.count(-1,field.returns[1]),1)
        self.assertEqual(field.count(field.returns[1],field.returns[1]),0)

    def test_state_changes_dynamics_label_does_not(self):
        baseline=self.runs['baseline']
        altered=self.runs['one_fewer_346_constituent']
        self.assertNotEqual(baseline.fields['P'].rd,altered.fields['P'].rd)
        self.assertNotEqual(baseline.fields['P'].returns[2:],altered.fields['P'].returns[2:])
        contract=copy.deepcopy(self.small);contract['selected_label']='arbitrary renamed metadata'
        relabelled=c.Engine(contract,'baseline').run()
        self.assertEqual(baseline.trajectory_hash.hexdigest(),relabelled.trajectory_hash.hexdigest())

    def test_matched_prefix_and_feedback_control(self):
        baseline,changed,disabled=(self.runs[k] for k in
                                 ('baseline','add_346_to_parent','same_addition_feedback_disabled'))
        self.assertEqual(baseline.prefix_hash.hexdigest(),changed.prefix_hash.hexdigest())
        self.assertEqual(baseline.prefix_hash.hexdigest(),disabled.prefix_hash.hexdigest())
        self.assertNotEqual(baseline.trajectory_hash.hexdigest(),changed.trajectory_hash.hexdigest())
        self.assertEqual(baseline.trajectory_hash.hexdigest(),disabled.trajectory_hash.hexdigest())
        incoming=[x for x in changed.clicks if not x['formation'] and
                  (x['receiver'],x['sender'])==('P','B2')]
        first_use=next(x for x in changed.pressures if x['field']=='P' and
                       any(t.get('channel')==['P','B2'] for t in x['terms']))
        self.assertGreaterEqual(first_use['cut'],incoming[1]['committed'])

    def test_reference_has_independent_returns(self):
        engine=self.runs['baseline'];p,r=engine.fields['P'],engine.fields['R']
        self.assertNotEqual(p.returns[2:],r.returns[2:])
        self.assertTrue(all(t.lineage=='folded:R' for t,_,_ in r.records))
        self.assertGreater(r.count(p.returns[1],engine.end),0)

    def test_hinge_is_not_atomic_displacement(self):
        engine=self.runs['baseline'];p=engine.fields['P']
        stop=p.returns[2]
        steps=[x for x in p.actions if x['cut']<=stop]
        self.assertEqual(sum(x['kind']=='edge' for x in steps),2*p.branch)
        self.assertEqual(sum(x['kind']=='hinge' for x in steps),1)
        self.assertEqual(p.count(p.returns[1],stop),1)
        self.assertTrue(all(c.n.hamming(x['from'],x['to'])==1 for x in steps if x['kind']=='edge'))

    def test_tick_click_conservation_and_same_current_seating(self):
        engine=self.runs['baseline'];checks=engine.validate()
        self.assertTrue(checks['counter_conservation'])
        self.assertGreater(checks['actual_tick_count'],0)
        for state in checks['admitted_returned_currents']:
            self.assertEqual(state['duon_identity'],state['duad_identity'])
            self.assertIsNone(state['added_propagation_slowdown'])

    def test_altered_emission_prefix_rejected(self):
        engine=self.runs['baseline'];packet=engine.packets[0];original=packet['source_prefix']
        try:
            packet['source_prefix']='0'*64
            with self.assertRaisesRegex(ValueError,'Emission prefix'):
                engine.validate()
        finally:packet['source_prefix']=original

    def test_altered_contact_prefix_rejected(self):
        engine=self.runs['baseline'];ch=engine.channels[('P','R')];original=ch.events[0]
        try:
            ch.events[0]=replace(original,left_prefix='0'*64)
            with self.assertRaisesRegex(ValueError,'Contact binds'):
                engine.validate()
        finally:ch.events[0]=original

    def test_nonnegative_load_and_window_additivity(self):
        engine=self.runs['baseline'];rows=c.window_rows(engine)
        self.assertTrue(all(x['nonnegative_term']>=0 for x in engine.loads))
        disjoint=[x for x in rows if x['kind']=='disjoint']
        total=[x for x in rows if x['kind']=='cumulative'][-1]
        for field in ('new_parent_closures','reference_bips','parent_atomic_traversals','parent_window_load'):
            self.assertEqual(sum(x[field] for x in disjoint),total[field])

    def test_zero_denominator_and_unassigned_decay(self):
        self.assertIsNone(c.ratio(0,0));self.assertEqual(c.ratio(0,3),'0')
        for row in c.window_rows(self.runs['baseline']):
            self.assertIsNone(row['parent_capacity'])
            self.assertIsNone(row['parent_loss'])
            self.assertIsNone(row['seconds'])

    def test_native_directional_rcd(self):
        engine=self.runs['baseline'];a,b=engine.fields['P'],engine.fields['R']
        lo=a.returns[1];hi=engine.end
        for receiver,sender in (('P','R'),('R','P')):
            ch=engine.channels[(receiver,sender)]
            report=c.n.compare(engine.fields[receiver].wave(),engine.fields[sender].wave(),
                               tuple(ch.events[-2:]),(lo,hi))
            self.assertEqual(report['duration'],ch.operative()[0])
            self.assertEqual(report['rcd'].support,engine.fields[sender].rd)

    def test_horizon_cannot_change_prior_events(self):
        engine=self.runs['baseline'];short=c.Engine(self.small,'baseline').run(700000)
        self.assertEqual(short.actions,[r for r in engine.actions if r['cut']<=700000])
        self.assertEqual(short.packets,[r for r in engine.packets if r['emitted']<=700000])


if __name__=='__main__':unittest.main(verbosity=2)
