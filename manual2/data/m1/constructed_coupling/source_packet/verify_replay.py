"""Compare two complete executions without regenerating or repairing either."""
import argparse
import hashlib
import json
from pathlib import Path

import constructed_coupling as c


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('normal',type=Path)
    parser.add_argument('optimized',type=Path)
    args=parser.parse_args()
    c.check_sources()
    def hashes(root):
        return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(root.rglob('*')) if p.is_file()}
    normal,optimized=hashes(args.normal),hashes(args.optimized)
    c.require(bool(normal),'No normal execution artifacts')
    c.require(normal==optimized,'Normal/optimized artifact bytes differ')
    for case in json.loads((c.HERE/'contract.json').read_text())['cases']:
        record=json.loads((args.normal/case/'prediction.json').read_text())
        claimed=record.pop('prediction_sha256')
        c.require(c.digest(record)==claimed,'Prediction digest changed')
        c.require(record['implementation_sha256']==c.IMPLEMENTATION_SHA256,'Wrong execution code')
        for name,expected in record['file_sha256'].items():
            c.require(normal[case+'/'+name]==expected,'Prediction contains a stale file binding')
    print(json.dumps({'passed':True,'identical_files':len(normal),
                      'normal_optimized_byte_equality':True,'source_bindings_verified':True,
                      'implementation_sha256':c.IMPLEMENTATION_SHA256,
                      'file_sha256':normal},indent=2,sort_keys=True))


if __name__=='__main__':main()
