# Cardiopulmonary Coupling NorthStar v1

This frozen regression bench protects only the **interface behavior** between the independently validated circulation and lung modules.

Scenarios:
- neutral spontaneous coupling
- hypoxia (FiO2 0.12)
- reduced lung compliance
- PEEP 8 cmH2O

The coupling layer is deliberately reduced-order. It exchanges only high-value teaching signals: pulmonary flow, oxygen extraction/mixed venous boundary, pleural-pressure effects, and a simple PVR response to lung volume/hypoxia.

Do not overwrite the accepted snapshot merely to make a new system pass. Any accepted drift must be documented as an intentional model change.
