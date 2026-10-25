#!/usr/bin/env python3
"""Generate the static Matter I reference and its same-data HTML companion.

This renderer reads the canonical v2 ledger. Geometry expresses declared
enclosure membership, role and seat order; it is not a physical trajectory.
Generation is explicit. Importing this module does not read or write files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

WIDTH = 704.0
HEIGHT = 804.0
WIDTH_MM = 180.0
HEIGHT_MM = WIDTH_MM * HEIGHT / WIDTH
FONT_PT = 9.3
MM_PER_INCH = 25.4
POINTS_PER_INCH = 72.0
BASE = 85.0
PITCH = 26.0
CX, CY = 352.0, 350.0
BADGE_WIDTH, BADGE_HEIGHT = 52.0, 24.0
COLORS = {
    "ink": "#182737", "muted": "#536270", "line": "#a4afb9",
    "alpha": "#f8eee0", "omega": "#e7f0f7", "hinge": "#eef0f3",
    "boundary": "#e1e7ed", "slot": "#ffffff", "surface": "#eff4f5",
}
INT_FIELDS = (
    "z", "mass_a", "m_order", "enclosure_l", "seat_s", "a_tritrio",
    "b_tetratrio", "c_dimon", "support_sum", "is_group_boundary",
    "is_named_anchor",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def role(m: int, seat: int) -> str:
    if seat < m:
        return "alpha"
    if seat == m:
        return "hinge"
    if seat < 2 * m:
        return "omega"
    return "boundary"


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        required = {*INT_FIELDS, "symbol", "record_kind", "declaration_id"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: missing v2 fields {sorted(required - set(reader.fieldnames or []))}")
        records = []
        for number, raw in enumerate(reader, 2):
            try:
                row = dict(raw)
                for key in INT_FIELDS:
                    if not raw[key] or raw[key].strip() != raw[key]:
                        raise ValueError(f"invalid {key}")
                    row[key] = int(raw[key])
            except (KeyError, ValueError) as error:
                raise ValueError(f"{path}:{number}: malformed integer: {error}") from error
            records.append(row)
    if [r["z"] for r in records] != list(range(1, 127)):
        raise ValueError(f"{path}: expected ordered unique slots 1 through 126")
    if len({r["declaration_id"] for r in records}) != 126:
        raise ValueError(f"{path}: declaration IDs must be unique")
    for row in records:
        z, m, seat = row["z"], row["m_order"], row["seat_s"]
        if not (3 <= m <= 11 and m * (m - 1) - 6 < z <= m * (m + 1) - 6):
            raise ValueError(f"{path}: Z={z}: incorrect enclosure")
        if seat != z - (m * (m - 1) - 6) or row["enclosure_l"] != 2 * m:
            raise ValueError(f"{path}: Z={z}: incorrect seat or enclosure order")
        if [row[k] for k in ("a_tritrio", "b_tetratrio", "c_dimon")] != [(seat + 1) // 2, seat // 2, seat % 2]:
            raise ValueError(f"{path}: Z={z}: incorrect local tuple")
        expected = 30 * z + 68 * (row["mass_a"] - z) + 1 + 4 * seat
        if row["mass_a"] < z or row["support_sum"] != expected:
            raise ValueError(f"{path}: Z={z}: inconsistent reference count/support sum")
        kind = "element_reference" if z <= 118 else "unfilled_reference_slot"
        if row["record_kind"] != kind:
            raise ValueError(f"{path}: Z={z}: expected {kind}")
        if row["is_group_boundary"] != int(seat == 2 * m) or row["is_named_anchor"] != int(seat == 2 * m and z <= 118):
            raise ValueError(f"{path}: Z={z}: incorrect boundary attribute")
        if z <= 118 and (not row["symbol"].isalpha() or len(row["symbol"]) > 2):
            raise ValueError(f"{path}: Z={z}: malformed element symbol")
    return records


def build_layout(rows: list[dict]) -> dict:
    marks = []
    for row in rows:
        z, m, seat = row["z"], row["m_order"], row["seat_s"]
        theta = math.pi * seat / m
        radius = BASE + PITCH * (m - 3) - PITCH * (1 - seat / (2 * m))
        marks.append({
            "z": z, "symbol": row["symbol"] if z <= 118 else None,
            "record_kind": row["record_kind"], "declaration_id": row["declaration_id"],
            "reference_a": row["mass_a"], "m": m, "enclosure": 2 * m,
            "seat": seat, "local": [row[k] for k in ("a_tritrio", "b_tetratrio", "c_dimon")],
            "support_sum": row["support_sum"], "role": role(m, seat),
            "label": f"{z} {row['symbol']}" if z <= 118 else str(z),
            "x": CX + radius * math.sin(theta), "y": CY - radius * math.cos(theta),
            "width": BADGE_WIDTH, "height": BADGE_HEIGHT,
        })
    return {
        "schema": "matter1-visual-layout-v1", "width": WIDTH, "height": HEIGHT,
        "width_mm": WIDTH_MM, "height_mm": HEIGHT_MM, "font_pt": FONT_PT,
        "coordinate_scope": "display coordinates, not physical radii",
        "guide_relation": "seat_order", "marks": marks,
        "enclosures": [{"m": m, "order": 2 * m, "x": CX, "y": CY,
                        "radius": BASE + PITCH * (m - 3)} for m in range(3, 12)],
    }


def intersects(a: list[float], b: list[float], tolerance: float = 0.05) -> bool:
    return min(a[2], b[2]) > max(a[0], b[0]) + tolerance and min(a[3], b[3]) > max(a[1], b[1]) + tolerance


def validate_geometry(layout: dict, objects: list[dict]) -> dict:
    """Check the actual renderer's text bounds, not estimated character widths."""
    marks = layout["marks"]
    badges = {m["z"]: [m["x"] - m["width"] / 2, m["y"] - m["height"] / 2,
                       m["x"] + m["width"] / 2, m["y"] + m["height"] / 2] for m in marks}
    errors = []
    for index, mark in enumerate(marks):
        for other in marks[index + 1:]:
            if intersects(badges[mark["z"]], badges[other["z"]]):
                errors.append(f"badge overlap {mark['z']}/{other['z']}")
    for obj in objects:
        bounds = obj["bounds"]
        if bounds[0] < 0 or bounds[1] < 0 or bounds[2] > WIDTH or bounds[3] > HEIGHT:
            errors.append(f"clipped text {obj['id']}")
        if obj["font_pt"] < 9.0:
            errors.append(f"undersized text {obj['id']}")
        own = obj.get("z")
        if own is not None:
            badge = badges[own]
            if bounds[0] < badge[0] + 1 or bounds[1] < badge[1] + 1 or bounds[2] > badge[2] - 1 or bounds[3] > badge[3] - 1:
                errors.append(f"badge text overflow {own}")
        for z, badge in badges.items():
            if z != own and intersects(bounds, badge):
                errors.append(f"text {obj['id']} overlaps badge {z}")
    for index, obj in enumerate(objects):
        for other in objects[index + 1:]:
            if intersects(obj["bounds"], other["bounds"]):
                errors.append(f"text collision {obj['id']}/{other['id']}")
    if errors:
        raise ValueError("figure geometry failed: " + "; ".join(errors))
    return {"status": "PASS", "marks_checked": len(marks), "text_objects_checked": len(objects),
            "badge_overlaps": [], "text_collisions": [], "clipping": [], "minimum_font_pt": min(x["font_pt"] for x in objects)}


