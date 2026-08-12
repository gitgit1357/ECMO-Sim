# Ready mechanism/fault/observation registration + first scenario family — completion
**Date:** 2026-08-10

## Implemented
- canonical supported-mechanism registry factory
- six authoritative-state observation providers
- learner observation execution + frozen result persistence through scenario snapshot/restore
- supported fault catalog containing only hypovolemia
- production-structured `lowflow-hypovolemia` scenario family member (`lf-01-preload` provenance)
- learner-disclosure hardening against scenario-ID and scenario-engine mechanism leakage

## Validation
Fresh batches: 45 + 21 + 22 + 125 = **213 passed, 0 failed**.

Clinical note: software/system validation here does not validate the scenario's blood-loss or replacement magnitudes. Those remain caller-supplied and require a Clinical Behavior Contract before clinical acceptance.

## Collection/provenance
- exact tree collection: **348 tests**
- capability matrix: **62 unique rows**
- embedded migration backing data retained unchanged: 79 actions / 36 complications / 28 scenario IDs
- deterministic RNG guardrail: only `src/neoscenarios/rng.py` imports `random`
