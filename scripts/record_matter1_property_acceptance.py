#!/usr/bin/env python3
"""Record source/data and native-diagnostic scope after fresh property replay.

Physical property laws remain missing premises. Supplied logs and browser/
reproduction receipts are execution evidence, not independent attestation.
The output must live beside the checks, outside the scientific source tree.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
import record_matter1_acceptance as evidence
from record_matter1_v2_acceptance import validate_logs
from check_matter1_reproduction import expected_output_paths, snapshot

PRIOR_RECEIPTS = ('acceptance.json', 'v2-acceptance.json', 'isotope-acceptance.json')
LANES = {'properties': 'verify_matter1_properties.py',
         'property-model': 'verify_matter1_property_model.py'}
INPUT_NAMES = {*PRIOR_RECEIPTS, 'tests.txt', 'tests-optimized.txt', 'browser.json',
               'publication.json', 'reproduction.json',
               *(name + suffix + '.json' for name in LANES for suffix in ('', '-optimized'))}
BROWSER_PATHS = {'manual2/visuals/matter1-reference.html', 'manual2/visuals/matter1-layout.json'}


def validate_prior_documents(documents, source_inventory, logs, source_ids):
    """Check exact source/test binding and retain each older recorder's scope."""
    evidence.require(set(documents) == set(PRIOR_RECEIPTS), 'All three preceding acceptances are required')
    for name, value in documents.items():
        evidence.check_equal(value['source_test_model_artifact_inventory'], source_inventory,
                             name + ': stale source/artifact inventory')
        for mode in ('normal', 'optimized'):
            evidence.check_equal(value['test_runs'][mode], logs[mode], name + ': stale test log binding')
        rows = value['records']
        evidence.require(type(rows) is list and rows and len({r['id'] for r in rows}) == len(rows),
                         name + ': missing or duplicate criterion')
    core = documents['acceptance.json']
    ids = ({f'P0-{n:02}' for n in range(1, 3)} | {f'P1-{n:02}' for n in range(1, 10)} |
           {f'P2-{n:02}' for n in range(1, 7)} | {f'P3-{n:02}' for n in range(1, 6)} |
           {f'P4-{n:02}' for n in range(1, 4)} | {f'P5-{n:02}' for n in range(1, 7)} |
           {f'F-{n:02}' for n in range(1, 9)})
    evidence.require(core['document_kind'] == 'executed_scoped_acceptance_receipt' and
                     type(core['record_count']) is int and core['record_count'] == len(core['records']) == 39 and
                     {r['id'] for r in core['records']} == ids and
                     all(r['outcome'] == 'executed_scope_pass' for r in core['records']), 'Core acceptance incomplete')
    evidence.require(core['native_admission_status'] == core['atomic_mapping_status'] == 'pending' and
                     core['physical_empirical_status'] == 'not_compared', 'Core acceptance scope promoted')
    v2 = documents['v2-acceptance.json']
    ids = {f'SI-{n:02}' for n in range(1, 19)} | {f'PRED-{n:02}' for n in range(1, 6)}
    evidence.require(type(v2['criteria_count']) is int and v2['criteria_count'] == len(v2['records']) == 23 and
                     {r['id'] for r in v2['records']} == ids and
                     all(r['assertion_outcome'] == 'executed_scope_pass' for r in v2['records']), 'V2 acceptance incomplete')
    evidence.require(v2['atomic_prediction_objective'] == 'incomplete' and v2['native_atomic_admission'] == 'pending',
                     'V2 physical objective promoted')
    isotope = documents['isotope-acceptance.json']
    from record_matter1_isotope_acceptance import GROUPS
    expected_tests = {t for t in source_ids if t.split('.')[2] in GROUPS}
    observed_tests = [r['test_id'] for r in isotope['records'] if 'test_id' in r]
    expected_extra = {'VIS-01', 'VIS-02', 'FOUND-01', 'PUB-01', 'REPRO-01'}
    evidence.require(set(observed_tests) == expected_tests and len(observed_tests) == len(expected_tests) and
                     {r['id'] for r in isotope['records'] if 'test_id' not in r} == expected_extra and
                     type(isotope['record_count']) is int and isotope['record_count'] == len(isotope['records']) and
                     all(r['outcome'] == 'executed_scope_pass' for r in isotope['records']), 'Isotope acceptance incomplete')
    evidence.require(isotope['physical_isotope_half_life_prediction'] == 'not_established' and
                     isotope['native_isotope_admission'] == 'not_established', 'Isotope physical scope promoted')


