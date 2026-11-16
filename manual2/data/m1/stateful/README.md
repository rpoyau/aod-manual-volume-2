# Sequential finite folding model v2

The v1 folding/temporal files remain unchanged. The new parameterized model
executes an explicit state transition for each integer commit cut. Its states
and inputs have no intrinsic SI time unit or atomic identity.

Two inner square histories finish at cut 19. Their certificates, distinct
scopes, handedness and injective maps are retained by the outer fold at cut 20.
Each retained outer lineage then commits one path token per cut: a start
sample, one Hamming-1 edge, or an optional zero-edge hinge dwell. The turn
vertex supplies the mandatory structural hinge; it is not an extra H1 edge.
Only a completed path can produce a finite retained-return witness.

Each contact attempts an actual three-sample two-edge trace. Its final binding
requires two recurrent retained histories, and repeated bound contacts permit
the exact comparator. A computed capacity response is queued at cut k and
consumed at k+1 before any further path or contact event. Loss is absorbing in
v2: no automatic re-admission, photon identification or routed reclosure is
implemented. Completed events and exposed inner maps are retained. An
interrupted partial cycle retains its committed events without a return.

| Run | Capacity intervention | Outer-plus completions | Bound contacts | Final window count ratio |
| --- | --- | --- | --- | --- |
| Baseline | 100 throughout | 26,33,40,47,54,61,68 | 8 | 6/5 |
| Early loss | 2 from comparison cut 40 | 26,33,40 | 2 | 2/5 |

Loss commits at 41. Records through 39 are identical; the response queued at
40 differs. The final counts cover (20,68] and exclude each lineage's first
return as its origin. The final ratio is a finite-window count comparison,
not an admitted atomic frequency or stationary recurrence rate. The last
actual coupled comparison in the loss run is at 40. No outer-plus event or
new bound contact is emitted after loss.

The model permits declared dwell, phase bias, positive boundary weight,
orientation, finite horizon, contact schedule and nonnegative capacity
interventions within validated domains. Those are application inputs; Main's
definitions do not uniquely choose them. Changing a future capacity input
does not rewrite earlier committed prefixes.

Generate explicitly with `python3 -B manual2/scripts/generate_matter1_stateful.py`.
Verify without writes using `python3 -B manual2/scripts/verify_matter1_stateful.py`.
`--check-data` is a read-only alias; unknown CLI options are rejected.
The verifier checks source/geometry bindings, finite witnesses and a fresh
sequential replay before comparing the delivered scenarios, traces and report.

The tests exercise positive scenarios, next-cut causality, partial-cycle
loss, future-input isolation, source/lineage preservation and real persisted
corruptions through normal and optimized verifier processes. These checks
establish declared finite behavior, not complete native admission, an atomic
observation map or empirical agreement.
