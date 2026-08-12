# START HERE — Fix Map v6 Phase 11 Audit
Date: 2026-08-11
Status: PHASE 11 AUDIT COMPLETE — STOP / RESCOPE

The project owner opened the next sequential item after Phase 10b. Because differential hypoxemia requires a new regional arterial-distribution/mixing-point mechanism, Fix Map v6's audit-before-authority rule was applied before physiology implementation.

## Result
Do **not** add generic Harlequin/North-South physiology to the current neonatal carotid-return model.

The current simulator lacks arterial return-topology state, an aortic mixing-zone state, and separate proximal/right-radial versus distal arterial compartments. ELSO's classic differential-hypoxemia description located in the supplied Red Book is topology-dependent, centered on peripheral femoral VA ECMO with competing antegrade native and retrograde extracorporeal flows.

## Recommended next phase
Phase 11a — topology-aware regional-perfusion foundation audit/design.

No `src/` physiology code changed in this audit package.
No CBC12 was fabricated.
The blocked capability remains blocked, now with the reason sharpened.

## Verification correction
A post-delivery independent check correctly identified two closure issues:
1. the audit regression count is **68 passed, 0 failed** for the reproducible Phase 5c/5d/5e/5f/5g capability/release/validation surface, not 73/73;
2. the stale historical PEEP-to-ECMO drainage capability row has now been corrected in `.md`, `.csv`, and `.json` and marked as a superseded duplicate of the authoritative CBC07/Phase 10a row.

See `PHASE11_AUDIT_VERIFICATION_CORRECTION_2026-08-11.md`.

