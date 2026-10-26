#!/usr/bin/env python3
"""Explicit generation of synthetic, typed SI observation examples."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_metrology import ValidationError, generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-root', type=Path)
    args = parser.parse_args()
    try:
        result = generate(args.root, args.output_root)
    except (ValidationError, OSError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
