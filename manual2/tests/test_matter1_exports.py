"""Actual hostile export mutations, without modifying delivered artifacts."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_matter1_figure import verify


@unittest.skipUnless(importlib.util.find_spec("pdfplumber"), "PDF export checks require pdfplumber")
class ExportIntegrity(unittest.TestCase):
    def test_actual_exports_and_data_agree(self):
        result = verify(ROOT / "data/m1/matter1_elements_1_118_ledger.csv", ROOT / "figures", ROOT / "visuals")
        self.assertEqual(result["pdf"]["marks_checked"], 126)
        self.assertTrue(result["inputs_unchanged"])

    def test_semantic_corruptions_rejected_even_with_updated_output_hash(self):
        for mutation in ("svg_label", "svg_small_font", "companion_identity", "layout_slot"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                figures, visuals = root / "figures", root / "visuals"
                figures.mkdir(); visuals.mkdir()
                for name in ("aod_matter1_wheel_accessible.pdf", "aod_matter1_wheel_accessible.svg", "matter1_figure_manifest.json"):
                    shutil.copyfile(ROOT / "figures" / name, figures / name)
                for name in ("matter1-reference.html", "matter1-layout.json"):
                    shutil.copyfile(ROOT / "visuals" / name, visuals / name)
                ledger = root / "ledger.csv"
                shutil.copyfile(ROOT / "data/m1/matter1_elements_1_118_ledger.csv", ledger)
                manifest_path = figures / "matter1_figure_manifest.json"
                manifest = json.loads(manifest_path.read_text())
                if mutation == "svg_label":
                    target = figures / "aod_matter1_wheel_accessible.svg"
                    text = target.read_text()
                    self.assertIn(">100 Fm</text>", text)
                    target.write_text(text.replace(">100 Fm</text>", ">100 ZZ</text>"))
                elif mutation == "svg_small_font":
                    target = figures / "aod_matter1_wheel_accessible.svg"
                    text = target.read_text()
                    self.assertIn("font-size: 9.3px", text)
                    target.write_text(text.replace("font-size: 9.3px", "font-size: 8px", 1))
                elif mutation == "companion_identity":
                    target = visuals / "matter1-reference.html"
                    text = target.read_text()
                    self.assertIn('"symbol": "Fm"', text)
                    target.write_text(text.replace('"symbol": "Fm"', '"symbol": "ZZ"'))
                else:
                    target = visuals / "matter1-layout.json"
                    data = json.loads(target.read_text())
                    data["marks"][-1]["seat"] = 21
                    target.write_text(json.dumps(data))
                manifest["files"][target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
                manifest_path.write_text(json.dumps(manifest))
                paths = [x for x in root.rglob("*") if x.is_file()]
                before = {p: p.read_bytes() for p in paths}
                with self.assertRaises(ValueError):
                    verify(ledger, figures, visuals)
                self.assertEqual({p: p.read_bytes() for p in paths}, before)


if __name__ == "__main__":
    unittest.main()
