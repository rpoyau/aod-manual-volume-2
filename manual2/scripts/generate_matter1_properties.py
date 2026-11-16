#!/usr/bin/env python3
"""Explicitly generate the source-bound property inventory."""
import argparse
from pathlib import Path
from matter1_properties import BASE, ROOT, build, canonical

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output-root',type=Path)
    a=p.parse_args();out=(a.output_root or a.root)/BASE
    products=build(a.root);out.mkdir(parents=True,exist_ok=True)
    for name,data in products.items():(out/name).write_bytes(canonical(data))
    print('GENERATED_ELEMENT_PROPERTY_CATALOG')

if __name__=='__main__':main()
