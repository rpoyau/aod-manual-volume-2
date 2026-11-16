#!/usr/bin/env python3
"""Score an already emitted attempt; unselected residuals remain diagnostic."""
import argparse
from pathlib import Path
from matter1_atomic import SUBDIR, canonical, compare, read_json, validate_prediction


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--prediction', type=Path)
    parser.add_argument('--target', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        prediction = read_json(args.prediction or args.root/SUBDIR/'prediction.json')
        validate_prediction(args.root, prediction)
        target = read_json(args.target or args.root/SUBDIR/'evaluation_target.json')
        blob = canonical(compare(prediction, target))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(blob)
        else:
            print(blob.decode(), end='')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'atomic comparison failed: {exc}\n')


if __name__ == '__main__':
    main()
