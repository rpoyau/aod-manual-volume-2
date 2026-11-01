"""Preserve old receipt meaning across the reviewed full-M3 migration."""
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'manual2/scripts'))
from matter1_foundation import ARCHIVE, FOUNDATION, binding, legacy_source_bytes

ADAPTERS = Path('manual2/evidence/m3-legacy-adapters.json')
ADAPTERS_SHA256 = '77e6692e699ef55bfa4ccf667529896e381636479d8c70504dd2c64e349094aa'


def preserved_digest(root, name):
    root, name = Path(root), str(name)
    current = (root / name).read_bytes()
    if name == str(FOUNDATION):
        binding(root)
        return hashlib.sha256((root / ARCHIVE / name).read_bytes()).hexdigest()
    if name.startswith(('sections/', 'appendices/')) or name == 'main.tex':
        return hashlib.sha256(legacy_source_bytes(root, name)).hexdigest()
    if name in ('manual2/scripts/matter1_temporal.py', 'manual2/scripts/matter1_atomic.py',
                'manual2/scripts/matter1_metrology.py'):
        data = (root / ADAPTERS).read_bytes()
        if hashlib.sha256(data).hexdigest() != ADAPTERS_SHA256:
            raise ValueError('Preservation: unreviewed legacy adapter manifest')
        row = json.loads(data)['files'][name]
        if hashlib.sha256(current).hexdigest() != row['after_sha256']:
            raise ValueError('Preservation: current adapter changed: ' + name)
        previous = (root / ARCHIVE / name).read_bytes()
        if hashlib.sha256(previous).hexdigest() != row['before_sha256']:
            raise ValueError('Preservation: original adapter changed: ' + name)
        return row['before_sha256']
    return hashlib.sha256(current).hexdigest()
