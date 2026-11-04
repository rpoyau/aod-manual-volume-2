#!/usr/bin/env python3
"""Explicit generation of the constructed-to-retention binding assessment."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_retention_adapter import DATA, generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-root', type=Path)
    args = parser.parse_args()
    try:
        products = generate(args.root)
        destination = (args.output_root or args.root)/DATA
        destination.mkdir(parents=True, exist_ok=True)
        for name, value in products.items():
            (destination/name).write_bytes(value)
        print('Generated retention adapter assessment; no combined loss model or physical prediction.')
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f'retention adapter generation failed: {exc}\n')


if __name__ == '__main__':
    main()
