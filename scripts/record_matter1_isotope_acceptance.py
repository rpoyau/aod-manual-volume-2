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
 'test_matter1_retention_adapter':('RA','replayed_aggregate_construction_and_explicit_missing_retention_premises'),
 'test_matter1_m3_observation':('OBS','typed_M3_observation_context_and_original_input_replay_not_physical_calibration'),
 'test_matter1_m3_metrology':('MET','source_bound_comparison_reductions_and_missing_input_dispositions_not_atomic_prediction'),
}


# Only completed inputs consumed below belong to this receipt. Runner journals,
# this command's stdout and later acceptance outputs are deliberately excluded.
LANES = ('isotopes', 'survival', 'bipm_precision', 'constructed_coupling',
         'witnessed_retention', 'retention_adapter', 'm3_observation', 'm3_metrology')
EVIDENCE_INPUTS = tuple(sorted(
    [name + suffix + '.json' for name in LANES for suffix in ('', '-optimized')]
    + ['tests.txt', 'tests-optimized.txt', 'browser.json', 'm3-consumer.json',
       'm3-consumer-optimized.json', 'publication.json', 'reproduction.json']))
QUANTITY_ROUTES = ('bounds', 'conversion', 'finite_joint_law', 'metadata',
                   'multi_output', 'nonlinear_moments', 'published',
                   'published_moments', 'shared_cancel', 'shared_reinforce')
COUPLED_CASES = {'H1-E0', 'H1-E1', 'H2-E0', 'H2-E1', 'H3-E0', 'H3-E1'}


def evidence_input_hashes(checks, output):
    checks, output = Path(checks), Path(output)
    paths = [checks / name for name in EVIDENCE_INPUTS]
    evidence.require(all(path.resolve() != output.resolve() for path in paths),
                     'acceptance output aliases an input')
    return {path.name: evidence.sha(evidence.read_bytes(path)) for path in paths}


def replay_current_coupled(root):
    """Replay the checker's six default two-round cases, not one-round pilots."""
    sys.path.insert(0, str(Path(root) / 'manual2/scripts'))
    import matter1_coupled_preparations as coupled
    return {name: coupled.run_case(coupled.default_config(1, mass, electrons), root)
            for name, mass, electrons in coupled.PILOTS}


