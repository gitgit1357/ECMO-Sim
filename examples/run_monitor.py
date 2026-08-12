from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from neocirculation import (
    TARGETS,
    ResultTelemetryAdapter,
    RollingTelemetryAverager,
    build_normal_term_neonate,
)
from neocirculation.demo_monitor import DetachableNeonatalMonitor


model = build_normal_term_neonate()
# A longer result allows the temporary monitor to replay continuously enough
# for visual inspection. The engine itself remains completely headless.
result = model.simulate(duration_s=60.0, sample_hz=100.0)
adapter = ResultTelemetryAdapter(result, TARGETS.heart_rate_bpm)
smoothed = RollingTelemetryAverager(adapter.frames(), window_seconds=15)
DetachableNeonatalMonitor(smoothed.frames(), playback_speed=1.0).run()
