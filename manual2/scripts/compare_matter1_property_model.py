#!/usr/bin/env python3
"""Replay prediction before opening targets, then write a separate comparison."""
import argparse
import json
import sys
from pathlib import Path
import matter1_property_model as model

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=model.ROOT)
    parser.add_argument('--prediction-root',type=Path)
    parser.add_argument('--target',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    products=model.verify_predictions(args.root,lambda s:print(s,file=sys.stderr,flush=True),args.prediction_root)
    target=args.target or args.root/'manual2/data/m1/properties/catalog.json'
    result=model.compare_catalog(args.root,products['prediction.json'],products['protocol.json'],model.read_json(target))
    output=args.output or (args.prediction_root or args.root)/model.DATA/'comparison.json'
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(model.canonical(result))
    print(json.dumps({'status':'separate_retrospective_property_diagnostic_written','output':str(output),
                     'whole_law_disposition':result['whole_law_disposition']},indent=2))
