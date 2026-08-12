from __future__ import annotations
from .core import CirculationModel
VENOUS_RESERVOIR_NODES=("SVC","IVC","UPPER_VEINS","LOWER_VEINS")
def build_with_blood_volume_delta(base: CirculationModel, delta_ml: float) -> CirculationModel:
    initial={n:float(base.initial_volumes_ml[base.index[n]]) for n in base.node_order}
    if abs(delta_ml)<1e-12:
        return CirculationModel(list(base.nodes.values()),list(base.edges),initial)
    total=sum(initial[n] for n in VENOUS_RESERVOIR_NODES)
    if delta_ml<0:
        delta_ml=max(delta_ml,-sum(initial[n]*0.9 for n in VENOUS_RESERVOIR_NODES))
    for n in VENOUS_RESERVOIR_NODES:
        initial[n]=max(0.1,initial[n]+delta_ml*(initial[n]/total))
    return CirculationModel(list(base.nodes.values()),list(base.edges),initial)
