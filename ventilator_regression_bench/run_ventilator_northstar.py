from pathlib import Path
import json, sys, hashlib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
from bench_fixtures.ventilator_bench import run_ventilator_case, ventilator_northstar_matrix

rows=[]
for name, vent, changes in ventilator_northstar_matrix():
    m=run_ventilator_case(name, vent, lung_changes=changes)
    rows.append(m.__dict__)
manifest='Ventilator NorthStar v1|'+','.join(r['name'] for r in rows)
out={'schema_version':'ventilator-northstar-v1','manifest_sha256':hashlib.sha256(manifest.encode()).hexdigest(),'cases':rows}
path=ROOT/'ventilator_regression_bench'/'current_ventilator_northstar.json'
path.write_text(json.dumps(out,indent=2))
print(path)
