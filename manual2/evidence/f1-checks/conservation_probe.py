#!/usr/bin/env python3
"""Strict F1 scientific conservation against pinned pre-repair Git objects.

Read-only. No modules from either checkout are imported. Scientific JSON permits
only enumerated digest leaves; all other values and types must be unchanged.
Existing tracked files outside explicit repair/delivery allowlists stay byte
identical. New evidence is execution evidence, not independently attested here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

UPSTREAM_BASE = 'b78b48dd7aa1608dbb7141e9814e33c3cfcf900b'
MATTER_BASE = '6bb55ca9dff91bbef015ae56c3c4e627c54f2193'
UPSTREAM_CODE = 'manual/scripts/aod_mapping_error.py'
VENDOR_CODE = 'manual2/vendor/aod_m3/aod_mapping_error.py'
SURVIVAL = 'manual2/data/m1/survival/'
VARIANTS = ('baseline', 'capacity_0', 'feedback_off', 'loss_gain_2')
GUARD = b"            require(rational(payload['value']) >= 0, 'nonnegative evidence error value required')\n"
GUARD_ANCHOR = b"            require(isinstance(payload, dict) and set(payload) == payload_fields, 'evidence payload fields')\n"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def base_blob(root, base, name):
    return git(root, 'show', base + ':' + name)


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def digest(value, matter=False):
    data = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n') if matter else json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return sha(data.encode())


def leaf_differences(before, after, path=()):
    if type(before) is not type(after):
        yield path, before, after
    elif isinstance(before, dict):
        require(before.keys() == after.keys(), 'JSON field set changed at ' + repr(path))
        for key in sorted(before):
            yield from leaf_differences(before[key], after[key], path + (key,))
    elif isinstance(before, list):
        require(len(before) == len(after), 'JSON list length changed at ' + repr(path))
        for index, (a, b) in enumerate(zip(before, after)):
            yield from leaf_differences(a, b, path + (index,))
    elif before != after:
        yield path, before, after


def pointer(path):
    return '/' + '/'.join(str(x).replace('~', '~0').replace('/', '~1') for x in path)


def check_json(root, base, name, allowed, sha_only=True):
    old_blob = base_blob(root, base, name)
    blob = (root / name).read_bytes()
    old, current = json.loads(old_blob), json.loads(blob)
    changes = list(leaf_differences(old, current))
    require(all(p in allowed for p, a, b in changes),
            name + ': forbidden JSON changes: ' + repr([pointer(p) for p, a, b in changes if p not in allowed]))
    if sha_only:
        for path, before, after in changes:
            require(isinstance(before, str) and isinstance(after, str) and
                    re.fullmatch(r'[0-9a-f]{64}', before) and re.fullmatch(r'[0-9a-f]{64}', after),
                    name + ': changed leaf is not a SHA-256: ' + pointer(path))
    return current, {'path': name, 'before_sha256': sha(old_blob), 'after_sha256': sha(blob),
                     'changed_leaves': [pointer(p) for p, a, b in changes],
                     'all_other_values_types_and_structure_unchanged': True}


def execution_digest_paths(prefix, output='y'):
    output_prefix = prefix + ('outputs', output)
    return {prefix + ('spec_sha256',), output_prefix + ('sha256',),
            output_prefix + ('origin', 'execution_sha256'),
            output_prefix + ('origin', 'map', 'code_sha256'),
            output_prefix + ('origin', 'map', 'spec_sha256')}


def upstream_paths():
    mapping = set()
    for index in range(3):
        mapping |= {('maps', index, 'code_sha256'), ('maps', index, 'spec_sha256')}
    for index in range(2):
        mapping |= execution_digest_paths(('composition', 'stages', index))
        mapping |= execution_digest_paths(('exact_lossy_projection', 'witnesses', index))
    nested = ('composition', 'stages', 1, 'outputs', 'y', 'origin', 'inputs', 'x')
    mapping |= {nested + ('sha256',), nested + ('origin', 'execution_sha256'),
                nested + ('origin', 'map', 'code_sha256'), nested + ('origin', 'map', 'spec_sha256'),
                ('composition', 'stages', 1, 'input_sha256')}
    temporal = {('prediction', 'mapping_contract', 'code_sha256'),
                ('prediction', 'mapping_contract', 'spec_sha256'),
                ('comparison', 'prediction_sha256'),
                ('evaluation_only_mutation', 'prediction_sha256')}
    for output in ('elapsed_seconds', 'average_rate_hz'):
        temporal |= execution_digest_paths(('prediction', 'mapped'), output)
    return {'manual/data/m3/mapping_error.json': mapping, 'manual/data/m3/temporal.json': temporal}


def tracked_conservation(root, base, allowed, new_prefixes=(), new_files=()):
    tree = {}
    for entry in git(root, 'ls-tree', '-rz', base).split(b'\0'):
        if not entry:
            continue
        metadata, path = entry.split(b'\t', 1)
        mode, kind, object_id = metadata.decode().split()
        require(kind == 'blob', 'unexpected tracked object type: ' + path.decode())
        tree[path.decode()] = (mode, object_id)
    changed = []
    for name, (mode, object_id) in sorted(tree.items()):
        path = root / name
        require(path.exists() or path.is_symlink(), 'tracked file removed: ' + name)
        blob = str(path.readlink()).encode() if path.is_symlink() else path.read_bytes()
        current_id = hashlib.sha1(b'blob ' + str(len(blob)).encode() + b'\0' + blob).hexdigest()
        if current_id != object_id:
            require(name in allowed, 'unexpected tracked file changed: ' + name)
            changed.append(name)
    current = set(git(root, 'ls-files', '-z').decode().split('\0')) - {''}
    added = sorted(current - tree.keys())
    for name in added:
        require(name in new_files or any(name.startswith(prefix) for prefix in new_prefixes),
                'unexpected newly tracked file: ' + name)
    return {'base': base, 'current_head': git(root, 'rev-parse', 'HEAD').decode().strip(),
            'baseline_tracked_files': len(tree), 'allowed_changed_files': changed,
            'unchanged_tracked_files': len(tree) - len(changed), 'new_tracked_deliverables': added,
            'untracked_files': 'not treated as tracked scientific inputs'}


def check_upstream(root):
    old = base_blob(root, UPSTREAM_BASE, UPSTREAM_CODE)
    require(old.count(GUARD_ANCHOR) == 1, 'upstream guard anchor ambiguous')
    require((root / UPSTREAM_CODE).read_bytes() == old.replace(GUARD_ANCHOR, GUARD_ANCHOR + GUARD),
            'upstream production change is not exactly the reviewed one-line guard')
    paths = upstream_paths()
    reports = []
    for name, allowed in paths.items():
        current, receipt = check_json(root, UPSTREAM_BASE, name, allowed)
        reports.append(receipt)
        if name.endswith('/mapping_error.json'):
            for record in current['maps']:
                require(record['code_sha256'] == sha((root / UPSTREAM_CODE).read_bytes()), 'map code digest mismatch')
                require(record['spec_sha256'] == digest({k:v for k,v in record.items() if k != 'spec_sha256'}), 'map specification digest mismatch')
        else:
            require(current['comparison']['prediction_sha256'] == digest(current['prediction']), 'temporal comparison prediction digest mismatch')
            require(current['evaluation_only_mutation']['prediction_sha256'] == digest(current['prediction']), 'temporal evaluation prediction digest mismatch')
    inventory = tracked_conservation(root, UPSTREAM_BASE,
        set(paths) | {UPSTREAM_CODE, 'tests/test_m3_mapping_error.py'})
    return {'inventory': inventory, 'reports': reports, 'production_change': 'exactly_reviewed_one_line_guard'}


def check_matter(root, upstream):
    paths = {
        SURVIVAL + 'model_contract.json': {('source_bindings', 6, 'sha256')},
        SURVIVAL + 'prediction.json': {('contract_sha256',)} |
            {('runs', variant, 'contract_sha256') for variant in VARIANTS} |
            {('isotope_candidates', index, 'finite_run_sha256') for index in range(11)},
        SURVIVAL + 'comparison.json': {('prediction_sha256',)},
        SURVIVAL + 'survival_report.json': {('prediction_sha256',), ('comparison_sha256',)},
    }
    reports, values = [], {}
    for name, allowed in paths.items():
        values[name], receipt = check_json(root, MATTER_BASE, name, allowed)
        reports.append(receipt)
    require((root / VENDOR_CODE).read_bytes() == (upstream / UPSTREAM_CODE).read_bytes(), 'vendor is not exact repaired upstream')
    contract, prediction, comparison = (values[SURVIVAL + name] for name in ('model_contract.json', 'prediction.json', 'comparison.json'))
    report = values[SURVIVAL + 'survival_report.json']
    require(contract['source_bindings'][6]['path'] == VENDOR_CODE, 'source index no longer identifies mapping module')
    require(contract['source_bindings'][6]['sha256'] == sha((root / VENDOR_CODE).read_bytes()), 'contract source digest mismatch')
    require(prediction['contract_sha256'] == digest(contract, True), 'prediction contract digest mismatch')
    for variant in VARIANTS:
        require(prediction['runs'][variant]['contract_sha256'] == digest(contract, True), 'run contract digest mismatch')
    for candidate in prediction['isotope_candidates']:
        require(candidate['finite_run_sha256'] == digest(prediction['runs']['baseline'], True), 'candidate run digest mismatch')
    require(comparison['prediction_sha256'] == digest(prediction, True), 'comparison prediction digest mismatch')
    require(report['prediction_sha256'] == digest(prediction, True), 'report prediction digest mismatch')
    require(report['comparison_sha256'] == digest(comparison, True), 'report comparison digest mismatch')
    binding_name = 'manual2/vendor/aod_m3/binding.json'
    binding, receipt = check_json(root, MATTER_BASE, binding_name,
        {('files', 'aod_mapping_error.py', 'sha256'), ('upstream_head',), ('upstream_tree',)}, False)
    reports.append(receipt)
    require(binding['upstream_head'] == git(upstream, 'rev-parse', 'HEAD').decode().strip(), 'vendor upstream head mismatch')
    require(binding['upstream_tree'] == git(upstream, 'rev-parse', 'HEAD^{tree}').decode().strip(), 'vendor upstream tree mismatch')
    require(binding['files']['aod_mapping_error.py']['sha256'] == sha((root / VENDOR_CODE).read_bytes()), 'vendor source hash mismatch')
    foundation = json.loads((root / 'manual2/evidence/foundation-source.json').read_bytes())
    require(foundation['upstream_head'] == UPSTREAM_BASE, 'Main foundation was rebound unnecessarily')
    for name, expected in foundation['files'].items():
        require(sha((root / name).read_bytes()) == expected, 'Main source changed: ' + name)
        require((root / name).read_bytes() == (upstream / name).read_bytes(), 'current upstream Main differs: ' + name)
    publication_name = 'manual2/evidence/publication-build.json'
    publication_paths = {('manual_inputs', path) for path in paths} | {
        ('published_artifacts', path) for path in ('main.pdf', 'manual2.pdf', 'manual2/main.pdf')}
    publication, receipt = check_json(root, MATTER_BASE, publication_name, publication_paths)
    reports.append(receipt)
    for name in paths:
        require(publication['manual_inputs'][name] == sha((root / name).read_bytes()), 'publication input receipt stale: ' + name)
    for name, expected in publication['published_artifacts'].items():
        require(sha((root / name).read_bytes()) == expected, 'publication PDF receipt stale: ' + name)
    dependency_name = '.agents/dependencies.json'
    dependency, receipt = check_json(root, MATTER_BASE, dependency_name, {('scientific_dependency', 'scope')}, False)
    reports.append(receipt)
    allowed = set(paths) | {binding_name, VENDOR_CODE, publication_name, dependency_name,
        'README.md', 'docs/ai-dependencies.md', 'manual2/vendor/aod_m3/README.md',
        'manual2/scripts/matter1_m3.py', 'scripts/check_matter1_m3_consumer.py',
        'manual2/tests/test_matter1_m3.py', '.github/workflows/matter1.yml',
        'scripts/record_matter1_acceptance.py', 'scripts/record_matter1_isotope_acceptance.py',
        'main.pdf', 'manual2.pdf', 'manual2/main.pdf'}
    inventory = tracked_conservation(root, MATTER_BASE, allowed,
        new_prefixes=('manual2/evidence/f1-checks/',),
        new_files=('manual2/evidence/f1-repair.md', 'manual2/tests/test_matter1_m3_evidence.py'))
    return {'inventory': inventory, 'reports': reports,
            'foundation_and_all_other_tracked_science': 'byte_preserved',
            'survival_values_types_statuses_full_histories_and_comparisons': 'unchanged',
            'foundation_head': UPSTREAM_BASE, 'executable_head': binding['upstream_head']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--matter', type=Path)
    args = parser.parse_args()
    try:
        result = {'status': 'PASS_F1_CONSERVATION', 'upstream': check_upstream(args.upstream.resolve()),
                  'scope': 'Pinned-source byte conservation and exact JSON leaf comparison; separate runtime and publication checks establish execution.'}
        if args.matter:
            result['matter'] = check_matter(args.matter.resolve(), args.upstream.resolve())
        print(json.dumps(result, indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({'status': 'FAIL_F1_CONSERVATION', 'error': str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
