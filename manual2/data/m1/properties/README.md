# Element and isotope property records

This additive inventory separates element, isotope-unspecified atom/ion, nuclear
isotope/state and isotope-specific atomic state. It does not change the 118
reference placements, 126 slots, source selections, older calculations or chart.

`states.json` owns identities. `definitions.json` defines property domains,
coordinates and units. `catalog.json` owns values and qualifications.
`coverage.json` reports actual missing values. `source_manifest.json` binds the
retained source bytes used by deterministic offline generation; `inputs.json`
contains the reviewed source/selection manifest and is itself hash-bound in the
implementation. Source uncertainty magnitudes, statistical conventions,
distribution and shared covariance are separate fields.

## Acquired scope

The existing AME2020 raw table supplies neutral atomic masses, mass excesses,
binding energy per nucleon and beta-minus energies. Additional binding energies,
neutron/proton separation energies and alpha-decay Q values use explicit decimal
reductions of those masses. They retain systematics markers and input identity;
the unchanged catalog retains absent separation/Q uncertainties from its original
adoption, which did not acquire joint covariance. A positive Q is not an
observation of a decay branch.

NUBASE2020 supplies verbatim spin/parity, decay-mode and isotopic-abundance fields.
Tentative and estimated designations survive; source text is not silently turned
into normalized probabilities or universal sample abundances. Candidate isomers
are not replaced by ground-state values. Reference-A selections remain the
inherited unresolved choices.

The six pilots are H-1, H-2, H-3, He-3, He-4 and Cs-133. Existing H/D/T frequency
and Cs defining-anchor records retain reference dependence and prior exposure.
The Cs definition does not supply an exact realized oscillator. Two historical
ENSDF ground-state magnetic moments, one quadrupole moment and one H charge radius
are retained with their dated evaluation locators; they are not advertised as
current recommended values.

The package has identities for all 118 elements and their neutral/singly ionized
ground states. It has **not acquired** the broad NIST electronic configuration,
ionization, level or line tables, WebBook affinities, CIAAW weights or the full
response/moment/radius sources. Their entries are explicitly missing. A missing
source here does not assert that no physical data exist. No missing value is
filled by a reference mass number, a numerical zero, a generic isotope label or
a fitted native law. `acquisition_complete` remains false.

## Record interface

An adopted row has `id`, `entity_id`, `property`, `value`, `unit`, `value_kind`,
`uncertainty`, `method`, `exposure`, `source_id`, `locator`, `qualification`,
`selection_status` and `conditions`. Numerical values and uncertainty magnitudes
are decimal strings. Unknown/not-applicable values are null; a CIAAW-style
interval has `value_kind: interval`, `value: null`, and
`interval: {lower: "...", upper: "..."}`. An interval is not a standard deviation.

Stable examples are `element:Z001`, `atom:Z001:q0:ground`,
`isotope:H-1:ground` and `atomic-isotope:H-1:q0:ground`. Atomic mass uses the
nuclear-isotope identity with unit `u` and explicitly denotes the neutral atom.
The adopted pilot hyperfine IDs are `hyperfine:H-1`, `hyperfine:H-2`,
`hyperfine:H-3`, and `hyperfine:Cs-133`. A source-bound numerical line requires
lower/upper level IDs, transition and wavelength medium. A level energy requires
its level and reference-level IDs. Multiple transitions are separate records;
an additional source for the same selected transition must be marked alternative
rather than silently replacing or duplicating the adopted result.

`build(root)` returns the five original generated dictionaries and the additive
`mass_derivations.json`. `verify(root)` rebuilds
in memory, compares exact bytes and returns a scoped receipt.
`validate_catalog(catalog, states, definitions, sources=None)` checks the public
identity, quantity, uncertainty and selection contract. A consumer requiring
authentic retained inputs must also call `verify`; schema validity alone does not
authenticate scientific provenance.

## Mass reductions and shared inputs

`mass_derivations.json` records the 24 binding/separation/alpha-Q entries for the
six pilots: 15 exact nominal reductions and nine missing-input nulls. Source
quantity identity includes the source, locator and field; equal numerical values
do not merge distinct operands. Repeated occurrences of one source quantity are
combined before uncertainty propagation. Binding energy uses `B = A b` and scales
the quoted magnitude by the exact integer `A`, preserving its qualification.

