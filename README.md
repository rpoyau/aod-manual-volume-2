# Alpha↔Omega Dynamics — Manual Volume II: Matter I

A compact elemental reference for Z = 1–118, downstream of the reviewed AOD M3 Main candidate `b78b48d` (PR43, canonical marker v41.02) and AFC v2.4. The consumed M3 executable has its own [exact vendor binding](manual2/vendor/aod_m3/binding.json), including the F1 evidence-value validation repair. The nine nested enclosure surfaces, local roles and seat-order line visualize the declared relations. Eight additional positions are explicitly unfilled reference slots.

This revision preserves the candidate’s element identities, positions, local counts and conditional support values. The element ledger retains its **static relational reference** profile: element-wide admission and native execution remain pending. A separately scoped finite folding application now executes declared traversal, retained-return, mapped-fold, recurrence, causal-response and retention predicates. Its finite witnesses do not establish complete AOD motif admission or an atomic prediction. Reference A values retain their candidate provenance and unresolved original selection policy.

## Read the candidate

- [`manual2.pdf`](manual2.pdf) and [`main.pdf`](main.pdf) are the canonical publication pair; keep them together for external references.
- [`manual2/main.pdf`](manual2/main.pdf) is the same Manual text with a path-correct `../main.pdf` target.
- [`compact chart`](manual2/figures/aod_matter1_wheel_accessible.pdf) and [SVG](manual2/figures/aod_matter1_wheel_accessible.svg) are 180 mm wide, with 9.3 pt essential text.
- [`interactive companion`](manual2/visuals/matter1-reference.html) opens directly in a browser. It uses the same data/layout and supports keyboard selection and narrow screens.

At fixed Z, changing the companion’s integer A preserves placement and changes the support sum by 68ΔA. This is conditional count exploration. The separate sourced isotope selector and optional half-life color layer use the versioned catalog; changing the arithmetic input does not change that selection.

## Data and authority

