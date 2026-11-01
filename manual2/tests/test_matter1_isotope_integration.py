"""Cross-layer conservation failures use persisted disposable copies."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import isotope_preservation as preservation

class IsotopeIntegrationTests(unittest.TestCase):
    def test_frozen_data_skills_and_geometry_are_preserved(self):
        report=preservation.verify(ROOT)
        self.assertEqual(report['preserved_files'],70)
        self.assertEqual(report['archived_ui_files'],4)
        self.assertEqual(report['active_ui'],'verified_successor')

    def test_persisted_baseline_and_resealed_inventory_mutations_fail(self):
        doc=preservation.receipt(ROOT)
        for mutation in ('stateful_trace','archived_ui','resealed_inventory'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                names=list(doc['preserved_sha256'])+[str(preservation.RECEIPT)]+[doc['historical_ui_archive']+'/'+n for n in doc['historical_ui_sha256']]
                for name in names:
                    target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
                if mutation=='stateful_trace':
                    target=root/'manual2/data/m1/stateful/baseline_trace.json'
                    target.write_bytes(target.read_bytes()+b' ')
                elif mutation=='archived_ui':
                    target=root/doc['historical_ui_archive']/'manual2/visuals/matter1-reference.html'
                    target.write_bytes(target.read_bytes()+b' ')
                else:
                    target=root/preservation.RECEIPT;value=json.loads(target.read_bytes());value['preserved_sha256'].pop(next(iter(value['preserved_sha256'])));target.write_text(json.dumps(value))
                def snapshot():return{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
                before=snapshot()
                with self.assertRaisesRegex(ValueError,'Preservation'):
                    preservation.verify(root)
                self.assertEqual(snapshot(),before)

    def test_source_and_model_artifacts_are_distinct(self):
        catalog=json.loads((ROOT/'manual2/data/m1/isotopes/catalog.json').read_bytes())
        prediction=json.loads((ROOT/'manual2/data/m1/survival/prediction.json').read_bytes())
        self.assertNotEqual(catalog.get('status'),prediction.get('status'))
        fl=next(r for r in catalog['isotopes'] if r['id']=='Fl-298:ground')
        self.assertEqual(fl['empirical_status'],'unobserved_model_target')
        self.assertIsNone(fl['half_life']['value_seconds'])
        self.assertEqual(fl['support_coordinates']['r_n'],70)

if __name__=='__main__':unittest.main()