For `Q = sum(c_i X_i)`, the conditional standard-deviation range is
`[max(0, 2 max(w_i) - S), S]`, where `w_i = abs(c_i) u_i` and `S = sum(w_i)`.
The retained AME2020 Part I, printed page030002-2 (PDFpage3), identifies quoted
uncertainties as one standard deviation. The original catalog qualifications
remain historical; this new source binding does not rewrite them. The range
uses those marginal magnitudes without choosing their covariance. It is not a
hard error interval, confidence interval or selected covariance.
Missing magnitudes remain missing. Different output endpoints need not be
attainable under one common covariance matrix.

Deuterium has the same source expression for neutron and proton separation:
`ME(H-1) + ME(n) - ME(H-2) = 2224.566229 keV`, with conditional SD range
`[0.000412, 0.000468] keV`. These are the same source-derived quantity.
The binding-energy route retains `2224.5662 keV`; its `0.000029 keV` difference
comes from the separately rounded source fields. A further identity is
`Sn(He-4) - Sp(He-4) = Sn(H-3) - Sp(He-3) = 763.754976 keV`.
The nine numerical separation/Q rows have coefficient rank seven; this is
algebraic rank, not seven independent experiments.

The separately bound `covariance_inputs.json` retains the official covariance
archive and both AME2020 papers. All ten required nuclides and 55 matrix entries
are present. Six light-nuclide separation calculations use the precise atomic
masses in Part II Table A (printed page030003-2, PDFpage3). Their `C Sigma C^T`
is retained in `(nano-u)^2`, including shared-output dependence. Published
coefficients are preserved exactly and the selected matrix passes exact PSD
checking; displayed square roots use ten significant digits, round half even.

The three Cs calculations remain held: the Cs-133 covariance diagonal falls
outside the declared nearest-last-place compatibility interval for its retained
marginal uncertainty. This is a chosen conservative check, not a claim about a
universal AME rounding policy or missing Cs covariance. Neither the matrix nor
the printed marginal is altered. The new mass-unit means are separate from the
unchanged baseline keV values and binding-energy-per-nucleon fields.

Part I Table A (printed page030002-3, PDFpage4) supplies the mass-to-energy
coefficient and its standard uncertainty. It is retained as context and not
applied; its dependence on the mass inputs is unresolved. Current M3 supplies
raw affine evaluation and moment propagation. Matter I owns units and source
interpretation; typed M3 acceptance, a complete physical budget and native mass
prediction are not claimed. The original catalog and source manifest remain
byte-preserved.

## Explicit offline source adoption

Later authorized acquisition can populate this structure without replacing the
native engine. Retain the raw official response, its URL, acquisition date,
version/citation and SHA256 in `inputs.json.sources`; record the exact requested
units and isotope/charge scope. Do not promote a theoretical or semiempirical
value to measured data.

Two offline adoption interfaces exist in `matter1_property_adoption.py`:

1. `nist_asd_ionization_csv_v1`: provide `source_id`, `energy_unit: eV` and an
   explicit `columns` mapping for `z`, `charge`, `configuration`, `term`, `energy`,
   `uncertainty` and optional `reference`. Actual source headers determine that
   mapping. Square/round energy brackets retain semiempirical/theoretical roles.
   No actual downloaded ASD table is claimed in this version; synthetic tests
   check parser behavior only.
2. `curated_property_records_v1`: each record binds a precise source locator and
   an exact `source_match` excerpt in retained source text. This supports a
   reviewed WebBook/CIAAW/ENSDF transcription, including interval and transition
   records. The four historical ENSDF properties exercise this route. Exact
   excerpt matching is a source-binding check, not automatic semantic review.

Review the transcription, entity/state/condition identity, source uncertainty
convention, selection status and raw hashes. Update the explicit
`INPUTS_SHA256` binding only as part of that reviewed adoption. Generate to a
disposable destination first, inspect changed coverage and run normal/optimized
verification and hostile tests. Generation does not itself establish scientific
correctness, source completeness, a native prediction or held-out exposure.

```sh
python3 -B manual2/scripts/generate_matter1_properties.py --output-root /tmp/property-adoption
python3 -B manual2/scripts/verify_matter1_properties.py
python3 -B -O manual2/scripts/verify_matter1_properties.py
python3 -B -m unittest manual2.tests.test_matter1_properties
```
