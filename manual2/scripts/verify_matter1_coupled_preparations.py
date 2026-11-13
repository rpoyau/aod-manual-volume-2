"""Verify coupled products by original-input native replay; never repair them."""
import argparse
import json
from pathlib import Path
import matter1_coupled_preparations as coupled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=coupled.ROOT)
    args = parser.parse_args()
    print(json.dumps(coupled.verify(args.root), indent=2))


if __name__ == '__main__':
    main()
