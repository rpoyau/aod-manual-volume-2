#!/usr/bin/env python3
"""Read-only original-input pilot replay and optional separate target comparison."""
import argparse
import json
import sys
from pathlib import Path
import matter1_property_model as model

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=model.ROOT)
    parser.add_argument('--prediction-root',type=Path)
    parser.add_argument('--prediction-only',action='store_true')
    args=parser.parse_args()
    products=model.verify_predictions(args.root,lambda s:print(s,file=sys.stderr,flush=True),args.prediction_root)
    if not args.prediction_only:
        target=model.read_json(args.root/'manual2/data/m1/properties/catalog.json')
        result=model.compare_catalog(args.root,products['prediction.json'],products['protocol.json'],target)
        path=(args.prediction_root or args.root)/model.DATA/'comparison.json'
        model.require(path.read_bytes()==model.canonical(result),'Stored comparison differs; verifier does not repair')
    print(json.dumps({'status':'PASS_PROPERTY_MODEL_ORIGINAL_INPUT_REPLAY',
        'native_pilots':6,'comparison_checked':not args.prediction_only,
        'physical_prediction_complete':False,'whole_law_disposition':'incomplete_missing_premises'},indent=2))
