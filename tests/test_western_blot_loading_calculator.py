from __future__ import annotations

import pytest

from labtools.western_blot import WBLoadingCalculatorError, WBLoadingConfig, WBSampleInput, calculate_wb_loading


def _row(result, sample_name: str):
    return next(row for row in result.rows if row.sample_name == sample_name)


def test_4x_loading_buffer_without_reducing_agent_builds_lane_layout() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(target_protein_ug=20, final_volume_ul=20, loading_buffer_factor=4, reducing_agent_mode="none"),
        (
            WBSampleInput("S1", 2.0),
            WBSampleInput("S2", 1.0),
            WBSampleInput("S3", 0.5),
            WBSampleInput("S4", 4.0),
        ),
    )

    assert _row(result, "S1").sample_volume_ul == pytest.approx(10)
    assert _row(result, "S1").loading_buffer_volume_ul == pytest.approx(5)
    assert _row(result, "S1").reducing_agent_volume_ul == pytest.approx(0)
    assert _row(result, "S1").diluent_volume_ul == pytest.approx(5)
    assert _row(result, "S1").status == "OK"
    assert _row(result, "S2").sample_volume_ul == pytest.approx(20)
    assert _row(result, "S2").diluent_volume_ul == pytest.approx(-5)
    assert _row(result, "S2").status == "Error"
    assert _row(result, "S3").sample_volume_ul == pytest.approx(40)
    assert _row(result, "S3").diluent_volume_ul == pytest.approx(-25)
    assert _row(result, "S3").status == "Error"
    assert _row(result, "S4").sample_volume_ul == pytest.approx(5)
    assert _row(result, "S4").diluent_volume_ul == pytest.approx(10)
    assert _row(result, "S4").status == "OK"
    assert [lane.sample_name for lane in result.lanes] == ["Protein Marker", "S1", "S2", "S3", "S4"]
    assert result.lanes[0].lane_type == "marker"
    assert result.lanes[1].lane_label == "Lane 2"
    assert "横向 lane layout" in result.as_text()


def test_acceptance_4x_scenario_keeps_vertical_and_horizontal_errors_aligned() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(
            experiment_name="WB test A",
            target_protein_ug=20,
            final_volume_ul=20,
            loading_buffer_factor=4,
            reducing_agent_mode="none",
            diluent_name="ddH2O",
        ),
        (
            WBSampleInput("S1", 2.0),
            WBSampleInput("S2", 1.5),
            WBSampleInput("S3", 1.0),
            WBSampleInput("S4", 0.8),
            WBSampleInput("S5", 4.0),
        ),
    )

    assert _row(result, "S1").sample_volume_ul == pytest.approx(10)
    assert _row(result, "S1").diluent_volume_ul == pytest.approx(5)
    assert _row(result, "S2").sample_volume_ul == pytest.approx(13.3333333333)
    assert _row(result, "S2").diluent_volume_ul == pytest.approx(1.6666666667)
    assert _row(result, "S3").sample_volume_ul == pytest.approx(20)
    assert _row(result, "S3").diluent_volume_ul == pytest.approx(-5)
    assert _row(result, "S3").status == "Error"
    assert _row(result, "S4").sample_volume_ul == pytest.approx(25)
    assert _row(result, "S4").diluent_volume_ul == pytest.approx(-10)
    assert _row(result, "S4").status == "Error"
    assert _row(result, "S5").sample_volume_ul == pytest.approx(5)
    assert _row(result, "S5").diluent_volume_ul == pytest.approx(10)
    assert [lane.sample_name for lane in result.lanes] == ["Protein Marker", "S1", "S2", "S3", "S4", "S5"]
    assert [lane.lane_label for lane in result.lanes] == ["Lane 1", "Lane 2", "Lane 3", "Lane 4", "Lane 5", "Lane 6"]
    status_row = next(row for row in result.lane_layout_table if row[0] == "状态")
    assert status_row == ("状态", "Marker", "OK", "OK", "Error", "Error", "OK")


def test_5x_loading_buffer_without_reducing_agent() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(target_protein_ug=20, final_volume_ul=20, loading_buffer_factor=5, reducing_agent_mode="none"),
        (WBSampleInput("S1", 2.0),),
    )

    row = _row(result, "S1")
    assert row.sample_volume_ul == pytest.approx(10)
    assert row.loading_buffer_volume_ul == pytest.approx(4)
    assert row.reducing_agent_volume_ul == pytest.approx(0)
    assert row.diluent_volume_ul == pytest.approx(6)
    assert row.status == "OK"


def test_percent_reducing_agent_beta_me() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(
            target_protein_ug=20,
            final_volume_ul=20,
            loading_buffer_factor=4,
            reducing_agent_mode="percent_of_final",
            reducing_agent_name="β-ME",
            reducing_agent_percent=5,
        ),
        (WBSampleInput("S1", 2.0),),
    )

    row = _row(result, "S1")
    assert row.sample_volume_ul == pytest.approx(10)
    assert row.loading_buffer_volume_ul == pytest.approx(5)
    assert row.reducing_agent_volume_ul == pytest.approx(1)
    assert row.diluent_volume_ul == pytest.approx(4)
    assert any(layout_row[0] == "β-ME" for layout_row in result.lane_layout_table)


