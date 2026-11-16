#!/usr/bin/env python3
"""Explicit generation of a declared survival experiment and separate comparison."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_survival import DATA, canonical, default_contract, generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-root', type=Path)
    parser.add_argument('--isotope-catalog', type=Path, help='Freshly generated catalog, checked against bound source regeneration.')
    parser.add_argument('--initialize-contract', action='store_true', help='Explicitly bind current sources and declared model inputs.')
    args = parser.parse_args()
    try:
        destination = (args.output_root or args.root)/DATA
        destination.mkdir(parents=True, exist_ok=True)
        if args.initialize_contract:
            (args.root/DATA).mkdir(parents=True, exist_ok=True)
            (args.root/DATA/'model_contract.json').write_bytes(canonical(default_contract(args.root)))
        products = generate(args.root, catalog_path=args.isotope_catalog)
        for name,value in products.items():
            (destination/name).write_bytes(canonical(value))
        print(canonical(products['survival_report.json']).decode(), end='')
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f'survival generation failed: {exc}\n')


if __name__ == '__main__':
    main()
