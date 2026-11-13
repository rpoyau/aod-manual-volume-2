#!/usr/bin/env python3
"""Emit a target-independent atomic attempt and explicit countermodel proof."""
import argparse
from pathlib import Path
from matter1_atomic import canonical, predict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, help='Explicit output file; default is stdout.')
    args = parser.parse_args()
    try:
        blob = canonical(predict(args.root))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(blob)
        else:
            print(blob.decode(), end='')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'atomic prediction attempt failed: {exc}\n')


if __name__ == '__main__':
    main()
