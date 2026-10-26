#!/usr/bin/env python3
"""Record the 39 scoped outcomes from completed tests and check receipts.

Run the checks separately, then call this recorder with their output directory.
This does not run tests, certify native admission, or establish physical results.
The current source snapshot and supplied evidence are hashed at recording time;
plain test logs are execution evidence, not independently attested provenance.
"""
from __future__ import annotations
import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[1]
PLAN = Path('manual2/evidence/fusion-acceptance-plan.json')
OPTIMIZED_MODULES = {'test_matter1_application', 'test_matter1_data', 'test_matter1_folding',
                     'test_matter1_temporal', 'test_matter1_hyperfine'}
RECEIPTS = ('ledger', 'ledger-optimized', 'figure', 'conservation', 'publication', 'browser',
            'reproduction', 'folding', 'folding-optimized', 'temporal', 'temporal-optimized',
            'hyperfine', 'hyperfine-optimized')
TEST_START = re.compile(r'^(test\w*) \(((?:manual2\.tests\.)?test_matter1_\w+\.\w+\.test\w*)\)(.*)$')
TEST_RESULT = re.compile(r'\.\.\. (.+)$')
SUMMARY = re.compile(r'^Ran (\d+) tests? in ([0-9.]+)s$')


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def read_bytes(path):
    try:
        return Path(path).read_bytes()
    except OSError as exc:
        raise EvidenceError(f'{path.name}: {exc.strerror}') from exc


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'{path.name}: duplicate key {key}')
            result[key] = value
        return result
    try:
        return json.loads(read_bytes(path), object_pairs_hook=unique)
    except (ValueError, UnicodeError) as exc:
        raise EvidenceError(f'{path.name}: invalid JSON: {exc}') from exc


def parse_test_log(path):
    """Accept complete verbose unittest logs, including a second docstring line."""
    try:
        lines = read_bytes(path).decode('utf-8').splitlines()
    except UnicodeError as exc:
        raise EvidenceError(f'{path.name}: non-UTF8 test log') from exc
    require(lines and [line.strip() for line in lines if line.strip()][-1] == 'OK',
            f'{path.name}: complete successful unittest trailer required')
    methods, pending, summaries = {}, None, []
    for number, line in enumerate(lines, 1):
        start = TEST_START.match(line)
        if start:
            require(pending is None, f'{path.name}:{number}: preceding test has no result')
            short, test_id, tail = start.groups()
            require(test_id.rsplit('.', 1)[1] == short, f'{path.name}:{number}: method ID mismatch')
            if not test_id.startswith('manual2.tests.'):
                test_id = 'manual2.tests.' + test_id
            require(test_id not in methods, f'{path.name}:{number}: duplicate method {test_id}')
            pending = (test_id, number)
            line = tail
        result = TEST_RESULT.search(line)
        if result and pending is not None:
            require(result.group(1) == 'ok', f'{path.name}:{number}: nonpassing test {pending[0]}: {result.group(1)}')
            methods[pending[0]] = {'start_line': pending[1], 'result_line': number, 'outcome': 'ok'}
            pending = None
        summary = SUMMARY.match(line)
        if summary:
            summaries.append((int(summary.group(1)), summary.group(2)))
    require(pending is None and len(summaries) == 1, f'{path.name}: incomplete or multiple test runs')
    require(summaries[0][0] == len(methods) and methods, f'{path.name}: summary count differs from successful method records')
    return {'method_count': len(methods), 'elapsed_seconds_as_reported': summaries[0][1], 'methods': methods}


def source_test_ids():
    result = set()
    for path in sorted((REPO / 'manual2/tests').glob('test_matter1_*.py')):
        tree = ast.parse(path.read_text())
        for cls in tree.body:
            if isinstance(cls, ast.ClassDef):
                for method in cls.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name.startswith('test_'):
                        result.add(f'manual2.tests.{path.stem}.{cls.name}.{method.name}')
    require(result, 'no repository test methods found')
    return result


def check_equal(a, b, context):
    require(canonical(a) == canonical(b), context)


