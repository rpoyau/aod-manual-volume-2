"""Explicit UI successor exception; never relabel changed source as unchanged."""
from pathlib import Path
import hashlib
import json
from m3_preservation import preserved_digest as previous_digest
RECEIPT = Path('manual2/evidence/isotope-preservation.json')
RECEIPT_SHA256 = '6ae7bed4df23beb17e322003a48d54ebc0da5a9681c829cf45727985252d7da8'
def receipt(root):
    data=(Path(root)/RECEIPT).read_bytes()
    if hashlib.sha256(data).hexdigest()!=RECEIPT_SHA256:
        raise ValueError('Preservation: isotope receipt changed')
    return json.loads(data)
def preserved_digest(root,name):
    doc=receipt(root)
    if name in doc['historical_ui_sha256']:
        value=hashlib.sha256((Path(root)/doc['historical_ui_archive']/name).read_bytes()).hexdigest()
        if value!=doc['historical_ui_sha256'][name]:
            raise ValueError('Preservation: historical UI changed: '+name)
        return value
    return previous_digest(root,name)
def verify(root):
    root=Path(root);doc=receipt(root)
    for name,expected in doc['preserved_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Preservation: frozen isotope baseline changed: '+name)
    for name in doc['historical_ui_sha256']:preserved_digest(root,name)
    # Active UI is a successor: verify current projection, catalog and executor.
    import sys
    sys.path.insert(0,str(root/'manual2/scripts'))
    from check_matter1_figure import verify as figure
    figure(root/'manual2/data/m1/matter1_elements_1_118_ledger.csv',root/'manual2/figures',root/'manual2/visuals', source_root=root/'manual2')
    return {'status':'PASS','preserved_files':len(doc['preserved_sha256']),'archived_ui_files':len(doc['historical_ui_sha256']),'active_ui':'verified_successor'}
