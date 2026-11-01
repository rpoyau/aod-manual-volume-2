# Authoring and scientific dependencies

Matter I uses two upstream repositories:

| Dependency | Role | Binding |
|---|---|---|
| [`rpoyau/aod-skills`](https://github.com/rpoyau/aod-skills) | Four portable authoring/review skills | [`.agents/dependencies.json`](../.agents/dependencies.json), commit `630af16a7c51fb8836e603eb54c67bf8560fb463` |
| [`rpoyau/aod`](https://github.com/rpoyau/aod) | Main mathematics | [`foundation-source.json`](../manual2/evidence/foundation-source.json), commit `b78b48dd7aa1608dbb7141e9814e33c3cfcf900b` |
| [`rpoyau/aod`](https://github.com/rpoyau/aod) | Consumed M3 implementation and contracts | Exact executable commit/tree and file hashes in [`vendor binding`](../manual2/vendor/aod_m3/binding.json) |

The skills pin was read from the canonical repository's `main` on 1 November
2026. Its dated source snapshots do not identify today's accepted AOD head. Its
seed statement that M3 is planned concerns that seed; the actual Matter I M3
execution and remaining dependencies are recorded in
[`m3-migration.md`](../manual2/evidence/m3-migration.md) and
[`isotope-results.md`](../manual2/evidence/isotope-results.md).
The AOD bindings identify reviewed PR43 candidates, not a version-43 release.
The executable binding includes the F1 evidence-value validation repair; Main's
mathematical source bytes retain their earlier binding. Consumer replay checks
both imported Main bytes and the executable against the repaired checkout.
A newer upstream head is an update to review, not permission
to replace these pins silently.

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
compares imported Main and vendor bytes, and replays the actual consumer. A pass
does not establish native atomic/isotope admission or physical prediction.
The separate skills checkout is not required to reproduce the scientific build;
its project-history area and AOD-specific authoring profile are not imported.

## Updating a dependency

Review the upstream diff, preserve intervening work and record the new commit,
tree, role and actual authority status. For skills, reread changed entries and
references, update the authoring pin and explain any changed owner resolution.
For AOD, follow the foundation/vendor rebind and preservation mechanisms and run
the affected scientific, consumer and paired-publication checks. Never change a
historical receipt to make an old result appear to validate a new source.
