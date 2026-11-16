#!/usr/bin/env python3
"""Execute target-independent finite survival and identifiability witnesses."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_survival import canonical, predict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        blob = canonical(predict(args.root))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(blob)
        else:
            print(blob.decode(), end='')
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f'survival prediction failed: {exc}\n')


if __name__ == '__main__':
    main()
