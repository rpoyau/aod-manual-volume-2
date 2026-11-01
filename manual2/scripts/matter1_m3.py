"""Checked import of the exact M3 map/uncertainty dependency."""
from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[2]
VENDOR = Path('manual2/vendor/aod_m3')
BINDING_SHA256 = 'd0ab973827dc45f4ff6f4f0c13b96357f3843bc4df6bb32fa783642949a42cd6'


def verify_vendor(root=ROOT):
    root = Path(root)
    data = (root / VENDOR / 'binding.json').read_bytes()
    if hashlib.sha256(data).hexdigest() != BINDING_SHA256:
        raise ValueError('M3 vendor binding changed')
    result = json.loads(data)
    for name, source in result['files'].items():
        if hashlib.sha256((root / VENDOR / name).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('M3 vendor source changed: ' + name)
    return result


def mapping(root=ROOT):
    verify_vendor(root)
    path = Path(root) / VENDOR / 'aod_mapping_error.py'
    spec = importlib.util.spec_from_file_location('matter1_exact_aod_m3_mapping', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
