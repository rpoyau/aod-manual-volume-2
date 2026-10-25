"""Focused static-reference tests; all mutation copies are disposable."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("figure_generator", ROOT / "scripts/generate_matter1_wheel.py")
visual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visual)
LEDGER = ROOT / "data/m1/matter1_elements_1_118_ledger.csv"


class FigureContract(unittest.TestCase):
    def setUp(self):
        self.rows = visual.read_rows(LEDGER)
        self.layout = visual.build_layout(self.rows)

    def test_named_identities_and_unfilled_slots_are_separate(self):
        self.assertEqual([m["z"] for m in self.layout["marks"] if m["record_kind"] == "element_reference"], list(range(1, 119)))
        self.assertEqual([m["z"] for m in self.layout["marks"] if m["record_kind"] == "unfilled_reference_slot"], list(range(119, 127)))
        self.assertTrue(all(m["symbol"] is None for m in self.layout["marks"][118:]))

    def test_boundary_examples_and_local_roles(self):
        expected = {3: (3, 3, "hinge"), 6: (3, 6, "boundary"), 8: (4, 2, "alpha"),
                    118: (11, 14, "omega"), 126: (11, 22, "boundary")}
        for z, triplet in expected.items():
            mark = self.layout["marks"][z - 1]
            self.assertEqual((mark["m"], mark["seat"], mark["role"]), triplet)

    def test_all126_geometry_with_real_text_metrics(self):
        from matplotlib import pyplot as plt
        figure, measured, report = visual.draw_figure(self.layout)
        self.addCleanup(plt.close, figure)
        self.assertEqual(report["marks_checked"], 126)
        self.assertGreaterEqual(report["minimum_font_pt"], 9)
        self.assertLessEqual(visual.HEIGHT_MM, 210)
        self.assertEqual(visual.WIDTH_MM, 180)
        self.assertEqual(len([x for x in measured if "z" in x]), 126)

    def test_geometry_rejects_overlap_including_unfilled_slots(self):
        from matplotlib import pyplot as plt
        figure, measured, _ = visual.draw_figure(self.layout)
        self.addCleanup(plt.close, figure)
        bad = copy.deepcopy(self.layout)
        bad["marks"][125]["x"] = bad["marks"][124]["x"]
        bad["marks"][125]["y"] = bad["marks"][124]["y"]
        with self.assertRaisesRegex(ValueError, "badge overlap 125/126"):
            visual.validate_geometry(bad, measured)

    def test_geometry_rejects_vertical_text_overflow(self):
        from matplotlib import pyplot as plt
        figure, measured, _ = visual.draw_figure(self.layout)
        self.addCleanup(plt.close, figure)
        bad = copy.deepcopy(measured)
        target = next(x for x in bad if x.get("z") == 126)
        target["bounds"][3] += 20
        with self.assertRaisesRegex(ValueError, "badge text overflow 126"):
            visual.validate_geometry(self.layout, bad)

    def test_malformed_persisted_rows_rejected_without_repair(self):
        original = LEDGER.read_bytes()
        mutations = {
            "missing_slot": lambda rows: rows.pop(),
            "duplicate_slot": lambda rows: rows.append(dict(rows[-1])),
            "wrong_seat": lambda rows: rows[7].update(seat_s="3"),
            "unsupported_slot_kind": lambda rows: rows[-1].update(record_kind="element_reference"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                with LEDGER.open(newline="", encoding="utf-8") as source:
                    raw = list(csv.DictReader(source))
                mutate(raw)
                path = Path(temp) / "corrupt.csv"
                with path.open("w", newline="", encoding="utf-8") as output:
                    writer = csv.DictWriter(output, fieldnames=raw[0].keys())
                    writer.writeheader(); writer.writerows(raw)
                before = path.read_bytes()
                with self.assertRaises(ValueError):
                    visual.read_rows(path)
                self.assertEqual(path.read_bytes(), before)
        self.assertEqual(LEDGER.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
