"""Strict M3 successor and historical source bindings for frozen v1/v2 records.

An old record retains its original source digest. The archived bytes are selected
only after checking the reviewed current successor, never by accepting an arbitrary
hash or silently rebinding a historic calculation to a newer mathematical source.
"""
from pathlib import Path
import hashlib
import json

ARCHIVE = Path('manual2/evidence/pre-m3-main')
FOUNDATION = Path('manual2/evidence/foundation-source.json')
REBIND = Path('manual2/evidence/m3-source-rebind.json')
FOUNDATION_SHA256 = '7c2117141de36d94f18fd21b178a243c3923495a9f1c494579b21f9e7f9fe921'
REBIND_SHA256 = 'd6387c4c6e24e558a00264d455fdea82906940eb9122378b8a2002492a096513'
HISTORICAL_FOUNDATION_SHA256 = '267ec6f0ae1f785a47e8901021ec3db19f8fbbcb2a8ae0c90f8127e5b8cfe8f1'
ADAPTERS_SHA256 = '77e6692e699ef55bfa4ccf667529896e381636479d8c70504dd2c64e349094aa'


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def binding(root):
    root = Path(root)
    data = (root / FOUNDATION).read_bytes()
    require(digest(data) == FOUNDATION_SHA256, 'Preservation: unreviewed active foundation manifest')
    active = json.loads(data)
    data = (root / REBIND).read_bytes()
    require(digest(data) == REBIND_SHA256, 'Preservation: unreviewed Main successor allowlist')
    migration = json.loads(data)
    data = (root / ARCHIVE / FOUNDATION).read_bytes()
    require(digest(data) == HISTORICAL_FOUNDATION_SHA256, 'Preservation: historical foundation changed')
    historic = json.loads(data)
    expected = dict(historic['files'])
    for row in migration['files']:
        name = row['path']
        require(expected.get(name) == row['before_sha256'], 'Preservation: predecessor not bound')
        expected[name] = row['after_sha256']
        if row['before_sha256'] is not None:
            require(digest((root / ARCHIVE / name).read_bytes()) == row['before_sha256'],
                    'Preservation: archived Main source changed: ' + name)
    require(active['files'] == expected, 'Preservation: active Main is not the reviewed successor')
    return active, historic


def legacy_source_bytes(root, name):
    """Resolve a pre-M3 authority without changing a frozen source receipt."""
    root = Path(root)
    active, historic = binding(root)
    require(name in historic['files'], 'Unknown historical Main authority: ' + name)
    current = (root / name).read_bytes()
    require(digest(current) == active['files'][name], 'Preservation: active Main source changed: ' + name)
    data = (root / ARCHIVE / name).read_bytes() if active['files'][name] != historic['files'][name] else current
    require(digest(data) == historic['files'][name], 'Preservation: historical authority changed: ' + name)
    return data


def legacy_engine_digest(root, name):
    """Return the frozen engine identity after checking its reviewed adapter.

The new adapter manifest separately binds the actual current executor. This
preserves old output receipts, rather than representing an adapter as old code.
"""
    root = Path(root)
    data = (root / 'manual2/evidence/m3-legacy-adapters.json').read_bytes()
    require(digest(data) == ADAPTERS_SHA256, 'Preservation: unreviewed legacy adapter manifest')
    adapters = json.loads(data)['files']
    current = digest((root / name).read_bytes())
    if name not in adapters:
        return current
    row = adapters[name]
    require(current == row['after_sha256'], 'Preservation: current adapter changed: ' + name)
    require(digest((root / ARCHIVE / name).read_bytes()) == row['before_sha256'],
            'Preservation: original adapter changed: ' + name)
    return row['before_sha256']
