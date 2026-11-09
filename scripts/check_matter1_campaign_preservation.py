#!/usr/bin/env python3
"""Check the frozen pre-campaign data, historical skills and static chart."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'manual2/evidence/campaign-baseline.json'
BASELINE_SHA256 = '3bc7013c16c800fe6dc96e2cc6e4857e0184207e89a345afa20a0ff0f0a291fe'


def verify(root=ROOT):
    root = Path(root)
    raw = (root / BASELINE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_SHA256:
        raise ValueError('Changed campaign preservation baseline')
    baseline = json.loads(raw)
    for name, expected in baseline['files'].items():
        path = root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Changed frozen pre-campaign input: ' + name)
    return {'status': 'PASS_CAMPAIGN_PRESERVATION', 'baseline_head': baseline['head'],
            'checked_files': len(baseline['files']),
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
