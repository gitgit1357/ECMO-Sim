from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PumpHeadCurveParameters:
    """
    Provisional, replaceable affinity-law parameters for the uncoated LivaNova/
    Sorin revOlution centrifugal pump head (catalog 050300000).

    STATUS: PROVISIONAL. The manufacturer's exact neonatal low-flow H-Q surface
    has not been supplied. These coefficients are a literature-typical
    centrifugal-pump affinity-law shape (head falls off with flow at a fixed
    RPM, and scales with RPM^2 / RPM at zero flow), tuned only so that the
    curve's rough operating envelope is plausible for neonatal ECMO
    (order-of-magnitude open-circuit max head near the ~800 mmHg / ~8 L/min
    spec ceiling from the handoff, with typical neonatal points landing in a
    sane RPM/flow/head range). This must be replaced with a real manufacturer
    or bench-derived curve before any value here is treated as clinically
    accurate. Nothing downstream should assume these numbers are validated.

    Model form (affinity-law shutoff-and-droop shape):
        head_mmhg(rpm, flow_ml_min) =
            k_shutoff * (rpm / rpm_ref) ** 2
            - k_droop_linear * (rpm / rpm_ref) * flow_ml_min
            - k_droop_quad * flow_ml_min ** 2
        clipped at 0 (a centrifugal pump head cannot go negative; at high
        enough flow for a given RPM the pump can only add zero head, and
        the circuit resistance/back-pressure would then determine flow
        direction, not the pump).
    """

    rpm_ref: float = 3000.0
    k_shutoff_mmhg: float = 300.0
    k_droop_linear_mmhg_per_ml_min: float = 0.10
    k_droop_quad_mmhg_per_ml_min2: float = 0.00006


DEFAULT_REVOLUTION_CURVE = PumpHeadCurveParameters()


def pump_head_mmhg(
    rpm: float,
    flow_ml_min: float,
    curve: PumpHeadCurveParameters = DEFAULT_REVOLUTION_CURVE,
) -> float:
    """
    Provisional revOlution pump head (P2 - P1) as a function of commanded RPM
    and the flow actually passing through the pump head.

    Governing rules enforced by construction (handoff section 12.3 / 31):
      - RPM never directly assigns flow; this function only returns the head
        the pump head is capable of generating at that RPM/flow point. The
        circuit hydraulics (not this module) intersect this with resistance
        and pressure boundaries to solve for actual flow.
      - rpm <= 0 always yields zero head (a stopped pump generates no head;
        a free-wheeling head is a circuit hydraulics question, not a pump
        curve question).
      - Head is clipped at zero: a centrifugal pump head cannot produce
        negative (suction-side) head from its own rotation.
    """
    if rpm <= 0.0:
        return 0.0
    rpm_ratio = rpm / curve.rpm_ref
    head = (
        curve.k_shutoff_mmhg * rpm_ratio**2
        - curve.k_droop_linear_mmhg_per_ml_min * rpm_ratio * flow_ml_min
        - curve.k_droop_quad_mmhg_per_ml_min2 * flow_ml_min**2
    )
    return max(0.0, float(head))
