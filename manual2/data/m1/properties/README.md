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
derived separation/Q uncertainties stay absent because joint covariance was not
acquired. A positive Q is not an observation of a decay branch.

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

`build(root)` returns all five generated dictionaries. `verify(root)` rebuilds
in memory, compares exact bytes and returns a scoped receipt.
`validate_catalog(catalog, states, definitions, sources=None)` checks the public
identity, quantity, uncertainty and selection contract. A consumer requiring
authentic retained inputs must also call `verify`; schema validity alone does not
authenticate scientific provenance.

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
