#!/usr/bin/env python3
"""Read-only verification of the external hyperfine inventory and pending map."""
import argparse
import json
import sys
from pathlib import Path
sys.dont_write_bytecode = True
from matter1_hyperfine import ValidationError, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2], help='repository root')
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except ValidationError as exc:
        parser.exit(1, f'hyperfine verification failed: {exc}\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
