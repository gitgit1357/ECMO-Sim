import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from neocirculation.failure import run_failure_suite, run_recovery_sequence

profiles = run_failure_suite()
out = {}
for name, p in profiles.items():
    out[name] = {
        "map_mmhg": p.metrics.mean_aortic_mmhg,
        "cardiac_output_ml_min": p.metrics.native_output_ml_min,
        "ra_mmhg": p.metrics.mean_ra_mmhg,
        "la_mmhg": p.metrics.mean_la_mmhg,
        "mean_pa_mmhg": p.metrics.mean_pa_mmhg,
        "lv_peak_volume_ml": p.lv_peak_volume_ml,
        "rv_peak_volume_ml": p.rv_peak_volume_ml,
    }
print(json.dumps(out, indent=2))
print("\nRecovery sequences:")
for side in ("lv", "rv"):
    seq = run_recovery_sequence(side)
    print(side.upper(), {k: {"MAP": round(v.mean_aortic_mmhg, 1), "CO": round(v.native_output_ml_min, 0)} for k, v in seq.items()})
