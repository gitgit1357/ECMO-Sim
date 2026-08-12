from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neolung.engineering import default_bench_cases, run_case

print("Standalone lung mechanics bench")
print(f"{'case':24s} {'VT ml/kg':>10s} {'MV ml/min':>10s} {'Ppl min':>9s} {'EELV ml':>9s}")
for case in default_bench_cases():
    m = run_case(case)
    print(f"{case.name:24s} {m.tidal_volume_ml_per_kg:10.2f} {m.minute_ventilation_ml_min:10.0f} {m.min_pleural_pressure_cmh2o:9.2f} {m.end_expiratory_volume_ml:9.1f}")
