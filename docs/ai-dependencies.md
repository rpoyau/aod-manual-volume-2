# Authoring and scientific dependencies

Matter I uses two upstream repositories:

| Dependency | Role | Binding |
|---|---|---|
| [`rpoyau/aod-skills`](https://github.com/rpoyau/aod-skills) | Four portable authoring/review skills | [`.agents/dependencies.json`](../.agents/dependencies.json), commit `630af16a7c51fb8836e603eb54c67bf8560fb463` |
| [`rpoyau/aod`](https://github.com/rpoyau/aod) | Main mathematics | [`foundation-source.json`](../manual2/evidence/foundation-source.json), commit `8c3149b9d3d924b80b9385b178da4ba2c39175e8` |
| [`rpoyau/aod`](https://github.com/rpoyau/aod) | Historical temporal implementation and contracts (71cb) | Exact executable commit/tree and file hashes in [`vendor binding`](../manual2/vendor/aod_m3/binding.json) |
| [`rpoyau/aod`](https://github.com/rpoyau/aod) | Historical metrology companion and H/Cs profiles (71cb) | Same upstream commit, separately pinned [`metrology binding`](../manual2/vendor/aod_m3_metrology/binding.json) |

The skills pin was read from the canonical repository's `main` on 1 November
2026. Its dated source snapshots do not identify today's accepted AOD head. Its
seed statement that M3 is planned concerns that seed; the actual Matter I M3
execution and remaining dependencies are recorded in
[`m3-migration.md`](../manual2/evidence/m3-migration.md) and
[`isotope-results.md`](../manual2/evidence/isotope-results.md).
The AOD bindings identify reviewed PR43 candidates, not a version-43 release.
Main and the current producer-relative API closure consume verified M3 commit
`8c3149b9d3d924b80b9385b178da4ba2c39175e8`, tree
`b2b55cbcf18354828f7b34418ab3fa26d747a927`. The
[`11 November identity rebind`](../manual2/evidence/m3-source-rebind-2026-11-11.json)
retains the previous Main manifest; every imported Main input is unchanged.
The [`current producer binding`](../manual2/vendor/aod_m3_producer/binding.json)
authenticates the native, temporal, quantity-propagation and frozen-comparison
APIs, their contracts and published-source bytes. Load these through
`matter1_m3_producer.load(root)`. Producer readiness records a verified producer
scope; the required consumer check separately verifies actual downstream use.

The flat `manual2/vendor/aod_m3/current/` directory and metrology exports retain
commit `71cbcf7e637ababcde3b2e073fb4ceec4b1681b9` for historical R03, campaign and
property profiles. Their historical directory name is preserved for exact replay.
The original common-surrogate survival model retains its older separately verified
`legacy-binding.json`. These models and their failed or unresolved outcomes are
not relabelled as new producer results. The property source adapter selects the
archived 71cb Main manifest and binds its actual adapter separately from the
original recipe hash. Existing receipts remain intact.

The required consumer checker compares Main and every new exported byte against
the exact actual 8c checkout, replays historical reports with their original
executors, then compares current producer execution and downstream coupled
preparations against the new vendor. The exact closure omits unrelated generic
CLI fixture repositories; use its API, not repository-wide producer CLIs.
A newer upstream head requires an explicit reviewed rebind.

## Load the canonical skills

Use an existing external checkout through `AOD_SKILLS_ROOT`, or a sibling
`../aod-skills`, after verifying it. To obtain a disposable checkout without
changing a user's existing skills installation:

```sh
AOD_SKILLS_ROOT=$(mktemp -d /tmp/matter1-aod-skills.XXXXXX)
git clone git@github.com:rpoyau/aod-skills.git "$AOD_SKILLS_ROOT"
git -C "$AOD_SKILLS_ROOT" checkout --detach 630af16a7c51fb8836e603eb54c67bf8560fb463
export AOD_SKILLS_ROOT
```

The repository requires the user's GitHub access. Verify the exact revision and
unchanged tracked guidance, then validate its linked source snapshots:

```sh
test "$(git -C "$AOD_SKILLS_ROOT" rev-parse HEAD)" = 630af16a7c51fb8836e603eb54c67bf8560fb463
test "$(git -C "$AOD_SKILLS_ROOT" rev-parse 'HEAD^{tree}')" = 9d571826e270b79e3c43aac7ebbf259a6372b1e1
git -C "$AOD_SKILLS_ROOT" diff --exit-code HEAD
(cd "$AOD_SKILLS_ROOT" && python3 -B scripts/validate_repository.py)
```

Read the four `SKILL.md` entry points listed in the dependency manifest, starting
with `skills/aod/SKILL.md`. Read the referenced authority, ontology, calculus and
presentation material needed for the task. Explicitly select those paths; this
setup does not claim automatic skill discovery. If installing into a separate
agent environment, retain each complete skill directory and its relative paths
as upstream directs. Do not overwrite the five preserved local skill snapshots
or create a same-named AF installation over them.

## Use the scientific dependency

Existing CI checks out the exact AOD commit into `.m3-upstream` and executes the
consumer in both Python modes. For local work, point `AOD_SOURCE_ROOT` at a clean
checkout of the executable commit in the vendor binding, then run from Matter I:

```sh
python3 -B scripts/check_matter1_m3_consumer.py --upstream-root "$AOD_SOURCE_ROOT"
python3 -B -O scripts/check_matter1_m3_consumer.py --upstream-root "$AOD_SOURCE_ROOT"
```

This read-only check rejects the wrong upstream head or modified tracked files,
compares imported Main and vendor bytes, and replays the actual consumer. The R03
adapter supplies admitted waves, complete directed contacts, preparation,
committed prefixes, pending returns and the prior comparison to `ObservationContext`.
Whole artifacts replay from separately supplied original R03 inputs. Gains remain
stipulated at one cycle per return; no physical clock or isotope map is supplied. A pass
does not establish native atomic/isotope admission or physical prediction.
The metrology adapter freezes its calculations before loading evaluation targets.
It consumes M3's source-bound comparison API, hydrogen reductions and caesium
uncertainty records. D/T and selected Lv records expose missing inputs separately
from the computations that can execute. This application has a new profile; it
does not claim recovery of the unavailable historical consumer `3e40b178`.
The separate skills checkout is not required to reproduce the scientific build;
its project-history area and AOD-specific authoring profile are not imported.

## Updating a dependency

Review the upstream diff, preserve intervening work and record the new commit,
tree, role and actual authority status. For skills, reread changed entries and
references, update the authoring pin and explain any changed owner resolution.
For AOD, follow the foundation/vendor rebind and preservation mechanisms and run
the affected scientific, consumer and paired-publication checks. Never change a
historical receipt to make an old result appear to validate a new source.
