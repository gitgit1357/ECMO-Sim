# ECMO Console NorthStar Regression Bench v1

Independent of all prior standalone, wiring-stage, gas-exchange, and CDI
NorthStar benches. Covers the consolidated control surface
(`neoecmo.ecmo_console`) — the single entry point that applies every
real learner-adjustable control (RPM, bridge target flow, shunt
configuration, FdO2, sweep gas flow) and returns the complete solved
monitor/CDI state in one call.

This bench is an integration check, not a new physics model: it freezes
representative console states across a handful of realistic control
combinations (bridge closed / bridge titrated to a target flow / CKRT
configured / low FdO2), each exercising the full underlying stack
(pump -> oxygenator -> shunt/bridge/cannula junction -> gas exchange ->
CDI) through the console's single interface.

Real patient physiology is still not coupled in — native_venous_saturation
and native_venous_paco2_mmhg remain fixed external inputs here, not
computed values.

Replacing any underlying provisional model (pump curve, oxygenator
transfer curve, cannula defaults, etc.) will change this snapshot too,
since the console composes all of them — a deliberate re-accept is
expected whenever any of those change, not a silent overwrite.
