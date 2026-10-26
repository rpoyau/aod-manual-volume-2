#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import matter1_bipm as model

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-root',type=Path)
    args=parser.parse_args()
    try:
        result=model.generate(args.root,args.output_root)
    except (ValueError,OSError,KeyError,TypeError,StopIteration) as exc:
        parser.exit(1,f'BIPM check failed: {exc}\n')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
