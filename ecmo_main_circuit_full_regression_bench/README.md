# ECMO Main Circuit Full NorthStar Regression Bench v1

Independent of all prior standalone and wiring-stage NorthStar benches.
Covers Wiring Stage 4 (final circuit-only wiring stage): the complete
standalone circuit with real cannulas replacing the flat patient-path
placeholder (`neoecmo.main_circuit_full`).

Real patient physiology (neocirculation/neopatient) is still not coupled
in — the "patient vasculature" term remains a placeholder, though a much
narrower one than Wiring Stages 2-3 used (see patient_path.py for
derivation).

Frozen cases: RPM sweep at bridge closed (the primary real-numbers
cross-check case), and a bridge clamp-position sweep at fixed RPM
(weaning-trial case).

**Validated against the clinical author's real numbers**: at RPM=3000,
bridge closed, this solves to ~630 mL/min total / ~254 shunt / ~376
patient — within 10% of the reported ~600/240/360 example, using real
cannula physics (not a value tuned to force the match the way the flat
placeholder in Stages 2-3 was). Shunt fraction now increases with RPM
(37.2% at 2000 RPM to 43.1% at 4000 RPM) rather than staying flat, because
the cannula terms are quadratic while the shunt stays linear — this is an
emergent prediction of the model, not something calibrated in.

This bench freezes the *behavior* of the current provisional models
composed together (pump, oxygenator, shunt, bridge, real cannulas, plus
the narrower vasculature-only placeholder). Replacing the vasculature
placeholder with real coupled patient physiology (a future, separate
integration effort outside this package) will require a deliberate
re-accept of this snapshot.
