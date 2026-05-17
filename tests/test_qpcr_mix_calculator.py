from __future__ import annotations

import pytest

from labtools.calculators.calculator_models import CalculationError
from labtools.calculators.qpcr_mix_calculator import calculate_qpcr_mix


def test_qpcr_mix_calculates_volume_mode() -> None:
    result = calculate_qpcr_mix(10, 20, 10, 0.4, 0.4, 2, loss_percent=10)

    outputs = result.record_outputs

    assert outputs["per_reaction_uL"]["nuclease_free_water_uL"] == pytest.approx(7.2)
    assert outputs["total_uL"]["master_mix_uL"] == pytest.approx(100)
    assert outputs["total_with_loss_uL"]["master_mix_uL"] == pytest.approx(110)
    assert result.result_value == pytest.approx(220)
    assert "nuclease-free water" in result.as_text()
    assert "请人工复核计算结果后再用于实验" in result.as_text()


def test_qpcr_mix_calculates_ratio_mode() -> None:
    result = calculate_qpcr_mix(10, 20, 50, 0.4, 0.4, 2, master_mix_mode="ratio", loss_percent=0)

    assert result.record_outputs["per_reaction_uL"]["master_mix_uL"] == pytest.approx(10)
    assert result.record_outputs["total_with_loss_uL"]["nuclease_free_water_uL"] == pytest.approx(72)


def test_qpcr_mix_rejects_components_exceeding_total_volume() -> None:
    with pytest.raises(CalculationError, match="组分体积总和超过单反应总体积"):
        calculate_qpcr_mix(10, 10, 8, 1, 1, 2)


def test_qpcr_mix_rejects_negative_loss() -> None:
    with pytest.raises(CalculationError, match="损耗比例不能为负数"):
        calculate_qpcr_mix(10, 20, 10, 0.4, 0.4, 2, loss_percent=-5)


def test_qpcr_mix_rejects_ratio_over_100() -> None:
    with pytest.raises(CalculationError, match="master mix 比例不能超过 100%"):
        calculate_qpcr_mix(10, 20, 110, 0.4, 0.4, 2, master_mix_mode="ratio")
