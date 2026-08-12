from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from bench_fixtures.cannulas import load_medtronic_life_support_mini
from bench_fixtures.cannula_overlay import format_cannula_overlay, overlay_cannula_hydraulics
from neocirculation.va_ecmo_bench import run_closed_loop_va_ecmo_bench

circulation = run_closed_loop_va_ecmo_bench(flow_steps_ml_kg_min=(0, 50, 100, 150, 200))
points = overlay_cannula_hydraulics(circulation, load_medtronic_life_support_mini())
print(format_cannula_overlay(points))
