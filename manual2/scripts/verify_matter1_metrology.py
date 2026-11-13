#!/usr/bin/env python3
"""Read-only verification of delivered metrology examples and scope."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_metrology import ValidationError, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--check-data', action='store_true', help='Alias for default read-only check')
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (ValidationError, OSError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
