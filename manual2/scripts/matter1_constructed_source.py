"""Bind the R02 source-resolution adapter separately from its frozen recipe."""
from pathlib import Path
import hashlib
import json

import matter1_foundation as foundation

APPLICATION = 'manual2/scripts/matter1_constructed_coupling.py'
RECEIPT = Path('manual2/evidence/constructed-source-rebind-2026-11-09.json')
RECEIPT_SHA256 = '9128a4d24e536dea7bc4393a842ab6fac43af6c788a3d2c62a840ddab9671848'
RETENTION_APPLICATION = 'manual2/scripts/matter1_retention_adapter.py'
RETENTION_RECEIPT = Path('manual2/evidence/retention-source-rebind-2026-11-09.json')
RETENTION_RECEIPT_SHA256 = '006cbb6e2c226af436f4ce4b0f38eab7f3995cd0956e60593180cfb1ab95ab38'
UNCHANGED_RECIPES = {
    'manual2/scripts/generate_matter1_constructed_coupling.py',
    'manual2/scripts/verify_matter1_constructed_coupling.py',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError('Constructed adapter: ' + message)


def verify_adapter(root):
    """Verify both actual executor bytes and the archived historical recipe."""
    root = Path(root)
    data = (root / RECEIPT).read_bytes()
    require(digest(data) == RECEIPT_SHA256, 'unreviewed successor receipt')
    record = json.loads(data)
    require(record['path'] == APPLICATION, 'unexpected application')
    foundation.binding(root)
    require(record['historical_foundation_sha256'] == foundation.PRIOR_FOUNDATION_SHA256
            and record['active_foundation_sha256'] == foundation.M3_FOUNDATION_SHA256,
            'foundation chain differs')
    require(digest((root / APPLICATION).read_bytes()) == record['after_sha256'],
            'current executor changed')
    require(digest((root / record['archive']).read_bytes()) == record['before_sha256'],
            'historical recipe changed')
    return record


def historical_recipe_digest(root, name=APPLICATION):
    """Keep frozen recipe fields; the receipt identifies the actual adapter."""
    if name == APPLICATION:
        return verify_adapter(root)['before_sha256']
    if name == RETENTION_APPLICATION:
        return verify_retention_adapter(root)['before_sha256']
    require(name in UNCHANGED_RECIPES, 'unknown recipe')
    return digest((Path(root) / name).read_bytes())


def verify_retention_adapter(root):
    """Bind the retention wrapper's current executor and frozen recipe fields."""
    root = Path(root)
    data = (root / RETENTION_RECEIPT).read_bytes()
    require(digest(data) == RETENTION_RECEIPT_SHA256, 'unreviewed retention successor receipt')
    record = json.loads(data)
    require(record['path'] == RETENTION_APPLICATION, 'unexpected retention application')
    require(record['constructed_adapter_receipt'] == str(RECEIPT)
            and record['constructed_adapter_receipt_sha256'] == RECEIPT_SHA256,
            'constructed successor differs')
    verify_adapter(root)
    require(digest((root / RETENTION_APPLICATION).read_bytes()) == record['after_sha256'],
            'current retention executor changed')
    require(digest((root / record['archive']).read_bytes()) == record['before_sha256'],
            'historical retention recipe changed')
    return record
