# Exact finite-history isotope-survival experiment

This version executes a common state-dependent retention/loss law and tests one
restricted consequence against the adopted isotope catalog. It does **not**
identify its finite paths with admitted nuclear states or report physical AOD
half-lives. The v1 folding and v2 stateful fixtures are separate and unchanged.

## Premises and executed consequences

The authority order is inherited axiom, distinction, induced relations, admitted
motif, declared model and mathematical consequence. Main supplies conditional
H1/kernel normalization, orientation antisymmetry, excess and mapping forms.
The contract binds those source files and semantic labels. Native motif admission
is an unsatisfied premise for the physical application; finite Q4 geometry does
not bypass it.

The declared application fills in the finite state and observation choices:

- Two distinct recurrent lineages, each initialized by two committed square
  returns, share a comparison scope. A new reference return precedes each bound
  contact. Reference-return counts are not universal scheduler ticks or seconds.
- At the retained root, two continuations execute different closed squares; a
  third reaches an exit. The fourth Q4 slot is the incoming ancestor. The exit
  remains structurally admitted when its probability is zero.
- Each retained choice commits a paired response `(sigma,-sigma)`. Its contribution
  changes signed memory `R` and thus the **next** kernel. Unit response uses a
  declared pressure of 2 and lag magnitude 1/2; these are model inputs, not measured
  decay data or admitted atomic support accessors.
- Common weights are `(1,1,lambda*max(0,abs(R)-C))`. The two exit continuations carry
  equal conditional weights. Their alpha/fission labels are hypotheses, not an
  established nuclear observation map.
- Every choice prefix remains a distinct history. Loss is absorbing; completed
  events and inner scope-map provenance survive. Exact rational masses sum to one.
- `S(c)=Pr(C_loss>c)` sums retained histories. The first discrete median crossing
  is recorded as `(c-1,c]`, without interpolation; no crossing yields a lower bound.
  The M3 finite-law implementation computes the survival indicator's exact mean
  and variance. Ensemble spread is not uncertainty in the physical model.

No measured half-life, isotope-specific loss gain, capacity, fitted parameter or
evaluation value enters `prediction.json`. Formal grouping
`q=min(Z//2,N//2)` and residuals preserve nucleon arithmetic; they do not alter
kernel weights. The 11 isotope labels therefore share one unestablished surrogate.

| Declared run | Exact native median interval / bound | Purpose |
|---|---|---|
| `baseline`: C=1, lambda=1 | (6,7] reference returns | Common finite law |
| `loss_gain_2`: C=1, lambda=2 | (4,5] | Remaining loss-law freedom |
| `capacity_0`: C=0, lambda=1 | (2,3] | Common retention intervention |
| `feedback_off`: stop committing new responses at return 2 | >8 | Causal feedback control |

The baseline survival is
`[1,1,1,5/6,3/4,3/5,19/36,703/1680,211/576]` at counts 0 through 8.
Feedback removal changes the first later survival at count 3 from `5/6` to `1`.
Each run preserves all 255 retained prefixes, plus its absorbed histories.

## Separate comparison and unresolved dependencies

`comparison.json` first validates a complete target-free replay, then reads the
source-validated isotope catalog. Equal configurations plus a common observation
and clock map imply equal physical half-lives. The adopted Og-294/Lv-290,
Lv-290/Fl-286 and Lv-293/Fl-289 central ratios are `29/415`, `1/20` and `19/480`.
All three source-envelope ranges exclude 1. This rejects that **restricted
identity-insensitive/shared-clock specialization** within the source envelopes.
It is not a significance calculation and does not falsify AOD generally.

Known Og/Lv/Fl targets were exposed before selection and are retrospective. No
independence or covariance is invented. The unobserved Fl-298 target remains
unscored. The conventional exponential benchmark imports each half-life as its
calibrant; its exact survival at multiples of that calibrant is a calculation
check, not a prediction.

| Dependency | Exact missing premise |
|---|---|
| SURV-ATOM-01 | Distinct isotope/state configurations with native admission and support-accessor evidence. Formal Z/N/q arithmetic cannot supply this. |
| SURV-ATOM-02 | Independent state-to-kernel, retention and loss-observation construction. Main's conditional normalization does not select this application's weights, response magnitude, capacity, gain or exit partition. |
| SURV-ATOM-03 | A justified mapping from completed native reference returns to observed cycles and physical decay endpoints. Fixing Cs at 9,192,631,770 Hz does not fix that map. |
| SURV-ATOM-04 | Physical model discrepancy, reference realization, applicable transfer effects, uncertainty and covariance; source uncertainty conventions must remain visible. |

Unselected clock gains 1 and 2 produce different conditional time intervals from
the same finite history and Cs definition. They demonstrate the missing map and
are explicitly not physical predictions. No nuclear or SI uncertainty budget is
claimed complete.

## Reproduction and non-mutating verification

From the repository root:

```bash
python3 -B manual2/scripts/predict_matter1_survival.py --output /tmp/survival-prediction.json
python3 -B manual2/scripts/compare_matter1_survival.py --prediction /tmp/survival-prediction.json --output /tmp/survival-comparison.json
python3 -B manual2/scripts/verify_matter1_survival.py --check-data
python3 -B -O manual2/scripts/verify_matter1_survival.py --check-data
python3 -B -m unittest manual2.tests.test_matter1_survival -v
python3 -B -O -m unittest manual2.tests.test_matter1_survival -v
```

Explicit generation into a disposable directory uses
`generate_matter1_survival.py --output-root /tmp/survival-reproduction`.
`--isotope-catalog PATH` optionally consumes a freshly generated catalog, checked
against independent regeneration from source bytes and curation. The ordinary
verifier never generates or repairs inputs. Updating the model contract is a
separate explicit `--initialize-contract` operation, not a verification side effect.

The tests assert finite geometry, exact normalization, history retention, causal
feedback, competing outcomes, censoring, M3 full-law propagation, target isolation
and the stated conditional comparison. Persisted hostile mutations run in both
normal and optimized Python, with before/after file hashes and modification times
proving rejection without repair. These assertions cannot certify native atomic
admission, physical calibration or empirical agreement.
