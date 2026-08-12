from pathlib import Path
import ast

from neolung import GasBenchCase, run_gas_case


def test_normal_room_air_gas_exchange_is_plausible_for_reference_neonate():
    r = run_gas_case(GasBenchCase("normal", {}, {}))
    assert 30.0 <= r.arterial_pco2_mmhg <= 45.0
    assert 70.0 <= r.arterial_po2_mmhg <= 110.0
    assert 95.0 <= r.arterial_saturation_pct <= 100.0


def test_increasing_fio2_increases_arterial_oxygenation():
    base = run_gas_case(GasBenchCase("base", {}, {}))
    high = run_gas_case(GasBenchCase("high", {}, {"fio2": 0.40}))
    assert high.arterial_po2_mmhg > base.arterial_po2_mmhg
    assert high.arterial_saturation_pct >= base.arterial_saturation_pct


def test_hypoventilation_increases_co2():
    base = run_gas_case(GasBenchCase("base", {}, {}))
    low = run_gas_case(GasBenchCase("low", {"inspiratory_muscle_swing_cmh2o": 3.5}, {}))
    assert low.alveolar_ventilation_ml_min < base.alveolar_ventilation_ml_min
    assert low.arterial_pco2_mmhg > base.arterial_pco2_mmhg


def test_dead_space_increases_co2_at_same_mechanics():
    base = run_gas_case(GasBenchCase("base", {}, {}))
    ds = run_gas_case(GasBenchCase("ds", {}, {"alveolar_dead_space_fraction": 0.35}))
    assert ds.alveolar_ventilation_ml_min < base.alveolar_ventilation_ml_min
    assert ds.arterial_pco2_mmhg > base.arterial_pco2_mmhg


def test_shunt_reduces_oxygenation_without_directly_changing_ventilation():
    base = run_gas_case(GasBenchCase("base", {}, {}))
    shunt = run_gas_case(GasBenchCase("shunt", {}, {"shunt_fraction": 0.30}))
    assert shunt.alveolar_ventilation_ml_min == base.alveolar_ventilation_ml_min
    assert shunt.arterial_saturation_pct < base.arterial_saturation_pct
    assert shunt.arterial_po2_mmhg < base.arterial_po2_mmhg


def test_reduced_diffusion_reduces_oxygenation():
    base = run_gas_case(GasBenchCase("base", {}, {}))
    impaired = run_gas_case(GasBenchCase("impaired", {}, {"diffusion_efficiency": 0.60}))
    assert impaired.arterial_po2_mmhg < base.arterial_po2_mmhg


def test_neolung_still_does_not_import_neocirculation():
    root = Path(__file__).resolve().parents[1] / "src" / "neolung"
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(not a.name.startswith("neocirculation") for a in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("neocirculation")

def test_high_vq_mismatch_behaves_like_added_dead_space():
    base = run_gas_case(GasBenchCase("base", {}, {}))
    high_vq = run_gas_case(GasBenchCase("hvq", {}, {"high_vq_fraction": 0.30}))
    assert high_vq.alveolar_ventilation_ml_min < base.alveolar_ventilation_ml_min
    assert high_vq.arterial_pco2_mmhg > base.arterial_pco2_mmhg


def test_low_vq_mismatch_reduces_oxygenation():
    base = run_gas_case(GasBenchCase("base", {}, {}))
    low_vq = run_gas_case(GasBenchCase("lvq", {}, {"low_vq_fraction": 0.20}))
    assert low_vq.arterial_saturation_pct < base.arterial_saturation_pct
    assert low_vq.arterial_po2_mmhg < base.arterial_po2_mmhg
