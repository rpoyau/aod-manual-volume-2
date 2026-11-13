# Matter I repository instructions

## Read at task entry

This repository is the downstream **AOD Manual Volume II — Matter I** application.
Use the canonical authoring skills from
[`rpoyau/aod-skills`](https://github.com/rpoyau/aod-skills), and the mathematical
interfaces from [`rpoyau/aod`](https://github.com/rpoyau/aod). They have different
roles and independent source bindings.

1. Read [the dependency setup](docs/ai-dependencies.md) and
   [the authoring dependency pin](.agents/dependencies.json). Resolve and verify
   the canonical skills checkout before relying on its contents. `AOD_SKILLS_ROOT`
   may name an existing external checkout; a sibling `../aod-skills` is another
   option. Use the documented disposable checkout if neither is available.
2. Read these actual files from that verified checkout, including their directly
   linked references as applicable:
   - `skills/aod/SKILL.md`: source authority, ontology and downstream ownership;
   - `skills/axiomatic-fundamentalism/SKILL.md`: premises, derivation and scope;
   - `skills/afc/SKILL.md`: exact finite memory/kernel calculations;
   - `skills/general-mechanics/SKILL.md`: manuscript presentation and references.
   Address these files explicitly. A checkout path alone does not install or
   automatically activate skills. If unavailable, report that limitation and
   continue work that does not depend on unseen instructions.
3. Read `manual2/evidence/foundation-source.json`,
   `manual2/evidence/m3-source-rebind.json` and `manual2/vendor/aod_m3/binding.json`
   for the active scientific dependency. Resolve actual source labels and
   definitions before making a scientific change.
4. Inspect the current branch, working tree, active include graph and task scope.
   Refresh remote metadata when working on a PR. Preserve intervening work.

The five checked-in `.agents/skills/` directories are preserved historical review
inputs. They are not a live mirror of `aod-skills`. Apply their relevant guidance
through the owner-resolved scope in `manual2/evidence/fusion-request.json`:
AF premises and model declarations belong in General Mechanics Setup; Main owns
ontology; this Manual owns applications; schematic Null sameness does not install
an implicit runtime reducer; use the actual downstream tests and publication
checks. Keep those five skill files and their referenced assets byte-preserved.
Use the canonical AF entry point above even when an older skill has the same name.

## Scientific and presentation discipline

Follow axiom → distinction → induced relations → admitted motif → declared model
→ mathematical consequence. Bind formation witnesses, scope, lineage and the
actual transition law before assigning an accessor or claiming native execution.
Keep arithmetic, admission, declared simulation, representation, metrology and
empirical agreement distinct. Preserve committed history through folding and
projection; declare inner-to-outer maps rather than asserting scope equality.

Use exact integers/rationals for exact claims. Recurrence counts and relational
cadence acquire physical units only through a declared observation/calibration
map and its uncertainty. A target previously exposed to the model remains
retrospective unless independence is evidenced. Hold only results that depend on
missing premises and continue independent work.

Use applicable General Mechanics blocks: Setup, Derivation, Specialization,
Calibration, Falsification, Provenance, Literature note. Do not manufacture an
inapplicable block or import a physical premise from a style example. Preserve
semantic labels and Main-reference macros. Keep workflow status in evidence
records rather than scientific prose.

## Ownership and verification

- Root `main.tex`, `sections/`, `appendices/`, `preamble.tex` and `refs.bib` are
  imported, source-bound AOD foundation material. Do not independently rewrite
  Main ontology here. A foundation update needs an explicit rebind and consumer
  verification.
- `manual2/` owns the application, isotope catalog, simulations, compact view and
  Manual. `manual2/data/m1/` is canonical; preserve declared compatibility copies.
- Preserve all 118 element placements, 126 reference slots, frozen numerical and
  historical records, and renderer locks/tolerances unless the task explicitly
  authorizes a reviewed migration. Source-dependent historical receipts remain
  historical; do not relabel them as current validation.
- Use the real commands in [README.md](README.md) and
  [.github/workflows/matter1.yml](.github/workflows/matter1.yml). Run persisted
  verification before explicit generation. Verifiers must not repair inputs.
  Use disposable copies for hostile mutations and reproduction.
- Run tests appropriate to the change. Scientific/executable changes require the
  affected normal/optimized verifiers and actual hostile tests. Publication
  changes require Main-first paired builds, PDF-reference checks and inspection
  of changed rendered pages. Visual changes require actual export/browser checks.
  A static scan is neither a successful build nor a proof.
- The required M3 consumer check uses the exact upstream `aod` checkout. The private
  `aod-skills` repository supplies authoring guidance, not a new scientific CI or
  runtime dependency. Do not import its unrelated `projects/aod/` work requests or
  AOD-specific authoring profile into this application's build.

Follow the current user's authorization for commits and remote writes. For the
existing Matter I PR, work on its branch, refresh the remote head before a normal
push, integrate intervening changes and revalidate. Do not merge, force-push,
push to main or create a replacement PR without explicit authorization. Report
the final head, actual check scope and remaining scientific dependencies.
