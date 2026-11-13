#!/usr/bin/env python3
"""Read-only verification of property sources, identities and reductions."""
import argparse
import json
from pathlib import Path
from matter1_properties import ROOT, verify

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    try:print(json.dumps(verify(a.root),sort_keys=True))
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:p.exit(1,'FAIL_ELEMENT_PROPERTY_CATALOG: '+str(exc)+'\n')

if __name__=='__main__':main()
