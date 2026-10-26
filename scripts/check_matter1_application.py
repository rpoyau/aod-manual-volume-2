#!/usr/bin/env python3
"""Read-only conservation and historical request-binding check for this update."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root):
    root = Path(root).resolve()
    sys.path.insert(0, str(root / 'manual2/scripts'))
    from matter1_model import verify as verify_ledger
    receipt = json.loads((root / 'manual2/evidence/fusion-request.json').read_bytes())
    require(receipt['schema_version'] == 1, 'Unsupported receipt schema')
    require(receipt['base_head'] == '34843ea6f40b07c68f61cdc9427ecaa29864c6bc', 'Historical request head changed')
    require(receipt['base_tree'] == 'cb88126f228f070e1f8598bcc1924a9d69811a73', 'Historical request tree changed')
    require(receipt['request_archive_sha256'] == '6d19d3dd8a9d6e88ee6f642359ac29156fb4632dda6d562b5b4cad82e3bcb689', 'Request archive binding changed')
    require(receipt['target_branch'] == 'matter-1-elements-1-118', 'Wrong requested branch')
    require(receipt['intake_remote_binding'] == 'matched_current_PR_head_at_intake', 'Unsupported intake status')
    preservation = receipt['preservation_sha256']
    require(len(preservation) == 85 and hashlib.sha256(json.dumps(preservation, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == 'f24a4ffb2df6d1a9f78eed1431f58f394e088eb07a9411418a5b8ee1e7178302', 'Preservation inventory binding changed')
    require(sum(p.startswith('.agents/skills/') for p in preservation) == 11, 'Skill asset inventory changed')
    for name, expected in preservation.items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts, 'Nonportable preservation locator')
        require(hashlib.sha256((root / path).read_bytes()).hexdigest() == expected, 'Preservation changed: ' + name)
    entries = receipt['tracked_skill_entry_points']
    require(len(entries) == 5 and len(set(entries)) == 5, 'Five distinct tracked skill entry points required')
    require(set(entries) == {f'.agents/skills/{name}/SKILL.md' for name in (
        'axiomatic-fundamentalism', 'aod-ontology-compaction', 'aod-style-and-format',
        'general-mechanics-style', 'paper-formatter-gm')}, 'Wrong skill inventory')
    require(all(name in receipt['preservation_sha256'] for name in entries), 'Unbound skill entry point')
    audit = verify_ledger(root / 'manual2')
    require(audit['named_element_references'] == 118 and audit['total_reference_slots'] == 126, 'Placement inventory changed')
    with (root / 'manual2/evidence/pr1_baseline_ledger_v1.csv').open(newline='') as handle:
        baseline = list(csv.DictReader(handle))
    count = sum(bool(re.fullmatch(r'-?(?:0|[1-9][0-9]*)', value)) for row in baseline for value in row.values())
    require(count == 3024, 'Baseline numeric comparison inventory changed')
    checks = audit['executed_checks']
    require(checks['v94_placement_field_comparisons'] == 708 and checks['r24_declaration_joins'] == 118, 'Historical join inventory changed')
    require(set(audit['native_evidence_lanes'].values()) == {'not_executed'}, 'Element-wide native status changed')
    return {'status': 'PASS_CONSERVATION', 'historical_request_head': receipt['base_head'],
            'historical_request_tree': receipt['base_tree'], 'preserved_files': len(receipt['preservation_sha256']),
            'tracked_skill_entry_points': 5, 'tracked_skill_files': sum(p.startswith('.agents/skills/') for p in receipt['preservation_sha256']),
            'elements': 118, 'slots': 126, 'baseline_numeric_comparisons': count,
            'v94_placement_field_comparisons': 708, 'r24_declaration_joins': 118,
            'source_unchanged': True,
            'scope': 'Byte conservation against the request base and existing exact/historical ledger checks; no live remote, native or physical claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(verify(args.root), indent=2, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        print('FAIL_APPLICATION: ' + str(exc), file=sys.stderr)
        raise SystemExit(1)
