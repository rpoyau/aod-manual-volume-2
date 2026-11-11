#!/usr/bin/env python3
"""Generate target-free pilot model diagnostics; comparison is a separate command."""
import argparse
import json
import sys
from pathlib import Path
import matter1_property_model as model

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=model.ROOT)
    parser.add_argument('--output-root',type=Path)
    args=parser.parse_args()
    print(json.dumps(model.generate_predictions(args.root,args.output_root,lambda s:print(s,file=sys.stderr,flush=True)),indent=2))
