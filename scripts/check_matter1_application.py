#!/usr/bin/env python3
"""Read-only conservation of scientific sources and historical results."""
import argparse
from isotope_preservation import preserved_digest, verify as verify_isotope_preservation
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
    data = (root / 'manual2/contracts/REFERENCE_CONSERVATION.json').read_bytes()
    require(hashlib.sha256(data).hexdigest() == 'b810839e4de5030ede09504528f6ed2c41fa2d5872b2ecdd5f1106f25d8a0a8c', 'Preservation inventory binding changed')
    receipt = json.loads(data)
    require(receipt['schema_version'] == 2, 'Unsupported conservation schema')
    preservation = receipt['preservation_sha256']
    for name, expected in preservation.items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts, 'Nonportable preservation locator')
        require(preserved_digest(root, name) == expected, 'Preservation changed: ' + name)
    audit = verify_ledger(root / 'manual2')
    require(audit['named_element_references'] == 118 and audit['total_reference_slots'] == 126, 'Placement inventory changed')
    with (root / 'manual2/evidence/pr1_baseline_ledger_v1.csv').open(newline='') as handle:
        baseline = list(csv.DictReader(handle))
    count = sum(bool(re.fullmatch(r'-?(?:0|[1-9][0-9]*)', value)) for row in baseline for value in row.values())
    require(count == 3024, 'Baseline numeric comparison inventory changed')
    checks = audit['executed_checks']
    require(checks['v94_placement_field_comparisons'] == 708 and checks['r24_declaration_joins'] == 118, 'Historical join inventory changed')
    require(set(audit['native_evidence_lanes'].values()) == {'not_executed'}, 'Element-wide native status changed')
    isotope_preservation = verify_isotope_preservation(root)
    return {'status': 'PASS_CONSERVATION', 'historical_source_head': receipt['base_head'],
            'historical_source_tree': receipt['base_tree'], 'preserved_files': len(receipt['preservation_sha256']),
            'elements': 118, 'slots': 126, 'baseline_numeric_comparisons': count,
            'v94_placement_field_comparisons': 708, 'r24_declaration_joins': 118,
            'source_unchanged': False, 'isotope_preservation': isotope_preservation, 'preservation_scope': 'Historical scientific sources retained; active sources, adapters and isotope UI are separately checked successors',
            'scope': 'Byte conservation against the scientific base and existing exact/historical ledger checks; no live remote, native or physical claim.'}


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
