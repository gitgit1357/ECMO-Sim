from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/'src', ROOT):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from neocoupling.equipment_bench import run_combined_equipment_bench, format_combined_equipment_report
print(format_combined_equipment_report(run_combined_equipment_bench()))
