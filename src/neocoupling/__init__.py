from .core import CouplingConfig, CoupledResult, run_coupled_neonate

__all__ = ["CouplingConfig","CoupledResult","run_coupled_neonate"]

# External equipment benches are optional by design. Core cardiopulmonary
# coupling must remain importable even when bench_fixtures is absent.
try:
    from .equipment_bench import CombinedEquipmentPoint, run_combined_equipment_bench, format_combined_equipment_report
    __all__ += ["CombinedEquipmentPoint","run_combined_equipment_bench","format_combined_equipment_report"]
except ModuleNotFoundError as exc:
    if exc.name != "bench_fixtures":
        raise