def verify_prior_file_hashes(checks, documents):
    for name, value in documents.items():
        bindings = value['evidence_sha256']
        evidence.require(type(bindings) is dict and bindings, name + ': evidence hashes missing')
        seen = set()
        for path, expected in bindings.items():
            evidence.require(not Path(path).is_absolute() and '..' not in Path(path).parts,
                             name + ': nonportable evidence path')
            basename = Path(path).name
            evidence.require(basename not in seen and basename not in ('', '.', '..'), 'Ambiguous evidence filename')
            seen.add(basename)
            file = checks / basename
            digest = expected['sha256'] if isinstance(expected, dict) else expected
            evidence.require(evidence.sha(evidence.read_bytes(file)) == digest, name + ': stale evidence ' + basename)
            if isinstance(expected, dict):
                evidence.require(type(expected['bytes']) is int and file.stat().st_size == expected['bytes'],
                                 name + ': evidence size differs')
        evidence.require({'tests.txt', 'tests-optimized.txt'} <= seen, name + ': test evidence hashes missing')


def validate_hash_bindings(root, bindings, paths, context):
    evidence.require(type(bindings) is dict and set(bindings) == set(paths), context + ': input inventory differs')
    for name, digest in bindings.items():
        path = Path(name)
        evidence.require(not path.is_absolute() and '..' not in path.parts, context + ': unsafe input path')
        evidence.require(evidence.sha(evidence.read_bytes(root / path)) == digest, context + ': stale input ' + name)


def validate_browser(root, browser, entity_count):
    evidence.require(browser['status'] == 'PASS' and browser['inputs_unchanged'] is True and
                     browser['page_errors'] == [], 'Browser verification failed')
    validate_hash_bindings(root, browser['input_sha256'], BROWSER_PATHS, 'Browser')
    rows = browser['property_checks']
    evidence.require(type(rows) is list and len(rows) == 6 and
                     {(r['width'], r['theme']) for r in rows} ==
                     {(w, t) for w in (736, 360, 320) for t in ('light', 'dark')},
                     'Property browser viewport/theme coverage incomplete')
    evidence.require(all(type(r['entities']) is int and r['entities'] == entity_count and
                         type(r['element_coverage']) is int and r['element_coverage'] == 118 and
                         r['source_state_separate_from_count'] is True and r['horizontal_overflow'] is False
                         for r in rows), 'Property browser assertion failed')


def validate_reproduction(root, receipt, expected_paths, current_snapshot):
    evidence.require(receipt['status'] == 'PASS_REPRODUCTION' and receipt['source_unchanged'] is True,
                     'Reproduction failed or changed inputs')
    evidence.check_equal(receipt['source_sha256'], current_snapshot, 'Reproduction source snapshot is stale')
    rows = receipt['outputs']; paths = [r['path'] for r in rows]
    evidence.require(len(paths) == len(set(paths)) and set(paths) == expected_paths, 'Reproduction output inventory incomplete')
    allowed = {'byte equality', 'PDF text, vector geometry, colors and size', 'manifest excluding PDF binary hash'}
    for row in rows:
        path = Path(row['path'])
        evidence.require(not path.is_absolute() and '..' not in path.parts and
                         (root / 'manual2' / path).is_file() and row['comparison'] in allowed,
                         'Invalid reproduction output/comparison')


def fresh_verifier(root, relative, optimized=False):
    command = [sys.executable, '-B', *(['-O'] if optimized else []), str(root / relative), '--root', str(root)]
    process = subprocess.run(command, cwd=root, text=True, capture_output=True)
    evidence.require(process.returncode == 0, 'Fresh verification failed: ' + relative + '\n' + process.stderr + process.stdout)
    try:
        result = json.loads(process.stdout)
    except ValueError as exc:
        raise evidence.EvidenceError('Fresh verifier did not return one JSON receipt: ' + relative) from exc
    return result


