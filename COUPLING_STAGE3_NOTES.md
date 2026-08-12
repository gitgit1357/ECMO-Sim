# ECMO–Patient Coupling Stage 3

Stage 3 adds a live hydraulic boundary between the neonatal patient and the ECMO circuit.

## Implemented

- Patient MAP is used as arterial return afterload.
- Patient CVP is used as the drainage-side pressure source.
- At unchanged RPM, increased MAP reduces patient-directed ECMO flow.
- At unchanged RPM and MAP, increased CVP improves P1 and generally increases patient-directed flow.
- Shunt and bridge flows remain circuit-owned recirculation branches and are not counted as patient perfusion.
- Standalone circuit behavior remains available when live patient pressures are omitted.
- The patient physiology modules remain independent of `neoecmo`; blood mixing was moved to the neutral `neoblood` utility package.

## Deliberately not yet implemented

- ECMO drainage reducing native cardiac preload/output.
- Blood-volume-dependent drainage collapse or chatter.
- Iterative patient/circuit convergence across time.
- Dynamic pressure and flow transitions.

These belong to Stage 4 and later.
