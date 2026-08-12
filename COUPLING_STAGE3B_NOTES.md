# Coupling Stage 3B — Closed-loop VA-ECMO MAP response

- Added a separate reduced-order VA pressure-coupling solver.
- Patient MAP remains patient-owned and supplies circuit return afterload.
- True patient-directed arterial ECMO flow raises settled patient MAP.
- The raised MAP feeds back into the circuit and partially limits additional flow.
- Shunt and bridge flow are excluded from MAP support.
- Estimated pulse pressure may decrease while mean arterial pressure rises.
- The pressure-response gain is isolated and explicitly provisional for later clinical tuning.
- Existing standalone ECMO behavior remains available.

Validation:
- 6 new closed-loop MAP tests.
- 24 focused Stage 3/3B tests passed.
- 159 broader ECMO, gas, CDI, GUI-model, and coupling tests passed.
