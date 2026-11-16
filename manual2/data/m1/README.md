# Matter I static reference contract, schema v2

`matter1_elements_1_118_ledger.csv` is the authoritative generated ledger. There are 118 supplied element references and eight unfilled reference slots, Z=119..126. One supplied A is retained per named element. Its selection provenance is unresolved; the reference list does not assert a stable-isotope, most-abundant-isotope, standard-weight or observed-isotope policy. The unfilled slots retain the old projected A operands solely as comparison fixtures.

`reference_inputs.csv` binds each row to the frozen PR fixture. `model_inputs.json` declares the support operands, capacity/window rules and legacy pressure/TTL/class assignments. `input_provenance.json` states their evidence status. `schema.json` specifies the exact columns and types. `field_migration.json` records the v1-to-v2 names and six legacy class mappings. `evidence/input_manifest.json` hashes these inputs, the immutable v1 numeric fixture and the six historical source excerpts.

The local seat tuple `(a_tritrio,b_tetratrio,c_dimon)` is `((s+1)//2,s//2,s%2)`. It is separate from the nuclear counts `(baryon_tritrio,baryon_tetratrio)=(Z,A-Z)`. `shell_dimon` preserves the legacy aggregate Z operand; it is not the local parity count. Seat parity and assigned pressure residual are separate fields. `is_group_boundary` includes unfilled slot 126; `is_named_anchor` applies only to named element references. Anchor membership and assigned surplus status can overlap.

`support_sum = 30Z + 68(A-Z) + 1 + 4s` preserves all legacy `rd_fuse` numeric values as a conditional expression. `support_declaration` is formatted motif syntax, not a certificate. `declaration_id` identifies a supplied reference; it is not an occurrence or completed event. Every row has `admission_status=pending` and `execution_status=not_executed`. The exact integer A parameter can be varied at fixed Z: the sum changes by 68 times the change in A, while the placement stays fixed. This conditional algebra does not establish isotope existence, stability, abundance, measured masses or isotope-specific routes.

Pressure, TTL and class/path/Yro fields have the `assigned_` prefix. Their historic values remain unchanged. `s_residual` and `x_shedding` are arithmetic consequences of the assigned pressure and capacity; they are not independently executed native dynamics. The C22 labelled-reference occupancy is 14/22 = 7/11; the fraction satisfying the assigned TTL window is 0. The audit reports both separately.

## Historical evidence

`history/v94_placements.csv`, `v94_observable_matrix.csv` and `v94_value_maps.csv` are exact source members from the v94 archive. `history/r24_occurrence_cards.csv`, `r24_transition_packets.csv` and `r24_sadar_declarations.csv` are exact members of the r24 archive's nested `source.zip`. `evidence/historical_sources.json` records archive, nested archive and member hashes.

The derived `declaration_crosswalk.csv` checks all 118 six-field v94 placements and joins the r24 occurrence/transition/SADAR declaration IDs. Those IDs do not establish completed native events. `observable_coverage.csv` retains 118 registry rows and 590 unscored observable-lane rows. `value_map_status.csv` retains ten deferred maps. No unrelated molecular or protein artifacts are needed for this reference profile.

## Generation and verification

From the repository root, deliberately regenerate with:

```sh
python3 -B manual2/scripts/generate_matter1_ledger.py --output-root manual2
```

The optional `--root PATH` supplies another Manual input directory. `--output-root PATH` is mandatory and can point to a disposable destination. The generator validates source binding, exact numeric conservation and historical joins before writing its ten output artifacts.

Verify persisted bytes without altering them:

```sh
python3 -B manual2/scripts/verify_matter1_ledger.py --check-data
python3 -B -m unittest discover -s manual2/tests -p 'test_matter1_data.py' -v
```

The checker has the same optional `--root PATH`; `--check-data` is a compatibility alias for its default read-only operation. Unknown flags fail. It checks the canonical ledger, generated longtable, historical joins/coverage and all three byte-identical convenience mirrors in `manual2/data/`: ledger, enclosure summary and audit report. Corruption fails without rewriting any input or output. The audit PASS covers reference integrity and conditional arithmetic. Its seven native evidence lanes remain explicitly `not_executed`.
