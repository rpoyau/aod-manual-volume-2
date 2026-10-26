#!/usr/bin/env python3
"""Record the 18 SI and five prediction criteria from complete successful logs.

Passing bounded assertions does not complete the atomic prediction objective.
Like the original recorder, this consumes logs; it is not execution attestation.
"""
import argparse
import csv
import io
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import record_matter1_acceptance as old
from check_matter1_v2_application import verify as conservation

LANES = ('stateful', 'metrology', 'bipm', 'atomic')


def criteria(root, actual_ids):
    rows = list(csv.DictReader(io.StringIO((root / 'manual2/evidence/v2-request/SI_ACCEPTANCE.csv').read_text())))
    old.require(len(rows) == 18 and {r['id'] for r in rows} == {f'SI-{n:02}' for n in range(1, 19)}, '18 SI IDs required')
    for row in rows:
        old.require(row.pop('status') == 'PLANNED', 'request criterion was promoted')
        number = row['id'][3:]
        matches = sorted(t for t in actual_ids if '.test_matter1_metrology.' in t and f'.test_si_{number}_' in t)
        if number == '13':
            matches = sorted(t for t in actual_ids if '.test_matter1_bipm.' in t and any(x in t for x in ('test_full_covariance', 'test_rounding_includes')))
        if number == '14':
            matches += sorted(t for t in actual_ids if '.test_matter1_bipm.' in t and '.test_covariance_scaling_' in t)
        old.require(bool(matches), 'criterion has no actual assertion: ' + row['id'])
        row.update(test_ids=matches, assertion_scope=('published_data_covariance_and_rounding' if number == '13' else
                   'synthetic_stateful_observation_map_only' if number == '18' else 'synthetic_measurement_equations_and_guards'),
                   objective_status='scoped_assertions_only_physical_application_pending')
    requirements = [
        'Calculate an AOD atomic observable without the target value',
        'Use Cs to anchor units without isotope-specific target fitting',
        'Freeze and bind a target-independent prediction artifact',
        'Compare separately with full applicable uncertainty and exposure',
        'A controlled dynamics intervention affects the mapped observable',
    ]
    for n, requirement in enumerate(requirements, 1):
        matches = sorted(t for t in actual_ids if '.test_matter1_atomic.' in t and f'.test_PRED_{n:02}_' in t)
        old.require(bool(matches), 'prediction criterion has no actual assertion')
        rows.append({'id': f'PRED-{n:02}', 'requirement': requirement, 'test_ids': matches,
                     'expected_evidence': 'Actual atomic result required for completion; current countermodels/guards are scoped evidence.',
                     'assertion_scope': 'finite_countermodel_or_separation_guard_not_atomic_prediction',
                     'objective_status': 'incomplete_atomic_map_unresolved'})
    return rows


def validate_logs(directory, actual_ids):
    logs = {mode: old.parse_test_log(directory / filename) for mode, filename in
            [('normal', 'tests.txt'), ('optimized', 'tests-optimized.txt')]}
    old.require(set(logs['normal']['methods']) == actual_ids, 'normal log lacks the complete current suite')
    expected = {t for t in actual_ids if t.split('.')[2] in old.OPTIMIZED_MODULES}
    old.require(set(logs['optimized']['methods']) == expected, 'optimized log lacks the complete validation subset')
    return logs


def validate_lane_receipts(root, directory):
    # Re-execute read-only lane verifiers so a stale/promoted receipt is rejected.
    sys.path.insert(0, str(root / 'manual2/scripts'))
    import matter1_stateful, matter1_metrology, matter1_bipm, matter1_atomic
    modules = (matter1_stateful, matter1_metrology, matter1_bipm, matter1_atomic)
    reports = {}
    for lane, module in zip(LANES, modules):
        expected = module.verify(root)
        for suffix in ('', '-optimized'):
            value = old.read_json(directory / (lane + suffix + '.json'))
            old.check_equal(value, expected, lane + suffix + ': current verified receipt differs')
        reports[lane] = expected
    old.check_equal(old.read_json(directory / 'v2-conservation.json'), conservation(root), 'v2 preservation receipt differs')
    return reports


def record(directory, output):
    root = old.REPO
    old.require(directory.is_dir(), 'checks directory missing')
    inputs = [directory / f'{lane}{suffix}.json' for lane in LANES for suffix in ('', '-optimized')]
    inputs += [directory / 'v2-conservation.json', directory / 'tests.txt', directory / 'tests-optimized.txt']
    old.require(output.resolve() not in {p.resolve() for p in inputs}, 'output must not overwrite evidence')
    ids = old.source_test_ids()
    logs = validate_logs(directory, ids)
    reports = validate_lane_receipts(root, directory)
    rows = criteria(root, ids)
    for row in rows:
        for test in row['test_ids']:
            old.require(all(test in logs[m]['methods'] for m in logs), 'required assertion missing from a test mode')
        row['assertion_outcome'] = 'executed_scope_pass'
        row['successful_modes'] = ['normal', 'optimized']
    result = {'schema_version': 1, 'criteria_count': 23, 'records': rows,
              'atomic_prediction_objective': 'incomplete', 'native_atomic_admission': 'pending',
              'interpretation': 'Executed synthetic metrology, external consistency checks and finite countermodels do not constitute an AOD atomic frequency prediction.',
              'evidence_scope': 'Completed supplied logs and fresh read-only checks, hashed with current sources. Plain logs are not independently attested execution provenance.',
              'test_runs': logs,
              'lane_results': reports,
              'evidence_sha256': {p.name: old.sha(old.read_bytes(p)) for p in inputs},
              'source_test_model_artifact_inventory': old.input_inventory(output)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(old.canonical(result))
    return {'status': 'RECORDED_V2_SCOPED_ACCEPTANCE', 'criteria': 23,
            'atomic_prediction_objective': 'incomplete', 'output_sha256': old.sha(output.read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checks-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(record(args.checks_dir, args.output), indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f'v2 acceptance failed: {exc}\n')


if __name__ == '__main__':
    main()
