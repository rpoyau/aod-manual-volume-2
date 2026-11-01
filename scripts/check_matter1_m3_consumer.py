#!/usr/bin/env python3
"""Required integration with the separately checked-out, exact M3 candidate.

This command does not skip when the upstream checkout is missing. It executes
the upstream temporal adapter against this consumer and tests the feedback
intervention. The imported mathematical dependency is not an admission receipt.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'manual2/scripts'))
from matter1_m3 import verify_vendor
from publication_support import verify_foundation

HEAD = '3ffb3c9984eef95ca4b105ac323d249f30412816'


def verify(root, upstream):
    root, upstream = Path(root).resolve(), Path(upstream).resolve()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(upstream), *args], text=True).strip()
    if git('rev-parse', 'HEAD') != HEAD:
        raise ValueError('M3 consumer integration requires the exact pinned upstream head')
    if git('diff', '--name-only', 'HEAD'):
        raise ValueError('M3 integration upstream has modified tracked files')
    binding = verify_vendor(root)
    if binding['upstream_head'] != HEAD or git('rev-parse', 'HEAD^{tree}') != binding['upstream_tree']:
        raise ValueError('M3 consumer and executable binding disagree')
    for name, row in binding['files'].items():
        if (upstream / row['upstream_path']).read_bytes() != (root / 'manual2/vendor/aod_m3' / name).read_bytes():
            raise ValueError('M3 vendored file differs from actual upstream: ' + name)
    foundation = verify_foundation(root)
    for name in foundation['files']:
        if (upstream / name).read_bytes() != (root / name).read_bytes():
            raise ValueError('Main import differs from actual upstream: ' + name)
    sys.path.insert(0, str(upstream / 'manual/scripts'))
    spec = importlib.util.spec_from_file_location('matter1_checked_m3_temporal', upstream / 'manual/scripts/aod_m3_temporal.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = module.consumer_integration(root)
    if result['common_prefix_through_cut'] != 39 or not result['feedback_disabled_original_validator_rejected']:
        raise ValueError('M3 feedback/history integration failed')
    cases = result['cases']
    if cases['baseline']['counts'] != {'outer_plus': 6, 'outer_minus': 5} or cases['intervention']['counts'] != {'outer_plus': 2, 'outer_minus': 5}:
        raise ValueError('M3 consumer counts changed')
    if result['atomic_point_prediction']['frequency_hz'] is not None:
        raise ValueError('Integration cannot promote the unresolved atomic point prediction')
    return {'status': 'PASS_REQUIRED_M3_CONSUMER', 'upstream_head': HEAD,
            'foundation_upstream_head': foundation['upstream_head'],
            'foundation_source_digest': foundation['source_digest'],
            'scope': 'Exact dependency and stateful feedback replay; no isotope admission, physical calibration or empirical agreement',
            'executed': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--upstream-root', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root, args.upstream_root), indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'M3 consumer integration failed: {exc}\n')


if __name__ == '__main__':
    main()
