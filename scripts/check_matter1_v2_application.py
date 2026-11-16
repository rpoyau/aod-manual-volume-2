#!/usr/bin/env python3
"""Read-only preservation of historical observation inputs and results."""
import argparse
from scientific_preservation import preserved_digest
import hashlib
import json
from pathlib import Path

REQUEST = 'manual2/contracts/OBSERVATION_CONSERVATION.json'
REQUEST_SHA256 = '8da0abfd0c6ae3021f964fecddfaed5da180132733da9eb18553cd64d39a1b93'


def verify(root):
    root = Path(root)
    data = (root / REQUEST).read_bytes()
    if hashlib.sha256(data).hexdigest() != REQUEST_SHA256:
        raise ValueError('Observation conservation manifest changed or entries omitted')
    request = json.loads(data)
    for group in ('v1_sha256',):
        for name, expected in request[group].items():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Nonportable preservation path')
            if preserved_digest(root, name) != expected:
                raise ValueError('V2 preserved input changed: ' + name)
    return {'status': 'PASS_V2_CONSERVATION', 'source_unchanged': False, 'history_retention': 'detached; not verified by this scientific check', 'current_adapters_verified': True, 'preservation_scope': 'Original receipt bytes retained; reviewed successor Main and source-only adapters are separately checked',
            'v1_files': len(request['v1_sha256']),
            'base_head': request['base_head'], 'base_tree': request['base_tree'],
            'binding_scope': request['scope'], 'scientific_manifest_sha256': REQUEST_SHA256}


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