AI-assisted work follows [`AGENTS.md`](AGENTS.md) and the pinned four portable
skills from [`rpoyau/aod-skills`](https://github.com/rpoyau/aod-skills). The
scientific dependency is separately pinned to [`rpoyau/aod`](https://github.com/rpoyau/aod).
See [dependency setup and scope](docs/ai-dependencies.md). The five original
`.agents/skills/` snapshots remain unchanged as historical review inputs.

`manual2/data/m1/` is canonical. Its version-2 schema separates reference inputs, structural fields, assigned classifications and pending admission/execution. `support_sum` replaces the legacy `rd_fuse` name; `support_declaration` has no certificate semantics. The three existing `manual2/data/` compatibility files must match their canonical counterparts byte for byte.

`manual2/evidence/pr1_baseline_ledger_v1.csv`, `input_manifest.json` and `historical_sources.json` bind the reviewed PR and small historical excerpts. The 118×6 v94 placement comparison is separate from observable coverage and the r24 declaration joins. Predecessor deferred/unscored/not-executed statuses are retained. Whole historical ZIPs are comparison evidence, not runtime dependencies.

`manual2/evidence/foundation-source.json` pins the exact reviewed M3 Main mathematical sources and text; the prior release sources and executors are archived under `pre-m3-main/`. The paired build produces an exact source/PDF/AUX/FLS receipt, then resolves semantic Manual citations against that same Main build. A fresh checkout must run this paired build before publication verification; ignored AUX/FLS/binding files are recreated, never accepted merely because their timestamps look current.

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
python3 -B scripts/check_matter1_application.py
python3 -B scripts/check_matter1_v2_application.py
for lane in folding temporal hyperfine stateful metrology bipm atomic bipm_precision isotopes survival; do
  python3 -B "manual2/scripts/verify_matter1_${lane}.py"
  python3 -B -O "manual2/scripts/verify_matter1_${lane}.py"
done
node manual2/scripts/check_matter1_companion.cjs
```

Both ledger-check forms are read-only, reject unknown flags and never repair corrupted inputs. Importing the modules does not generate files. The figure checker inspects the actual PDF/SVG, embedded fonts, every mark and the companion binding; the browser checker exercises the actual standalone page.

## Explicit generation and paired publication

Generate the data/chart and build the publication pair explicitly, then verify:

```sh
python3 -B manual2/scripts/generate_matter1_ledger.py --output-root manual2
python3 -B manual2/scripts/generate_matter1_isotopes.py
MPLCONFIGDIR=/tmp/matter1-mpl python3 -B manual2/scripts/generate_matter1_wheel.py
for lane in folding temporal hyperfine stateful metrology bipm atomic; do
  python3 -B "manual2/scripts/generate_matter1_${lane}.py"
done
python3 -B manual2/scripts/generate_matter1_bipm_precision.py
python3 -B manual2/scripts/generate_matter1_survival.py
python3 -B scripts/build_matter1_documents.py
python3 -B scripts/verify_matter1_publication.py
```

The build copies inputs into a fresh temporary directory, builds Main first with `latexmk -xelatex -recorder`, then both Manual variants. It publishes only after source binding, released Main text, semantic PDF destinations, identical Manual text and the final placed chart size pass. `--build-dir PATH` selects a new/empty directory and preserves build logs for inspection. Do not use a standalone Manual compilation as a release check.

To reproduce data and chart outputs without replacing delivered files:

```sh
python3 -B scripts/check_matter1_reproduction.py
```

The reproduction check generates into a disposable directory, compares the exact 33-output inventory, data/table/layout/HTML/SVG/application JSON bytes and PDF text/vector geometry and colors, and checks that source bytes remain unchanged. Character coordinates remain compared to 0.001 pt; PDF tolerance was not widened to hide renderer drift. `--generator-python PATH` supports a separate interpreter satisfying the same renderer profile.

## Tests and CI scope

After the paired build:

```sh
python3 -B -m unittest discover -s manual2/tests -p 'test_matter1_*.py' -v
python3 -B -O -m unittest discover -s manual2/tests -p 'test_matter1_data.py' -v
for lane in folding temporal hyperfine stateful metrology bipm atomic application v2_application; do
  python3 -B -O -m unittest discover -s manual2/tests -p "test_matter1_${lane}.py" -v
done
```

Tests mutate disposable copies: operand compensation, fixed hinge, unsupported certification/execution, identity/types, mirrors, history joins, inputs, actual exports, renderer binaries/fonts and publication bindings. Browser checks cover all 126 marks, 320/360 px layouts, pointer/keyboard, light/dark modes and invalid A inputs. They measure visible invalid-input text contrast in both themes against a 4.5:1 threshold, and boundary badge text against a scoped 7:1 target. These checks do not certify whole-page WCAG conformance. The additional suites exercise persisted coordinate-alias, event replay, wrong-map, hinge, causal-order, atomic-identity, target-exposure and status mutations without rewriting inputs. These establish the stated finite model and software guards; complete native motif admission and empirical agreement remain pending.

`.github/workflows/matter1.yml` runs persisted checks before generation, a paired build, tests and reproduction, and uploads PDFs/logs. A local passing run is not a hosted CI result. The implementation handoff records the actual local commands and inspected pages separately.

## Folding and hyperfine application

The folding and hyperfine sections follow one branch–hinge–return construction through folding, distinct retained returns, two-lineage comparison and a declared causal response. The injective two-square Q4 example has three traversals in each leg: `x = 3n`, `2x = 6n` for n repetitions of that pattern. Its traversal count is separate from hinge support, a closure phase, a recurrence interval and physical time. Inner-to-outer maps retain distinct scopes, identities and histories.

`manual2/data/m1/folding/` stores the illustrative ledger and a declared finite recurrence model. The deterministic edge rule, optional dwell, phase bias, reflection-count map and capacity schedule are declared inputs. The resulting exact cadence, lag, directional duration, causal SADAR response and exposure records are checked against those inputs. No stochastic kernel or physical atomic period is inferred from geometry.

`manual2/data/m1/hyperfine/` stores two isotopes, four hyperfine states, two transitions and five primary sources. The historical hydrogen uncertainty is **0.002 Hz**, visually bound to printed page 200 of Hellwig et al. The hydrogen target was previously exposed, so the known pilot is retrospective. The quoted H/Cs ratio is external reference arithmetic; predicted ratio and empirical score remain null. A physical observation map still requires isotope-specific P2 construction and P3 coupling/recurrence in addition to the P4a source inventory. A later model freeze does not establish independent prediction.

The new generators accept `--root SOURCE_REPO --output-root OUTPUT_REPO`; they write only owned generated outputs. Verification always reads persisted inputs and outputs. `manual2/evidence/fusion-request.json` binds the execution request, unchanged skills, foundation, static inputs and chart. The 39-ID acceptance records distinguish actual finite assertions and guard results from unresolved native and physical dependencies.

The committed `manual2/evidence/fusion-acceptance-results.json` records the 39 scoped results and hashes the supporting logs in `manual2/evidence/fusion-checks/`. After rerunning the commands into a checks directory, use `python3 -B scripts/record_matter1_acceptance.py --checks-dir CHECKS --output RESULT.json` to record a new receipt. This recorder validates complete successful logs and current source/test/model bindings; it does not execute tests or independently attest plain logs. CI records its own receipt from that run.

## Stateful v2 and the Cs/H prediction attempt

The separate `manual2/data/m1/stateful/` model consumes each committed response at the next cut. A controlled capacity change at cut 40 causes retention loss at 41: later affected returns at 47, 54, 61 and 68 disappear, contacts fall from eight to two, and the finite-window reclosure-count ratio changes from 6/5 to 2/5. Earlier history and exposed inner lineages remain intact. The v1 fixture and its outputs are byte-preserved.

The atomic lane executes a target-independent **underdetermination experiment**, a separately bound diagnostic comparison, and a conventional spin-Hamiltonian benchmark. It does **not** deliver an AOD hydrogen frequency prediction. The current finite histories and Cs anchor leave the relative atomic observation gain unconstrained: the explicit one-parameter countermodels give different H reports under the same constraints. No countermodel is selected or fitted. `prediction.json` has a null atomic point prediction; `obligations.json` names the missing atomic construction and observable law. The known hydrogen target remains retrospective. The conventional benchmark imports its zero-field splittings and uses an explicitly approximate spin-only magnetic response; it is not an AOD prediction or a precision spectroscopy calculation.

The metrology lane separates transition period from elapsed interval and implements a declared synthetic cycle map, full covariance propagation, exact positive-semidefinite checks, correlated corrections, inclusion guards, nonlinear and cycle-slip examples. Its connection to the actual v2 histories is labelled synthetic. Cs defines the unit exactly; a realized clock and an atomic observation map require their own uncertainty budgets. Unknown terms remain unknown.

The BIPM lane binds the original numerical source files and checks 153 measurement rows, 1168 listed correlations, a 14×14 output covariance, and all 105 published ratio uncertainties. Rounding intervals include both input and output precision. This is an output-consistency check, not a reproduction of the global adjustment or an atomic prediction.

Run the prediction and comparison separately:

```sh
python3 -B manual2/scripts/predict_matter1_atomic.py --output /tmp/matter1-prediction.json
python3 -B manual2/scripts/compare_matter1_atomic.py --prediction /tmp/matter1-prediction.json --target manual2/data/m1/atomic/evaluation_target.json --output /tmp/matter1-comparison.json
```

`manual2/evidence/v2-request.json` pins the available 63,942-byte R02 archive and six contract documents. The later approximately 136 KB / 42-entry archive mentioned in the handoff was not attached among the available files; its integrity is not claimed. The explicit amendments in the execution message govern the added target separation, intervention and rounding checks.

The additional 18 SI and five prediction criteria are recorded with actual assertion scope by `scripts/record_matter1_v2_acceptance.py`. It consumes the complete normal/optimized test logs and lane receipts, reruns read-only lane verification, and records the atomic objective as incomplete. The original 39 criteria remain separately recorded. CI exercises both receipts, all tests, persisted hostile mutations, paired publication, browser/export checks and disposable reproduction. Passing software tests does not promote atomic admission or physical prediction status.

## Isotopes, M3 and the survival experiment

The catalog contains 27 isotope/state records and 29 source records at a declared 1 November 2026 snapshot. Og/Lv/Fl family coverage includes tentative assignments, isomer candidates and unobserved targets with distinct statuses. ENSDF adopted values remain the default; newer experimental results are selectable source records, never silently averaged. NUBASE2020 cross-checks are separate. H-1/Cs-133 anchor records, Fe-56/Pb-208 benchmarks and Ni-62 binding-energy control have their own scopes. Pb-208's alpha partial-life lower limit is distinct from observational stability. Fl-298 is unobserved and has no scored empirical half-life.

The compact view retains all chart coordinates and original structural colors by default. The optional half-life view uses a logarithmic scale for finite selected total half-lives, with separate unknown/stable/limit labels. Isotope/state and source selectors show uncertainty and routes. The two actual alpha chains are Og-294 → Lv-290 → Fl-286 and Lv-293 → Fl-289. The three targets Fl-289, Og-294 and Fl-298 are a comparison progression, not a decay chain.

The new survival model enumerates an exact stochastic ensemble of retained histories. Committed paired currents change subsequent loss weights. Its common baseline median is in `(6,7]` coupled reference returns; changing the common loss gain gives `(4,5]`, changing capacity gives `(2,3]`, and disabling feedback at return 2 leaves the median censored beyond 8. These are executed declared-model results. Applying the same constructed state and shared reference map to different isotopes predicts equal half-lives; the separately frozen retrospective comparison rejects that specialization. No isotope-specific capacity or hazard was fitted, and no physical isotope half-life is claimed. Native isotope construction, loss-observation identification and reference/SI gain remain explicit dependencies.

M3's exact finite-law mapping module is vendored byte-for-byte with its source binding. CI additionally checks out the exact upstream commit and replays its actual Matter I consumer integration in normal and optimized Python; this lane cannot silently skip. The older v1/v2 data and all 118 placements/126 slots remain byte-preserved. The separate BIPM precision successor preserves 105 point results while recording unresolved printed-zero precision and rejecting the targeted sigma mutation.

See `manual2/data/m1/isotopes/README.md`, `manual2/data/m1/survival/`, and `manual2/evidence/m3-migration.md` for exact premises, source locators and unresolved dependencies. The complete element ledger remains in the Manual appendix. Generation is explicit; verification never repairs persisted files.

## Witnessed coupling and retention

Two separately bound examples extend the isotope-survival section. `constructed_coupling/` preserves the R02 engine and its four original experiments, with complete constituent formation, scope maps, directed contacts and return histories. Five aggregate fields evolve while their inner formation histories remain retained. The same update law gives four parent returns over 1,940 reference bips for the declared Fl-286 construction, 1,920 for Fl-289, and 1,902 for the Og-294 control. Each window starts after its own parent formation and ends at the same execution cut. The isotope labels do not enter the update law.

`witnessed_retention/` retains the distinct R03 square-return model. The raw unit and closure capacity are both 5. Opposite signed responses cancel while their burden remains: the exact third-return survivals are 5/6 for net memory and 2/3 for burden. The feedback, window and pending-background controls retain complete committed histories and exposed inner lineage. The earlier common-surrogate survival model, its nine-point curves and retrospective rejection are unchanged.

Both lanes use explicit generators and read-only complete replay:

```sh
python3 -B manual2/scripts/verify_matter1_constructed_coupling.py
python3 -B -O manual2/scripts/verify_matter1_constructed_coupling.py
python3 -B manual2/scripts/verify_matter1_witnessed_retention.py
python3 -B -O manual2/scripts/verify_matter1_witnessed_retention.py
```

Their `generate_matter1_*.py` commands accept `--root SOURCE_REPO --output-root OUTPUT_REPO`. The complete reproduction check regenerates both lanes in a disposable directory; CI and the scoped isotope acceptance recorder include their tests. Full constructed-coupling replay takes several minutes.

The two examples have separate state, reference and capacity choices. No combined retention model or physical isotope half-life is asserted. The constructed report records the missing adapter, preparation, nuclear loss, observation and uncertainty premises individually; Fl-298 remains unscored. The existing exact M3 executable pin remains active until the separately requested observation-interface candidate is supplied and replayed.
