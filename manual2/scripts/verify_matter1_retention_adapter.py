#!/usr/bin/env python3
"""Read-only replay of the complete construction/retention assessment."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_retention_adapter import canonical, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--artifact-root', type=Path)
    parser.add_argument('--check-data', action='store_true')
    args = parser.parse_args()
    try:
        print(canonical(verify(args.root, args.artifact_root)).decode(), end='')
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f'retention adapter verification failed: {exc}\n')


if __name__ == '__main__':
    main()
