# Isotope reference snapshot

This catalog adds isotope/state observations beside the frozen 118-element reference. It does not change that reference's `mass_a` inputs, certify an AOD state, or supply a nuclear survival law.

The snapshot contains 27 isotope/state records and 29 source records. ENSDF adopted ground-state records are the default; named newer experimental analyses are selectable separately. NUBASE2020 is a cross-check, not an automatic observation classifier. The source snapshot was retrieved on 2026-11-01. Evaluation dates and literature cutoffs are attached to individual sources; a recent retrieval does not make an older evaluation current.

## Coverage and interpretation

- Og: observed 294; 295 is explicitly unobserved after the candidate-chain reanalysis. Its finite NUBASE entry is not promoted to a measurement.
- Lv: 288 and 289 are reported experimental 2025 results in the NNDC XUNDL compilation; 290–293 are adopted observations; 294 remains a tentative alternative chain assignment with no measured total half-life supplied.
- Fl: 284–289 are adopted observations; 290 remains tentative. Fl-298 is an unobserved model target, without an invented half-life.
- Candidate isomers of Lv-293 and Fl-289 remain separate NUBASE comparison records, not confirmed adopted states or a partition of the ground-state evaluation's event sample.
- H-1, Cs-133, Fe-56, Ni-62 and Pb-208 anchor identity/stability/binding checks. Cn-280, Cn-282 and Cn-285 retain daughter endpoint information. Other daughters retain identity and channel qualifications without claiming full catalog coverage.
- Estimated NUBASE Og-293 and Fl-291 entries are listed in the exclusions. Absence of a `#` is insufficient evidence of observation.

`half_life` always names a **total half-life**. It preserves original notation, exact decimal conversion to seconds, asymmetric errors and the stated confidence convention. If the adopted record does not explicitly state confidence, this remains unresolved; no Gaussian law is invented. `event_times` are individual waiting times. `limits` and the Gates2024 `channel_partial_half_lives` have their own quantity types. Stable means observationally stable, not a measured infinity.

Pb-208 retains its alpha-channel lower bound of 2.6×10^21 y at 90% confidence separately from the adopted stable classification (Beeman et al., PDF page 6, equation 5). Year conversions use 31,557,600 seconds per Julian year. Fe-56 and Ni-62 retain the AME2020 binding-per-nucleon values; Ni-62 exceeds Fe-56, so Fe-56 is not labelled the binding-per-nucleon maximum.

The Gates2024 supplemental table (PDF page 11, printed page 3) gives newer Lv-290, Fl-286 and Cn-282 estimates. These combine older and new events and are not statistically independent of the older evaluations. No averages are formed here. Its Fl-286 partial-channel uncertainties exclude uncertainty in estimated branching fractions, as the source states. The newer 2025 XUNDL Fl-284 alpha channel is preserved separately from the older adopted SF-only observation.

The formal coordinates are `q=min(Z//2,N//2)`, `r_p=Z-2q`, `r_n=N-2q`, hence `A=4q+r_p+r_n`. These are bookkeeping groups; they do not establish physical alpha clustering. Cs-133 yields `q=27, r_p=1, r_n=24`.

## Source and result separation

`curation.json` is the reviewed input snapshot. Its SHA-256 is pinned in `matter1_isotopes.py`; every consumed original source and extracted text is hash-bound. Original PDF bytes are retained. `source_records` provide the page/table/row locators. XUNDL original returned HTML is retained alongside the extracted fixed-width records and the retrieval form fields. The source's occasional reaction-label inconsistency is preserved verbatim; isotope identity is taken from its dataset identity, discovery record and corresponding parent dataset, not silently rewritten.

Every known numerical observation is marked retrospective because it was read before model freeze. Fl-298 is an unscored target with no measured lifetime. Native admission, execution and empirical agreement are separate fields. Reference verification does not promote any of them.

## Replay

From the repository root:

```sh
python3 -B manual2/scripts/verify_matter1_isotopes.py --check-data
python3 -B -O manual2/scripts/verify_matter1_isotopes.py --check-data
python3 -B -m unittest manual2/tests/test_matter1_isotopes.py
python3 -B -O -m unittest manual2/tests/test_matter1_isotopes.py
```

Generation is explicit and deterministic. `--root` accepts the repository or Manual directory. `--output-root` selects a separate Manual output directory while reading source inputs from `--root`; generation never consumes the delivered generated catalog.

```sh
python3 -B manual2/scripts/generate_matter1_isotopes.py --output-root /tmp/isotope-reproduction
```

Generated outputs are `catalog.json`, `verification.json`, and the four `sections/generated_isotope_{anchors,benchmarks,superheavy,chains}.tex` files. Verification rejects altered source bytes, data, status promotions, unknown flags and stale tables without changing file bytes or mtimes, including under optimized Python.
