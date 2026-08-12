# ECMO–Patient Coupling Stage 2B

Implemented a reduced-order one-way gas-support connection between the solved ECMO circuit and the unified neonatal patient.

## Behavioral rules protected by tests

- More patient-directed ECMO blood flow generally raises mixed patient arterial PO2 and oxygen delivery.
- Sweep gas is the dominant control of CO2 removal at a fixed ECMO blood flow.
- Sweep changes have little direct effect on patient PO2 when FdO2 and blood flow are unchanged.
- ECMO blood flow can have a secondary effect on patient PCO2 because it changes the fraction of treated blood delivered.

## Important distinction

Post-oxygenator PO2 may remain stable or decrease modestly as blood flow rises, while patient arterial PO2 rises because a larger volume of oxygenated blood reaches systemic circulation.

## Current limitation

Native cardiac output is not yet reduced by ECMO drainage. That two-way preload and hydraulic interaction is reserved for a later coupling stage.
