"""Copy source-history evidence required by a disposable legacy consumer."""
from pathlib import Path
import shutil

def copy_foundation_receipts(source, target):
    source, target = Path(source), Path(target)
    shutil.copytree(source/'manual2/evidence/pre-m3-main', target/'manual2/evidence/pre-m3-main', dirs_exist_ok=True)
    shutil.copytree(source/'manual2/evidence/pre-isotope-ui', target/'manual2/evidence/pre-isotope-ui', dirs_exist_ok=True)
    for name in ('manual2/evidence/isotope-preservation.json', 'manual2/evidence/foundation-source.json', 'manual2/evidence/m3-source-rebind.json', 'manual2/evidence/m3-source-rebind-2026-11-08.json', 'manual2/evidence/m3-source-rebind-2026-11-11.json', 'manual2/evidence/m3-legacy-adapters.json', 'manual2/evidence/constructed-source-rebind-2026-11-09.json', 'manual2/evidence/retention-source-rebind-2026-11-09.json', 'manual2/evidence/property-source-rebind-2026-11-11.json', 'manual2/vendor/aod_m3_producer/binding.json', 'manual2/scripts/matter1_foundation.py', 'manual2/scripts/matter1_m3_producer.py'):
        dest = target/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source/name, dest)
