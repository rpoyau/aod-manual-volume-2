# F1 numerical evidence repair — 1 November 2026

The valid P2 finding in the AOD PR43 review is repaired upstream and imported
here. A trusted evidence payload must pass the existing exact-rational parser
and nonnegative guard before it can match a numerical error-budget claim.
Python equality alone previously admitted Boolean/integral-float aliases.
The repair preserves representation-sensitive matching, complete evidence
bindings and the finite-law standard-uncertainty variance check.

## Source authority and binding

- Upstream repair: `rpoyau/aod` commit
  `3ffb3c9984eef95ca4b105ac323d249f30412816`, tree
  `4e260a7c8e22ab5b78a73a0a12e784f1be46c984`.
- Matter I baseline for this repair:
  `6bb55ca9dff91bbef015ae56c3c4e627c54f2193`.
- Main mathematical sources remain byte-preserved at their existing
  `b78b48dd7aa1608dbb7141e9814e33c3cfcf900b` foundation binding. The executable
  vendor pin advances independently. The required consumer check now verifies
  this distinction, the exact upstream tree, all vendor bytes and Main sources.
- The verified canonical `aod-skills` checkout at
  `630af16a7c51fb8836e603eb54c67bf8560fb463` supplied AOD, AF, AFC and General
  Mechanics guidance. The five tracked historical skills are unchanged and
  retain the owner-resolved scope in `fusion-request.json`.

## Executed checks

The accompanying `f1-checks/` records are local execution evidence, not
independent attestation or native admission certificates. Historical evidence
directories remain historical. The final delivery records Git heads and hosted
CI separately; these files were recorded before the downstream commit.

| Check | Completed outcome and scope |
| --- | --- |
| Upstream full suite | 836 passed, one optional sibling-consumer test skipped, in both ordinary and optimized Python 3.12.14 |
| Actual upstream/consumer integration | Separately passed in both modes against the exact upstream checkout; the required downstream check never skips |
| Matter I full suite | 221 tests passed |
| Matter I optimized validation subset | 194 tests passed |
| Final publication suite after reproduction | 12 tests passed |
| New persisted evidence cases | 35 per mode, grouped into seven downstream methods; full `run_map()` execution with independently resealed trusted payloads |
| Numeric alias counterexamples | Eight cases per mode (Boolean/float, bound/standard uncertainty) rejected; the original implementation accepted them |
| Positive and negative controls | Exact integers/rational strings execute; negative, malformed, mismatched representation/value and wrong variance reject; persisted files remain unchanged |
| Data and model verification | Normal/optimized data and ten lane checks pass |
| Acceptance records | 39 original criteria, 23 SI/prediction criteria and 69 isotope/M3 criteria recorded with explicit assertion scopes; the latter includes seven new F1 records |
| Export/browser | Locked renderer and geometry pass; six isotope browser views pass, with source switching, chain navigation and no horizontal overflow |
| Publication | Main 73 pages, Manual 33 pages; 74 semantic destinations and 104 external Main links per Manual variant pass |
| Reproduction | 43 generated outputs reproduced in a disposable copy without modifying inputs |

Main-first paired builds completed. Full extracted Manual text matches the prior
publication, and rendered pages 7, 22 and 24 were inspected. Upstream Main/Manual
text also matches the prior publication; representative mapping pages were
inspected. Renderer locks and tolerances are unchanged.

## Conservation and unresolved dependencies

The standalone `f1-checks/conservation_probe.py` compares pinned Git objects
without importing either repository's verifier. Upstream report differences
are exactly 31 mapping and 13 temporal source-dependent digest leaves. Downstream
survival contract, prediction, comparison and report differences are respectively
1, 16, 1 and 2 digest leaves. All other values, JSON types, scientific statuses,
histories, probabilities, medians and comparisons are unchanged. Publication
receipts change only for those four input hashes and the three rebuilt PDFs.
The 118 placements, 126 slots, isotope catalog and historical numerical records
are preserved.

F1 is a validation repair; it supplies no new atomic or nuclear prediction.
M3 retains 32/36 criteria verified within scope: MAP-07, MAP-21/22 and MAP-28
remain partial, and G6 remains unopened. Native isotope-state admission,
physical loss/observation laws, the reference-clock map and physical uncertainty
remain unresolved. The hydrogen comparison remains retrospective. The declared
equal-state/shared-clock isotope specialization remains rejected within the
source envelopes. No physical agreement or fitted parameter is introduced.

## Replay

Use the documented locked Matter I environment and exact upstream checkout.
Run the commands in `.github/workflows/matter1.yml` for the full pipeline.
Focused checks are:

```sh
python -B -m unittest manual2.tests.test_matter1_m3_evidence -v
python -B -O -m unittest manual2.tests.test_matter1_m3_evidence -v
python -B scripts/check_matter1_m3_consumer.py --upstream-root /path/to/aod
python -B -O scripts/check_matter1_m3_consumer.py --upstream-root /path/to/aod
python -B manual2/evidence/f1-checks/conservation_probe.py \
  --upstream /path/to/aod --matter /path/to/aod-manual-volume-2
```

The conservation probe also needs the two baseline Git objects named above.
Upstream full tests are `python -B -m pytest -q` and
`python -B -O -m pytest -q`; its optional sibling test is reported separately
from the mandatory downstream consumer check.
