from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(ROOT/'lung_regression_bench'/'run_lung_northstar.py')],check=True)
a=json.loads((ROOT/'lung_regression_bench'/'accepted_lung_northstar_v1.json').read_text())
c=json.loads((ROOT/'lung_regression_bench'/'current_lung_northstar.json').read_text())
tols={"tidal_volume_ml_per_kg":0.08,"minute_ventilation_ml_min":12.0,"min_pleural_pressure_cmh2o":0.05,"end_expiratory_volume_ml":0.5}
fail=[]
for name,av in a['cases'].items():
    for key,v in av.items():
        d=abs(c['cases'][name][key]-v)
        if d>tols[key]: fail.append((name,key,v,c['cases'][name][key],d,tols[key]))
if fail:
    print('Lung NorthStar differences outside tolerance:')
    for x in fail: print(x)
    raise SystemExit(1)
print('Lung NorthStar v1: PASS — 0 differences outside tolerance')
