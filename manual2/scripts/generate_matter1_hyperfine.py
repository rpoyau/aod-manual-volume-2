#!/usr/bin/env python3
"""Explicitly generate the external retrospective hyperfine inventory report."""
import argparse
import sys
from pathlib import Path
sys.dont_write_bytecode = True
from matter1_hyperfine import OUTPUT, SUBDIR, ValidationError, generated_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2], help='input repository root')
    parser.add_argument('--output-root', type=Path, help='output repository root (default: input root)')
    args = parser.parse_args()
    try:
        output = generated_bytes(args.root)
        target = (args.output_root or args.root) / SUBDIR / OUTPUT
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
    except ValidationError as exc:
        parser.exit(1, f'hyperfine generation failed: {exc}\n')
    print(f'Generated {SUBDIR / OUTPUT}')


if __name__ == '__main__':
    main()
