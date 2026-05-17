from __future__ import annotations

import pytest

from labtools.calculators.experiment_calculator_center import (
    QpcrMixInput,
    WesternBlotLoadingInput,
    calculate_qpcr_mix_v1,
    calculate_western_blot_loading_v1,
)


def test_l5c_qpcr_mix_v1_calculates_volume_mode_with_overage() -> None:
    result = calculate_qpcr_mix_v1(QpcrMixInput(10, 20, 10, 0.4, 0.4, 2, overage_percentage=10))

    assert result.valid is True
    assert result.per_reaction_ul["nuclease_free_water_uL"] == pytest.approx(7.2)
    assert result.total_ul["master_mix_uL"] == pytest.approx(100)
    assert result.total_with_overage_ul["master_mix_uL"] == pytest.approx(110)
    assert result.total_reaction_volume_with_overage_ul == pytest.approx(220)
    assert "实验辅助草稿" in result.summary
    assert "人工核对" in result.as_text()


def test_l5c_qpcr_mix_v1_calculates_ratio_mode() -> None:
    result = calculate_qpcr_mix_v1(QpcrMixInput(10, 20, 50, 0.4, 0.4, 2, master_mix_mode="ratio", overage_percentage=0))

    assert result.valid is True
    assert result.per_reaction_ul["master_mix_uL"] == pytest.approx(10)
    assert result.total_with_overage_ul["nuclease_free_water_uL"] == pytest.approx(72)


def test_l5c_qpcr_mix_v1_reports_invalid_inputs() -> None:
    too_much = calculate_qpcr_mix_v1(QpcrMixInput(10, 10, 8, 1, 1, 2))
    bad_ratio = calculate_qpcr_mix_v1(QpcrMixInput(10, 20, 110, 0.4, 0.4, 2, master_mix_mode="ratio"))
    bad_overage = calculate_qpcr_mix_v1(QpcrMixInput(10, 20, 10, 0.4, 0.4, 2, overage_percentage=-5))

    assert too_much.valid is False
    assert "组分体积总和超过单反应总体积" in too_much.errors[0]
    assert bad_ratio.valid is False
    assert "比例不能超过 100%" in bad_ratio.errors[0]
    assert bad_overage.valid is False
    assert "overage 比例不能为负数" in bad_overage.errors[0]


def test_l5c_western_blot_loading_calculates_sample_buffer_and_water() -> None:
    result = calculate_western_blot_loading_v1(WesternBlotLoadingInput(2, "mg/mL", 20, 20, "uL", 4))

    assert result.valid is True
    assert result.sample_volume == pytest.approx(10)
    assert result.sample_volume_unit == "µL"
    assert result.loading_buffer_volume == pytest.approx(5)
    assert result.water_volume == pytest.approx(5)
    assert result.final_loading_volume == pytest.approx(20)
    assert "不做" not in result.summary
    assert "人工核对" in result.as_text()


def test_l5c_western_blot_loading_supports_microgram_per_microliter_alias() -> None:
    result = calculate_western_blot_loading_v1(WesternBlotLoadingInput(1, "ug/uL", 10, 20, "µL", 5))

    assert result.valid is True
    assert result.sample_volume == pytest.approx(10)
    assert result.loading_buffer_volume == pytest.approx(4)
    assert result.water_volume == pytest.approx(6)


def test_l5c_western_blot_loading_reports_invalid_inputs() -> None:
    too_small_volume = calculate_western_blot_loading_v1(WesternBlotLoadingInput(1, "mg/mL", 20, 20, "µL", 4))
    bad_buffer = calculate_western_blot_loading_v1(WesternBlotLoadingInput(2, "mg/mL", 20, 20, "µL", 1))
    bad_unit = calculate_western_blot_loading_v1(WesternBlotLoadingInput(2, "cells/mL", 20, 20, "µL", 4))

    assert too_small_volume.valid is False
    assert "已超过目标上样体积" in too_small_volume.errors[0]
    assert bad_buffer.valid is False
    assert "loading buffer 倍数必须大于 1" in bad_buffer.errors[0]
    assert bad_unit.valid is False
    assert "蛋白浓度单位必须是 mg/mL 或 µg/µL" in bad_unit.errors[0]
