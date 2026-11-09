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
SUCCESSOR = Path('manual2/evidence/m3-source-rebind-2026-11-08.json')
PRIOR_ARCHIVE = ARCHIVE / 'rebind-2026-11-08'
FOUNDATION_SHA256 = '3741e275bfdba1566321058c71eb7c9ed9eacaf8edafcd3bd6b87157c8b082e1'
REBIND_SHA256 = 'd6387c4c6e24e558a00264d455fdea82906940eb9122378b8a2002492a096513'
SUCCESSOR_SHA256 = '64f032fe6885d4cd6de870b1808c4700b352be7187fe6655bd3fac49571606b6'
PRIOR_FOUNDATION_SHA256 = '7c2117141de36d94f18fd21b178a243c3923495a9f1c494579b21f9e7f9fe921'
HISTORICAL_FOUNDATION_SHA256 = '267ec6f0ae1f785a47e8901021ec3db19f8fbbcb2a8ae0c90f8127e5b8cfe8f1'
ADAPTERS_SHA256 = '77e6692e699ef55bfa4ccf667529896e381636479d8c70504dd2c64e349094aa'


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _record(root, path, expected_sha256, message):
    data = (root / path).read_bytes()
    require(digest(data) == expected_sha256, 'Preservation: ' + message)
    return json.loads(data)


def _successor_files(root, previous, migration, archive):
    expected = dict(previous['files'])
    for row in migration['files']:
        name = row['path']
        require(expected.get(name) == row['before_sha256'], 'Preservation: predecessor not bound')
        expected[name] = row['after_sha256']
        if row['before_sha256'] is not None:
            require(digest((root / archive / name).read_bytes()) == row['before_sha256'],
                    'Preservation: archived Main source changed: ' + name)
    return expected


def binding(root):
    root = Path(root)
    active = _record(root, FOUNDATION, FOUNDATION_SHA256, 'unreviewed active foundation manifest')
    migration = _record(root, REBIND, REBIND_SHA256, 'unreviewed Main successor allowlist')
    historic = _record(root, ARCHIVE / FOUNDATION, HISTORICAL_FOUNDATION_SHA256,
                       'historical foundation changed')
    prior = _record(root, PRIOR_ARCHIVE / FOUNDATION, PRIOR_FOUNDATION_SHA256,
                    'previous foundation changed')
    require(prior['files'] == _successor_files(root, historic, migration, ARCHIVE),
            'Preservation: previous Main is not the reviewed successor')
    successor = _record(root, SUCCESSOR, SUCCESSOR_SHA256, 'unreviewed current Main successor allowlist')
    require(successor['previous_foundation_sha256'] == PRIOR_FOUNDATION_SHA256
            and successor['previous_rebind'] == str(REBIND)
            and successor['previous_rebind_sha256'] == REBIND_SHA256
            and successor['archive'] == str(PRIOR_ARCHIVE),
            'Preservation: successor chain not bound')
    require(successor['previous_upstream_head'] == prior['upstream_head']
            and successor['previous_upstream_tree'] == prior['upstream_tree']
            and successor['upstream_head'] == active['upstream_head']
            and successor['upstream_tree'] == active['upstream_tree']
            and active['reviewed_rebind'] == str(SUCCESSOR)
            and active['reviewed_rebind_sha256'] == SUCCESSOR_SHA256,
            'Preservation: successor authority mismatch')
    expected = _successor_files(root, prior, successor, PRIOR_ARCHIVE)
    require(active['files'] == expected, 'Preservation: active Main is not the reviewed successor')
    return active, historic


def legacy_source_bytes(root, name):
    """Resolve a pre-M3 authority without changing a frozen source receipt."""
    root = Path(root)
    active, historic = binding(root)
    require(name in historic['files'], 'Unknown historical Main authority: ' + name)
    current = (root / name).read_bytes()
    require(digest(current) == active['files'][name], 'Preservation: active Main source changed: ' + name)
    data = current
    if active['files'][name] != historic['files'][name]:
        original = root / ARCHIVE / name
        data = (original if original.is_file() else root / PRIOR_ARCHIVE / name).read_bytes()
    require(digest(data) == historic['files'][name], 'Preservation: historical authority changed: ' + name)
    return data


def prior_m3_source_bytes(root, name):
    """Resolve the prior M3 authority retained by the frozen survival contract."""
    root = Path(root)
    active, _ = binding(root)
    prior = _record(root, PRIOR_ARCHIVE / FOUNDATION, PRIOR_FOUNDATION_SHA256,
                    'previous foundation changed')
    require(name in prior['files'], 'Unknown prior M3 Main authority: ' + name)
    current = (root / name).read_bytes()
    require(digest(current) == active['files'][name], 'Preservation: active Main source changed: ' + name)
    data = ((root / PRIOR_ARCHIVE / name).read_bytes()
            if active['files'][name] != prior['files'][name] else current)
    require(digest(data) == prior['files'][name], 'Preservation: prior M3 authority changed: ' + name)
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
