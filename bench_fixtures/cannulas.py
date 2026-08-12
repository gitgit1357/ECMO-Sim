from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class CannulaCurve:
    """Power-law interpolation of manufacturer bench points.

    Uses |dP| = k * Q**n, fitted through the manufacturer's -40 and +100 mmHg
    water-test points. This is deliberately an external test approximation.
    """

    k: float
    n: float

    @classmethod
    def from_two_points(
        cls,
        flow1_l_min: float,
        dp1_mmhg: float,
        flow2_l_min: float,
        dp2_mmhg: float,
    ) -> "CannulaCurve":
        if min(flow1_l_min, flow2_l_min, dp1_mmhg, dp2_mmhg) <= 0:
            raise ValueError("Flows and pressure-loss magnitudes must be positive")
        n = math.log(dp2_mmhg / dp1_mmhg) / math.log(flow2_l_min / flow1_l_min)
        k = dp1_mmhg / (flow1_l_min ** n)
        return cls(k=k, n=n)

    def pressure_loss_mmhg(self, flow_l_min: float) -> float:
        q = max(float(flow_l_min), 0.0)
        return self.k * (q ** self.n)

    def flow_l_min(self, pressure_loss_mmhg: float) -> float:
        dp = max(float(pressure_loss_mmhg), 0.0)
        return (dp / self.k) ** (1.0 / self.n) if dp > 0 else 0.0


@dataclass(frozen=True)
class CannulaRecord:
    manufacturer: str
    family: str
    size_fr: int
    diameter_mm: float
    tip_length_cm: float
    connector_in: float
    return_model: str
    drainage_model: str
    flow_l_min_at_plus_100_mmhg: float
    flow_l_min_at_minus_40_mmhg: float
    curve: CannulaCurve
    source_url: str
    source_description: str
    clinical_caveat: str

    def estimated_pressure_loss_mmhg(self, flow_l_min: float) -> float:
        return self.curve.pressure_loss_mmhg(flow_l_min)

    def estimated_flow_at_pressure_loss_l_min(self, dp_mmhg: float) -> float:
        return self.curve.flow_l_min(dp_mmhg)


def load_medtronic_life_support_mini() -> List[CannulaRecord]:
    path = Path(__file__).with_name("manufacturer_data") / "medtronic_bio_medicus_life_support_mini.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    records: List[CannulaRecord] = []
    for item in raw["records"]:
        curve = CannulaCurve.from_two_points(
            item["flow_l_min_at_minus_40_mmhg"], 40.0,
            item["flow_l_min_at_plus_100_mmhg"], 100.0,
        )
        records.append(
            CannulaRecord(
                manufacturer=raw["manufacturer"],
                family=raw["family"],
                size_fr=item["size_fr"],
                diameter_mm=item["diameter_mm"],
                tip_length_cm=item["tip_length_cm"],
                connector_in=item["connector_in"],
                return_model=item["return_model"],
                drainage_model=item["drainage_model"],
                flow_l_min_at_plus_100_mmhg=item["flow_l_min_at_plus_100_mmhg"],
                flow_l_min_at_minus_40_mmhg=item["flow_l_min_at_minus_40_mmhg"],
                curve=curve,
                source_url=raw["source_url"],
                source_description=raw["source_description"],
                clinical_caveat=raw["clinical_caveat"],
            )
        )
    return records


def format_cannula_library(records: Iterable[CannulaRecord]) -> str:
    lines = [
        "EXTERNAL CANNULA BENCH LIBRARY — NOT PART OF PATIENT PHYSIOLOGY",
        "Medtronic Bio-Medicus Life Support Mini manufacturer bench data",
        "",
        "Fr  Return model   Drain model    Q@+100  Q@-40   Fit n   dP@0.5  dP@1.0",
        "                              (L/min) (L/min)         (mmHg)  (mmHg)",
    ]
    for r in records:
        lines.append(
            f"{r.size_fr:2d}  {r.return_model:12s} {r.drainage_model:12s} "
            f"{r.flow_l_min_at_plus_100_mmhg:7.2f} {r.flow_l_min_at_minus_40_mmhg:7.2f} "
            f"{r.curve.n:6.2f} {r.estimated_pressure_loss_mmhg(0.5):8.1f} {r.estimated_pressure_loss_mmhg(1.0):8.1f}"
        )
    return "\n".join(lines)
