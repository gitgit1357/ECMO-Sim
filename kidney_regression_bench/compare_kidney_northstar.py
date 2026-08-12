import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=json.loads((ROOT/"kidney_regression_bench"/"accepted_kidney_northstar_v1.json").read_text())
c=json.loads((ROOT/"kidney_regression_bench"/"current_kidney_northstar.json").read_text())
print("Kidney Integration NorthStar v1: PASS — snapshots identical" if a==c else "Kidney Integration NorthStar v1: FAIL — current snapshot differs")
raise SystemExit(0 if a==c else 1)
