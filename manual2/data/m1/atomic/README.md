# Atomic observation attempt and conventional benchmark

**The AOD atomic prediction objective is incomplete.** These records execute a
target-independent non-identifiability demonstration, a separately bound
retrospective comparison, and a conventional externally calibrated hyperfine
benchmark. No record supplies a native H/Cs atomic prediction.

## Setup and consequence

The common finite v2 dynamics yields six retained `outer_plus` reclosures and
five `outer_minus` reclosures in the baseline window, after treating each
lineage's first completed return as its anchor. The declared capacity
intervention changes subsequent committed history to two versus five. These
are finite-window count comparisons; stationary atomic frequency has not been
established. The temporary assignment of atomic names to the two lineages is a
counterexample assumption, with no claim of native atomic admission.

For both species use the single observation-map family

\[
g_\lambda(Z)=1+\lambda(55-Z)/54,\qquad
R_\lambda=r\,g_\lambda(1)/g_\lambda(55)=r(1+\lambda),\quad \lambda>-1.
\]

Every member preserves the same underlying finite history and the Cs
normalization `g(55)=1`. The two executed witnesses `lambda=0,1` give baseline
ratios `6/5,12/5` and intervention ratios `2/5,4/5`. Cs scale conversion gives
11,031,158,124; 22,062,316,248; 3,677,052,708; and 7,354,105,416 Hz, respectively.
These are unselected diagnostic values. Since any positive ratio can be
obtained with `lambda=R/r-1`, normalization alone does not determine the missing
relative observation gain. Neither witness is selected, fitted or called an
atomic model. This argument concerns the currently established constraints,
not every possible future AOD atomic construction.

Main's proposed/admitted-trace rule, declared wave update, cadence comparator
and protocol-dependent duration are bound by SHA-256 and exact source-label
lines in `model_contract.json` and `obligations.json`. The latter identifies
the additional premises: state-specific Cs/H constructions and support
accessors (P2), atomic coupled lineages (P3), a relative state-to-observable
rule independent of the tested H splitting (P4), and applicable physical
uncertainty/covariance. The external inventory (P4a) does not supply these.

## Prediction and comparison boundary

`predict_matter1_atomic.py` reads the target-free model contract, source-bound
geometry and fresh finite v2 dynamics. It works with both evaluation and
benchmark input files removed. It records contract, engine, calibration and
trace hashes. The `atomic_prediction` fields remain null. Only the separate
comparison command reads the historical H target, 1,420,405,751.768 Hz with
one-sigma uncertainty **0.002 Hz**, printed page 200 of
[Hellwig et al.](https://tf.nist.gov/general/pdf/13.pdf). Prior H exposure is
explicitly retrospective. Its residuals are diagnostic and have no empirical
atomic score or standardized residual; the required atomic map and full joint
uncertainty are absent. A synthetic evaluation mutation changes these
residuals without changing prediction bytes.

The Cs value 9,192,631,770 Hz is the
[exact SI definition](https://www.bipm.org/en/si-base-units/second). It does not
describe a realized device with zero uncertainty. Frequency reciprocal is a
transition period, and is not an independently observed elapsed interval.

## Conventional benchmark

The separate benchmark uses the external hyperfine/Zeeman Hamiltonian described
in [Steck's cesium data, revision 2.3.4, section 3](https://steck.us/alkalidata/cesiumnumbers.pdf).
For the `m_F=0`, `J=1/2` block, in the product basis, it evaluates

\[
H/h=\begin{pmatrix}-a/4+\beta B/2&\Delta/2\\
\Delta/2&-a/4-\beta B/2\end{pmatrix},\quad
a=\Delta/(I+1/2),\quad \nu(B)=\sqrt{\Delta^2+(\beta B)^2}.
\]

The **declared leading spin-only approximation** sets `g_J=2,g_I=0` for both
species. It omits bound-state corrections, nuclear Zeeman terms and
environmental shifts, so it is not precision spectroscopy. `beta=(g_J-g_I)
mu_B/h` uses [NIST's 2022 CODATA table, Bohr magneton in Hz/T row](https://physics.nist.gov/cuu/Constants/Table/allascii.txt),
13,996,244,917.1 Hz/T with standard uncertainty 4.4 Hz/T. The measured H
splitting and exact Cs splitting are explicitly benchmark calibrants.
Zero-field agreement reproduces those inputs and establishes no prediction.
Five stipulated fields per species give ten computed rows. At `B=0.0001 T`,
the approximate shifts are 2,758.291865986 Hz (H) and 426.199748102 Hz (Cs).
The full physical uncertainty remains partial: field realization, approximation
error and applicable covariance have not been supplied. Independent NumPy
diagonalization checks the exact-matrix evaluation.

## Replay

From the repository root:

```sh
python3 -B manual2/scripts/verify_matter1_atomic.py --check-data
python3 -B -O manual2/scripts/verify_matter1_atomic.py --check-data
python3 -B manual2/scripts/predict_matter1_atomic.py --output /tmp/atomic-prediction.json
python3 -B manual2/scripts/compare_matter1_atomic.py --prediction /tmp/atomic-prediction.json --output /tmp/atomic-comparison.json
python3 -B -m unittest manual2.tests.test_matter1_atomic -v
python3 -B -O -m unittest manual2.tests.test_matter1_atomic -v
```

Verification rejects persisted corruption without changing bytes or file
timestamps. Regeneration is an explicit separate command,
`generate_matter1_atomic.py --output-root /tmp/atomic-regeneration`.
PRED-01 through PRED-05 each carry their actual assertion scope; software and
counterexample checks do not promote the missing atomic calculation to a pass.
