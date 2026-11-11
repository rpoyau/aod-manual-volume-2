# Current M3 producer dependency

These unmodified scientific sources come from AOD commit `8c3149b9d3d924b80b9385b178da4ba2c39175e8`, tree `b2b55cbcf18354828f7b34418ab3fa26d747a927`. `binding.json` authenticates every exported file; `M3_PRODUCER_HANDOFF.json` retains the verified producer receipt. This receipt does not claim completion of consumer work.

`current/` preserves upstream relative paths so the frozen comparison API can authenticate its own code and contracts. Load with `matter1_m3_producer.load(root)`. Its namespace supplies `native`, `mapping`, `temporal`, `metrology`, `experimental`, `cells`, and `binding`. For the reduction fixture's lazy cell import, use `with api.activate():`. The loader restores existing import aliases and verifies file bytes on every load, including cached module loads.

The exported closure supports the consumed native, observation, quantity and comparison APIs, including primary H/Cs source authentication. It omits unrelated historical fixture repositories and generic command-line runners. Flat exports in adjacent `aod_m3` and `aod_m3_metrology` remain the original historical dependencies. No historical result is rewritten by this export.
