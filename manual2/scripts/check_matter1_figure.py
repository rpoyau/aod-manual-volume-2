#!/usr/bin/env python3
"""Read-only validation of the actual static PDF/SVG and shared layout.

Requires pdfplumber. It does not regenerate an artifact or repair an input.
JSON results go to stdout, so callers choose where to save a test record.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from generate_matter1_wheel import build_layout, read_rows, intersects
from matter1_renderer import release_binding


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(ledger: Path, figures: Path, visuals: Path) -> dict:
    import pdfplumber
    from pdfminer.pdftypes import resolve1

    pdf_path = figures / "aod_matter1_wheel_accessible.pdf"
    svg_path = figures / "aod_matter1_wheel_accessible.svg"
    manifest_path = figures / "matter1_figure_manifest.json"
    layout_path = visuals / "matter1-layout.json"
    html_path = visuals / "matter1-reference.html"
    paths = [ledger, pdf_path, svg_path, manifest_path, layout_path, html_path]
    original_hashes = {str(p): sha(p) for p in paths}
    rows = read_rows(ledger)
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    expected = build_layout(rows)
    expected["source_sha256"] = sha(ledger)
    need(layout == expected, "layout differs from canonical ledger/projection")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    need(manifest["source_sha256"] == sha(ledger), "figure manifest source hash mismatch")
    need(manifest.get("renderer_binding") == release_binding(), "figure renderer binding mismatch")
    for p in [pdf_path, svg_path, layout_path, html_path]:
        need(manifest["files"].get(p.name) == sha(p), f"artifact hash mismatch: {p.name}")
    match = re.search(r'<script id="matter1-data" type="application/json">(.*?)</script>', html_path.read_text(encoding="utf-8"), re.S)
    need(match is not None and json.loads(match.group(1).replace("<\\/", "</")) == layout, "companion data differs from layout")

    with pdfplumber.open(pdf_path) as pdf:
        need(len(pdf.pages) == 1, "static reference must be a single PDF page")
        page = pdf.pages[0]
        width_mm, height_mm = page.width * 25.4 / 72, page.height * 25.4 / 72
        need(abs(width_mm - 180) < .01 and height_mm <= 210.01, "PDF physical dimensions fail 180 mm / 210 mm contract")
        need(page.chars and min(c["size"] for c in page.chars) >= 9 - .001, "PDF contains scientific text smaller than 9 pt")
        need(all(c["upright"] for c in page.chars), "PDF has rotated labels")
        need(all("DejaVuSans" in c["fontname"] for c in page.chars), "unexpected chart font family")
        for ref in resolve1(page.page_obj.resources.get("Font", {})).values():
            font = resolve1(ref)
            descendants = font.get("DescendantFonts", [ref])
            for descendant in descendants:
                resolved = resolve1(descendant)
                descriptor = resolve1(resolved.get("FontDescriptor", {}))
                need(any(key in descriptor for key in ("FontFile", "FontFile2", "FontFile3")), "PDF font is not embedded")
        words = page.extract_words(keep_blank_chars=True, use_text_flow=True)
        counts = Counter(w["text"] for w in words)
        scale = page.width / layout["width"]
        boxes = {}
        for mark in layout["marks"]:
            need(counts[mark["label"]] == 1, f"PDF label count incorrect: {mark['label']}")
            word = next(w for w in words if w["text"] == mark["label"])
            actual = [word["x0"], word["top"], word["x1"], word["bottom"]]
            badge = [(mark["x"] - mark["width"] / 2) * scale,
                     (mark["y"] - mark["height"] / 2) * scale,
                     (mark["x"] + mark["width"] / 2) * scale,
                     (mark["y"] + mark["height"] / 2) * scale]
            need(actual[0] >= badge[0] and actual[1] >= badge[1] and actual[2] <= badge[2] and actual[3] <= badge[3], f"PDF text leaves badge {mark['z']}")
            boxes[mark["z"]] = badge
        entries = list(boxes.items())
        for i, (z, box) in enumerate(entries):
            need(box[0] >= 0 and box[1] >= 0 and box[2] <= page.width and box[3] <= page.height, f"PDF badge clipped {z}")
            for other_z, other in entries[i + 1:]:
                need(not intersects(box, other), f"PDF projected badge overlap {z}/{other_z}")
        for i, word in enumerate(words):
            bounds = [word["x0"], word["top"], word["x1"], word["bottom"]]
            need(bounds[0] >= 0 and bounds[1] >= 0 and bounds[2] <= page.width and bounds[3] <= page.height, f"PDF text clipping {word['text']}")
            for mark in layout["marks"]:
                if word["text"] != mark["label"]:
                    need(not intersects(bounds, boxes[mark["z"]]), f"PDF text overlaps other badge: {word['text']} / {mark['z']}")
            for other in words[i + 1:]:
                other_bounds = [other["x0"], other["top"], other["x1"], other["bottom"]]
                need(not intersects(bounds, other_bounds, .1), f"PDF text collision: {word['text']} / {other['text']}")
        text = page.extract_text()
        for required in ["Line: seat order", "Unfilled reference slot", "Slots 119–126 are unfilled", "Boundary seat"]:
            need(required in text, f"PDF missing scope/key: {required}")
        pdf_result = {"width_mm": width_mm, "height_mm": height_mm,
                      "minimum_font_pt": min(c["size"] for c in page.chars),
                      "fonts_embedded": True, "upright_text": True, "marks_checked": len(boxes), "text_runs_checked": len(words)}

    tree = ET.parse(svg_path)
    ns = {"s": "http://www.w3.org/2000/svg"}
    element = tree.getroot()
    width_pt = float(element.attrib["width"].removesuffix("pt"))
    need(abs(width_pt * 25.4 / 72 - 180) < .01, "SVG width is not 180 mm")
    view_width = float(element.attrib["viewBox"].split()[2])
    svg_sizes = []
    for text in element.findall(".//s:text", ns):
        size = re.search(r"font-size:\s*([0-9.]+)px", text.attrib.get("style", ""))
        need(size is not None, "SVG text has no explicit resolved font size")
        actual_pt = float(size.group(1)) * width_pt / view_width
        need(actual_pt >= 9 - .001, "SVG contains scientific text smaller than 9 pt")
        svg_sizes.append(actual_pt)
    for mark in layout["marks"]:
        group = element.find(f".//s:g[@id='label-{mark['z']}']", ns)
        need(group is not None, f"missing SVG label group {mark['z']}")
        need("".join(group.itertext()).strip() == mark["label"], f"incorrect SVG label {mark['z']}")
        need(element.find(f".//s:g[@id='slot-{mark['z']}']", ns) is not None, f"missing SVG mark {mark['z']}")
    need({str(p): sha(p) for p in paths} == original_hashes, "verification changed input bytes")
    return {"status": "PASS", "scope": "static figure/data/export only; not native execution or empirical agreement",
            "source_sha256": sha(ledger), "pdf": pdf_result, "svg_mark_labels": 126,
            "svg_minimum_font_pt": min(svg_sizes),
            "companion_data_binding": "equal", "inputs_unchanged": True}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=root / "data/m1/matter1_elements_1_118_ledger.csv")
    parser.add_argument("--figure-dir", type=Path, default=root / "figures")
    parser.add_argument("--visual-dir", type=Path, default=root / "visuals")
    args = parser.parse_args()
    print(json.dumps(verify(args.ledger, args.figure_dir, args.visual_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
