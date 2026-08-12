from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/'ventilator_regression_bench'/'run_ventilator_northstar.py')], check=True)
accepted=json.loads((ROOT/'ventilator_regression_bench'/'accepted_ventilator_northstar_v1.json').read_text())
current=json.loads((ROOT/'ventilator_regression_bench'/'current_ventilator_northstar.json').read_text())
if accepted['manifest_sha256'] != current['manifest_sha256']:
    raise SystemExit('FAIL: Ventilator NorthStar manifest changed')
# Tight enough to detect regression but tolerant of insignificant floating point variation.
tols={'tidal_volume_ml':0.15,'tidal_volume_ml_per_kg':0.05,'minute_ventilation_ml_min':8.0,'mean_airway_pressure_cmh2o':0.05,'end_expiratory_volume_ml':0.2,'intrinsic_peep_proxy_cmh2o':0.08}
fail=[]
for a,c in zip(accepted['cases'],current['cases']):
    if a['name']!=c['name']: fail.append((a['name'],'case_name',a['name'],c['name'])); continue
    for k,tol in tols.items():
        if abs(a[k]-c[k])>tol: fail.append((a['name'],k,a[k],c[k]))
if fail:
    print('Ventilator NorthStar v1: FAIL')
    for x in fail: print(x)
    raise SystemExit(1)
print('Ventilator NorthStar v1: PASS — 0 differences outside tolerance')
