# Current AOD producer dependency

These unmodified scientific sources come from AOD commit `dc1a434c8fc2b7b958e44d7da63277c7856a8d67`, tree `7a120ca70c571074a720f99919a6a5776d355075`. The independently pinned `binding.json` authenticates each exported module, contract and source file. Task-readiness receipts are not scientific inputs.

`current/` preserves upstream relative paths so the comparison API can authenticate its own code and contracts. Load with `matter1_aod_producer.load(root)`. Its namespace supplies `native`, `mapping`, `temporal`, `metrology`, `experimental`, `cells`, and `binding`. For the reduction fixture's lazy cell import, use `with api.activate():`. The loader restores existing import aliases and verifies file bytes on every load, including cached module loads.

The export supports native observation, quantity propagation and comparison, including primary H/Cs source authentication. Physical clock correspondence, atomic transitions and lifetimes require application-owned laws and uncertainty evidence; missing terms stay unknown. Finite reduction results retain their declared window and response scope. The export omits unrelated historical fixture repositories and generic command-line runners. Adjacent `aod_m3` and `aod_m3_metrology` preserve the original historical dependencies.
