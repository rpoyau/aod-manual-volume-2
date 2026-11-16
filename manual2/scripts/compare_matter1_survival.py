#!/usr/bin/env python3
"""Compare a replay-verified conditional survival model with sourced lifetimes."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_survival import DATA, canonical, compare, read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--prediction', type=Path)
    parser.add_argument('--isotope-catalog', type=Path, help='Catalog authenticated against source regeneration.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        prediction = read_json(args.prediction or args.root/DATA/'prediction.json')
        blob = canonical(compare(args.root, prediction, catalog_path=args.isotope_catalog))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(blob)
        else:
            print(blob.decode(), end='')
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f'survival comparison failed: {exc}\n')


if __name__ == '__main__':
    main()
