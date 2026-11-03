#!/usr/bin/env python3
"""Explicit deterministic generation of the separately named R03 retention model."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_witnessed_retention import DATA, generate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-root',type=Path)
    args=parser.parse_args()
    try:
        products=generate(args.root)
        destination=(args.output_root or args.root)/DATA
        destination.mkdir(parents=True,exist_ok=True)
        for name,value in products.items():(destination/name).write_bytes(value)
        print('Generated six witnessed-retention products; original R03 cases conserved.')
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        parser.exit(1,f'witnessed retention generation failed: {exc}\n')


if __name__=='__main__':main()
