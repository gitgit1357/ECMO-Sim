# Combined Equipment NorthStar v1

Frozen cross-system regression bench for the coupled neonatal heart-lung patient under simultaneous external pressure-control ventilation and VA support.

This bench is intended to be rerun **unchanged after every new patient-system integration**. Any accepted change to the reference snapshot requires an explicit reason and a new version.

Device ownership remains external:
- ventilator fixture does not belong to `neolung`
- VA pump/circuit assumptions do not belong to `neocirculation`
- idealized oxygenator return saturation is a bench-only mixing assumption

Run:
`py .\combined_equipment_regression_bench\compare_combined_northstar.py`
