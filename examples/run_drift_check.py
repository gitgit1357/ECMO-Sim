from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from neocirculation import build_normal_term_neonate, calculate_drift

model = build_normal_term_neonate()
result = model.simulate(duration_s=600.0, sample_hz=20.0)
print(json.dumps(calculate_drift(result), indent=2))
