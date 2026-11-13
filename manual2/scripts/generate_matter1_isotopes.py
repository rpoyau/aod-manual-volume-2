#!/usr/bin/env python3
"""Explicit deterministic isotope catalog and manuscript table generation."""
import argparse,json
from pathlib import Path
from matter1_isotopes import BASE,expected_artifacts,manual_root,require

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-root',type=Path,help='Separate Manual output root; reads only declared source inputs from --root.')
    args=parser.parse_args();root=manual_root(args.root);destination=manual_root(args.output_root) if args.output_root else root
    artifacts=expected_artifacts(root)
    for relative,data in artifacts.items():
        path=destination/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        require(path.read_bytes()==data,'generated output differs')
    print(json.dumps(json.loads(artifacts[str(BASE/'verification.json')]),sort_keys=True))
if __name__=='__main__':main()
