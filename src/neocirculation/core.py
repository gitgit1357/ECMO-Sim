from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Mapping, Optional
import math

import numpy as np
from scipy.integrate import solve_ivp


PressureFn = Callable[[float, float], float]


@dataclass(frozen=True)
class NodeSpec:
    """A volume-containing anatomical or lumped hydraulic compartment."""

    name: str
    kind: str
    unstressed_volume_ml: float
    compliance_ml_per_mmhg: Optional[float] = None
    external_pressure_mmhg: float = 0.0
    pressure_fn: Optional[PressureFn] = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def pressure(self, t_s: float, volume_ml: float) -> float:
        if self.pressure_fn is not None:
            return float(self.pressure_fn(t_s, volume_ml))
        if self.compliance_ml_per_mmhg is None or self.compliance_ml_per_mmhg <= 0:
            raise ValueError(f"Passive node {self.name!r} requires positive compliance")
        return self.external_pressure_mmhg + (
            volume_ml - self.unstressed_volume_ml
        ) / self.compliance_ml_per_mmhg


@dataclass(frozen=True)
class EdgeSpec:
    """A hydraulic connection between two nodes."""

    name: str
    source: str
    target: str
    resistance_mmhg_s_per_ml: float
    valve: bool = False
    reverse_resistance_mmhg_s_per_ml: Optional[float] = None
    source_resistance_mmhg_s_per_ml: float = 0.0
    enabled: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)

    def flow(self, source_pressure: float, target_pressure: float) -> float:
        if not self.enabled:
            return 0.0
        delta = source_pressure - target_pressure
        if self.valve and delta <= 0:
            if self.reverse_resistance_mmhg_s_per_ml is None:
                return 0.0
            return delta / self.reverse_resistance_mmhg_s_per_ml
        total_resistance = self.resistance_mmhg_s_per_ml + self.source_resistance_mmhg_s_per_ml
        return delta / total_resistance


@dataclass
class SimulationResult:
    time_s: np.ndarray
    volumes_ml: np.ndarray
    node_order: List[str]
    pressure_mmhg: np.ndarray
    edge_flows_ml_s: Dict[str, np.ndarray]

    def node_series(self, node_name: str) -> np.ndarray:
        return self.volumes_ml[self.node_order.index(node_name)]

    def pressure_series(self, node_name: str) -> np.ndarray:
        return self.pressure_mmhg[self.node_order.index(node_name)]


