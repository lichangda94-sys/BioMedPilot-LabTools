from __future__ import annotations

import pytest

from labtools.calculators.calculator_models import CalculationError
from labtools.calculators.dilution_calculator import calculate_dilution


def test_dilution_calculates_stock_and_solvent_volumes() -> None:
    result = calculate_dilution(10, "mM", 100, "µM", 1, "mL", output_volume_unit="µL")

    assert result.result_value == pytest.approx(10.0)
    assert result.result_unit == "µL"
    text = result.as_text()
    assert "C1V1 = C2V2" in text
    assert "原液浓度：10 mM" in text
    assert "目标浓度：100 µM" in text
    assert "目标体积：1 mL" in text
    assert "所需原液体积：10 µL" in text
    assert "所需溶剂体积：990 µL" in text
    assert "请人工复核计算结果后再用于实验" in text


def test_dilution_rejects_zero_stock_concentration() -> None:
    with pytest.raises(CalculationError, match="原液浓度必须大于 0"):
        calculate_dilution(0, "mM", 100, "µM", 1, "mL")


def test_dilution_rejects_zero_target_volume() -> None:
    with pytest.raises(CalculationError, match="目标体积必须大于 0"):
        calculate_dilution(10, "mM", 100, "µM", 0, "mL")


def test_dilution_rejects_target_higher_than_stock() -> None:
    with pytest.raises(CalculationError, match="不能通过稀释获得"):
        calculate_dilution(10, "µM", 100, "µM", 1, "mL")


def test_dilution_requires_molecular_weight_when_concentration_types_differ() -> None:
    with pytest.raises(CalculationError, match="请填写分子量"):
        calculate_dilution(1, "mg/mL", 100, "µM", 1, "mL")