def test_fixed_volume_reducing_agent_dtt() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(
            target_protein_ug=20,
            final_volume_ul=20,
            loading_buffer_factor=4,
            reducing_agent_mode="fixed_volume",
            reducing_agent_name="DTT",
            reducing_agent_fixed_volume_ul=1,
        ),
        (WBSampleInput("S1", 2.0),),
    )

    row = _row(result, "S1")
    assert row.sample_volume_ul == pytest.approx(10)
    assert row.loading_buffer_volume_ul == pytest.approx(5)
    assert row.reducing_agent_volume_ul == pytest.approx(1)
    assert row.diluent_volume_ul == pytest.approx(4)


def test_marker_can_be_disabled() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(marker_enabled=False),
        (WBSampleInput("S1", 2.0), WBSampleInput("S2", 4.0)),
    )

    assert [lane.sample_name for lane in result.lanes] == ["S1", "S2"]
    assert result.lanes[0].lane_label == "Lane 1"
    assert result.lanes[0].lane_type == "sample"


def test_fixed_10_lane_layout_adds_empty_lanes() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(marker_enabled=True, lane_count_mode="fixed", fixed_lane_count=10),
        (WBSampleInput("S1", 2.0), WBSampleInput("S2", 4.0), WBSampleInput("S3", 5.0)),
    )

    assert len(result.lanes) == 10
    assert [lane.sample_name for lane in result.lanes[:4]] == ["Protein Marker", "S1", "S2", "S3"]
    assert all(lane.lane_type == "empty" for lane in result.lanes[4:])


@pytest.mark.parametrize(("fixed_lane_count", "expected_empty_count"), ((10, 6), (12, 8), (15, 11)))
def test_fixed_lane_layout_10_12_15_adds_expected_empty_lanes(fixed_lane_count: int, expected_empty_count: int) -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(marker_enabled=True, lane_count_mode="fixed", fixed_lane_count=fixed_lane_count),
        (WBSampleInput("S1", 2.0), WBSampleInput("S2", 4.0), WBSampleInput("S3", 5.0)),
    )

    assert len(result.lanes) == fixed_lane_count
    assert sum(1 for lane in result.lanes if lane.lane_type == "empty") == expected_empty_count
    assert result.lanes[-1].lane_label == f"Lane {fixed_lane_count}"


def test_low_volume_warning() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(target_protein_ug=1, final_volume_ul=20, loading_buffer_factor=4, min_pipette_volume_ul=0.5),
        (WBSampleInput("S1", 10),),
    )

    row = _row(result, "S1")
    assert row.sample_volume_ul == pytest.approx(0.1)
    assert row.status == "Warning"
    assert any("低于 0.5 µL" in warning for warning in row.warnings)


def test_fixed_lane_count_capacity_reports_error() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(lane_count_mode="fixed", fixed_lane_count=10, marker_enabled=True),
        tuple(WBSampleInput(f"S{index}", 2.0) for index in range(1, 11)),
    )

    assert "固定 lane 数不足" in "\n".join(result.summary_errors)
    assert "固定 lane 数不足" in result.as_text()
    assert len(result.lanes) == 10
    assert [lane.sample_name for lane in result.lanes[-2:]] == ["S8", "S9"]
    assert "S10" not in [lane.sample_name for lane in result.lanes]


def test_custom_diluent_name_is_used_in_lane_layout() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(diluent_name="lysis buffer"),
        (WBSampleInput("S1", 2.0),),
    )

    assert any(row[0] == "lysis buffer" for row in result.lane_layout_table)
    assert "lysis buffer" in result.as_text()


def test_invalid_sample_rows_report_errors_without_blank_lane_label() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(),
        (
            WBSampleInput("Zero", 0),
            WBSampleInput("Negative", -1),
            WBSampleInput("", 2),
        ),
    )

    assert _row(result, "Zero").status == "Error"
    assert _row(result, "Negative").status == "Error"
    unnamed = _row(result, "未命名样本 3")
    assert unnamed.status == "Error"
    assert "样本名不能为空" in "\n".join(unnamed.errors)
    assert all(lane.sample_name for lane in result.lanes)


def test_large_reducing_percent_reports_negative_diluent_error() -> None:
    result = calculate_wb_loading(
        WBLoadingConfig(
            target_protein_ug=20,
            final_volume_ul=20,
            loading_buffer_factor=4,
            reducing_agent_mode="percent_of_final",
            reducing_agent_name="β-ME",
            reducing_agent_percent=80,
        ),
        (WBSampleInput("S1", 2.0),),
    )

    row = _row(result, "S1")
    assert row.reducing_agent_volume_ul == pytest.approx(16)
    assert row.diluent_volume_ul == pytest.approx(-11)
    assert row.status == "Error"
    assert any("补足液体积为负" in error for error in row.errors)


@pytest.mark.parametrize(
    ("config", "message"),
    (
        (WBLoadingConfig(target_protein_ug=0), "目标上样蛋白量必须大于 0"),
        (WBLoadingConfig(final_volume_ul=0), "目标终体积必须大于 0"),
        (WBLoadingConfig(loading_buffer_factor=1), "Loading buffer 倍数必须大于 1"),
        (WBLoadingConfig(loading_buffer_factor=3), "仅支持 4X 或 5X"),
    ),
)
def test_invalid_config_errors(config: WBLoadingConfig, message: str) -> None:
    with pytest.raises(WBLoadingCalculatorError, match=message):
        calculate_wb_loading(config, (WBSampleInput("S1", 2.0),))
