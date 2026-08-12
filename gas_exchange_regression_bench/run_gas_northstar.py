from pathlib import Path
import json, sys, hashlib
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from neolung import default_gas_bench_cases, run_gas_case

rows=[]
for c in default_gas_bench_cases():
    r=run_gas_case(c)
    rows.append({
        'id': c.name,
        'alveolar_ventilation_ml_min': round(r.alveolar_ventilation_ml_min,3),
        'alveolar_po2_mmhg': round(r.alveolar_po2_mmhg,3),
        'arterial_po2_mmhg': round(r.arterial_po2_mmhg,3),
        'arterial_pco2_mmhg': round(r.arterial_pco2_mmhg,3),
        'arterial_saturation_pct': round(r.arterial_saturation_pct,4),
    })
payload={'schema':'gas-northstar-v1','cases':rows}
payload['manifest_sha256']=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
out=ROOT/'gas_exchange_regression_bench'/'current_gas_northstar.json'
out.write_text(json.dumps(payload,indent=2))
print(out)
