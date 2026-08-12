from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/'gas_exchange_regression_bench'/'run_gas_northstar.py')], check=True, capture_output=True)
a=json.loads((ROOT/'gas_exchange_regression_bench'/'accepted_gas_northstar_v1.json').read_text())
b=json.loads((ROOT/'gas_exchange_regression_bench'/'current_gas_northstar.json').read_text())
fields={'alveolar_ventilation_ml_min':1.0,'alveolar_po2_mmhg':1.0,'arterial_po2_mmhg':1.0,'arterial_pco2_mmhg':0.5,'arterial_saturation_pct':0.25}
diffs=[]
for x,y in zip(a['cases'],b['cases']):
    if x['id']!=y['id']: diffs.append(f"case mismatch {x['id']} != {y['id']}"); continue
    for f,t in fields.items():
        if abs(x[f]-y[f])>t: diffs.append(f"{x['id']} {f}: {x[f]} -> {y[f]}")
print(f"Gas Exchange NorthStar v1: {'PASS' if not diffs else 'FAIL'} — {len(diffs)} differences outside tolerance")
for d in diffs: print(' -',d)
raise SystemExit(1 if diffs else 0)
