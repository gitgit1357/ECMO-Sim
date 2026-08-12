from pathlib import Path
import sys,json
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/'src',ROOT):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from neocoupling.equipment_bench import run_combined_equipment_bench
out={'schema_version':'1.0','bench_id':'combined-heart-lung-equipment-northstar-v1','points':[asdict(x) for x in run_combined_equipment_bench()]}
path=ROOT/'combined_equipment_regression_bench'/'current_combined_northstar.json'
path.write_text(json.dumps(out,indent=2))
print(path)
