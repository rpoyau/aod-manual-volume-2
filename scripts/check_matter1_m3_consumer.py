#!/usr/bin/env python3
"""Required integration with the separately checked-out, exact M3 candidate.

This command does not skip when the upstream checkout is missing. It executes
the upstream temporal adapter against this consumer and tests the feedback
intervention. The imported mathematical dependency is not an admission receipt.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'manual2/scripts'))
from matter1_m3 import verify_vendor, verify_legacy_vendor
import matter1_m3_observation as observation
import matter1_m3_metrology as metrology
from publication_support import verify_foundation

from matter1_m3_producer import HEAD, verify as verify_producer, load, load_upstream
from unittest.mock import patch


def verify(root, upstream):
    root, upstream = Path(root).resolve(), Path(upstream).resolve()
    binding = verify_producer(root, upstream)
    current_api, actual_api = load(root), load_upstream(root, upstream)
    foundation = verify_foundation(root)
    if foundation['upstream_head'] != HEAD:
        raise ValueError('Main and current producer authority differ')
    for name in foundation['files']:
        if (upstream / name).read_bytes() != (root / name).read_bytes():
            raise ValueError('Main import differs from actual upstream: ' + name)
    # Historical reports retain their original executors and complete receipts.
    historical = verify_legacy_vendor(root)
    prior = verify_vendor(root)
    old_metrology = metrology.verify_vendor(root)
    if prior['upstream_head'] != old_metrology['upstream_head']:
        raise ValueError('Historical observation/metrology identities disagree')
    persisted = observation.verify(root)
    persisted_metrology = metrology.verify(root)
    # Replay real R03 inputs through both current producer copies. These current
    # results are compared independently; historical reports are not relabelled.
    current = observation.report(root, temporal_api=current_api.temporal)
    actual = observation.report(root, temporal_api=actual_api.temporal)
    if observation.canonical(current) != observation.canonical(actual):
        raise ValueError('Current typed observation differs from actual producer')
    with current_api.activate():
        quantities = current_api.experimental.build_report()
    with actual_api.activate():
        actual_quantities = actual_api.experimental.build_report()
    if observation.canonical(quantities) != observation.canonical(actual_quantities):
        raise ValueError('Current quantity/comparison API differs from actual producer')
    result = actual_api.temporal.consumer_integration(root)
    if result['common_prefix_through_cut'] != 39 or not result['feedback_disabled_original_validator_rejected']:
        raise ValueError('M3 feedback/history integration failed')
    cases = result['cases']
    if cases['baseline']['counts'] != {'outer_plus': 6, 'outer_minus': 5} or cases['intervention']['counts'] != {'outer_plus': 2, 'outer_minus': 5}:
        raise ValueError('M3 consumer counts changed')
    if result['atomic_point_prediction']['frequency_hz'] is not None:
        raise ValueError('Integration cannot promote the unresolved atomic point prediction')
    import matter1_coupled_preparations as coupled
    import matter1_preparation_workflow as workflow
    coupled_checks = {}
    for label, a, e in coupled.PILOTS:
        config = coupled.default_config(1, a, e)
        expected = coupled.run_case(config, root=root)
        with patch.object(coupled.producer, 'load', return_value=actual_api):
            direct = coupled.run_case(config, root=root)
        if coupled.canonical(expected) != coupled.canonical(direct):
            raise ValueError('Coupled preparation differs from actual producer: ' + label)
        coupled_checks[label] = {'actual_upstream_equals_vendored': True,
                                'result_sha256': coupled.digest(expected)}
    ensemble = coupled.enumerate_paths(coupled.default_config(1, 1, 1, rounds=1), root=root)
    propagation = workflow.propagate_ensemble(ensemble, current_api)
    actual_propagation = workflow.propagate_ensemble(ensemble, actual_api)
    if workflow.canonical(propagation) != workflow.canonical(actual_propagation):
        raise ValueError('Application joint uncertainty differs from actual producer')
    import matter1_preparation_freeze as freeze
    frozen = freeze.build(root, current_api)
    actual_frozen = freeze.build(root, actual_api)
    if workflow.canonical(frozen) != workflow.canonical(actual_frozen):
        raise ValueError('Complete application prediction freeze differs from actual producer')
    return {'status': 'PASS_REQUIRED_M3_CONSUMER', 'upstream_head': HEAD,
            'upstream_tree': binding['upstream_tree'],
            'api_contract_sha256': binding['files']['contracts/scientific/TEMPORAL_OBSERVATION.json']['sha256'],
            'historical_survival_executor_head': historical['upstream_head'],
            'historical_observation_metrology_head': prior['upstream_head'],
            'foundation_upstream_head': foundation['upstream_head'],
            'foundation_source_digest': foundation['source_digest'],
            'scope': 'Exact producer export, real R03 replay, historical report preservation and six current coupled preparations; no physical calibration or empirical agreement',
            'metrology': {'persisted_historical_verification': persisted_metrology},
            'quantity_comparison_dependency': {'actual_upstream_equals_vendored': True,
                'routes': sorted(quantities['quantity_routes']),
                'scope': 'Producer API fixtures; distinct from the downstream coupled application'},
            'coupled_preparations': coupled_checks,
            'application_joint_propagation': {'actual_upstream_equals_vendored': True,
                'result_sha256': workflow.digest(propagation),
                'scope': 'Actual H1 neutral coupled-path finite law; conditional native diagnostics'},
            'complete_application_freeze': {'actual_upstream_equals_vendored': True,
                'result_sha256': workflow.digest(frozen), 'output': frozen['prediction']['output'],
                'scope': frozen['scope']},
            'typed_observation': {**persisted, 'current_actual_upstream_equals_vendored': True,
                'cases': {name: {'original_input_sha256': item['original_input_sha256'],
                    'counts': item['prediction']['complete_temporal_record']['counts'],
                    'context_sha256': item['prediction']['complete_temporal_record']['observation_context']['input_sha256']}
                    for name, item in actual['cases'].items()}},
            'executed': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--upstream-root', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root, args.upstream_root), indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'M3 consumer integration failed: {exc}\n')


if __name__ == '__main__':
    main()
