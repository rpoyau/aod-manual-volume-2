#!/usr/bin/env python3
"""Read-only source and generated-isotope verification; never repairs files."""
import argparse,json,sys
from pathlib import Path
from matter1_isotopes import ValidationError,verify

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--check-data',action='store_true',help='Explicit read-only data verification (also the default).')
    args=parser.parse_args()
    try: result=verify(args.root)
    except (ValidationError,KeyError,TypeError) as exc:print(f'isotope verification failed: {exc}',file=sys.stderr);return 1
    print(json.dumps(result,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
