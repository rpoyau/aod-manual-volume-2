"""Independent conservation and hostile persisted-data tests (stdlib only).

Tests operate on disposable copies. Passing proves the static reference contract;
these tests do not execute Q4, a native kernel, SADAR dynamics or admission.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import matter1_model as model


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    return list(csv.DictReader(io.StringIO(path.read_text(), newline='')))


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def snapshot(root):
    return {str(p.relative_to(root)): (digest(p), p.stat().st_size, p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


def update_manifest(root, relative):
    path=root/'evidence/input_manifest.json'
    data=json.loads(path.read_text())
    data['files'][relative]=digest(root/relative)
    path.write_bytes(model.json_bytes(data))


class Matter1DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.refs, cls.inputs, cls.baseline = model.load_contract(ROOT)
        cls.rows = model.typed_rows(ROOT/'data/m1/matter1_elements_1_118_ledger.csv')
        cls.artifacts = model.expected_artifacts(ROOT, cls.rows)

    def fixture(self):
        temp=tempfile.TemporaryDirectory(prefix='matter1-data-test-')
        self.addCleanup(temp.cleanup)
        target=Path(temp.name)/'manual2'
        names=set(json.loads((ROOT/'evidence/input_manifest.json').read_text())['files'])
        names.add('evidence/input_manifest.json')
        names.update(self.artifacts)
        names.update('scripts/'+name for name in ('matter1_model.py','verify_matter1_ledger.py','generate_matter1_ledger.py'))
        for relative in names:
            destination=target/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/relative,destination)
        return target

    def command(self, root, *args, optimized=False):
        command=[sys.executable,'-B']+(['-O'] if optimized else [])
        command += [str(root/'scripts/verify_matter1_ledger.py'),'--root',str(root),*args]
        return subprocess.run(command,capture_output=True,text=True,check=False)

    def rejected_without_writes(self, root, *args, optimized=False):
        before=snapshot(root)
        result=self.command(root,*args,optimized=optimized)
        self.assertNotEqual(result.returncode,0,result.stdout)
        self.assertEqual(snapshot(root),before,'verification altered persisted bytes or mtimes')
        return result

    def mutate_row(self, root, z, values):
        path=root/'data/m1/matter1_elements_1_118_ledger.csv'
        rows=read_csv(path)
        rows[z-1].update({key:str(value) for key,value in values.items()})
        write_csv(path,rows)

    def test_126_frozen_numeric_rows_and_118_placements(self):
        self.assertEqual(len(self.rows),126)
        self.assertEqual(digest(ROOT/'evidence/pr1_baseline_ledger_v1.csv'),model.BASELINE_SHA256)
        numeric=0
        for row,old in zip(self.rows,self.baseline):
            self.assertEqual(row['z'],int(old['z']))
            for key,value in old.items():
                if value.lstrip('-').isdigit():
                    self.assertEqual(row[model.MIGRATION.get(key,key)],int(value),(row['z'],key))
                    numeric+=1
        self.assertEqual(numeric,3024)  # 24 old integer columns × 126 rows.
        history=read_csv(ROOT/'data/m1/history/v94_placements.csv')
        self.assertEqual(len(history),118)
        for row,old in zip(self.rows,history):
            self.assertEqual((row['symbol'],row['m_order'],row['seat_s'],row['gamma_prev'],row['gamma_m'],row['enclosure_l']),
                             (old['Symbol'],int(old['coord0_group_m']),int(old['range_position']),int(old['Gamma_prev']),int(old['Gamma_m']),int(old['closure_lane'].removeprefix('C_'))))

    def test_independent_exact_relations_for_all126(self):
        endpoints=(6,14,24,36,50,66,84,104,126)
        for row in self.rows:
            z,A=row['z'],row['mass_a']
            index=next(i for i,end in enumerate(endpoints) if z<=end)
            lower=0 if index==0 else endpoints[index-1]
            s=z-lower; length=endpoints[index]-lower
            self.assertEqual((row['gamma_prev'],row['gamma_m'],row['m_order'],row['enclosure_l'],row['seat_s']),
                             (lower,endpoints[index],length//2,length,s))
            self.assertEqual((row['a_tritrio'],row['b_tetratrio'],row['c_dimon']),((s+1)//2,s//2,s%2))
            self.assertEqual((row['baryon_tritrio'],row['baryon_tetratrio'],row['shell_dimon']),(z,A-z,z))
            self.assertEqual(row['pi_minus'],68*A-38*z)
            self.assertEqual(row['pi_plus'],4*s)
            self.assertEqual(row['h_mu'],1)
            self.assertEqual(row['support_sum'],68*A-38*z+4*s+1)
            self.assertEqual(row['c_close'],3*length)
            self.assertEqual(row['s_residual'],row['assigned_pressure']-3*length)
            self.assertEqual(row['x_shedding'],max(row['s_residual'],0))
            self.assertEqual(row['n_f_count'],s)

    def test_isotope_parameterization_472_conditional_cases(self):
        keys=('m_order','enclosure_l','gamma_prev','gamma_m','seat_s','hemisphere','a_tritrio','b_tetratrio','c_dimon')
        total=0
        for ref in self.refs[:118]:
            z,A=ref['z'],ref['mass_a']
            reference=model.evaluate_support(z,A)
            for candidate in (max(z,A-1),A,A+1,A+2):
                actual=model.evaluate_support(z,candidate)
                self.assertEqual(actual['support_sum']-reference['support_sum'],68*(candidate-A))
                self.assertEqual(tuple(actual[k] for k in keys),tuple(reference[k] for k in keys))
                self.assertEqual(actual['baryon_tetratrio'],candidate-z)
                total+=1
        self.assertEqual(total,472)
        self.assertEqual([model.evaluate_support(6,A)['support_sum'] for A in (12,13,14)],[613,681,749])
        with self.assertRaises(model.ValidationError):model.evaluate_support(6,5)
        with self.assertRaises(model.ValidationError):model.evaluate_support(6,12.0)
        with self.assertRaises(model.ValidationError):model.evaluate_support(6,True)

    def test_nuclear_counts_and_local_tuple_cannot_be_collapsed(self):
        carbon=self.rows[5]
        self.assertEqual((carbon['baryon_tritrio'],carbon['baryon_tetratrio']),(6,6))
        self.assertEqual((carbon['a_tritrio'],carbon['b_tetratrio'],carbon['c_dimon']),(3,3,0))
        root=self.fixture()
        self.mutate_row(root,6,{'baryon_tritrio':3,'baryon_tetratrio':3})
        self.rejected_without_writes(root)

    def test_parity_is_separate_from_assigned_residual(self):
        lithium,oxygen=self.rows[2],self.rows[7]
        self.assertEqual((lithium['c_dimon'],lithium['s_residual'],lithium['assigned_route_class']),(1,0,'neutral'))
        self.assertEqual((oxygen['c_dimon'],oxygen['s_residual'],oxygen['assigned_route_class']),(0,-3,'deficit'))
        self.assertEqual(sum((r['c_dimon']==1)!=(r['s_residual']<0) for r in self.rows[:118]),58)

    def test_occupancy_and_assigned_ttl_are_separate(self):
        report=model.audit_report(self.rows)
        self.assertEqual(report['c22_labelled_reference_occupancy_fraction'],'7/11')
        self.assertEqual(report['c22_assigned_ttl_qualified_fraction'],'0')
        self.assertEqual(sum(report['disjoint_class_counts'].values()),126)
        self.assertEqual(report['independent_attributes'],{'named_anchors':8,'named_anchors_with_assigned_surplus':2})
        self.assertEqual(self.rows[125]['is_group_boundary'],1)
        self.assertEqual(self.rows[125]['is_named_anchor'],0)

    def test_check_default_and_compatibility_alias_never_write(self):
        root=self.fixture();before=snapshot(root)
        for flags in ((),('--check-data',)):
            result=self.command(root,*flags)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['profile'],'static_relational_reference')
            self.assertEqual(snapshot(root),before)

    def test_unknown_flags_are_rejected_without_writes(self):
        result=self.rejected_without_writes(self.fixture(),'--pretend-to-check')
        self.assertIn('unrecognized arguments',result.stderr)

    def test_mutations_of_reference_arithmetic_and_status_are_rejected(self):
        cases=[
            ('odd enclosure',6,{'enclosure_l':7}),
            ('wrong seat',6,{'seat_s':5}),
            ('wrong local count',6,{'a_tritrio':4}),
            ('wrong parity',8,{'c_dimon':1}),
            ('invalid reference mass',6,{'mass_a':5}),
            ('wrong aggregate dimon',6,{'shell_dimon':6+1}),
            ('wrong conditional sum',6,{'support_sum':614}),
            ('compensated support terms',6,{'pi_minus':589,'pi_plus':23}),
            ('coherent false hinge',6,{'h_mu':2,'support_sum':614}),
            ('wrong filled count',6,{'n_f_count':5}),
            ('wrong role',3,{'hemisphere':'Pi_alpha (+1)'}),
            ('false route equivalence',3,{'assigned_route_class':'deficit'}),
            ('false pressure',8,{'assigned_pressure':24,'s_residual':0}),
            ('false TTL',84,{'assigned_ttl':19}),
            ('false path',84,{'assigned_sheddic_path':'none (retained)'}),
            ('false Yro',84,{'assigned_yro_status':'none'}),
            ('promoted admission',6,{'admission_status':'certified'}),
            ('promoted execution',6,{'execution_status':'executed'}),
            ('unnamed slot promoted',119,{'record_kind':'element_reference'}),
            ('unfilled boundary promoted',126,{'is_named_anchor':1}),
        ]
        for label,z,values in cases:
            with self.subTest(mutation=label):
                root=self.fixture();self.mutate_row(root,z,values)
                self.rejected_without_writes(root,'--check-data')

    def test_prior_14_primary_and_3_extended_probes_revisited(self):
        lithium=self.rows[2]
        cases=[
            ('forged_cycle_certificate_now_declaration_syntax',1,{'support_declaration':'C_f[FORGED_NO_TRACE]_AO'}),
            ('invalid_mass_input',2,{'mass_a':-9}),
            ('interior_count_grammar',3,{'a_tritrio':999,'b_tetratrio':-2,'c_dimon':7}),
            ('odd_support_enclosure',3,{'enclosure_l':7}),
            ('wrong_hemisphere',3,{'hemisphere':'Spine (filled 2m)'}),
            ('unbound_field_count',3,{'n_f_count':999}),
            ('false_route_label_now_assigned_class',3,{'assigned_route_class':'deficit'}),
            ('invalid_yro_status',43,{'assigned_yro_status':'Yro_16(even_wrong_scope)'}),
            ('coherent_wrong_support',3,{'pi_minus':lithium['pi_minus']+7,'support_sum':lithium['support_sum']+7}),
            ('duplicate_and_missing_z',1,{'z':2}),
            ('broken_rd_sum_now_support_sum',3,{'support_sum':lithium['support_sum']+1}),
            ('broken_residual',3,{'s_residual':1}),
            ('missing_sheddic_path',43,{'assigned_sheddic_path':'missing'}),
            ('missing_hinge',3,{'h_mu':0}),
            ('float_pressure',3,{'assigned_pressure':float(lithium['assigned_pressure']),'c_close':float(lithium['c_close']),'s_residual':0.0,'x_shedding':0.0}),
            ('wrong_even_sheddic_target',43,{'assigned_sheddic_path':'C6'}),
            ('nonunit_hinge_consistent_sum',3,{'h_mu':2,'support_sum':lithium['support_sum']+1}),
        ]
        self.assertEqual(len(cases),17)
        for label,z,values in cases:
            with self.subTest(previous_probe=label):
                root=self.fixture();self.mutate_row(root,z,values)
                self.rejected_without_writes(root,'--check-data')

    def test_formatted_declaration_is_syntax_not_a_certificate(self):
        self.assertNotIn('cf_certified',model.FIELDS)
        self.assertEqual({r['admission_status'] for r in self.rows},{'pending'})
        self.assertEqual({r['execution_status'] for r in self.rows},{'not_executed'})
        root=self.fixture()
        self.mutate_row(root,6,{'support_declaration':'FORGED CERTIFICATE'})
        # This is an exact declaration-format failure, not a failed native witness.
        self.assertIn('support_declaration',self.rejected_without_writes(root).stderr)

    def test_missing_duplicate_reordered_and_extra_rows_fail(self):
        for label,mutator in (
            ('missing',lambda rows:rows[:-1]),
            ('duplicate',lambda rows:rows[:-1]+[rows[-2]]),
            ('reordered',lambda rows:[rows[1],rows[0]]+rows[2:]),
            ('extra',lambda rows:rows+[rows[-1]]),
        ):
            with self.subTest(mutation=label):
                root=self.fixture();path=root/'data/m1/matter1_elements_1_118_ledger.csv'
                write_csv(path,mutator(read_csv(path)))
                self.rejected_without_writes(root)

    def test_noncanonical_types_missing_and_unknown_columns_fail(self):
        for value in ('6.0','06','true','NaN','6 '):
            with self.subTest(value=value):
                root=self.fixture();self.mutate_row(root,6,{'z':value})
                self.rejected_without_writes(root)
        for mutation in ('missing','extra'):
            with self.subTest(column=mutation):
                root=self.fixture();path=root/'data/m1/matter1_elements_1_118_ledger.csv';rows=read_csv(path)
                for row in rows:
                    if mutation=='missing':del row['execution_status']
                    else:row['native_certified']='true'
                write_csv(path,rows);self.rejected_without_writes(root)

    def test_stale_mirror_audit_summary_and_table_fail(self):
        for relative in ('data/matter1_elements_1_118_ledger.csv','data/matter1_coord0_enclosure_summary.csv',
                         'data/matter1_audit_report.json','data/m1/matter1_audit_report.json',
                         'data/m1/matter1_coord0_enclosure_summary.csv','sections/generated_elements_longtable.tex'):
            with self.subTest(artifact=relative):
                root=self.fixture();path=root/relative;path.write_bytes(path.read_bytes()+b'\n')
                self.rejected_without_writes(root)

    def test_missing_artifacts_are_reported_and_not_created(self):
        root=self.fixture();(root/'data/m1/matter1_elements_1_118_ledger.csv').unlink()
        self.rejected_without_writes(root)

    def test_false_input_hash_and_provenance_drift_fail(self):
        for relative in ('data/m1/reference_inputs.csv','data/m1/model_inputs.json','data/m1/input_provenance.json','evidence/pr1_baseline_ledger_v1.csv'):
            with self.subTest(input=relative):
                root=self.fixture();path=root/relative;path.write_bytes(path.read_bytes()+b'\n')
                self.assertIn('SHA-256',self.rejected_without_writes(root).stderr)

    def test_reference_selection_change_rejected_even_after_manifest_refresh(self):
        root=self.fixture();relative='data/m1/reference_inputs.csv';path=root/relative;rows=read_csv(path)
        rows[5]['mass_a']='13';write_csv(path,rows);update_manifest(root,relative)
        self.assertIn('baseline identity/reference-A changed',self.rejected_without_writes(root).stderr)

    def test_assigned_model_reclassification_cannot_silently_change_fixture(self):
        root=self.fixture();relative='data/m1/model_inputs.json';path=root/relative;data=json.loads(path.read_text())
        data['acceptor_z']=sorted(data['acceptor_z']+[3]);path.write_bytes(model.json_bytes(data));update_manifest(root,relative)
        self.rejected_without_writes(root)
        destination=root/'generated'
        result=subprocess.run([sys.executable,'-B',str(root/'scripts/generate_matter1_ledger.py'),'--root',str(root),'--output-root',str(destination)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(destination.exists(),'generation partially wrote before conservation validation')

    def test_json_boolean_does_not_count_as_integer(self):
        root=self.fixture();relative='data/m1/model_inputs.json';path=root/relative;data=json.loads(path.read_text())
        data['support_operands']['hinge']=True;path.write_bytes(model.json_bytes(data));update_manifest(root,relative)
        self.assertIn('exact integers',self.rejected_without_writes(root).stderr)

    def test_source_member_hashes_and_generated_history_joins_are_checked(self):
        root=self.fixture();relative='data/m1/history/r24_transition_packets.csv';path=root/relative
        rows=read_csv(path);rows[0]['occurrence_id']='invented-occurrence';write_csv(path,rows);update_manifest(root,relative)
        self.assertIn('historical source member SHA-256',self.rejected_without_writes(root).stderr)
        root=self.fixture();relative='data/m1/history/declaration_crosswalk.csv';path=root/relative
        rows=read_csv(path);rows[0]['r24_occurrence_declaration_id']='invented-occurrence';write_csv(path,rows)
        self.rejected_without_writes(root)

    def test_history_does_not_promote_declared_execution_or_observables(self):
        crosswalk=read_csv(ROOT/'data/m1/history/declaration_crosswalk.csv')
        self.assertEqual(len(crosswalk),118)
        self.assertEqual({r['predecessor_transition_status'] for r in crosswalk},{'declared_not_executed_in_this_gate'})
        self.assertEqual({r['predecessor_sadar_status'] for r in crosswalk},{'declared_not_executed'})
        self.assertEqual({r['candidate_execution_status'] for r in crosswalk},{'not_executed'})
        coverage=read_csv(ROOT/'data/m1/history/observable_coverage.csv')
        self.assertEqual(len(coverage),708)
        self.assertEqual(sum(r['candidate_status']=='not_scored' for r in coverage),590)
        self.assertEqual(sum(r['candidate_status']=='reference_registry' for r in coverage),118)
        self.assertEqual(len(read_csv(ROOT/'data/m1/history/value_map_status.csv')),10)
        for relative,field,new in (
            ('data/m1/history/observable_coverage.csv','candidate_status','native_verified'),
            ('data/m1/history/value_map_status.csv','candidate_status','active'),
            ('data/m1/history/declaration_crosswalk.csv','candidate_execution_status','executed'),
        ):
            with self.subTest(promotion=relative):
                root=self.fixture();path=root/relative;rows=read_csv(path);rows[0][field]=new;write_csv(path,rows)
                self.rejected_without_writes(root)

    def test_optimized_python_preserves_validation(self):
        root=self.fixture();self.mutate_row(root,6,{'support_sum':0})
        self.rejected_without_writes(root,optimized=True)

    def test_explicit_generation_is_deterministic_and_separate(self):
        root=self.fixture();before=snapshot(root)
        with tempfile.TemporaryDirectory(prefix='matter1-generate-test-') as temp:
            out=Path(temp)/'output'
            result=subprocess.run([sys.executable,'-B',str(root/'scripts/generate_matter1_ledger.py'),'--root',str(root),'--output-root',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(snapshot(root),before)
            self.assertEqual({str(p.relative_to(out)):p.read_bytes() for p in out.rglob('*') if p.is_file()},self.artifacts)
        result=subprocess.run([sys.executable,'-B',str(root/'scripts/generate_matter1_ledger.py'),'--root',str(root)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('--output-root',result.stderr)
        self.assertEqual(snapshot(root),before)


if __name__=='__main__':
    unittest.main()
