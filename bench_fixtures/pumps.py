from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CentrifugalPumpFixture:
    """External synthetic centrifugal pump fixture for repeatable bench testing.

    This profile is NOT a manufacturer or clinical device model. It is a frozen,
    replaceable engineering fixture used only to make RPM/head/flow interaction
    deterministic across circulation-engine versions.

    Affinity-law form at reference speed:
        head(Q, rpm) = H0 * (rpm/ref_rpm)^2 - K * Q^2
    where Q is L/min and head is mmHg.
    """

    fixture_id: str
    reference_rpm: float
    shutoff_head_mmhg_at_reference: float
    zero_head_flow_l_min_at_reference: float
    min_rpm: float = 0.0
    max_rpm: float = 6000.0

    @property
    def k_mmhg_per_l_min2(self) -> float:
        q0 = self.zero_head_flow_l_min_at_reference
        return self.shutoff_head_mmhg_at_reference / (q0 * q0)

    def head_mmhg(self, rpm: float, flow_l_min: float) -> float:
        speed = max(min(float(rpm), self.max_rpm), self.min_rpm) / self.reference_rpm
        q = max(float(flow_l_min), 0.0)
        return self.shutoff_head_mmhg_at_reference * speed * speed - self.k_mmhg_per_l_min2 * q * q

    def free_flow_l_min(self, rpm: float) -> float:
        speed = max(min(float(rpm), self.max_rpm), self.min_rpm) / self.reference_rpm
        return self.zero_head_flow_l_min_at_reference * speed


# Frozen synthetic fixture. Changing these values requires a new fixture_id and
# an explicitly accepted regression snapshot.
NORTHSTAR_TEST_PUMP_V1 = CentrifugalPumpFixture(
    fixture_id="northstar-synthetic-centrifugal-v1",
    reference_rpm=4000.0,
    shutoff_head_mmhg_at_reference=320.0,
    zero_head_flow_l_min_at_reference=2.0,
    max_rpm=6000.0,
)