def draw_figure(layout: dict):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.patches import Circle, FancyBboxPatch
    from matplotlib.lines import Line2D

    matplotlib.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42,
                               "svg.fonttype": "none", "svg.hashsalt": "matter1-static-reference-v1"})
    fig = plt.figure(figsize=(WIDTH_MM / MM_PER_INCH, HEIGHT_MM / MM_PER_INCH), dpi=144, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, WIDTH), ylim=(HEIGHT, 0), aspect="equal")
    ax.axis("off")
    texts = []

    def label(identifier, x, y, value, size=FONT_PT, ha="center", z=None, color=None, weight="normal"):
        artist = ax.text(x, y, value, fontsize=size, ha=ha, va="center", color=color or COLORS["ink"], weight=weight, zorder=8)
        artist.set_gid(identifier)
        texts.append((identifier, artist, z))

    def badge(x, y, w, h, which, empty=False, identifier=None):
        patch = FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=3",
                              linewidth=.55, edgecolor=COLORS["muted"],
                              linestyle=(0, (1.5, 1.5)) if empty else "solid",
                              facecolor=COLORS["slot" if empty else which], zorder=5)
        if identifier:
            patch.set_gid(identifier)
        ax.add_patch(patch)
        left, right, top, bottom = x - w / 2, x + w / 2, y - h / 2, y + h / 2
        if which == "alpha":
            xs, ys = [left, left], [top + 3, bottom - 3]
        elif which == "omega":
            xs, ys = [right, right], [top + 3, bottom - 3]
        elif which == "hinge":
            xs, ys = [left + 3, right - 3], [bottom, bottom]
        else:
            xs, ys = [left + 3, right - 3], [top, top]
        ax.add_line(Line2D(xs, ys, linewidth=1.5, color=COLORS["ink"], solid_capstyle="butt", zorder=6))

    label("title", CX, 23, "AΩD · Matter I — element reference", 13, weight="bold")
    for shell in reversed(layout["enclosures"]):
        ax.add_patch(Circle((CX, CY), shell["radius"], facecolor=COLORS["surface"], edgecolor=COLORS["line"], lw=.4, zorder=0))
    marks = layout["marks"]
    ax.plot([m["x"] for m in marks], [m["y"] for m in marks], color="#758797", alpha=.6, lw=.55, zorder=1)
    ax.plot([CX, CX], [CY - 30, CY - 303], color=COLORS["muted"], lw=.55, zorder=2)
    ax.plot([CX, CX], [CY + 30, CY + 303], color=COLORS["muted"], lw=.55, ls="--", zorder=2)
    ax.add_patch(Circle((CX, CY), 29, facecolor="white", edgecolor=COLORS["muted"], lw=.7, zorder=3))
    label("core", CX, CY, "E₄", 11)
    for shell in layout["enclosures"]:
        order = str(shell["order"]).translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))
        label(f"enclosure-{shell['order']}", CX - 31, CY - shell["radius"] - 8, "C" + order, ha="right")
    for mark in marks:
        z = mark["z"]
        badge(mark["x"], mark["y"], BADGE_WIDTH, BADGE_HEIGHT, mark["role"], z > 118, f"slot-{z}")
        label(f"label-{z}", mark["x"], mark["y"], mark["label"], z=z)
    label("hinge-axis", CX, 669, "Hμ · hinge axis")
    # Samples use exactly the same edge-role function as the element badges.
    for x, which, wording in [(42, "alpha", "Πα role"), (198, "hinge", "Hμ hinge"),
                              (351, "omega", "ΠΩ role"), (506, "boundary", "Boundary seat")]:
        badge(x, 704, 23, 15, which)
        label("legend-" + which, x + 20, 704, wording, ha="left")
    badge(42, 735, 23, 15, "omega", True)
    label("legend-unfilled", 62, 735, "Unfilled reference slot", ha="left")
    ax.plot([351 - 12, 351 + 12], [735, 735], color="#758797", alpha=.6, lw=.55)
    label("legend-order", 371, 735, "Line: seat order", ha="left")
    label("scope-reference", CX, 768, "Reference set: Z = 1–118. Slots 119–126 are unfilled in this reference.")
    label("scope-geometry", CX, 789, "Enclosure and seat relations · shading and spacing are display cues.")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inverse = ax.transData.inverted()
    measured = []
    for identifier, artist, z in texts:
        box = artist.get_window_extent(renderer)
        corners = inverse.transform([[box.x0, box.y0], [box.x1, box.y1]])
        bounds = [float(min(corners[:, 0])), float(min(corners[:, 1])),
                  float(max(corners[:, 0])), float(max(corners[:, 1]))]
        measured.append({"id": identifier, "text": artist.get_text(), "font_pt": artist.get_fontsize(),
                         "bounds": bounds, **({"z": z} if z is not None else {})})
    checks = validate_geometry(layout, measured)
    return fig, measured, checks


