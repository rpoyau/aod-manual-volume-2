#!/usr/bin/env python3
"""
Generates figures/aod_matter1_wheel_accessible.pdf
Concentric Coord-0 Enclosure Wheel for Matter I: Elements 1-118 (AOD v41.02)
Okabe-Ito Colorblind-Safe + WCAG AAA Contrast + Redundant Glyph/Stroke Encoding
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.transforms import Affine2D
import numpy as np

ELEMENTS = [
    "", "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
    "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
    "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd",
    "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb",
    "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th",
    "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm",
    "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds",
    "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"
]

# Exoshedding / Yro unstable route elements (Tc=43, Pm=61, Po=84..Og=118)
SHEDDING_Z = {43, 61} | set(range(84, 119))
# Deficit / Open-Seat high-affinity acceptors (Halogens / Chalcogens / H)
ACCEPTOR_Z = {1, 8, 9, 16, 17, 34, 35, 52, 53}
# Coord-0 cumulative boundaries: Gamma_m = m(m+1) - 6 for m = 3..11
GAMMA_M = {m * (m + 1) - 6 for m in range(3, 12)}


def build_concentric_wheel(out_path: str = "figures/aod_matter1_wheel_accessible.pdf") -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10.2, 11.2), dpi=300)
    ax.set_xlim(-12.6, 12.6)
    ax.set_ylim(-13.6, 12.6)
    ax.set_aspect("equal")
    ax.axis("off")

    # Hemisphere background guides: Right = Alpha outbound (Pi_alpha), Left = Omega return (Pi_Omega)
    wedge_alpha = patches.Wedge((0, 0), 11.45, -90, 90, facecolor="#F8FAFC", edgecolor="none", zorder=0)
    wedge_omega = patches.Wedge((0, 0), 11.45, 90, 270, facecolor="#F1F5F9", edgecolor="none", zorder=0)
    ax.add_patch(wedge_alpha)
    ax.add_patch(wedge_omega)

    # 12 o'clock Filled Enclosure Spine & 6 o'clock Hinge Axis
    ax.plot([0, 0], [1.2, 11.65], color="#003366", lw=1.8, ls="-", zorder=1)
    ax.plot([0, 0], [-11.65, -1.2], color="#334155", lw=1.4, ls="--", zorder=1)
    ax.text(
        0, 11.9,
        r"12 o'clock Filled Enclosure Spine ($\Gamma_m = m(m+1)-6$, $m:m:0::2m$) [◆]",
        ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="#003366"
    )
    ax.text(
        0, -11.95,
        r"6 o'clock Structural Hinge Axis ($H_\mu$ Turnaround: $\Pi_\alpha \to \Pi_\Omega$)",
        ha="center", va="top", fontsize=8.8, fontweight="bold", color="#1E293B"
    )
    ax.text(6.2, 11.3, r"$\Pi_\alpha$ Outbound ($\chi_\mu = +1$)",
            ha="center", va="center", fontsize=8.0, fontweight="bold", color="#004D80")
    ax.text(-6.2, 11.3, r"$\Pi_\Omega$ Return ($\chi_\mu = -1$)",
            ha="center", va="center", fontsize=8.0, fontweight="bold", color="#334155")

    # Core E4 Tetron Anchor
    core = patches.Circle((0, 0), 1.18, facecolor="#000000", edgecolor="#E69F00", lw=2.4, zorder=4)
    ax.add_patch(core)
    ax.text(0, 0, "$E_4$\nTetron\n$0\\vdash$", ha="center", va="center",
            color="#FFFFFF", fontsize=8.2, fontweight="bold", zorder=5)

    # Concentric C_{2m} Rings (m = 3..11 -> C_6..C_22)
    z_prev = 0
    for idx, m in enumerate(range(3, 12)):
        seats = 2 * m
        gamma = m * (m + 1) - 6
        r = 2.02 + idx * 1.02

        ring = patches.Circle((0, 0), r, fill=False, edgecolor="#94A3B8", lw=1.0, zorder=2)
        ax.add_patch(ring)

        ax.text(-0.42, r + 0.34, f"$C_{{{seats}}}$", fontsize=7.0, fontweight="bold",
                color="#1E293B", ha="right", va="center")

        for s in range(1, seats + 1):
            z = z_prev + s
            theta_deg = 90.0 - (s / seats) * 360.0
            theta_rad = np.deg2rad(theta_deg)
            x, y = r * np.cos(theta_rad), r * np.sin(theta_rad)

            if z > 118:
                # [1] Unretained Open Cutoff (Z > 118 on C_22): hollow dotted slot
                fc, ec, tc, ls, lw = "#F8FAFC", "#64748B", "#475569", ":", 1.1
                label = f"{z}\n--"
            elif z in GAMMA_M:
                # [2] Filled Shared Enclosure Anchor (Z = Gamma_m): Deep Navy + Gold border + ◆
                fc, ec, tc, ls, lw = "#003366", "#E69F00", "#FFFFFF", "-", 2.0
                suffix = "↑" if z in SHEDDING_Z else ""
                label = f"{z}◆\n{ELEMENTS[z]}{suffix}"
            elif z in SHEDDING_Z:
                # [3] Exoshedding / Yro Route (X_shedding > 0): Vermilion-Orange + Dashed + ↑
                fc, ec, tc, ls, lw = "#FFF0E0", "#D55E00", "#000000", "--", 1.35
                label = f"{z}↑\n{ELEMENTS[z]}"
            elif z in ACCEPTOR_Z:
                # [4] Deficit / Open-Seat Acceptor (S_{n+1} < 0, E_2^0): Sky Cyan + Dash-dot + ∘
                fc, ec, tc, ls, lw = "#D5F0FF", "#004D80", "#000000", "-.", 1.3
                label = f"{z}∘\n{ELEMENTS[z]}"
            else:
                # [5] Seated Retained Closure (X_shedding = 0): Crisp White + Okabe Blue solid
                fc, ec, tc, ls, lw = "#FFFFFF", "#0072B2", "#000000", "-", 1.25
                label = f"{z}\n{ELEMENTS[z]}"

            w, h = 0.80, 0.54
            pill = patches.FancyBboxPatch(
                (-w / 2, -h / 2), w, h,
                boxstyle="round,pad=0.04,rounding_size=0.16",
                facecolor=fc, edgecolor=ec, linewidth=lw, linestyle=ls, zorder=4
            )

            rot_angle = theta_deg - 90.0
            if np.sin(theta_rad) < -0.01:
                rot_angle += 180.0
            t = Affine2D().rotate_deg(rot_angle).translate(x, y) + ax.transData
            ax.add_patch(pill)
            pill.set_transform(t)

            ax.text(x, y, label, ha="center", va="center", fontsize=5.8,
                    fontweight="bold", color=tc, rotation=rot_angle, zorder=5)

        z_prev = gamma

    legend_items = [
        patches.Patch(facecolor="#003366", edgecolor="#E69F00", lw=2.0, ls="-",
                      label=r"[◆] Filled Enclosure Anchor ($Z=\Gamma_m$, Navy / Solid Gold)"),
        patches.Patch(facecolor="#FFFFFF", edgecolor="#0072B2", lw=1.3, ls="-",
                      label=r"Seated Closure ($S_{n+1}=0, X_{\mathrm{shedding}}=0$, White / Solid Blue)"),
        patches.Patch(facecolor="#D5F0FF", edgecolor="#004D80", lw=1.3, ls="-.",
                      label=r"[∘] Open-Seat Acceptor ($S_{n+1}<0, E_2^0$, Cyan / Dash-Dot)"),
        patches.Patch(facecolor="#FFF0E0", edgecolor="#D55E00", lw=1.4, ls="--",
                      label=r"[↑] Exoshedding / Yro Route ($X_{\mathrm{shedding}}>0$, Vermilion / Dashed)"),
        patches.Patch(facecolor="none", edgecolor="#64748B", lw=1.1, ls=":",
                      label=r"[--] Unretained Open Cutoff ($Z=119\dots 126$ on $C_{22}$, Dotted Hollow)")
    ]
    ax.legend(handles=legend_items, loc="lower center", bbox_to_anchor=(0.5, -0.04),
              ncol=2, frameon=True, fontsize=7.6, edgecolor="#334155")

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    build_concentric_wheel()
