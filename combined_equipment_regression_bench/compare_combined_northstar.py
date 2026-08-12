from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/'src',ROOT):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from dataclasses import asdict
from neocoupling.equipment_bench import run_combined_equipment_bench
a=json.loads((ROOT/'combined_equipment_regression_bench'/'accepted_combined_northstar_v1.json').read_text())
b={'schema_version':'1.0','bench_id':'combined-heart-lung-equipment-northstar-v1','points':[asdict(x) for x in run_combined_equipment_bench()]}
(ROOT/'combined_equipment_regression_bench'/'current_combined_northstar.json').write_text(json.dumps(b,indent=2))
fail=[]
for i,(x,y) in enumerate(zip(a['points'],b['points'])):
    for k,v in x.items():
        if k=='scenario_id': continue
        tol=1.0
        if 'conservation' in k: tol=1e-4
        elif 'fraction' in k: tol=0.03
        elif 'output' in k or 'flow_ml_min' in k or 'aortic_inflow' in k: tol=20.0
        elif k in ('pao2_mmhg','paco2_mmhg','effective_systemic_sao2_pct'): tol=3.0
        elif 'tidal_volume' in k: tol=0.25
        if abs(float(v)-float(y[k]))>tol: fail.append((i,k,v,y[k],tol))
print(f"Combined Equipment NorthStar v1: {'PASS' if not fail else 'FAIL'} — {len(fail)} differences outside tolerance")
if fail: raise SystemExit(1)
