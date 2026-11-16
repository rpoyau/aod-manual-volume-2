#!/usr/bin/env python3
"""Check the frozen pre-campaign data, scientific sources and static chart."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'manual2/evidence/campaign-baseline.json'
BASELINE_SHA256 = '8a9aef94c7294014d7323dcacc140deb922a6f1821610f052c27824c358e72ee'


def verify(root=ROOT):
    root = Path(root)
    raw = (root / BASELINE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_SHA256:
        raise ValueError('Changed campaign preservation baseline')
    baseline = json.loads(raw)
    relocations = baseline.get('relocations', {})
    successors = baseline.get('source_successors', {})
    if not (relocations.keys() <= baseline['files'].keys()
            and successors.keys() <= baseline['files'].keys()):
        raise ValueError('Unbound campaign preservation successor')
    for name, expected in baseline['files'].items():
        path = root / relocations.get(name, name)
        successor = successors.get(name)
        if successor:
            if successor['original_sha256'] != expected:
                raise ValueError('Changed historical scientific identity: ' + name)
            expected = successor['current_sha256']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Changed frozen pre-campaign input: ' + name)
        if successor:
            value = deepcopy(json.loads(path.read_text()))
            pointers = successor['changed_metadata_pointers']
            if (not isinstance(pointers, list)
                    or any(not isinstance(p, str) or not p.startswith('/') for p in pointers)
                    or len(set(pointers)) != len(pointers)):
                raise ValueError('Invalid metadata pointers: ' + name)
            for pointer in pointers:
                if re.search(r'~(?![01])', pointer):
                    raise ValueError('Noncanonical metadata pointer: ' + pointer)
                tokens = [part.replace('~1', '/').replace('~0', '~')
                          for part in pointer.split('/')[1:]]
                parent = value
                for index, token in enumerate(tokens):
                    if isinstance(parent, list):
                        if not re.fullmatch(r'0|[1-9][0-9]*', token) or int(token) >= len(parent):
                            raise ValueError('Invalid metadata index: ' + pointer)
                        key = int(token)
                    elif isinstance(parent, dict) and token in parent:
                        key = token
                    else:
                        raise ValueError('Missing metadata leaf: ' + pointer)
                    child = parent[key]
                    if index == len(tokens) - 1:
                        if not isinstance(child, str) or not re.fullmatch(r'[0-9a-f]{64}', child):
                            raise ValueError('Metadata mask requires an existing SHA-256 leaf: ' + pointer)
                        parent[key] = None
                    else:
                        parent = child
            data = json.dumps(value, sort_keys=True, ensure_ascii=False,
                              separators=(',', ':'), allow_nan=False).encode()
            if hashlib.sha256(data).hexdigest() != successor['scientific_payload_sha256']:
                raise ValueError('Changed scientific successor payload: ' + name)
    return {'status': 'PASS_CAMPAIGN_PRESERVATION', 'baseline_head': baseline['head'],
            'checked_files': len(baseline['files']),
            'byte_preserved_files': len(baseline['files']) - len(successors),
            'source_metadata_successors': len(successors),
            'scope': baseline['scope']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'status': 'FAIL_CAMPAIGN_PRESERVATION', 'error': str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
