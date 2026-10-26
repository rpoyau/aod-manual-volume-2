#!/usr/bin/env python3
"""Read-only preservation of v1 and the available R02 request binding."""
import argparse
import hashlib
import json
from pathlib import Path

REQUEST = 'manual2/evidence/v2-request.json'
REQUEST_SHA256 = '06875ab87820e8118c0edbee8323dee68f1ad428a57e58297c111b441320aac4'


def verify(root):
    root = Path(root)
    data = (root / REQUEST).read_bytes()
    if hashlib.sha256(data).hexdigest() != REQUEST_SHA256:
        raise ValueError('V2 request manifest changed or entries omitted')
    request = json.loads(data)
    for group in ('v1_sha256', 'request_sha256'):
        for name, expected in request[group].items():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Nonportable preservation path')
            if hashlib.sha256((root / path).read_bytes()).hexdigest() != expected:
                raise ValueError('V2 preserved input changed: ' + name)
    return {'status': 'PASS_V2_CONSERVATION', 'source_unchanged': True,
            'v1_files': len(request['v1_sha256']), 'request_files': len(request['request_sha256']),
            'base_head': request['base_head'], 'base_tree': request['base_tree'],
            'available_archive': request['available_archive'],
            'mentioned_latest_archive': request['mentioned_latest_archive'],
            'binding_scope': request['binding_scope'], 'request_sha256': REQUEST_SHA256}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root), indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f'v2 conservation failed: {exc}\n')


if __name__ == '__main__':
    main()
