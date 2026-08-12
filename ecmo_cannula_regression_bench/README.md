# ECMO Cannula NorthStar Regression Bench v1

Independent of the pump, oxygenator, fixed shunt, bridge, cardiovascular,
lung, kidney, and coupling NorthStar benches. Covers only the Stage 5
standalone cannula hydraulics (`neoecmo.cannula`) for the return (8Fr)
and drain (10Fr) cannulae, per the clinical author's measured French
sizes (2026-07-25).

Unlike the tubing/shunt/bridge modules, this is deliberately an EMPIRICAL
quadratic (orifice-type) model, not Hagen-Poiseuille — see `cannula.py`
docstring for why (side holes, tip geometry, high local velocity make
straight-pipe laminar flow inapplicable) and for the literature source of
each default coefficient.

Frozen cases sweep flow through each cannula independently. No sensor,
gas exchange, patient-coupling, or circuit-level flow-distribution
coordinator logic is included yet.

IMPORTANT CAVEAT carried over from `cannula.py`: the drain (10Fr) default
reuses a single-end-hole ARTERIAL cannula bench figure as a placeholder
for what should be a multi-side-hole VENOUS cannula. It is very likely an
overestimate of true drain resistance. If/when real manufacturer or bench
data for the actual drain cannula becomes available, this snapshot must
be deliberately re-accepted, not silently overwritten.
