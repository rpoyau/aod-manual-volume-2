# Alpha↔Omega Dynamics — Manual Volume II: Matter I

A compact elemental reference for Z = 1–118, downstream of released AOD v41.02 and AFC v2.4. The nine nested enclosure surfaces, local roles and seat-order line visualize the declared relations. Eight additional positions are explicitly unfilled reference slots.

This revision preserves the candidate’s element identities, positions, local counts and conditional support values. Its validation profile is **static relational reference**. Scope/Q4 admission, exact native kernels, reversed-edge SADAR pairing, retained-return witnesses and fusion execution remain pending; successful arithmetic and publication checks do not certify those lanes. Reference A values retain their candidate provenance and unresolved original selection policy.

## Read the candidate

- [`manual2.pdf`](manual2.pdf) and [`main.pdf`](main.pdf) are the canonical publication pair; keep them together for external references.
- [`manual2/main.pdf`](manual2/main.pdf) is the same Manual text with a path-correct `../main.pdf` target.
- [`compact chart`](manual2/figures/aod_matter1_wheel_accessible.pdf) and [SVG](manual2/figures/aod_matter1_wheel_accessible.svg) are 180 mm wide, with 9.3 pt essential text.
- [`interactive companion`](manual2/visuals/matter1-reference.html) opens directly in a browser. It uses the same data/layout and supports keyboard selection and narrow screens.

At fixed Z, changing the companion’s integer A preserves placement and changes the support sum by 68ΔA. This is conditional count exploration, not a catalogue of observed isotopes, abundances, stability or decay events.

## Data and authority

`manual2/data/m1/` is canonical. Its version-2 schema separates reference inputs, structural fields, assigned classifications and pending admission/execution. `support_sum` replaces the legacy `rd_fuse` name; `support_declaration` has no certificate semantics. The three existing `manual2/data/` compatibility files must match their canonical counterparts byte for byte.

`manual2/evidence/pr1_baseline_ledger_v1.csv`, `input_manifest.json` and `historical_sources.json` bind the reviewed PR and small historical excerpts. The 118×6 v94 placement comparison is separate from observable coverage and the r24 declaration joins. Predecessor deferred/unscored/not-executed statuses are retained. Whole historical ZIPs are comparison evidence, not runtime dependencies.

`manual2/evidence/foundation-source.json` pins the unchanged Main mathematical sources and released text. The paired build produces an exact source/PDF/AUX/FLS receipt, then resolves semantic Manual citations against that same Main build. A fresh checkout must run this paired build before publication verification; ignored AUX/FLS/binding files are recreated, never accepted merely because their timestamps look current.

## Environment

Release generation and reproduction use **CPython 3.12.14 on Linux x86_64**, matching CI, plus XeLaTeX, latexmk, BibTeX and Node 22 or later. The exact data code uses Python’s standard library and does not need the renderer profile. Install the locked figure/PDF dependency wheels in a clean virtual environment and the browser package:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-matter1.txt
python -B manual2/scripts/matter1_renderer.py
npm install --ignore-scripts --no-audit --no-fund
npx playwright install chromium
```

`requirements-matter1.txt` pins the full transitive dependency closure by version and wheel SHA-256; binary wheels are required. `manual2/evidence/renderer-lock.json` also binds the Python/platform identity, FreeType version, Matplotlib native binaries and bundled regular/bold DejaVu font bytes. Generation rejects a different renderer before writing exports. The figure manifest records this path-independent binding. A matching Matplotlib version alone is insufficient: the system build and PyPI wheel can link different FreeType versions. Rendering resets Matplotlib defaults and selects the bound font files explicitly.

On Debian/Ubuntu, the TeX packages used by CI are `latexmk texlive-xetex texlive-latex-extra texlive-science texlive-fonts-recommended`. CI fixes Ubuntu 24.04, Python and Node versions and records the installed TeX/package versions; distribution TeX patches are not locked. This renderer profile does not claim byte-identical TeX PDFs across distributions. `CHROMIUM_EXECUTABLE` can select an existing Chromium binary. Other platforms may inspect the delivered files or run standard-library data checks; release generation uses the stated Linux profile.

## Verify persisted artifacts before generating

From the repository root:

```sh
python3 -B manual2/scripts/verify_matter1_ledger.py
python3 -B -O manual2/scripts/verify_matter1_ledger.py --check-data
python3 -B manual2/scripts/check_matter1_figure.py
node manual2/scripts/check_matter1_companion.cjs
```

Both ledger-check forms are read-only, reject unknown flags and never repair corrupted inputs. Importing the modules does not generate files. The figure checker inspects the actual PDF/SVG, embedded fonts, every mark and the companion binding; the browser checker exercises the actual standalone page.

## Explicit generation and paired publication

Generate the data/chart and build the publication pair explicitly, then verify:

```sh
python3 -B manual2/scripts/generate_matter1_ledger.py --output-root manual2
MPLCONFIGDIR=/tmp/matter1-mpl python3 -B manual2/scripts/generate_matter1_wheel.py
python3 -B scripts/build_matter1_documents.py
python3 -B scripts/verify_matter1_publication.py
```

The build copies inputs into a fresh temporary directory, builds Main first with `latexmk -xelatex -recorder`, then both Manual variants. It publishes only after source binding, released Main text, semantic PDF destinations, identical Manual text and the final placed chart size pass. `--build-dir PATH` selects a new/empty directory and preserves build logs for inspection. Do not use a standalone Manual compilation as a release check.

To reproduce data and chart outputs without replacing delivered files:

```sh
python3 -B scripts/check_matter1_reproduction.py
```

The reproduction check generates into a disposable directory, compares the exact 15-output inventory, data/table/layout/HTML/SVG bytes and PDF text/vector geometry and colors, and checks that source bytes remain unchanged. Character coordinates remain compared to 0.001 pt; PDF tolerance was not widened to hide renderer drift. `--generator-python PATH` supports a separate interpreter satisfying the same renderer profile.

## Tests and CI scope

After the paired build:

```sh
python3 -B -m unittest discover -s manual2/tests -p 'test_matter1_*.py' -v
python3 -B -O -m unittest discover -s manual2/tests -p 'test_matter1_data.py' -v
```

Tests mutate disposable copies: operand compensation, fixed hinge, unsupported certification/execution, identity/types, mirrors, history joins, inputs, actual exports, renderer binaries/fonts and publication bindings. Browser checks cover all 126 marks, 320/360 px layouts, pointer/keyboard, light/dark modes and invalid A inputs. They measure visible invalid-input text contrast in both themes against a 4.5:1 threshold, and boundary badge text against a scoped 7:1 target. These checks do not certify whole-page WCAG conformance. Tests do not claim native D.E.C. execution or empirical agreement.

`.github/workflows/matter1.yml` runs persisted checks before generation, a paired build, tests and reproduction, and uploads PDFs/logs. A local passing run is not a hosted CI result. The implementation handoff records the actual local commands and inspected pages separately.
