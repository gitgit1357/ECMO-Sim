# Coupling Stage 1 Release

This build adds the validated interface contract required before the ECMO circuit and unified neonatal patient are allowed to affect one another.

Implemented:
- Patient-owned boundary state
- ECMO-owned support-delivery state
- Translation adapters
- Flow-conservation validation
- Five focused contract tests

Deliberately not implemented yet:
- ECMO effect on MAP, oxygenation, CO2, kidneys, or native cardiac output
- Patient pressure/volume feedback into circuit flow
- Closed-loop time stepping

Next stage:
- Add a true patient venous blood-state output, then apply one-way ECMO flow and gas support through a separate coordinator.
