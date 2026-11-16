#!/usr/bin/env python3
"""Read-only exact replay and source-bound isotope-survival verification."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_survival import canonical, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--check-data', action='store_true', help='Alias for the default non-mutating verifier.')
    args = parser.parse_args()
    try:
        print(canonical(verify(args.root)).decode(), end='')
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f'survival verification failed: {exc}\n')


if __name__ == '__main__':
    main()
