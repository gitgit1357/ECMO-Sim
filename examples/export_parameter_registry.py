from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from neocirculation import BASELINE_PARAMETER_REGISTRY

out = ROOT / "baseline_parameter_registry_v0.3.0.json"
out.write_text(json.dumps(BASELINE_PARAMETER_REGISTRY.as_dict(), indent=2), encoding="utf-8")
print(out)
