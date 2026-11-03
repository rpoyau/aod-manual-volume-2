#!/usr/bin/env python3
"""Record scoped isotope/M3/survival assertions from actual complete test logs."""
import argparse
import json
from pathlib import Path
import sys
import record_matter1_acceptance as evidence
from record_matter1_v2_acceptance import validate_logs
from isotope_preservation import verify as preservation

GROUPS={
 'test_matter1_isotopes':('ISO','source_catalog_quantities_status_and_provenance'),
 'test_matter1_survival':('SURV','declared_history_ensemble_and_retrospective_conditional_test'),
 'test_matter1_m3':('M3','exact_source_binding_typed_maps_and_uncertainty_guards'),
 'test_matter1_m3_evidence':('F1','persisted_exact_evidence_typing_and_claim_binding_not_physical_uncertainty'),
 'test_matter1_bipm_precision':('PREC','conditional_printed_zero_policy_not_source_precision'),
 'test_matter1_isotope_integration':('INT','frozen_data_and_explicit_successor_conservation'),
 'test_matter1_constructed_coupling':('CC','constructed_aggregate_cadence_and_paired_configuration_not_physical_isotope_admission'),
 'test_matter1_witnessed_retention':('WR','committed_response_burden_and_later_retention_under_a_declared_finite_law'),
}

def record(checks,output):
 root=evidence.REPO;ids=evidence.source_test_ids();logs=validate_logs(checks,ids)
 rows=[]
 for module,(prefix,scope) in GROUPS.items():
  selected=sorted(t for t in ids if t.split('.')[2]==module)
  for i,test in enumerate(selected,1):
   evidence.require(all(test in logs[m]['methods'] for m in logs),'missing assertion '+test)
   rows.append({'id':f'{prefix}-{i:02}', 'test_id':test,'assertion_scope':scope,'outcome':'executed_scope_pass','modes':['normal','optimized']})
 sys.path.insert(0,str(root/'manual2/scripts'))
 import matter1_isotopes,matter1_survival,matter1_bipm_precision,matter1_constructed_coupling,matter1_witnessed_retention
 reports={}
 for name,module in [('isotopes',matter1_isotopes),('survival',matter1_survival),('bipm_precision',matter1_bipm_precision),('constructed_coupling',matter1_constructed_coupling),('witnessed_retention',matter1_witnessed_retention)]:
  reports[name]=module.verify(root)
  for suffix in ('','-optimized'):
   evidence.check_equal(reports[name],evidence.read_json(checks/(name+suffix+'.json')),name+suffix+' receipt stale')
 browser=evidence.read_json(checks/'browser.json')
 evidence.require(browser['status']=='PASS' and len(browser['isotope_checks'])==6,'browser isotope coverage missing')
 evidence.require(all(r['source_switch'] and r['chain_navigation'] and r['unknown_and_stable_distinct'] and not r['horizontal_overflow'] and r['minimum_badge_contrast']>=7 for r in browser['isotope_checks']),'isotope browser assertion failed')
 m3=evidence.read_json(checks/'m3-consumer.json')
 evidence.check_equal(m3,evidence.read_json(checks/'m3-consumer-optimized.json'),'M3 mode mismatch')
 evidence.require(m3['status']=='PASS_REQUIRED_M3_CONSUMER' and m3['upstream_head']=='3ffb3c9984eef95ca4b105ac323d249f30412816','required exact M3 execution missing')
 publication=evidence.read_json(checks/'publication.json');reproduction=evidence.read_json(checks/'reproduction.json')
 evidence.require(publication['status']=='PASS_PUBLICATION','publication failed')
 from check_matter1_reproduction import EXPECTED_OUTPUTS
 paths=[r['path'] for r in reproduction['outputs']]
 evidence.require(reproduction['status']=='PASS_REPRODUCTION' and len(paths)==len(set(paths)) and set(paths)==EXPECTED_OUTPUTS,'reproduction inventory incomplete')
 for identifier,scope in [('VIS-01','actual_source_and_state_selection_in_six_browser_views'),('VIS-02','unchanged_geometry_and_7_to_1_badge_contrast'),('FOUND-01','required_exact_upstream_consumer_replay_both_modes'),('PUB-01','paired_publication_semantic_reference_and_export_checks'),('REPRO-01','complete_disposable_generated_inventory_with_inputs_unchanged')]:
  rows.append({'id':identifier,'assertion_scope':scope,'outcome':'executed_scope_pass','evidence':'named check receipts'})
 result={'schema_version':1,'record_count':len(rows),'records':rows,'physical_isotope_half_life_prediction':'not_established','native_isotope_admission':'not_established','retrospective_comparison':'equal_state_shared_clock_specialization_rejected_within_source_envelopes','interpretation':'Software, finite model and source checks do not establish nuclear admission, an isotope-to-loss law or an SI prediction. Plain logs are execution evidence, not independent attestation.','test_runs':logs,'preservation':preservation(root),'lane_results':reports,'unresolved_dependencies':evidence.read_json(root/'manual2/data/m1/survival/prediction.json')['dependencies'],'evidence_sha256':{p.name:evidence.sha(p.read_bytes()) for p in sorted(checks.glob('*')) if p.is_file() and p!=output},'source_test_model_artifact_inventory':evidence.input_inventory(output)}
 output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(evidence.canonical(result));return{'status':'RECORDED_ISOTOPE_SCOPED_ACCEPTANCE','criteria':len(rows),'output_sha256':evidence.sha(output.read_bytes())}

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--checks-dir',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 try:print(json.dumps(record(args.checks_dir,args.output),sort_keys=True,indent=2))
 except (ValueError,OSError,KeyError,TypeError) as exc:parser.exit(1,'Isotope acceptance failed: '+str(exc)+'\n')
if __name__=='__main__':main()
