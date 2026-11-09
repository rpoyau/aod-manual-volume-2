#!/usr/bin/env python3
"""Required integration with the separately checked-out, exact M3 candidate.

This command does not skip when the upstream checkout is missing. It executes
the upstream temporal adapter against this consumer and tests the feedback
intervention. The imported mathematical dependency is not an admission receipt.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'manual2/scripts'))
from matter1_m3 import verify_vendor, verify_legacy_vendor
import matter1_m3_observation as observation
import matter1_m3_metrology as metrology
from publication_support import verify_foundation

HEAD = '71cbcf7e637ababcde3b2e073fb4ceec4b1681b9'


def upstream_apis(upstream):
    """Load the checked producer without reusing a consumer dependency alias."""
    folder = Path(upstream) / 'manual/scripts'
    tag = hashlib.sha256(str(folder.resolve()).encode()).hexdigest()[:16]
    names = ('aod_native_closure_wave', 'aod_mapping_error',
             'aod_m3_temporal', 'aod_m3_metrology')
    previous = {name: sys.modules.get(name) for name in names}
    loaded = {}
    try:
        for name in names:
            spec = importlib.util.spec_from_file_location('_matter1_upstream_' + tag + '_' + name,
                                                         folder / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            loaded[name] = module
            sys.modules[name] = module
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old
    temporal, companion = loaded['aod_m3_temporal'], loaded['aod_m3_metrology']
    if (temporal.n is not loaded['aod_native_closure_wave']
            or temporal.m is not loaded['aod_mapping_error']
            or companion.t is not temporal or companion.m is not temporal.m):
        raise ValueError('Actual upstream dependency identity substituted')
    return temporal, companion


def verify(root, upstream):
    root, upstream = Path(root).resolve(), Path(upstream).resolve()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(upstream), *args], text=True).strip()
    if git('rev-parse', 'HEAD') != HEAD:
        raise ValueError('M3 consumer integration requires the exact pinned upstream head')
    if git('diff', '--name-only', 'HEAD'):
        raise ValueError('M3 integration upstream has modified tracked files')
    binding = verify_vendor(root)
    metrology_binding = metrology.verify_vendor(root)
    historical = verify_legacy_vendor(root)
    if binding['upstream_head'] != HEAD or git('rev-parse', 'HEAD^{tree}') != binding['upstream_tree']:
        raise ValueError('M3 consumer and executable binding disagree')
    for name, row in binding['files'].items():
        if (upstream / row['upstream_path']).read_bytes() != (root / 'manual2/vendor/aod_m3' / name).read_bytes():
            raise ValueError('M3 vendored file differs from actual upstream: ' + name)
    if (metrology_binding['upstream_head'] != HEAD
            or metrology_binding['upstream_tree'] != binding['upstream_tree']):
        raise ValueError('M3 metrology and executable binding disagree')
    for name, row in metrology_binding['files'].items():
        if (upstream / row['upstream_path']).read_bytes() != (root / 'manual2/vendor/aod_m3_metrology' / name).read_bytes():
            raise ValueError('M3 metrology vendor differs from actual upstream: ' + name)
    foundation = verify_foundation(root)
    for name in foundation['files']:
        if (upstream / name).read_bytes() != (root / name).read_bytes():
            raise ValueError('Main import differs from actual upstream: ' + name)
    module, companion = upstream_apis(upstream)
    result = module.consumer_integration(root)
    current = observation.report(root)
    actual = observation.report(root, temporal_api=module)
    if observation.canonical(current) != observation.canonical(actual):
        raise ValueError('Vendored typed temporal execution differs from actual upstream')
    persisted = observation.verify(root)
    current_metrology = metrology.report(root)
    actual_metrology = metrology.report(root, temporal_api=module, metrology_api=companion)
    if observation.canonical(current_metrology) != observation.canonical(actual_metrology):
        raise ValueError('Vendored metrology report differs from actual upstream')
    persisted_metrology = metrology.verify(root)
    if result['common_prefix_through_cut'] != 39 or not result['feedback_disabled_original_validator_rejected']:
        raise ValueError('M3 feedback/history integration failed')
    cases = result['cases']
    if cases['baseline']['counts'] != {'outer_plus': 6, 'outer_minus': 5} or cases['intervention']['counts'] != {'outer_plus': 2, 'outer_minus': 5}:
        raise ValueError('M3 consumer counts changed')
    if result['atomic_point_prediction']['frequency_hz'] is not None:
        raise ValueError('Integration cannot promote the unresolved atomic point prediction')
    return {'status': 'PASS_REQUIRED_M3_CONSUMER', 'upstream_head': HEAD,
            'upstream_tree': binding['upstream_tree'],
            'api_contract_sha256': binding['files']['current/TEMPORAL_OBSERVATION.json']['sha256'],
            'historical_survival_executor_head': historical['upstream_head'],
            'foundation_upstream_head': foundation['upstream_head'],
            'foundation_source_digest': foundation['source_digest'],
            'scope': 'Exact dependencies, R03 replay, stateful feedback and complete metrology application replay; no isotope admission, physical calibration or empirical agreement',
            'metrology': {'actual_upstream_equals_vendored': True,
                'persisted_verification': persisted_metrology},
            'typed_observation': {**persisted, 'actual_upstream_equals_vendored': True,
                'cases': {name: {'original_input_sha256': item['original_input_sha256'],
                    'counts': item['prediction']['complete_temporal_record']['counts'],
                    'context_sha256': item['prediction']['complete_temporal_record']['observation_context']['input_sha256']}
                    for name, item in actual['cases'].items()}},
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
