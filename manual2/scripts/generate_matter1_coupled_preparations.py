"""Generate the versioned finite coupled-preparation application."""
import argparse
import json
from pathlib import Path
import matter1_coupled_preparations as coupled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=coupled.ROOT)
    parser.add_argument('--output-root', type=Path)
    args = parser.parse_args()
    print(json.dumps(coupled.generate(args.root, args.output_root), indent=2))


if __name__ == '__main__':
    main()
