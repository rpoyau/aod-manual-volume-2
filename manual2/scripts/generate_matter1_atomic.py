#!/usr/bin/env python3
"""Explicit generation; finite obstruction outputs are not atomic predictions."""
import argparse
from pathlib import Path
from matter1_atomic import SUBDIR, canonical, generated_products


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-root', type=Path)
    args = parser.parse_args()
    try:
        products = generated_products(args.root)
        destination = (args.output_root or args.root)/SUBDIR
        destination.mkdir(parents=True, exist_ok=True)
        for name, value in products.items():
            (destination/name).write_bytes(canonical(value))
        print(canonical(products['atomic_report.json']).decode(), end='')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'atomic generation failed: {exc}\n')


if __name__ == '__main__':
    main()
