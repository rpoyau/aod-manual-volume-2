"""Read-only original-input replay of all-element campaign cases and comparisons."""
import argparse
import json
from pathlib import Path
from matter1_campaign import ROOT, default_manifest, select_shard, verify

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--case',action='append',dest='case_ids')
    parser.add_argument('--shard',type=int,help='Zero-based balanced shard index')
    parser.add_argument('--shards',type=int,help='Total shard count')
    parser.add_argument('--products-only',action='store_true',help='Verify aggregate projections and reductions; explicitly does not replay native execution')
    parser.add_argument('--check-data',action='store_true',help='Compatibility flag: verification is always read-only')
    args=parser.parse_args()
    if (args.shard is None)!=(args.shards is None): parser.error('--shard and --shards must be supplied together')
    if args.shard is not None and (args.case_ids is not None or args.products_only): parser.error('Shard replay cannot be combined with --case or --products-only')
    try:
        selected=args.case_ids if args.shard is None else select_shard(default_manifest(args.root),args.shard,args.shards)
        print(json.dumps(verify(args.root,selected,args.products_only),sort_keys=True))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        parser.exit(1,f'Campaign verification failed: {exc}\n')
