from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench_fixtures.cannulas import format_cannula_library, load_medtronic_life_support_mini

print(format_cannula_library(load_medtronic_life_support_mini()))
