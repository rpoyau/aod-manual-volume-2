#!/usr/bin/env python3
"""Read-only verification of the persisted Matter I static-reference contract."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_model import ValidationError, verify


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1],help='Manual directory containing persisted inputs and outputs')
    parser.add_argument('--check-data',action='store_true',help='compatibility alias for the default read-only operation')
    args=parser.parse_args()
    try:
        result=verify(args.root)
    except ValidationError as exc:
        parser.exit(1,f'ERROR: {exc}\n')
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':
    main()
