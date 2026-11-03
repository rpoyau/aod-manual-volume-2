#!/usr/bin/env python3
"""Explicit generation of the bound R02 and paired aggregate constructions."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_constructed_coupling import DATA, canonical, default_contract, generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-root', type=Path)
    parser.add_argument('--initialize-contract', action='store_true')
    args = parser.parse_args()
    try:
        if args.initialize_contract:
            (args.root/DATA).mkdir(parents=True, exist_ok=True)
            (args.root/DATA/'model_contract.json').write_bytes(canonical(default_contract(args.root)))
        report = generate(args.root, args.output_root)
        print(canonical({'profile': report['profile'], 'status': 'generated', 'cases': list(report['cases'])}).decode(), end='')
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f'constructed-coupling generation failed: {exc}\n')


if __name__ == '__main__':
    main()