def expect(doc, key, value, name):
    require(key in doc and canonical(doc[key]) == canonical(value), f'{name}: unsupported/missing {key}')


def validate_receipts(directory):
    receipts = {name: read_json(directory / (name + '.json')) for name in RECEIPTS}
    for name in RECEIPTS:
        err = directory / (name + '.err')
        if err.exists():
            require(not read_bytes(err).strip(), f'{err.name}: stderr is not empty; resolve or document by rerunning the check')
        require(isinstance(receipts[name], dict), f'{name}: receipt must be an object')
    for name in ('ledger', 'folding', 'temporal', 'hyperfine'):
        check_equal(receipts[name], receipts[name + '-optimized'], f'{name}: optimized receipt differs')
    report_paths = {'ledger': 'manual2/data/m1/matter1_audit_report.json',
                    'folding': 'manual2/data/m1/folding/folding_report.json',
                    'temporal': 'manual2/data/m1/folding/temporal_report.json',
                    'hyperfine': 'manual2/data/m1/hyperfine/hyperfine_report.json'}
    for name, path in report_paths.items():
        check_equal(receipts[name], read_json(REPO / path), f'{name}: receipt differs from current persisted verified report')
    ledger = receipts['ledger']
    expect(ledger, 'status', 'PASS', 'ledger')
    expect(ledger, 'profile', 'static_relational_reference', 'ledger')
    expect(ledger, 'named_element_references', 118, 'ledger')
    expect(ledger, 'total_reference_slots', 126, 'ledger')
    require(ledger.get('native_evidence_lanes') and set(ledger['native_evidence_lanes'].values()) == {'not_executed'}, 'ledger: native lane promotion')
    folding = receipts['folding']
    for key, value in {'verification_status': 'verified_illustrative_contract', 'native_admission': 'not_asserted',
                       'native_execution': 'not_asserted', 'empirical_status': 'not_tested'}.items():
        expect(folding, key, value, 'folding')
    expect(folding['events'], 'native_closure_count', None, 'folding.events')
    expect(folding['events'], 'native_beat_count', None, 'folding.events')
    temporal = receipts['temporal']
    expect(temporal, 'finite_model_execution', 'executed', 'temporal')
    expect(temporal, 'statuses', {'atomic_mapping_status': 'pending', 'empirical_status': 'not_tested',
                                'native_admission_status': 'pending', 'native_execution_status': 'not_claimed',
                                'record_class': 'declared_finite_folding_model'}, 'temporal')
    for field, filename in [('geometry_sha256', 'two_square_fold.json'), ('model_sha256', 'temporal_model.json'), ('trace_sha256', 'temporal_trace.json')]:
        expect(temporal, field, sha(canonical(read_json(REPO / 'manual2/data/m1/folding' / filename))), 'temporal')
    hyperfine = receipts['hyperfine']
    for key, value in {'P4a_status': 'inventory_verified', 'classification': 'external_retrospective_reference_arithmetic',
                       'atomic_native_admission_status': 'pending', 'atomic_native_execution_status': 'not_executed',
                       'empirical_status': 'not_compared', 'physical_map_status': 'pending',
                       'predicted_frequency_ratio': None, 'empirical_score': None}.items():
        expect(hyperfine, key, value, 'hyperfine')
    for path, digest in hyperfine['input_sha256'].items():
        require(Path(path).name == path, 'hyperfine input path not portable')
        require(sha(read_bytes(REPO / 'manual2/data/m1/hyperfine' / path)) == digest, f'hyperfine input changed: {path}')
    conservation = receipts['conservation']
    for key, value in {'status': 'PASS_CONSERVATION', 'source_unchanged': True, 'elements': 118, 'slots': 126,
                       'baseline_numeric_comparisons': 3024, 'v94_placement_field_comparisons': 708,
                       'r24_declaration_joins': 118, 'tracked_skill_entry_points': 5, 'tracked_skill_files': 11}.items():
        expect(conservation, key, value, 'conservation')
    request = read_json(REPO / 'manual2/evidence/fusion-request.json')
    expect(conservation, 'historical_request_head', request['base_head'], 'conservation')
    expect(conservation, 'historical_request_tree', request['base_tree'], 'conservation')
    for name, expected in request['preservation_sha256'].items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts, 'preservation path not portable')
        require(sha(read_bytes(REPO / path)) == expected, f'preserved file changed: {name}')
    figure = receipts['figure']
    for key, value in {'status': 'PASS', 'inputs_unchanged': True, 'svg_mark_labels': 126, 'companion_data_binding': 'equal'}.items():
        expect(figure, key, value, 'figure')
    expect(figure['pdf'], 'marks_checked', 126, 'figure.pdf')
    expect(figure['pdf'], 'fonts_embedded', True, 'figure.pdf')
    expect(figure['pdf'], 'upright_text', True, 'figure.pdf')
    browser = receipts['browser']
    for key, value in {'status': 'PASS', 'inputs_unchanged': True, 'keyboard_and_pointer': True,
                       'light_and_dark': True, 'page_errors': []}.items():
        expect(browser, key, value, 'browser')
    for key, value in {'marks': 126, 'named_labels': 118, 'unfilled_slots': 8, 'overlaps': [], 'clipped_text': []}.items():
        expect(browser['desktop'], key, value, 'browser.desktop')
    require({r['width'] for r in browser['responsive']} == {320, 360}, 'browser: expected narrow-screen checks missing')
    require(all(r['horizontal_overflow'] is False and r['visible_roles'] is True for r in browser['responsive']), 'browser: responsive assertion failed')
    reproduction = receipts['reproduction']
    expect(reproduction, 'status', 'PASS_REPRODUCTION', 'reproduction')
    expect(reproduction, 'source_unchanged', True, 'reproduction')
    output_paths = [r['path'] for r in reproduction['outputs']]
    from check_matter1_reproduction import EXPECTED_OUTPUTS
    require(len(output_paths) == len(set(output_paths)) and set(output_paths) == EXPECTED_OUTPUTS, 'reproduction: incomplete or duplicate output inventory')
    for row in reproduction['outputs']:
        path = Path(row['path'])
        require(not path.is_absolute() and '..' not in path.parts and (REPO / 'manual2' / path).is_file(), 'reproduction: missing current output')
        require(row['comparison'] in {'byte equality', 'PDF text, vector geometry, colors and size', 'manifest excluding PDF binary hash'}, 'reproduction: unsupported comparison outcome')
    publication = receipts['publication']
    for key, value in {'status': 'PASS_PUBLICATION', 'manual_text_equal': True, 'main_text_matches_release': True}.items():
        expect(publication, key, value, 'publication')
    require(type(publication['manual_pages']) is int and publication['manual_pages'] > 0 and publication['root_main_links'] == publication['nested_main_links'] > 0, 'publication: page/link counts invalid')
    foundation = read_json(REPO / 'manual2/evidence/foundation-source.json')
    expect(publication, 'foundation_source_digest', foundation['source_digest'], 'publication')
    build = read_json(REPO / 'manual2/evidence/publication-build.json')
    expect(publication, 'main_pages', build['main_pages'], 'publication')
    for group in ('manual_inputs', 'published_artifacts'):
        require(build[group], f'publication: missing {group}')
        for name, expected in build[group].items():
            path = Path(name)
            require(not path.is_absolute() and '..' not in path.parts, 'publication path not portable')
            require(sha(read_bytes(REPO / path)) == expected, f'publication input/artifact changed: {name}')
    return receipts


