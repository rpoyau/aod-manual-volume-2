#!/usr/bin/env python3
"""Explicitly generate the declared finite folding/temporal model artifacts."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_temporal import ValidationError, generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2],
                        help='Repository root (Manual directory also accepted)')
    parser.add_argument('--output-root', type=Path, help='Write generated outputs to this repository instead')
    args = parser.parse_args()
    try:
        report = generate(args.root, args.output_root)
    except (ValidationError, OSError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
