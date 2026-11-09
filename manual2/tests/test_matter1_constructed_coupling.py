import copy
from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'manual2/scripts'))
import matter1_constructed_coupling as app
import matter1_constructed_source as source_adapter
from manual2.tests.foundation_fixture import copy_foundation_receipts
c = app.engine_module(ROOT)


class SourceAdapterTests(unittest.TestCase):
    def fixture(self, target):
        copy_foundation_receipts(ROOT, target)
        path = target/source_adapter.APPLICATION
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/source_adapter.APPLICATION, path)

    def test_current_executor_and_historical_recipe_are_separately_bound(self):
        record = source_adapter.verify_adapter(ROOT)
        contract = app.read_json(ROOT/app.DATA/'model_contract.json')
        self.assertEqual(app.default_contract(ROOT), contract)
        self.assertEqual(record['before_sha256'], contract['application_source_sha256']['matter1_constructed_coupling.py'])
        self.assertNotEqual(record['before_sha256'], record['after_sha256'])
        for case, context in app.contexts(contract).items():
            app.verify_case(ROOT, context, ROOT/app.DATA/case, replay=False)

    def test_changed_current_archive_and_self_resealed_receipt_rejected(self):
        for mutation in ('current', 'archive', 'receipt'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.fixture(root)
                record = source_adapter.verify_adapter(root)
                path = root/(record['archive'] if mutation == 'archive' else source_adapter.APPLICATION)
                path.write_bytes(path.read_bytes()+b'\n# altered\n')
                if mutation == 'receipt':
                    record['after_sha256'] = app.sha(path)
                    (root/source_adapter.RECEIPT).write_bytes(app.canonical(record))
                before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                with self.assertRaisesRegex(ValueError, 'Constructed adapter:'):
                    source_adapter.historical_recipe_digest(root)
                self.assertEqual(before, {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()})


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

    def test_consumed_pressure_is_committed_before_affected_action(self):
        engine=self.runs['add_346_to_parent']
        clicked={row['id']:row['committed'] for row in engine.clicks}
        pressure={row['binding']:row for row in engine.pressures}
        for row in engine.actions:
            if row['pressure_binding'] not in pressure or row['kind']=='start':continue
            response=pressure[row['pressure_binding']]
            self.assertLess(response['cut'],row['cut'])
            for term in response['terms']:
                for identity in term.get('contact_ids',[]):
                    self.assertLess(clicked[identity],row['cut'])


class ApplicationReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=app.default_contract(ROOT)
        cls.context=copy.deepcopy(app.contexts(cls.contract)['r02/baseline'])
        cls.context['contract'].update(Z=1,N=1,intervention_cut=400000,horizon_cut=1100000,
            window_endpoints=[400000,750000,1100000])
        cls.temp=tempfile.TemporaryDirectory(prefix='matter1-constructed-tests-')
        cls.case=Path(cls.temp.name)/'case'
        cls.summary=app.write_case(ROOT,cls.context,cls.case)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def clone(self):
        import shutil
        destination=Path(self.temp.name)/self._testMethodName
        shutil.copytree(self.case,destination)
        return destination

    def hashes(self,directory):
        return {str(p.relative_to(directory)):(app.sha(p),p.stat().st_mtime_ns)
            for p in directory.rglob('*') if p.is_file()}

    def rebind(self,directory):
        binding=app.read_json(directory/'application_binding.json')
        binding['file_sha256']={name:app.sha(directory/name) for name in app.ORIGINAL_FILES+('input_context.json',)}
        binding['input_context_sha256']=app.sha(directory/'input_context.json')
        (directory/'application_binding.json').write_bytes(app.canonical(binding))

    def test_source_packet_and_application_native_import_are_bound(self):
        binding=app.check_sources(ROOT)
        self.assertEqual(binding['selected_original_members'],39)
        self.assertEqual(binding['bound_inputs'],9)
        self.assertEqual(app.sha(c.n.__file__),binding['native_sha256'])
        self.assertIn('source_packet/upstream/manual/scripts',str(c.n.__file__))
        self.assertEqual(app.sha(c.__file__),binding['engine_sha256'])

    def test_declared_context_is_exact_and_cannot_import_capacity_or_seconds(self):
        app.validate_contract(ROOT,self.contract)
        for key,value in [('parent_capacity',5),('physical_seconds',1)]:
            changed=copy.deepcopy(self.contract);changed['r02_contract'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):app.validate_contract(ROOT,changed)

    def test_whole_case_replays_read_only_from_original_context(self):
        before=self.hashes(self.case)
        app.verify_case(ROOT,self.context,self.case)
        self.assertEqual(before,self.hashes(self.case))

    def test_target_only_and_extra_file_artifacts_are_rejected(self):
        directory=self.clone()
        for name in app.CASE_FILES:
            if name not in ('prediction.json','application_binding.json'):(directory/name).unlink()
        before=self.hashes(directory)
        with self.assertRaisesRegex(ValueError,'Incomplete'):app.verify_case(ROOT,self.context,directory)
        self.assertEqual(before,self.hashes(directory))
        (self.case/'unexpected.txt').write_text('not part of the artifact')
        try:
            with self.assertRaisesRegex(ValueError,'unexpected'):app.verify_case(ROOT,self.context,self.case)
        finally:(self.case/'unexpected.txt').unlink()

    def test_nested_input_names_cannot_hide_extra_artifact_files(self):
        with tempfile.TemporaryDirectory() as temp:
            data=Path(temp)/app.DATA
            for name in app.OUTPUTS:
                path=data/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}')
            for name in ('rogue/model_contract.json','rogue/source_packet/extra.json'):
                path=data/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}')
            with patch.object(app,'validate_contract',return_value=self.contract):
                with self.assertRaisesRegex(ValueError,'inventory'):
                    app.verify(ROOT,Path(temp))

    def test_rehashed_context_switch_is_not_original_context(self):
        directory=self.clone()
        changed=copy.deepcopy(self.context);changed['contract']['N']=2
        (directory/'input_context.json').write_bytes(app.canonical(changed))
        self.rebind(directory)
        before=self.hashes(directory)
        with self.assertRaisesRegex(ValueError,'original input context'):app.verify_case(ROOT,self.context,directory)
        self.assertEqual(before,self.hashes(directory))

    def test_rehashed_trace_and_prediction_cannot_replace_execution(self):
        directory=self.clone()
        target=directory/'outer_return_witnesses.jsonl.gz'
        rows=[json.loads(line) for line in gzip.decompress(target.read_bytes()).splitlines()]
        rows[0]['trace_digest']='0'*64
        c.write_jsonl_gz(target,rows)
        prediction=app.read_json(directory/'prediction.json')
        prediction['file_sha256'][target.name]=app.sha(target)
        prediction.pop('prediction_sha256');prediction['prediction_sha256']=c.digest(prediction)
        c.write_json(directory/'prediction.json',prediction)
        self.rebind(directory)
        before=self.hashes(directory)
        with self.assertRaisesRegex(ValueError,'original-context execution'):app.verify_case(ROOT,self.context,directory)
        self.assertEqual(before,self.hashes(directory))

    def test_duplicate_input_key_is_not_accepted_as_valid_serialization(self):
        directory=self.clone()
        content=(directory/'input_context.json').read_text()
        (directory/'input_context.json').write_text(content.replace('{','{"case":"forged",',1))
        self.rebind(directory)
        with self.assertRaisesRegex(ValueError,'input context'):app.verify_case(ROOT,self.context,directory)

    def test_same_committed_operands_supply_signed_and_burden_diagnostics(self):
        rows=[json.loads(line) for line in gzip.decompress((self.case/'nonnegative_load_terms.jsonl.gz').read_bytes()).splitlines()]
        clicks={row['id']:row for row in (json.loads(line) for line in gzip.decompress((self.case/'click_and_rcd_events.jsonl.gz').read_bytes()).splitlines())}
        signed=sum(row['rho']*clicks[row['contact_id']]['lag_at_emission'] for row in rows)
        burden=sum(row['rho']*abs(clicks[row['contact_id']]['lag_at_emission']) for row in rows)
        self.assertEqual(self.summary['signed_response_diagnostic'],signed)
        self.assertEqual(self.summary['nonnegative_burden'],burden)
        self.assertGreaterEqual(burden,abs(signed))

    def test_pair_has_actual_distinct_constituents_scope_maps_and_common_law(self):
        contexts=app.contexts(self.contract)
        fields=[]
        for identity,z,n,rd in [('Fl-286',114,172,30233),('Fl-289',114,175,30641)]:
            context=contexts['configurations/'+identity]
            self.assertEqual((context['contract']['Z'],context['contract']['N']),(z,n))
            field=c.FoldedField('P',c.inventory(z,n),context['contract']['engine_start_cut'])
            c.n.validate_wave(field.wave())
            self.assertEqual(len(field.inner),z+n)
            self.assertEqual(len({w.identity for w in field.inner}),z+n)
            self.assertEqual(field.rd,rd)
            fields.append(field)
        self.assertNotEqual(fields[0].identity,fields[1].identity)
        self.assertNotEqual(c.digest(fields[0].occurrence_map),c.digest(fields[1].occurrence_map))
        left=copy.deepcopy(contexts['configurations/Fl-286']['contract'])
        right=copy.deepcopy(contexts['configurations/Fl-289']['contract'])
        for contract in (left,right):
            contract.pop('N');contract.pop('selected_label')
        self.assertEqual(left,right)
        self.assertIsNone(self.contract['common_law']['capacity'])
        self.assertIsNone(self.contract['common_law']['loss'])

    def test_capacity_alternatives_do_not_identify_loss_or_half_life(self):
        alternatives=self.summary['capacity_countermodels']
        self.assertGreater(c.Fraction(alternatives[0]['residual']),0)
        self.assertEqual(c.Fraction(alternatives[1]['residual']),0)
        self.assertLess(c.Fraction(alternatives[2]['residual']),0)
        for key in ('parent_loss_witness','ensemble_median','survival_probability','physical_seconds'):
            self.assertIsNone(self.summary[key])

    def test_actual_fl_configuration_is_invariant_to_label_only_change(self):
        context=app.contexts(self.contract)['configurations/Fl-286']
        original=c.Engine(context['contract'],'baseline').run(1100000)
        renamed=copy.deepcopy(context['contract']);renamed['selected_label']='Og-294 metadata only'
        control=c.Engine(renamed,'baseline').run(1100000)
        self.assertEqual(original.fields['P'].identity,control.fields['P'].identity)
        self.assertEqual(original.actions,control.actions)
        self.assertEqual(original.packets,control.packets)
        self.assertEqual(original.fields['P'].returns,control.fields['P'].returns)


if __name__=='__main__':unittest.main(verbosity=2)



