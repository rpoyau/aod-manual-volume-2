"""Pinned M3 metrology exports, loaded against isolated temporal dependencies."""
import hashlib
import json
from pathlib import Path
import sys

import matter1_m3 as dependency

ROOT = Path(__file__).resolve().parents[2]
VENDOR = Path('manual2/vendor/aod_m3_metrology')
BINDING_SHA256 = '992a70a89bc3158b629fe9d7db5a5a909504e43b0a6eacb79f6af151e9c9d44b'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_vendor(root=ROOT):
    root = Path(root)
    path = root/VENDOR/'binding.json'
    if sha(path) != BINDING_SHA256:
        raise ValueError('M3 metrology vendor binding changed')
    binding = json.loads(path.read_text())
    current = dependency.verify_vendor(root)
    if any(binding[k] != current[k] for k in ('upstream_head', 'upstream_tree')):
        raise ValueError('M3 temporal and metrology producer pins differ')
    for name, item in binding['files'].items():
        if sha(root/VENDOR/name) != item['sha256']:
            raise ValueError('M3 metrology vendor source changed: '+name)
    return binding


def validate_api(api, root=ROOT, temporal_api=None):
    """Bind injected actual-upstream APIs as strictly as vendored execution."""
    binding = verify_vendor(root)
    if temporal_api is not None and api.t is not temporal_api:
        raise ValueError('Metrology temporal API identity differs')
    if api.m is not api.t.m:
        raise ValueError('Metrology mapping import substituted')
    for name, module in (('aod_m3_temporal.py', api.t),
                         ('aod_mapping_error.py', api.m),
                         ('aod_native_closure_wave.py', api.t.n)):
        if sha(module.__file__) != binding['dependencies'][name]:
            raise ValueError('Metrology runtime dependency differs: '+name)
    paths = {'current/aod_m3_metrology.py': Path(api.__file__),
             'current/TEMPORAL_METROLOGY.json': api.CONTRACT,
             'current/hydrogen/protocol.json': api.DATA/'hydrogen/protocol.json',
             'current/hydrogen/reported_uncertainty.json': api.DATA/'hydrogen/reported_uncertainty.json',
             'current/cesium/protocol.json': api.DATA/'cesium/protocol.json'}
    for name, path in paths.items():
        if sha(path) != binding['files'][name]['sha256']:
            raise ValueError('Metrology runtime source differs: '+name)
    return api


def metrology(root=ROOT, temporal_api=None):
    verify_vendor(root)
    temporal_api = dependency.temporal(root) if temporal_api is None else temporal_api
    folder = Path(root).resolve()/VENDOR/'current'
    aliases = {'aod_m3_temporal': temporal_api, 'aod_mapping_error': temporal_api.m}
    previous = {name: sys.modules.get(name) for name in aliases}
    tag = hashlib.sha256(str(folder).encode()).hexdigest()[:16]
    try:
        sys.modules.update(aliases)
        api = dependency._load('_matter1_m3_metrology_'+tag, folder/'aod_m3_metrology.py')
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old
    api.CONTRACT = folder/'TEMPORAL_METROLOGY.json'
    api.DATA = folder
    return validate_api(api, root, temporal_api)
