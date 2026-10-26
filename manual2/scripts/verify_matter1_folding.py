#!/usr/bin/env python3
"""Read-only verification of persisted folded-cell and traversal-ledger fixtures."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_folding import ValidationError, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2], help='Repository root')
    parser.add_argument('--check-data', action='store_true', help='Alias for default read-only verification')
    args = parser.parse_args()
    try:
        report = verify(args.root)
    except (ValidationError, KeyError, TypeError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
