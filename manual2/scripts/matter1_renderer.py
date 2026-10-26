"""Bind release rendering to the selected wheels, native renderer and fonts.

Read-only validation. Importing this module does not import Matplotlib or write
files. Rendering is deliberately scoped to the Linux x86_64 CPython release
profile; exact data arithmetic does not require this environment.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "manual2/evidence/renderer-lock.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_identity():
    return {"implementation": platform.python_implementation(),
            "python": platform.python_version(), "system": platform.system(),
            "machine": platform.machine()}


def font_paths():
    from matplotlib import get_data_path
    folder = Path(get_data_path()) / "fonts/ttf"
    return {"normal": folder / "DejaVuSans.ttf", "bold": folder / "DejaVuSans-Bold.ttf"}


def renderer_identity(packages):
    from matplotlib import ft2font

    binary_modules = ("matplotlib.ft2font", "matplotlib._path", "matplotlib.backends._backend_agg")
    fonts = {weight: sha256(path) for weight, path in font_paths().items()}
    return {
        "packages": {name: importlib.metadata.version(name) for name in packages},
        "freetype": ft2font.__freetype_version__,
        "native_modules_sha256": {name: sha256(importlib.import_module(name).__file__) for name in binary_modules},
        "fonts_sha256": fonts,
    }


def release_binding():
    """Expected manifest binding, readable without loading the renderer."""
    lock = json.loads(LOCK_PATH.read_text())
    if lock["schema"] != "matter1-renderer-lock-v1":
        raise ValueError("Unknown Matter I renderer profile schema")
    return {"profile": lock["profile"], "lock_sha256": sha256(LOCK_PATH),
            "runtime": lock["runtime"], "renderer": lock["renderer"],
            "requirements_sha256": lock["requirements_sha256"]}


def verify_renderer():
    lock = json.loads(LOCK_PATH.read_text())
    if lock["schema"] != "matter1-renderer-lock-v1":
        raise ValueError("Unknown Matter I renderer profile schema")
    mismatch = []

    def compare(expected, actual, prefix):
        for key, value in expected.items():
            field = prefix + key
            if isinstance(value, dict):
                compare(value, actual.get(key, {}), field + ".")
            elif actual.get(key) != value:
                mismatch.append(f"{field}: expected {value!r}, got {actual.get(key)!r}")

    # Fail before loading a different binary ABI or creating any export.
    compare(lock["runtime"], runtime_identity(), "runtime.")
    actual_requirements = sha256(ROOT / "requirements-matter1.txt")
    compare({"requirements_sha256": lock["requirements_sha256"]},
            {"requirements_sha256": actual_requirements}, "")
    if not mismatch:
        try:
            compare(lock["renderer"], renderer_identity(lock["renderer"]["packages"]), "renderer.")
        except (ImportError, importlib.metadata.PackageNotFoundError) as exc:
            mismatch.append(str(exc))
    if mismatch:
        raise ValueError("Renderer profile mismatch: " + "; ".join(mismatch)
                         + ". Use the documented CPython 3.12.14 Linux x86_64 wheel environment; "
                           "install requirements-matter1.txt in a clean virtual environment.")
    # Stable, path-independent binding for the figure manifest and CI receipt.
    return release_binding()


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        print(json.dumps({"status": "PASS_RENDERER", **verify_renderer()}, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print("FAIL_RENDERER: " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
