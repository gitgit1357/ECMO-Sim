from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from neolung.engineering import default_bench_cases, run_case

out={"schema":"lung-northstar-v1","cases":{}}
for case in default_bench_cases():
    m=run_case(case)
    out["cases"][case.name]={
        "tidal_volume_ml_per_kg":m.tidal_volume_ml_per_kg,
        "minute_ventilation_ml_min":m.minute_ventilation_ml_min,
        "min_pleural_pressure_cmh2o":m.min_pleural_pressure_cmh2o,
        "end_expiratory_volume_ml":m.end_expiratory_volume_ml,
    }
path=ROOT/'lung_regression_bench'/'current_lung_northstar.json'
path.write_text(json.dumps(out,indent=2)+"\n")
print(path)
