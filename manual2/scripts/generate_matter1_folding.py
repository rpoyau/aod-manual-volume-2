#!/usr/bin/env python3
"""Explicitly generate the declared illustrative event ledger and its report."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_folding import ValidationError, read_json, build_event_ledger, evaluate, canonical_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2], help='Source repository root')
    parser.add_argument('--output-root', type=Path, help='Output repository root; defaults to --root')
    args = parser.parse_args()
    directory = (args.output_root or args.root) / 'manual2/data/m1/folding'
    try:
        fixture = read_json(args.root / 'manual2/data/m1/folding/two_square_fold.json')
        ledger = build_event_ledger(fixture)
        report = evaluate(fixture, ledger)
    except (ValidationError, KeyError, TypeError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in [('event_ledger.json', ledger), ('folding_report.json', report)]:
        (directory / name).write_bytes(canonical_bytes(data))
    print(json.dumps({'generated': ['manual2/data/m1/folding/event_ledger.json',
                                  'manual2/data/m1/folding/folding_report.json'],
                      'scope': report['assertion_scope']}, indent=2))


if __name__ == '__main__':
    main()
