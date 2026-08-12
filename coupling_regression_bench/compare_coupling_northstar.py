from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
subprocess.run([sys.executable, str(HERE/'run_coupling_northstar.py')], check=True)
a=json.loads((HERE/'accepted_coupling_northstar_v1.json').read_text())
b=json.loads((HERE/'current_coupling_northstar.json').read_text())
tols={
 'map_mmhg':1.0,'native_output_ml_min':25.0,'pulmonary_flow_ml_min':25.0,
 'mean_pa_mmhg':1.0,'pvr_multiplier':0.08,'pao2_mmhg':3.0,'paco2_mmhg':3.0,
 'sao2_pct':2.0,'mixed_venous_sat_pct':3.0,'oxygen_delivery_ml_min':8.0,
}
diffs=[]
for scenario, vals in a['scenarios'].items():
    for k, expected in vals.items():
        actual=b['scenarios'][scenario][k]
        if abs(actual-expected)>tols[k]: diffs.append((scenario,k,expected,actual,tols[k]))
if diffs:
    print('Cardiopulmonary Coupling NorthStar v1: FAIL')
    for d in diffs: print(d)
    raise SystemExit(1)
print('Cardiopulmonary Coupling NorthStar v1: PASS — 0 differences outside tolerance')
