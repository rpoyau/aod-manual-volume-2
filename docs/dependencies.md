# Scientific and authoring dependencies

The scientific producer is AOD. The exact current commit, tree and exported
source hashes are recorded in
[the producer binding](../manual2/vendor/aod_producer/binding.json) and
[the Main source binding](../manual2/evidence/foundation-source.json).
The two roles are checked together; neither follows a floating upstream branch.

Historical observation and metrology exports retain their separately bound
source bytes under `manual2/vendor/aod_m3/` and
`manual2/vendor/aod_m3_metrology/`. Their identifiers and receipts describe those
historical models. A newer producer does not relabel their results.

For local verification, set `AOD_SOURCE_ROOT` to a clean checkout of the current
producer's exact commit, then run:

```sh
python3 -B scripts/check_matter1_aod_consumer.py --upstream-root "$AOD_SOURCE_ROOT"
python3 -B -O scripts/check_matter1_aod_consumer.py --upstream-root "$AOD_SOURCE_ROOT"
```

The check rejects mismatched commits, modified source and substituted modules.
It verifies Main and exported scientific bytes and exercises the actual consumer.
Its success does not establish a physical atomic observation law, clock
realization or complete physical uncertainty budget.

The four portable authoring skills come from
[`rpoyau/aod-skills`](https://github.com/rpoyau/aod-skills), pinned in
[the authoring dependency record](../.agents/dependencies.json). Use an external
checkout through `AOD_SKILLS_ROOT`, or the sibling `../aod-skills`. Verify its exact
commit/tree, entry-point hashes and source bindings before reading the listed
`SKILL.md` files. These are explicit reading instructions, not automatic skill
installation. The canonical checkout's validator checks its bundled snapshots.

The skills repository and its project history are not required for scientific
execution, CI or source-release reproduction. Task archives and historical
authoring snapshots remain detached. Scientific source manifests authenticate
only the sources and results needed by each calculation.

For an upstream change, review the diff, preserve historical identities, bind the
new commit/tree and source bytes, and run the affected consumer and paired
publication checks. Update current bindings in their owning records; retain
predecessor commit/blob identities without adding duplicate source snapshots
unless their exact bytes are required for historical execution.