def generate(ledger: Path, figure_dir: Path, visual_dir: Path, template: Path) -> dict:
    rows = read_rows(ledger)
    layout = build_layout(rows)
    layout["source_sha256"] = digest(ledger)
    figure, measured, checks = draw_figure(layout)
    figure_dir.mkdir(parents=True, exist_ok=True)
    visual_dir.mkdir(parents=True, exist_ok=True)
    basename = "aod_matter1_wheel_accessible"
    pdf, svg = figure_dir / (basename + ".pdf"), figure_dir / (basename + ".svg")
    figure.savefig(pdf, metadata={"Title": "Matter I — declared enclosure and seat reference", "Author": "Reginald Poyau",
                                 "Subject": "118 element references and eight unfilled reference slots; seat order, not physical trajectories",
                                 "CreationDate": None, "ModDate": None})
    figure.savefig(svg, metadata={"Title": "Matter I — declared enclosure and seat reference", "Date": None})
    from matplotlib import pyplot as plt
    plt.close(figure)
    # The companion and checks receive the same typed records and coordinates.
    serialized = json.dumps(layout, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    (visual_dir / "matter1-layout.json").write_text(serialized, encoding="utf-8")
    html = template.read_text(encoding="utf-8")
    if html.count("__MATTER1_LAYOUT_JSON__") != 1:
        raise ValueError("companion template must contain exactly one data binding")
    html = html.replace("__MATTER1_LAYOUT_JSON__", serialized.replace("</", "<\\/"))
    (visual_dir / "matter1-reference.html").write_text(html, encoding="utf-8")
    manifest = {"schema": "matter1-figure-manifest-v1", "source_sha256": digest(ledger),
                "profile": "static relational reference", "width_mm": WIDTH_MM, "height_mm": HEIGHT_MM,
                "geometry_checks": checks, "measured_text": measured,
                "files": {pdf.name: digest(pdf), svg.name: digest(svg),
                          "matter1-layout.json": digest(visual_dir / "matter1-layout.json"),
                          "matter1-reference.html": digest(visual_dir / "matter1-reference.html")}}
    (figure_dir / "matter1_figure_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=root / "data/m1/matter1_elements_1_118_ledger.csv")
    parser.add_argument("--figure-dir", type=Path, default=root / "figures")
    parser.add_argument("--visual-dir", type=Path, default=root / "visuals")
    parser.add_argument("--template", type=Path, default=root / "visuals/matter1-reference.template.html")
    args = parser.parse_args()
    report = generate(args.ledger, args.figure_dir, args.visual_dir, args.template)
    print(f"Generated 118 element references + 8 unfilled slots; {report['width_mm']} × {report['height_mm']:.3f} mm; geometry PASS")


if __name__ == "__main__":
    main()
