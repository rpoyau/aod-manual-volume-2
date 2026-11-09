# Manual I data-card binding

This overlay classifies selected Matter I artifact families and components. It
uses AOD Manual I at commit `71cbcf7e637ababcde3b2e073fb4ceec4b1681b9`, tree
`3ab04df3793beda481b4fb7ed0d628ba6765da70`. The copied Manual I sources are
reference evidence only and are not active Main or Manual II includes.
Their original TeX bytes use the local suffix `.tex.source`: the publication
validator scans `.tex` files beneath `manual2`, so reference snapshots must not
look like active publication inputs. The source lock records the original
upstream paths separately and verifies the unchanged bytes. No publication
validator rule or tolerance is bypassed or weakened.

The source anchors are `manual:scoped-errors-data-support`,
`manual:record-forms`, `tab:manual-data-support-classes` and
`manual:external-comparison`. The authoring template is separately bound to
`aod-skills` commit `630af16a7c51fb8836e603eb54c67bf8560fb463`.

The 14 cards keep five independent axes: applicable data-support code, record
form, scientific claim class, original execution/outcome fields, and decimal
display scope. D0 describes only the named internal comparator/current/gate
components. O0 describes the observation-map declaration or conditional map
comparison, with its original outcome preserved. Neither code is assigned to a
whole element table or atomic model merely because some arithmetic is exact.
A null support code means inapplicable support metadata; it is not a new class.

The finite isotope targets and nonpoint inventory are disjoint. Observational
stability, missing values, unobserved declarations and rejected candidates are
not converted to point estimates. The H-anchored D/T source reductions remain
derived external values, retaining reference dependence and untranscribed
uncertainty/covariance. The supplement's original scientific claim fields remain
null. Source acquisitions have no native-input role.

`source-bindings.json` pins existing artifact bytes and exact copied authority
bytes. The verifier pins that lock's digest, checks each file, resolves each JSON
pointer, checks its selected-value digest, and enforces the versioned semantic
card dispatch. A genuine source revision requires a reviewed binding revision;
resealing a modified record does not validate it. The overlay is reproducible
from the source lock and the module's `expected_registry` function. No existing
numerical artifact was regenerated for this classification change.

Run the read-only verifier and persisted hostile tests:

```sh
python3 -B manual2/scripts/verify_matter1_data_classes.py
python3 -B -O manual2/scripts/verify_matter1_data_classes.py
python3 -B -m unittest manual2.tests.test_matter1_data_classes -v
python3 -B -O -m unittest manual2.tests.test_matter1_data_classes -v
```

The test methods create disposable on-disk copies for D0/O0 swaps, raw-target
promotion, whole-table/campaign misclassification, false prediction/execution,
missing class, display-scope mutation, bool/integer substitution, source
corruption, resealing and changed authority. Byte hashes, sizes and modification
times are unchanged by both positive and rejected verification. A separate test
checks the complete disjoint partition of all 27 isotope/state catalog records.

`PASS_CLASSIFICATION_BINDINGS_ONLY` means classification and binding consistency.
It executes no model, replays no campaign case, and supplies no new native
admission, physical prediction, isotope lifetime or empirical agreement. The
existing scientific executors and their receipts retain those responsibilities.
