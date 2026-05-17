from __future__ import annotations

import pytest

from labtools.calculators.calculator_models import CalculationError
from labtools.calculators.concentration_calculator import (
    calculate_mass_for_molar_solution,
    calculate_molar_concentration,
    convert_concentration,
)


def test_convert_mass_concentration_to_molarity_requires_molecular_weight() -> None:
    with pytest.raises(CalculationError, match="请填写分子量"):
        convert_concentration(1, "mg/mL", "mM")


def test_convert_mass_concentration_to_molarity_uses_units_and_molecular_weight() -> None:
    result = convert_concentration(1, "mg/mL", "mM", molecular_weight=1000)

    assert result.result_value == pytest.approx(1.0)
    assert result.result_unit == "mM"
    assert "请人工复核计算结果后再用于实验" in result.as_text()


def test_convert_molarity_to_mass_concentration_uses_molecular_weight() -> None:
    result = convert_concentration(10, "µM", "mg/mL", molecular_weight=500)

    assert result.result_value == pytest.approx(0.005)
    assert result.result_unit == "mg/mL"


def test_calculate_molar_concentration_from_mass_volume_and_mw() -> None:
    result = calculate_molar_concentration(1, "mg", 1, "mL", 1000, output_unit="mM")

    assert result.result_value == pytest.approx(1.0)
    assert result.result_unit == "mM"
    text = result.as_text()
    assert "物质的量 n = 质量 / 分子量" in text
    assert "摩尔浓度：1 mM" in text


def test_calculate_mass_for_molar_solution() -> None:
    result = calculate_mass_for_molar_solution(1, "mM", 1, "mL", 1000, output_unit="mg")

    assert result.result_value == pytest.approx(1.0)
    assert result.result_unit == "mg"
    assert "所需质量：1 mg" in result.as_text()


def test_zero_volume_is_rejected_for_molarity_calculation() -> None:
    with pytest.raises(CalculationError, match="体积必须大于 0"):
        calculate_molar_concentration(1, "mg", 0, "mL", 1000)
