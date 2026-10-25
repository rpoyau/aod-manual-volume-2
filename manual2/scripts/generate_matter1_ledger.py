#!/usr/bin/env python3
"""Explicitly generate declared reference artifacts; verification is separate."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from matter1_model import ValidationError, build_rows, expected_artifacts, load_contract, verify_rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1],help='read input contract from this Manual directory')
    parser.add_argument('--output-root',type=Path,required=True,help='explicit destination Manual directory')
    args=parser.parse_args()
    try:
        refs,model,baseline=load_contract(args.root)
        rows=build_rows(refs,model)
        verify_rows(rows,rows,baseline)
        outputs=expected_artifacts(args.root,rows)
        for relative,payload in outputs.items():
            target=args.output_root/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(payload)
    except ValidationError as exc:
        parser.exit(1,f'ERROR: {exc}\n')
    print(f'Generated {len(outputs)} reference artifacts into {args.output_root}; native execution remains pending.')


if __name__=='__main__':
    main()
