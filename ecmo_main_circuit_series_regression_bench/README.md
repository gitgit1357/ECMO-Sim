# ECMO Main Circuit Series NorthStar Regression Bench v1

Independent of the standalone pump, oxygenator, fixed shunt, bridge,
cannula, cardiovascular, lung, kidney, and coupling NorthStar benches.
Covers only Wiring Stage 1: pump + oxygenator composed in series
(`neoecmo.main_circuit_series`) — the first step of tying the standalone
branch modules together into an actual solvable circuit.

No fixed shunt or bridge branch is included yet (those are separate later
wiring stages, added one at a time), and flow is bounded to non-negative
in this stage since the oxygenator is a one-way device in real use.

Frozen cases sweep RPM at two oxygenator states (clean, clotted), using
the grounded pre-pump/return tubing resistances from tubing_geometry.py.

Both the pump curve and the oxygenator resistance model remain explicitly
provisional (see pump.py and oxygenator.py docstrings). This bench freezes
the *behavior* of the current provisional models composed together; it
does not assert the absolute numbers are clinically validated. Replacing
either model requires a deliberate re-accept of this snapshot too, since
this stage's output depends on both.
