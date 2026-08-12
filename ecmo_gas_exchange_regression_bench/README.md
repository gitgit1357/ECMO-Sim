# ECMO Oxygenator Gas Exchange NorthStar Regression Bench v1

Independent of all hydraulics-only and wiring-stage NorthStar benches.
Covers the oxygenator gas exchange model (`neoecmo.oxygenator_gas_exchange`)
— O2 saturation transfer and CO2 clearance, separate from the
hydraulics-only oxygenator module.

Device: Eurosets AMG PMP Infant (confirmed as the correct device family,
chat 2026-07-26 — the ECMO-cleared Eurosets pediatric/infant line,
indicated for infants up to 20 kg). min_flow_ml_min (250 mL/min, minimum
flow to prevent clot formation) is REAL, confirmed directly. rated_flow_ml_min
and the transfer-efficiency shape are PROVISIONAL, grounded in a comparable
device (Maquet Quadrox-i Neonatal: rated 1.5 L/min, ~90 mL O2/min and ~73
mL CO2/min transfer at that flow) pending the AMG PMP Infant's own specs.

Sweep-gas practice (pure O2 vs. FdO2-titrated blend) is not yet confirmed;
fdo2 defaults to 1.0 (pure O2) as the more common assumption.

Frozen cases sweep blood flow at a fixed inlet condition, sweep-gas
setting, and FdO2.

This bench freezes the *behavior* of the current provisional model; it
does not assert the absolute numbers are clinically validated beyond the
min_flow_ml_min value. Replacing rated_flow_ml_min or the efficiency
shape with real AMG PMP Infant data will require a deliberate re-accept
of this snapshot.
