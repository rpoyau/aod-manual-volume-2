# SI observation examples

These inputs instantiate the R02 measurement equation with synthetic calibration,
observation and covariance. They do not calibrate a real clock or determine an
AOD atomic transition. Native event order, reclosure count, support and physical
oscillator cycles remain separate quantities.
The first closure remains in each prefix as the recurrence anchor; it is not
counted as an additional reclosure. Five completions yield four reclosures.

`metrology_inputs.json` contains a complete synthetic one-second interval and
three materially incomplete cases: unknown cross covariance, unresolved cycle
slips and unmodeled dead time. Verification rejects corrupted data; it never
repairs it. `metrology_report.json` recomputes the exact rational results and
decimal display uncertainties.

The complete example gives variance 4904 ps² and standard uncertainty about
70.0286 ps; omitting the declared cross covariance gives 3404 ps². The uncertainty
is a synthetic demonstration, not a device-performance estimate. Exact PSD checks
accept singular matrices and reject indefinite matrices without clipping.

The report also binds the actual sequential v2 baseline and early-loss traces,
including their coupled comparison histories, to one explicitly stipulated
synthetic cycle map. The unchanged reference count gives the same one-second
example interval; the changed compared count alters a finite-window cycle-average
rate. This is not a stationary atomic frequency or the requested H/Cs prediction.

`frequency_from_ratio` converts an independently supplied ratio into frequency
and reciprocal transition period. It does not derive the ratio. Exact defining
Cs uncertainty is zero; a realized-reference parameterization retains unknown
variance/covariance as unknown. First-order uncertainty output is conditional on
the declared approximation. Both marginal relative uncertainties and the
propagated relative uncertainty must be at most one percent. Cancellation of
the product gradient with two uncertain inputs requires joint distribution
information, even when the linearized variance is zero. These guards are not
distribution-free error bounds. An exact finite-support regression example
has zero first-order variance but product variance 1/64; it remains partial.
The Gaussian quadratic example uses exact moments under its stated distribution.

Generate explicitly from the repository root:

```sh
python3 -B manual2/scripts/generate_matter1_metrology.py
python3 -B manual2/scripts/verify_matter1_metrology.py --check-data
```

The generator accepts `--output-root` for disposable reproduction. The verifier
is read-only and behaves identically under `python -O`. Source binding imports
the released Main relational-time labels; the SI measurement equation and
uncertainty assumptions remain declared downstream application choices.