class CirculationModel:
    """
    Closed-loop, volume-conserving circulation graph.

    State variables are compartment volumes. Pressures are derived from volume,
    compliance, external pressure, or chamber elastance. Edge flow is derived
    from pressure gradient and hydraulic resistance.
    """

    def __init__(
        self,
        nodes: Iterable[NodeSpec],
        edges: Iterable[EdgeSpec],
        initial_volumes_ml: Mapping[str, float],
    ) -> None:
        self.nodes: Dict[str, NodeSpec] = {n.name: n for n in nodes}
        self.edges: List[EdgeSpec] = list(edges)
        if len(self.nodes) == 0:
            raise ValueError("At least one node is required")
        self.node_order = list(self.nodes.keys())
        self.index = {name: i for i, name in enumerate(self.node_order)}
        missing = set(self.node_order) - set(initial_volumes_ml)
        extra = set(initial_volumes_ml) - set(self.node_order)
        if missing or extra:
            raise ValueError(f"Initial volume mismatch. Missing={missing}, extra={extra}")
        self.initial_volumes_ml = np.array(
            [float(initial_volumes_ml[n]) for n in self.node_order], dtype=float
        )
        if np.any(self.initial_volumes_ml <= 0):
            raise ValueError("All starting compartment volumes must be positive")
        for edge in self.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise ValueError(f"Edge {edge.name!r} references unknown node")
            if edge.resistance_mmhg_s_per_ml <= 0:
                raise ValueError(f"Edge {edge.name!r} requires positive resistance")
            if edge.source_resistance_mmhg_s_per_ml < 0:
                raise ValueError(f"Edge {edge.name!r} source resistance cannot be negative")

    @property
    def total_blood_volume_ml(self) -> float:
        return float(np.sum(self.initial_volumes_ml))

    def pressures(self, t_s: float, volumes_ml: np.ndarray) -> np.ndarray:
        return np.array(
            [
                self.nodes[name].pressure(t_s, max(float(volumes_ml[i]), 1e-6))
                for i, name in enumerate(self.node_order)
            ],
            dtype=float,
        )

    def edge_flows(self, t_s: float, volumes_ml: np.ndarray) -> Dict[str, float]:
        pressures = self.pressures(t_s, volumes_ml)
        out: Dict[str, float] = {}
        for edge in self.edges:
            p_src = pressures[self.index[edge.source]]
            p_dst = pressures[self.index[edge.target]]
            out[edge.name] = edge.flow(p_src, p_dst)
        return out

    def derivative(self, t_s: float, volumes_ml: np.ndarray) -> np.ndarray:
        pressures = self.pressures(t_s, volumes_ml)
        dv = np.zeros_like(volumes_ml)
        for edge in self.edges:
            q = edge.flow(
                pressures[self.index[edge.source]],
                pressures[self.index[edge.target]],
            )
            src_i = self.index[edge.source]
            dst_i = self.index[edge.target]
            # Soft limiter prevents a numerical solver from pulling a tiny node negative.
            if q > 0 and volumes_ml[src_i] < 0.02:
                q *= max(volumes_ml[src_i], 0.0) / 0.02
            elif q < 0 and volumes_ml[dst_i] < 0.02:
                q *= max(volumes_ml[dst_i], 0.0) / 0.02
            dv[src_i] -= q
            dv[dst_i] += q
        return dv

    def simulate(
        self,
        duration_s: float,
        sample_hz: float = 200.0,
        method: str = "LSODA",
        rtol: float = 1e-7,
        atol: float = 1e-9,
    ) -> SimulationResult:
        if duration_s <= 0 or sample_hz <= 0:
            raise ValueError("duration_s and sample_hz must be positive")
        samples = int(round(duration_s * sample_hz)) + 1
        t_eval = np.linspace(0.0, duration_s, samples)
        solution = solve_ivp(
            self.derivative,
            (0.0, duration_s),
            self.initial_volumes_ml.copy(),
            method=method,
            t_eval=t_eval,
            rtol=rtol,
            atol=atol,
            max_step=min(0.01, 1.0 / sample_hz),
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        pressures = np.column_stack(
            [self.pressures(t, solution.y[:, i]) for i, t in enumerate(solution.t)]
        )
        flows: Dict[str, np.ndarray] = {
            edge.name: np.empty(solution.t.size, dtype=float) for edge in self.edges
        }
        for i, t in enumerate(solution.t):
            instantaneous = self.edge_flows(t, solution.y[:, i])
            for name, value in instantaneous.items():
                flows[name][i] = value
        return SimulationResult(
            time_s=solution.t,
            volumes_ml=solution.y,
            node_order=self.node_order.copy(),
            pressure_mmhg=pressures,
            edge_flows_ml_s=flows,
        )


def periodic_elastance(
    heart_rate_bpm: float,
    e_min: float,
    e_max: float,
    zero_pressure_volume_ml: float,
    activation_offset_fraction: float,
    systolic_fraction: float,
    external_pressure_mmhg: float = 0.0,
    passive_stiffness_k: float = 0.0,
    passive_threshold_ml: float = 0.0,
    passive_scale_ml: float = 1.0,
) -> PressureFn:
    """Return a smooth periodic chamber pressure law using a raised cosine."""

    if heart_rate_bpm <= 0:
        raise ValueError("heart_rate_bpm must be positive")
    if not 0 < systolic_fraction < 1:
        raise ValueError("systolic_fraction must lie between 0 and 1")
    period = 60.0 / heart_rate_bpm

    def activation(t_s: float) -> float:
        phase = ((t_s / period) - activation_offset_fraction) % 1.0
        if phase >= systolic_fraction:
            return 0.0
        # 0 -> 1 -> 0 smoothly over the active interval.
        return 0.5 * (1.0 - math.cos(2.0 * math.pi * phase / systolic_fraction))

    def pressure(t_s: float, volume_ml: float) -> float:
        e_t = e_min + (e_max - e_min) * activation(t_s)
        pressure_value = external_pressure_mmhg + e_t * (volume_ml - zero_pressure_volume_ml)
        if passive_stiffness_k > 0.0 and volume_ml > passive_threshold_ml:
            excess = (volume_ml - passive_threshold_ml) / max(passive_scale_ml, 1e-6)
            pressure_value += passive_stiffness_k * (math.exp(min(excess, 20.0)) - 1.0)
        return pressure_value

    return pressure