def validate_m3_consumer(root, receipt, historical_metrology, historical_observation,
                         coupled_results):
    """Bind a complete current receipt while retaining the old replay authority.

    The caller independently replays the historical reports. Current execution
    comes from the required upstream checker in both modes. Its six two-round
    result digests must match the caller's independent current replay; joint
    propagation and frozen prediction must match the persisted application.
    """
    root = Path(root)
    sys.path.insert(0, str(root / 'manual2/scripts'))
    import matter1_m3_producer as producer
    import matter1_m3 as historical
    import matter1_m3_metrology as old_metrology
    import matter1_coupled_preparations as coupled
    import matter1_preparation_workflow as workflow
    from publication_support import verify_foundation
    binding = producer.verify(root)
    prior = historical.verify_vendor(root)
    legacy = historical.verify_legacy_vendor(root)
    metrology_binding = old_metrology.verify_vendor(root)
    foundation = verify_foundation(root)
    evidence.require(receipt['status'] == 'PASS_REQUIRED_M3_CONSUMER',
                     'required exact M3 execution missing')
    for key in ('upstream_head', 'upstream_tree'):
        evidence.check_equal(receipt[key], binding[key], 'current M3 ' + key + ' mismatch')
        evidence.check_equal(foundation[key], binding[key], 'Main producer authority mismatch')
    evidence.check_equal(receipt['api_contract_sha256'],
        binding['files']['contracts/scientific/TEMPORAL_OBSERVATION.json']['sha256'],
        'current M3 contract mismatch')
    evidence.check_equal(receipt['foundation_upstream_head'], foundation['upstream_head'],
                         'Main head mismatch')
    evidence.check_equal(receipt['foundation_source_digest'], foundation['source_digest'],
                         'Main source mismatch')
    evidence.check_equal(prior['upstream_head'], metrology_binding['upstream_head'],
                         'historical observation/metrology identities differ')
    evidence.check_equal(receipt['historical_observation_metrology_head'], prior['upstream_head'],
                         'historical observation/metrology head mismatch')
    evidence.check_equal(receipt['historical_survival_executor_head'], legacy['upstream_head'],
                         'historical survival head mismatch')
    evidence.check_equal(receipt['metrology']['persisted_historical_verification'],
                         historical_metrology, 'historical metrology receipt stale')
    typed = receipt['typed_observation']
    evidence.require(typed['current_actual_upstream_equals_vendored'] is True,
                     'current upstream observation replay missing')
    for key in ('status', 'profile', 'report_sha256', 'physical_calibration'):
        evidence.check_equal(typed[key], historical_observation[key],
                             'historical observation receipt stale: ' + key)
    original = evidence.read_json(root / 'manual2/data/m1/m3_observation/observation_report.json')
    expected_cases = {}
    for name, item in original['cases'].items():
        record = item['prediction']['complete_temporal_record']
        expected_cases[name] = {'original_input_sha256': item['original_input_sha256'],
            'counts': record['counts'],
            'context_sha256': record['observation_context']['input_sha256']}
    evidence.check_equal(typed['cases'], expected_cases, 'typed observation coverage or input changed')
    quantity = receipt['quantity_comparison_dependency']
    evidence.require(quantity['actual_upstream_equals_vendored'] is True,
                     'current upstream quantity replay missing')
    evidence.check_equal(quantity['routes'], list(QUANTITY_ROUTES),
                         'current quantity route coverage incomplete')
    cases = receipt['coupled_preparations']
    evidence.require(set(cases) == COUPLED_CASES, 'coupled preparation coverage incomplete')
    evidence.require(set(coupled_results) == COUPLED_CASES, 'replayed coupled coverage incomplete')
    for name in sorted(COUPLED_CASES):
        evidence.require(cases[name]['actual_upstream_equals_vendored'] is True,
                         'actual coupled replay missing: ' + name)
        evidence.check_equal(cases[name]['result_sha256'], coupled.digest(coupled_results[name]),
                             'coupled result stale: ' + name)
    data = root / 'manual2/data/m1/preparation_workflow'
    joint = receipt['application_joint_propagation']
    evidence.require(joint['actual_upstream_equals_vendored'] is True,
                     'actual joint propagation missing')
    uncertainty = evidence.read_json(data / 'uncertainty.json')['cases']['H-1-neutral']
    evidence.check_equal(joint['result_sha256'], workflow.digest(uncertainty),
                         'application joint propagation stale')
    frozen = receipt['complete_application_freeze']
    evidence.require(frozen['actual_upstream_equals_vendored'] is True,
                     'actual full application freeze missing')
    product = evidence.read_json(data / 'frozen_diagnostic.json')
    evidence.check_equal(frozen['result_sha256'], workflow.digest(product), 'application freeze stale')
    evidence.check_equal(frozen['output'], product['prediction']['output'], 'application output changed')
    executed = receipt['executed']
    evidence.require(executed['common_prefix_through_cut'] == 39
        and executed['feedback_disabled_original_validator_rejected'] is True,
        'feedback/history integration incomplete')
    evidence.check_equal(executed['cases']['baseline']['counts'],
                         {'outer_plus': 6, 'outer_minus': 5}, 'baseline counts changed')
    evidence.check_equal(executed['cases']['intervention']['counts'],
                         {'outer_plus': 2, 'outer_minus': 5}, 'intervention counts changed')
    evidence.require(executed['atomic_point_prediction']['frequency_hz'] is None,
                     'unresolved physical prediction promoted')