def scope_for(row):
    if row['stage'] in ('P2', 'P3'):
        return 'finite_declared_model_only_native_pending'
    if row['stage'] == 'P4' or row['id'] in ('P5-01', 'P5-02', 'P5-03', 'P5-06'):
        return 'guard_only_physical_pending'
    if row['stage'] == 'P1':
        return 'finite_geometry_only_native_pending'
    return 'binding_integrity_or_publication_only'


def receipts_for(row):
    if row['stage'] == 'P0':
        return ['conservation', 'ledger', 'ledger-optimized']
    if row['stage'] == 'P1':
        return ['folding', 'folding-optimized']
    if row['stage'] in ('P2', 'P3'):
        return ['temporal', 'temporal-optimized']
    if row['stage'] == 'P4' or row['id'] in ('P5-01', 'P5-02', 'P5-03'):
        return ['hyperfine', 'hyperfine-optimized']
    if row['id'] == 'P5-05':
        return ['publication', 'figure', 'browser', 'reproduction']
    return ['ledger', 'ledger-optimized', 'folding', 'folding-optimized', 'temporal', 'temporal-optimized', 'hyperfine', 'hyperfine-optimized']


def input_inventory(output):
    patterns = ('.agents/skills/**/*', '.github/workflows/matter1.yml', '*.tex', '*.bib', 'sections/**/*.tex',
                'appendices/**/*.tex', 'manual2/**/*.bib', 'README.md', 'requirements-matter1.txt', 'package.json',
                'bib/**/*', 'scripts/*.py', 'manual2/**/*.tex', 'manual2/scripts/*.py', 'manual2/scripts/*.cjs',
                'manual2/tests/*.py', 'manual2/data/**/*', 'manual2/evidence/*.json', 'manual2/evidence/*.csv',
                'manual2/visuals/*', 'manual2/figures/*', 'main.pdf', 'manual2.pdf', 'manual2/main.pdf')
    result = {}
    for pattern in patterns:
        for path in REPO.glob(pattern):
            if path.is_file() and path.resolve() != output.resolve() and '__pycache__' not in path.parts:
                name = path.relative_to(REPO).as_posix()
                data = read_bytes(path)
                result[name] = {'sha256': sha(data), 'bytes': len(data)}
    require(str(PLAN) in result and 'scripts/record_matter1_acceptance.py' in result, 'source/test/model hash inventory incomplete')
    return dict(sorted(result.items()))


