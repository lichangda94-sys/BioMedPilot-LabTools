from __future__ import annotations

import pytest

from labtools.calculators.calculator_models import CalculationError
from labtools.calculators.solution_preparation_calculator import calculate_solution_preparation


def test_solution_preparation_from_mass_concentration() -> None:
    result = calculate_solution_preparation(1, "mg/mL", 10, "mL", output_mass_unit="mg")

    assert result.result_value == pytest.approx(10)
    assert result.result_unit == "mg"
    assert result.record_outputs["solvent_to_final_volume"] == pytest.approx(10)
    assert "需要称量质量 = 质量浓度 x 目标体积" in result.as_text()
    assert "请人工复核计算结果后再用于实验" in result.as_text()


def test_solution_preparation_from_molarity() -> None:
    result = calculate_solution_preparation(1, "mM", 1, "mL", molecular_weight=1000, output_mass_unit="mg")

    assert result.result_value == pytest.approx(1)
    assert result.result_unit == "mg"
    assert result.record_inputs["molecular_weight_g_per_mol"] == pytest.approx(1000)
    assert "需要称量质量 = 摩尔浓度 x 目标体积 x 分子量" in result.as_text()


def test_solution_preparation_requires_mw_for_molarity() -> None:
    with pytest.raises(CalculationError, match="请填写分子量"):
        calculate_solution_preparation(1, "mM", 1, "mL")


def test_solution_preparation_rejects_zero_volume() -> None:
    with pytest.raises(CalculationError, match="目标体积必须大于 0"):
        calculate_solution_preparation(1, "mg/mL", 0, "mL")


def test_solution_preparation_rejects_unknown_unit() -> None:
    with pytest.raises(CalculationError, match="暂不支持单位"):
        calculate_solution_preparation(1, "ppm", 1, "mL")
