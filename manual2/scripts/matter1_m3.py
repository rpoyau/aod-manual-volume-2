"""Exact current M3 exports and separately preserved historical mapping."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
VENDOR = Path('manual2/vendor/aod_m3')
BINDING_SHA256 = '51eb331eb9500f80245053dd55fde632e16a2d4f7e27976193ffa5378a0a0c02'
PRIOR_BINDING_SHA256 = '7e5eb5c6882d1e880fdbe51a74322457a0cbc376b8c8f8290d094db41ef07f7f'
LEGACY_BINDING_SHA256 = '68feb86e99330ee705f9a75161d8495d356d082740f88bf29a70217e4d331bb0'


def verify_vendor(root=ROOT):
    root = Path(root)
    data = (root / VENDOR / 'binding.json').read_bytes()
    if hashlib.sha256(data).hexdigest() != BINDING_SHA256:
        raise ValueError('M3 vendor binding changed')
    result = json.loads(data)
    for name, source in result['files'].items():
        if hashlib.sha256((root / VENDOR / name).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('M3 vendor source changed: ' + name)
    previous = result['previous_binding']
    path = root / previous['path']
    data = path.read_bytes()
    if previous['sha256'] != PRIOR_BINDING_SHA256 or hashlib.sha256(data).hexdigest() != PRIOR_BINDING_SHA256:
        raise ValueError('M3 prior vendor binding changed')
    for name, source in json.loads(data)['files'].items():
        if hashlib.sha256((path.parent / name).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('M3 prior vendor source changed: ' + name)
    return result


def verify_legacy_vendor(root=ROOT):
    root = Path(root)
    data = (root / VENDOR / 'legacy-binding.json').read_bytes()
    if hashlib.sha256(data).hexdigest() != LEGACY_BINDING_SHA256:
        raise ValueError('M3 historical vendor binding changed')
    result = json.loads(data)
    for name, source in result['files'].items():
        if hashlib.sha256((root / VENDOR / name).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('M3 historical vendor source changed: ' + name)
    return result


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def mapping(root=ROOT):
    verify_vendor(root)
    return _load('matter1_exact_aod_m3_mapping', Path(root) / VENDOR / 'current/aod_mapping_error.py')


def legacy_mapping(root=ROOT):
    verify_legacy_vendor(root)
    return _load('matter1_historical_aod_m3_mapping', Path(root) / VENDOR / 'aod_mapping_error.py')


def temporal(root=ROOT):
    """Load exact exports with isolated imports; relocate only the contract path."""
    verify_vendor(root)
    folder = Path(root).resolve() / VENDOR / 'current'
    tag = hashlib.sha256(str(folder).encode()).hexdigest()[:16]
    native = _load('_matter1_m3_native_' + tag, folder / 'aod_native_closure_wave.py')
    maps = _load('_matter1_m3_mapping_' + tag, folder / 'aod_mapping_error.py')
    aliases = {'aod_native_closure_wave': native, 'aod_mapping_error': maps}
    previous = {name: sys.modules.get(name) for name in aliases}
    try:
        sys.modules.update(aliases)
        result = _load('_matter1_m3_temporal_' + tag, folder / 'aod_m3_temporal.py')
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old
    if result.n is not native or result.m is not maps:
        raise ValueError('M3 temporal dependency import substituted')
    result.TEMPORAL_CONTRACT = folder / 'TEMPORAL_OBSERVATION.json'
    result._contract_binding()
    return result
