#!/usr/bin/env python3
"""Read-only source and whole-artifact replay of the R03 retention model."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_witnessed_retention import json_bytes, verify


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--check-data',action='store_true',help='Alias for default read-only verification.')
    args=parser.parse_args()
    try:print(json_bytes(verify(args.root)).decode(),end='')
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        parser.exit(1,f'witnessed retention verification failed: {exc}\n')


if __name__=='__main__':main()
