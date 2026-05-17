from __future__ import annotations

import pytest

from labtools.western_blot import (
    DEFAULT_LOADING_OVERAGE_PERCENT,
    PROTEIN_LOADING_REVIEW_NOTICE,
    REDUCING_AGENT_NOTICE,
    ProteinLoadingError,
    ProteinLoadingSampleInput,
    ProteinLoadingSettings,
    calculate_protein_loading,
    concentration_to_ug_per_ul,
)


def test_microgram_per_microliter_and_milligram_per_milliliter_are_equivalent() -> None:
    assert concentration_to_ug_per_ul(2, "µg/µL") == pytest.approx(2)
    assert concentration_to_ug_per_ul(2, "ug/uL") == pytest.approx(2)
    assert concentration_to_ug_per_ul(2, "mg/mL") == pytest.approx(2)
    assert concentration_to_ug_per_ul(2000, "µg/mL") == pytest.approx(2)
    assert concentration_to_ug_per_ul(2000, "ug/mL") == pytest.approx(2)


def test_four_x_loading_buffer_to_one_x_volume_is_correct() -> None:
    result = calculate_protein_loading(
        [ProteinLoadingSampleInput("S1", 2, "µg/µL")],
        ProteinLoadingSettings(target_protein_ug=20, final_loading_volume_ul=20, loading_buffer_multiple=4),
    )

    row = result.samples[0]
    assert row.loading_buffer_volume_ul == pytest.approx(5)
    assert row.sample_volume_ul == pytest.approx(10)
    assert row.water_volume_ul == pytest.approx(5)


def test_multi_sample_totals_and_default_overage_are_correct() -> None:
    result = calculate_protein_loading(
        [
            ProteinLoadingSampleInput("S1", 2, "mg/mL"),
            ProteinLoadingSampleInput("S2", 1, "µg/µL"),
        ],
        ProteinLoadingSettings(target_protein_ug=20, final_loading_volume_ul=30, loading_buffer_multiple=5),
    )

    assert result.settings.overage_percent == DEFAULT_LOADING_OVERAGE_PERCENT
    assert result.samples[0].sample_volume_ul == pytest.approx(10)
    assert result.samples[1].sample_volume_ul == pytest.approx(20)
    assert result.total_sample_volume_ul == pytest.approx(30 * 1.03)
    assert result.total_loading_buffer_volume_ul == pytest.approx(12 * 1.03)
    assert result.total_water_volume_ul == pytest.approx(18 * 1.03)


def test_negative_water_volume_returns_chinese_error() -> None:
    with pytest.raises(ProteinLoadingError, match="组分体积超过最终上样体积，无法计算"):
        calculate_protein_loading(
            [ProteinLoadingSampleInput("S1", 0.5, "µg/µL")],
            ProteinLoadingSettings(target_protein_ug=20, final_loading_volume_ul=20, loading_buffer_multiple=4),
        )


def test_small_sample_volume_returns_warning() -> None:
    result = calculate_protein_loading(
        [ProteinLoadingSampleInput("S1", 50, "µg/µL")],
        ProteinLoadingSettings(target_protein_ug=20, final_loading_volume_ul=20, loading_buffer_multiple=4),
    )

    assert "蛋白样品体积 < 1 µL" in result.samples[0].warnings[0]
    assert "S1: 蛋白样品体积 < 1 µL" in result.warnings[0]


def test_invalid_inputs_are_blocking_errors() -> None:
    with pytest.raises(ProteinLoadingError, match="蛋白浓度需要大于 0"):
        calculate_protein_loading(
            [ProteinLoadingSampleInput("S1", 0, "µg/µL")],
            ProteinLoadingSettings(target_protein_ug=20, final_loading_volume_ul=20, loading_buffer_multiple=4),
        )
    with pytest.raises(ProteinLoadingError, match="目标每孔蛋白量需要大于 0"):
        calculate_protein_loading(
            [ProteinLoadingSampleInput("S1", 1, "µg/µL")],
            ProteinLoadingSettings(target_protein_ug=0, final_loading_volume_ul=20, loading_buffer_multiple=4),
        )
    with pytest.raises(ProteinLoadingError, match="最终上样体积需要大于 0"):
        calculate_protein_loading(
            [ProteinLoadingSampleInput("S1", 1, "µg/µL")],
            ProteinLoadingSettings(target_protein_ug=20, final_loading_volume_ul=0, loading_buffer_multiple=4),
        )
    with pytest.raises(ProteinLoadingError, match="请检查 loading buffer 设置"):
        calculate_protein_loading(
            [ProteinLoadingSampleInput("S1", 1, "µg/µL")],
            ProteinLoadingSettings(target_protein_ug=20, final_loading_volume_ul=20, loading_buffer_multiple=1),
        )


def test_copy_text_contains_review_and_reducing_agent_notice() -> None:
    result = calculate_protein_loading(
        [ProteinLoadingSampleInput("S1", 2, "µg/µL")],
        ProteinLoadingSettings(target_protein_ug=20, final_loading_volume_ul=20, loading_buffer_multiple=4),
    )
    text = result.copy_text()

    assert REDUCING_AGENT_NOTICE in text
    assert PROTEIN_LOADING_REVIEW_NOTICE in text
    assert "总 loading buffer 体积" in text