def record(checks,output):
 input_hashes = evidence_input_hashes(checks, output)
 root=evidence.REPO;ids=evidence.source_test_ids();logs=validate_logs(checks,ids)
 rows=[]
 for module,(prefix,scope) in GROUPS.items():
  selected=sorted(t for t in ids if t.split('.')[2]==module)
  for i,test in enumerate(selected,1):
   evidence.require(all(test in logs[m]['methods'] for m in logs),'missing assertion '+test)
   rows.append({'id':f'{prefix}-{i:02}', 'test_id':test,'assertion_scope':scope,'outcome':'executed_scope_pass','modes':['normal','optimized']})
 sys.path.insert(0,str(root/'manual2/scripts'))
 import matter1_isotopes,matter1_survival,matter1_bipm_precision,matter1_constructed_coupling,matter1_witnessed_retention,matter1_retention_adapter,matter1_m3_observation,matter1_m3_metrology
 reports={}
 for name,module in [('isotopes',matter1_isotopes),('survival',matter1_survival),('bipm_precision',matter1_bipm_precision),('constructed_coupling',matter1_constructed_coupling),('witnessed_retention',matter1_witnessed_retention),('retention_adapter',matter1_retention_adapter),('m3_observation',matter1_m3_observation),('m3_metrology',matter1_m3_metrology)]:
  reports[name]=module.verify(root)
  for suffix in ('','-optimized'):
   evidence.check_equal(reports[name],evidence.read_json(checks/(name+suffix+'.json')),name+suffix+' receipt stale')
 browser=evidence.read_json(checks/'browser.json')
 evidence.require(browser['status']=='PASS' and len(browser['isotope_checks'])==6,'browser isotope coverage missing')
 evidence.require(all(r['source_switch'] and r['chain_navigation'] and r['unknown_and_stable_distinct'] and not r['horizontal_overflow'] and r['minimum_badge_contrast']>=7 for r in browser['isotope_checks']),'isotope browser assertion failed')
 m3=evidence.read_json(checks/'m3-consumer.json')
 evidence.check_equal(m3,evidence.read_json(checks/'m3-consumer-optimized.json'),'M3 mode mismatch')
 validate_m3_consumer(root, m3, reports['m3_metrology'], reports['m3_observation'],
                      replay_current_coupled(root))
 publication=evidence.read_json(checks/'publication.json');reproduction=evidence.read_json(checks/'reproduction.json')
 evidence.require(publication['status']=='PASS_PUBLICATION','publication failed')
 from check_matter1_reproduction import expected_output_paths
 paths=[r['path'] for r in reproduction['outputs']]
 evidence.require(reproduction['status']=='PASS_REPRODUCTION' and len(paths)==len(set(paths)) and set(paths)==expected_output_paths(root),'reproduction inventory incomplete')
 for identifier,scope in [('VIS-01','actual_source_and_state_selection_in_six_browser_views'),('VIS-02','unchanged_geometry_and_7_to_1_badge_contrast'),('FOUND-01','required_exact_upstream_consumer_replay_both_modes'),('PUB-01','paired_publication_semantic_reference_and_export_checks'),('REPRO-01','complete_disposable_generated_inventory_with_inputs_unchanged')]:
  rows.append({'id':identifier,'assertion_scope':scope,'outcome':'executed_scope_pass','evidence':'named check receipts'})
 result={'schema_version':1,'record_count':len(rows),'records':rows,'physical_isotope_half_life_prediction':'not_established','native_isotope_admission':'not_established','retrospective_comparison':'equal_state_shared_clock_specialization_rejected_within_source_envelopes','interpretation':'Software, finite model and source checks do not establish nuclear admission, an isotope-to-loss law or an SI prediction. Plain logs are execution evidence, not independent attestation.','test_runs':logs,'preservation':preservation(root),'lane_results':reports,'unresolved_dependencies':evidence.read_json(root/'manual2/data/m1/survival/prediction.json')['dependencies'],'evidence_sha256':input_hashes,'source_test_model_artifact_inventory':evidence.input_inventory(output)}
 evidence.check_equal(evidence_input_hashes(checks, output), input_hashes, 'acceptance inputs changed during replay')
 output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(evidence.canonical(result));return{'status':'RECORDED_ISOTOPE_SCOPED_ACCEPTANCE','criteria':len(rows),'output_sha256':evidence.sha(output.read_bytes())}

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--checks-dir',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 try:print(json.dumps(record(args.checks_dir,args.output),sort_keys=True,indent=2))
 except (ValueError,OSError,KeyError,TypeError) as exc:parser.exit(1,'Isotope acceptance failed: '+str(exc)+'\n')
if __name__=='__main__':main()
