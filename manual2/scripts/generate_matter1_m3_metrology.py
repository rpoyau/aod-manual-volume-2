"""Explicit generation of Matter I metrology application artifacts."""
import argparse
import json
from pathlib import Path
from matter1_m3_metrology import ROOT, generate

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output-root', type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.root, args.output_root), sort_keys=True))
