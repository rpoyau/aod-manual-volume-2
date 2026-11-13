#!/usr/bin/env python3
"""Read-only check of persisted atomic attempt, diagnostic and benchmark."""
import argparse
from pathlib import Path
from matter1_atomic import canonical, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--check-data', action='store_true', help='Compatibility alias; verification is always read-only.')
    args = parser.parse_args()
    try:
        print(canonical(verify(args.root)).decode(), end='')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'atomic verification failed: {exc}\n')


if __name__ == '__main__':
    main()
