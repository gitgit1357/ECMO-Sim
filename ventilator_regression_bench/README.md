# Ventilator NorthStar v1

Frozen external-fixture regression bench for the standalone neonatal lung.

The ventilator is **not** part of `neolung`. It applies only a generic airway-opening pressure input.
The frozen matrix challenges pressure-controlled ventilation across drive pressure, PEEP, rate,
inspiratory time, reduced compliance, and increased airway resistance.

Run:

```powershell
py .\examples\run_ventilator_bench.py
py .\ventilator_regression_bench\compare_ventilator_northstar.py
```

Do not overwrite the accepted snapshot merely to make a new module pass. A changed reference requires an explicit versioned acceptance decision.
