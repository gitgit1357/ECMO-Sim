# ECMO Main Circuit + Shunt NorthStar Regression Bench v1

Independent of the standalone pump, oxygenator, fixed shunt, bridge,
cannula, main-circuit-series, cardiovascular, lung, kidney, and coupling
NorthStar benches. Covers only Wiring Stage 2: the fixed shunt added as a
parallel branch off the Stage 1 backbone
(`neoecmo.main_circuit_with_shunt`).

No bridge branch, real cannulas, or patient physiology are included yet.
The patient-path resistance in this stage is a placeholder grounded in
the clinical author's own real cross-check numbers (bridge closed, ~40%
shunt fraction at ~600 mL/min total flow, 2026-07-25) — see
main_circuit_with_shunt.py for the exact sourcing.

Frozen cases sweep RPM at two shunt clot states (clean, moderately
clotted).

This bench freezes the *behavior* of the current provisional
pump/oxygenator/shunt models plus the placeholder patient-path
resistance, all composed together — it does not assert the absolute
numbers are clinically validated beyond the shunt-fraction cross-check
already performed against real numbers. Replacing the patient-path
placeholder with real composed cannula + patient-vasculature resistance
(a later wiring stage) will require a deliberate re-accept of this
snapshot.
