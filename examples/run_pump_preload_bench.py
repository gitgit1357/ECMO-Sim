from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from neocirculation.pump_bench import format_preload_extraction_report, run_preload_extraction_bench

points = run_preload_extraction_bench()
print(format_preload_extraction_report(points))
