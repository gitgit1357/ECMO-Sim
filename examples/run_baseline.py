from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import json

from neocirculation import TARGETS, build_normal_term_neonate, calculate_baseline_metrics


model = build_normal_term_neonate()
result = model.simulate(duration_s=30.0, sample_hz=200.0)
metrics = calculate_baseline_metrics(result, TARGETS.heart_rate_bpm)
print(json.dumps(metrics.as_dict(), indent=2))
