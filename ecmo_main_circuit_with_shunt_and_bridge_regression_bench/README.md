# ECMO Main Circuit + Shunt + Bridge NorthStar Regression Bench v1

Independent of all prior standalone and wiring-stage NorthStar benches.
Covers only Wiring Stage 3: the bridge added as a second parallel branch
alongside the fixed shunt
(`neoecmo.main_circuit_with_shunt_and_bridge`).

No real cannulas/patient physiology are wired in yet — the patient-path
term remains the Wiring Stage 2 placeholder (see
main_circuit_with_shunt.py for sourcing).

Frozen cases sweep RPM at a fixed bridge clamp position, and separately
sweep clamp position at a fixed RPM to capture the weaning-trial opening
behavior.

FINDING WORTH THE CLINICAL AUTHOR'S OWN CONFIRMATION: even a modest
partial opening of the bridge (e.g. clamp_position=0.1) diverts a large
majority of total flow through the bridge in this model (~84% at
RPM=3000 with the current placeholder patient-path resistance), because
the bridge is a short, wide, low-resistance direct connection compared to
routing through the full patient vascular bed. This is directionally
consistent with real clinical caution around bridge management (why the
bridge is normally kept fully clamped and opened only deliberately for
weaning trials), but the exact magnitude has not been clinically
validated the way the shunt fraction was — treat the specific numbers
here as provisional until checked against real bridge weaning-trial
experience.

This bench freezes the *behavior* of the current provisional models
composed together (pump, oxygenator, shunt, bridge, plus the
patient-path placeholder) — it does not assert the absolute numbers are
clinically validated. Replacing the patient-path placeholder with real
composed cannula + patient-vasculature resistance (a later wiring stage)
will require a deliberate re-accept of this snapshot.
