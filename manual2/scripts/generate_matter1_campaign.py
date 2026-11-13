"""Explicit all-element campaign generation, optionally resumable case shards."""
import argparse
import json
from pathlib import Path
from matter1_campaign import ROOT, default_manifest, select_shard, generate

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--output-root',type=Path)
    parser.add_argument('--case',action='append',dest='case_ids',help='Exact configuration ID, e.g. Z001-A001; repeat for multiple shards')
    parser.add_argument('--shard',type=int,help='Zero-based balanced shard index')
    parser.add_argument('--shards',type=int,help='Total shard count')
    parser.add_argument('--finalize',action='store_true',help='Assemble existing shards; does not certify their fresh replay')
    args=parser.parse_args()
    if (args.shard is None)!=(args.shards is None): parser.error('--shard and --shards must be supplied together')
    if args.shard is not None and (args.case_ids is not None or args.finalize): parser.error('Shard generation cannot be combined with --case or --finalize')
    try:
        selected=args.case_ids if args.shard is None else select_shard(default_manifest(args.root),args.shard,args.shards)
        print(json.dumps(generate(args.root,args.output_root,selected,args.finalize),sort_keys=True))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        parser.exit(1,f'Campaign generation failed: {exc}\n')