def validate_lane_reports(reports):
    data, model = reports['properties'], reports['property-model']
    evidence.require(type(data['acquisition_complete']) is bool and
                     type(data['missing_source_families']) is list and
                     all(type(s) is str and s for s in data['missing_source_families']) and
                     len(set(data['missing_source_families'])) == len(data['missing_source_families']) and
                     data['acquisition_complete'] == (not data['missing_source_families']),
                     'Property acquisition outcome is missing or inconsistent')
    evidence.require(data['status'] == 'PASS_ELEMENT_PROPERTY_CATALOG', 'Property source/data verifier did not pass')
    evidence.require(type(data['physical_predictions_executed']) is int and data['physical_predictions_executed'] == 0 and
                     type(data['counts']['element_z_coverage']) is int and data['counts']['element_z_coverage'] == 118 and
                     type(data['counts']['pilot_isotopes']) is int and data['counts']['pilot_isotopes'] == 6,
                     'Property identity coverage incomplete or source acquisition promoted to physical prediction')
    evidence.require(model['status'] == 'PASS_PROPERTY_MODEL_ORIGINAL_INPUT_REPLAY' and
                     type(model['native_pilots']) is int and model['native_pilots'] == 6 and
                     model['comparison_checked'] is True and model['physical_prediction_complete'] is False and
                     model['whole_law_disposition'] == 'incomplete_missing_premises', 'Property model status promoted or incomplete')
    return 'acquired_with_reported_coverage' if data['acquisition_complete'] else 'partial_source_acquisition'


def record(checks, output):
    root = evidence.REPO.resolve(); checks = checks.resolve(); output = output.resolve()
    evidence.require(checks.is_dir() and output.parent == checks and not output.is_relative_to(root) and
                     output.name not in INPUT_NAMES, 'Output must be a separate receipt beside checks outside the source tree')
    source_ids = evidence.source_test_ids()
    logs = validate_logs(checks, source_ids)
    inventory = evidence.input_inventory(output)
    prior = {name: evidence.read_json(checks / name) for name in PRIOR_RECEIPTS}
    evidence.require(all(output.name not in {Path(name).name for name in doc['evidence_sha256']}
                         for doc in prior.values()), 'Output is already an input to a preceding acceptance receipt')
    validate_prior_documents(prior, inventory, logs, source_ids)
    verify_prior_file_hashes(checks, prior)
    reports = {}
    for name, script in LANES.items():
        for optimized in (False, True):
            suffix = '-optimized' if optimized else ''
            supplied = evidence.read_json(checks / (name + suffix + '.json'))
            current = fresh_verifier(root, 'manual2/scripts/' + script, optimized)
            evidence.check_equal(supplied, current, name + suffix + ': receipt differs from fresh replay')
            if optimized:
                evidence.check_equal(current, reports[name], name + ': Python modes disagree')
            reports[name] = current
    data_disposition = validate_lane_reports(reports)
    states = evidence.read_json(root / 'manual2/data/m1/properties/states.json')
    browser = evidence.read_json(checks / 'browser.json')
    validate_browser(root, browser, len(states['entities']))
    publication = evidence.read_json(checks / 'publication.json')
    evidence.check_equal(publication, fresh_verifier(root, 'scripts/verify_matter1_publication.py'),
                         'Publication receipt differs from current source/PDF verification')
    evidence.require(publication['status'] == 'PASS_PUBLICATION', 'Publication verification failed')
    reproduction = evidence.read_json(checks / 'reproduction.json')
    validate_reproduction(root, reproduction, expected_output_paths(root), snapshot(root))
    evidence.check_equal(inventory, evidence.input_inventory(output), 'Acceptance verification changed source/artifacts')
    report = {'schema_version': 1, 'document_kind': 'element_property_scoped_acceptance',
        'status': 'RECORDED_PROPERTY_SCOPED_ACCEPTANCE', 'data_coverage_disposition': data_disposition,
        'data_acquisition_complete': reports['properties']['acquisition_complete'],
        'missing_source_families': reports['properties']['missing_source_families'],
        'native_diagnostic_execution': 'six_pilots_replayed', 'physical_property_laws': 'missing_premise',
        'whole_law_disposition': 'incomplete_missing_premises', 'physical_prediction_complete': False,
        'independent_empirical_predictions_verified': 0,
        'interpretation': 'Source/data coverage and declared native diagnostics only. Unselected map witnesses, acquired measurements and a defining Cs reference do not establish physical property laws. Unacquired source families remain partial.',
        'evidence_scope': 'Exact supplied test coverage, current prior acceptance bindings, fresh source/model/publication replay, supplied source-bound browser and reproduction receipts; not independent execution attestation.',
        'preceding_acceptance_receipts': list(PRIOR_RECEIPTS), 'test_runs': logs, 'lane_results': reports,
        'source_test_model_artifact_inventory': inventory,
        'evidence_sha256': {name: evidence.sha(evidence.read_bytes(checks / name)) for name in sorted(INPUT_NAMES)}}
    output.write_bytes(evidence.canonical(report))
    return {key: report[key] for key in ('status', 'data_coverage_disposition', 'physical_property_laws',
                                       'physical_prediction_complete')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checks-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = record(args.checks_dir, args.output)
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        parser.exit(1, 'Property acceptance failed: ' + str(exc) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
