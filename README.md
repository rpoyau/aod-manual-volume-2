# Alpha↔Omega Dynamics (AΩD) — Manual Volume II: Matter I (Elements 1–118)

Standalone downstream sector execution package of **Alpha↔Omega Dynamics (AΩD v41.02, DOI: `10.5281/zenodo.23426642`)** and **Axiomatic Fundamentalism Calculus (AFC, DOI: `10.5281/zenodo.17795590`)**.

## Repository Structure (`rpoyau/aod` Paired Layout)

```text
aod-manual-volume-2/
├── main.tex                  # Paired AΩD Main v41.02 root container (for xr-hyper cross-refs)
├── preamble.tex              # Paired Main preamble
├── refs.bib                  # Paired Main bibliography
├── sections/                 # Paired Main §1–§8 sections
├── appendices/               # Paired Main Appendices A–J
├── manual2/                  # Manual Volume II: Matter I (Elements 1–118)
│   ├── main.tex              # Root LaTeX container for Manual Volume II (16 pages)
│   ├── preamble.tex          # Manual Volume II preamble & semantic macros
│   ├── refs.bib              # Quarantined literature bibliography
│   ├── sections/             # Modular General Mechanics Corollary Block sections
│   │   ├── 00_scope.tex
│   │   ├── 01-scope-and-spine.tex
│   │   ├── 02-coord0-enclosures.tex
│   │   ├── 03-fusion-contact-ledger.tex
│   │   ├── 04-audits-and-falsification.tex
│   │   ├── 09_prediction_test_fixture_registry.tex
│   │   └── generated_elements_longtable.tex
│   ├── appendices/           # Simulation fixtures, quarantined comparisons, phase tables
│   │   ├── A_simulation_fixtures_and_context.tex
│   │   ├── B_quarantined_external_comparison.tex
│   │   └── C_coordinate_phase_delta3_fixture.tex
│   ├── figures/              # Generated accessible figures
│   │   └── aod_matter1_wheel_accessible.pdf
│   ├── data/                 # Structured CSV / JSON input data & generated ledgers
│   │   └── m1/
│   │       ├── matter1_elements_1_118_ledger.csv
│   │       ├── matter1_coord0_enclosure_summary.csv
│   │       └── matter1_audit_report.json
│   └── scripts/              # Reproducible exact-integer Python verification & plotting
│       ├── verify_matter1_ledger.py
│       └── generate_matter1_wheel.py
└── .agents/skills/           # Bundled authoring & verification skills
```

## Reproduction & Verification

From inside `manual2/`:

```bash
python3 scripts/verify_matter1_ledger.py
MPLCONFIGDIR=/tmp/mpl-cache python3 scripts/generate_matter1_wheel.py
xelatex -interaction=nonstopmode main.tex
bibtex main
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```
