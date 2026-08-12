from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from neocirculation import run_perturbation_suite

reports = run_perturbation_suite()
print(json.dumps({name: report.metrics.as_dict() for name, report in reports.items()}, indent=2))