def record(checks_dir, output):
    require(checks_dir.is_dir(), 'checks directory missing')
    supplied_inputs = [checks_dir / (name + '.json') for name in RECEIPTS] + [checks_dir / 'tests.txt', checks_dir / 'tests-optimized.txt', REPO / PLAN]
    require(output.resolve() not in {p.resolve() for p in supplied_inputs}, 'output must not overwrite any evidence input')
    try:
        evidence_prefix = checks_dir.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        evidence_prefix = 'checks'
    plan = read_json(REPO / PLAN)
    rows = plan['records']
    ids = {f'P0-{n:02d}' for n in range(1, 3)} | {f'P1-{n:02d}' for n in range(1, 10)} | {f'P2-{n:02d}' for n in range(1, 7)} | {f'P3-{n:02d}' for n in range(1, 6)} | {f'P4-{n:02d}' for n in range(1, 4)} | {f'P5-{n:02d}' for n in range(1, 7)} | {f'F-{n:02d}' for n in range(1, 9)}
    require(len(rows) == 39 and {r['id'] for r in rows} == ids, 'acceptance plan does not contain all 39 unique criteria')
    logs = {'normal': parse_test_log(checks_dir / 'tests.txt'), 'optimized': parse_test_log(checks_dir / 'tests-optimized.txt')}
    actual_ids = source_test_ids()
    require(set(logs['normal']['methods']) == actual_ids, 'normal log does not contain exactly the current complete test suite')
    optimized_ids = {t for t in actual_ids if t.split('.')[2] in OPTIMIZED_MODULES}
    require(set(logs['optimized']['methods']) == optimized_ids, 'optimized log does not contain the complete declared validation subset')
    final_publication = checks_dir / 'tests-publication-final.txt'
    if final_publication.exists():
        logs['publication_final'] = parse_test_log(final_publication)
        expected = {t for t in actual_ids if t.split('.')[2] == 'test_matter1_publication'}
        require(set(logs['publication_final']['methods']) == expected, 'final publication log does not cover its entire current test module')
    receipts = validate_receipts(checks_dir)
    evidence_paths = [checks_dir / (name + '.json') for name in RECEIPTS] + [checks_dir / 'tests.txt', checks_dir / 'tests-optimized.txt']
    if final_publication.exists():
        evidence_paths.append(final_publication)
    evidence_hashes = {evidence_prefix + '/' + p.name: {'sha256': sha(read_bytes(p)), 'bytes': p.stat().st_size} for p in evidence_paths}
    outcomes = []
    for original in rows:
        row = deepcopy(original)
        require(row['outcome'] == 'not_run' and row['scope_classification'] == scope_for(row), f"{row['id']}: plan outcome/scope promoted")
        for field in ('subject', 'stimulus', 'expected', 'assertion_scope', 'remaining_dependency'):
            require(isinstance(row[field], str) and bool(row[field].strip()), f"{row['id']}: required criterion/scope field missing")
        observed = []
        for test_id in row['test_ids']:
            require(test_id in logs['normal']['methods'], f"{row['id']}: referenced normal test absent: {test_id}")
            modes = ['normal']
            if test_id.split('.')[2] in OPTIMIZED_MODULES:
                require(test_id in logs['optimized']['methods'], f"{row['id']}: referenced optimized test absent: {test_id}")
                modes.append('optimized')
            if test_id.split('.')[2] == 'test_matter1_publication' and 'publication_final' in logs:
                require(test_id in logs['publication_final']['methods'], f"{row['id']}: final publication test absent: {test_id}")
                modes.append('publication_final')
            observed.append({'test_id': test_id, 'successful_logs': modes})
        row['outcome'] = 'executed_scope_pass'
        row['observed_tests'] = observed
        row['check_evidence'] = [evidence_prefix + '/' + name + '.json' for name in receipts_for(row)]
        row['physical_status'] = ('guard_only_physical_application_pending' if row['scope_classification'] == 'guard_only_physical_pending'
                                  else 'native_and_physical_admission_pending' if row['stage'] in ('P1', 'P2', 'P3')
                                  else 'no_native_or_physical_claim')
        outcomes.append(row)
    report = {
        'schema_version': 1, 'document_kind': 'executed_scoped_acceptance_receipt', 'record_count': len(outcomes),
        'request_archive_sha256': plan['request_archive_sha256'], 'request_acceptance_sha256': plan['request_acceptance_sha256'],
        'acceptance_plan_sha256': sha(read_bytes(REPO / PLAN)),
        'interpretation': 'All recorded assertions passed in their stated scope. Finite geometry, declared-model execution, guard rejection and publication integrity do not establish native motif admission, atomic prediction or empirical agreement.',
        'evidence_binding_scope': 'Supplied successful test/check outputs plus current source/test/model hashes at recording. Plain logs are not independently attested execution provenance. Run the listed commands separately before recording; no tests are run by this recorder.',
        'native_admission_status': 'pending', 'atomic_mapping_status': 'pending', 'physical_empirical_status': 'not_compared',
        'mutation_count': None, 'mutation_count_scope': 'Not inferred from unittest method totals or subtest descriptions.',
        'test_runs': logs, 'check_receipt_paths': [evidence_prefix + '/' + name + '.json' for name in RECEIPTS],
        'evidence_sha256': evidence_hashes, 'source_test_model_artifact_inventory': input_inventory(output),
        'unresolved_dependencies': receipts['hyperfine']['unresolved_dependencies'], 'records': outcomes,
    }
    # All input checks finish before the only write in this program.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical(report))
    return {'status': 'RECORDED_SCOPED_ACCEPTANCE', 'criteria': len(outcomes),
            'normal_test_methods': logs['normal']['method_count'], 'optimized_test_methods': logs['optimized']['method_count'],
            'final_publication_test_methods': logs.get('publication_final', {}).get('method_count'),
            'output_sha256': sha(read_bytes(output)), 'native_admission_status': 'pending', 'physical_empirical_status': 'not_compared'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checks-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = record(args.checks_dir, args.output)
    except (EvidenceError, OSError, KeyError, TypeError, SyntaxError) as exc:
        parser.exit(1, f'acceptance recording failed: {exc}\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
