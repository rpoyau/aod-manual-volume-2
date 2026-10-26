"""Release renderer mismatch probes; no delivered outputs are changed."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import shutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import matter1_renderer as renderer
import generate_matter1_wheel as visual
from check_matter1_figure import verify


class RendererBinding(unittest.TestCase):
    def test_current_environment_matches_release_profile(self):
        binding = renderer.verify_renderer()
        self.assertEqual(binding["renderer"]["freetype"], "2.6.1")
        self.assertEqual(binding["lock_sha256"], renderer.sha256(renderer.LOCK_PATH))

    def test_changed_binary_font_or_dependency_is_rejected_before_export(self):
        original = renderer.renderer_identity(json.loads(renderer.LOCK_PATH.read_text())["renderer"]["packages"])
        for category, key in (("fonts_sha256", "normal"), ("fonts_sha256", "bold"),
                              ("native_modules_sha256", "matplotlib.ft2font"),
                              ("native_modules_sha256", "matplotlib.backends._backend_agg"),
                              ("packages", "matplotlib")):
            with self.subTest(category=category, key=key), tempfile.TemporaryDirectory() as directory:
                altered = copy.deepcopy(original)
                altered[category][key] = "changed"
                out = Path(directory)
                sentinel = out / "keep.txt"
                sentinel.write_text("untouched")
                with patch.object(renderer, "renderer_identity", return_value=altered):
                    with self.assertRaisesRegex(ValueError, "Renderer profile mismatch"):
                        visual.generate(ROOT / "data/m1/matter1_elements_1_118_ledger.csv",
                                        out / "figures", out / "visuals", ROOT / "visuals/matter1-reference.template.html")
                self.assertEqual(list(out.iterdir()), [sentinel])
                self.assertEqual(sentinel.read_text(), "untouched")

    def test_changed_freetype_and_python_are_rejected(self):
        original = renderer.renderer_identity(json.loads(renderer.LOCK_PATH.read_text())["renderer"]["packages"])
        with patch.object(renderer, "renderer_identity", return_value={**original, "freetype": "2.14.3"}):
            with self.assertRaisesRegex(ValueError, "renderer.freetype"):
                renderer.verify_renderer()
        with patch.object(renderer, "runtime_identity", return_value={**renderer.runtime_identity(), "python": "3.14.8"}):
            with self.assertRaisesRegex(ValueError, "runtime.python"):
                renderer.verify_renderer()

    def test_actual_font_and_requirements_corruption_are_rejected_without_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            fonts = renderer.font_paths()
            altered = out / "DejaVuSans-Bold.ttf"
            altered.write_bytes(fonts["bold"].read_bytes() + b"CONTROLLED_CORRUPTION")
            before = altered.read_bytes()
            with patch.object(renderer, "font_paths", return_value={**fonts, "bold": altered}):
                with self.assertRaisesRegex(ValueError, "renderer.fonts_sha256.bold"):
                    renderer.verify_renderer()
            self.assertEqual(altered.read_bytes(), before)
            requirements = out / "requirements-matter1.txt"
            requirements.write_bytes((renderer.ROOT / requirements.name).read_bytes() + b"\n# controlled drift\n")
            before = requirements.read_bytes()
            with patch.object(renderer, "ROOT", out):
                with self.assertRaisesRegex(ValueError, "requirements_sha256"):
                    renderer.verify_renderer()
            self.assertEqual(requirements.read_bytes(), before)

    def test_user_matplotlibrc_does_not_change_release_text_metrics(self):
        import matplotlib
        from matplotlib import pyplot as plt
        layout = visual.build_layout(visual.read_rows(ROOT / "data/m1/matter1_elements_1_118_ledger.csv"))
        first, expected, _ = visual.draw_figure(layout)
        self.addCleanup(plt.close, first)
        with matplotlib.rc_context({"font.size": 42, "font.weight": "bold", "text.kerning_factor": 6}):
            second, actual, _ = visual.draw_figure(layout)
            self.addCleanup(plt.close, second)
        self.assertEqual(actual, expected)

    def test_forged_delivered_renderer_binding_is_rejected_without_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            shutil.copytree(ROOT / "figures", out / "figures")
            shutil.copytree(ROOT / "visuals", out / "visuals")
            manifest = out / "figures/matter1_figure_manifest.json"
            value = json.loads(manifest.read_text())
            value["renderer_binding"] = {"profile": "forged label"}
            manifest.write_text(json.dumps(value))
            before = {p: p.read_bytes() for p in out.rglob("*") if p.is_file()}
            with self.assertRaisesRegex(ValueError, "figure renderer binding mismatch"):
                verify(ROOT / "data/m1/matter1_elements_1_118_ledger.csv", out / "figures", out / "visuals")
            self.assertEqual({p: p.read_bytes() for p in before}, before)


if __name__ == "__main__":
    unittest.main()
