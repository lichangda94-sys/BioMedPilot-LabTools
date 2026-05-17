from __future__ import annotations

from labtools.western_blot.models import (
    WB_LOADING_REVIEW_NOTICE,
    WBLoadingCalculatorError,
    WBLoadingConfig,
    WBLoadingResult,
    WBLoadingResultRow,
    WBLane,
    WBSampleInput,
)


SUPPORTED_LOADING_BUFFER_FACTORS = (4.0, 5.0)
SUPPORTED_FIXED_LANE_COUNTS = (10, 12, 15)


def calculate_wb_loading(config: WBLoadingConfig, samples: tuple[WBSampleInput, ...] | list[WBSampleInput]) -> WBLoadingResult:
    normalized_samples = tuple(samples)
    _validate_config(config)
    if not normalized_samples:
        raise WBLoadingCalculatorError("请至少添加一个样本。")

    rows = tuple(_calculate_row(config, sample, index + 1) for index, sample in enumerate(normalized_samples))
    lanes, layout_warnings, layout_errors = _build_lanes(config, rows)
    summary_warnings = tuple(layout_warnings)
    summary_errors = tuple(layout_errors)
    return WBLoadingResult(
        config=config,
        rows=rows,
        lanes=lanes,
        lane_layout_table=_build_lane_layout_table(config, lanes),
        steps=_build_steps(config),
        review_notice=WB_LOADING_REVIEW_NOTICE,
        summary_warnings=summary_warnings,
        summary_errors=summary_errors,
    )


def _validate_config(config: WBLoadingConfig) -> None:
    if config.target_protein_ug <= 0:
        raise WBLoadingCalculatorError("目标上样蛋白量必须大于 0。")
    if config.final_volume_ul <= 0:
        raise WBLoadingCalculatorError("目标终体积必须大于 0。")
    if config.loading_buffer_factor <= 1:
        raise WBLoadingCalculatorError("Loading buffer 倍数必须大于 1。")
    if float(config.loading_buffer_factor) not in SUPPORTED_LOADING_BUFFER_FACTORS:
        raise WBLoadingCalculatorError("L4 MVP 仅支持 4X 或 5X loading buffer。")
    if config.reducing_agent_mode not in ("none", "fixed_volume", "percent_of_final"):
        raise WBLoadingCalculatorError("还原剂模式必须为 none、fixed_volume 或 percent_of_final。")
    if config.reducing_agent_fixed_volume_ul < 0:
        raise WBLoadingCalculatorError("还原剂固定体积不能为负数。")
    if config.reducing_agent_percent < 0:
        raise WBLoadingCalculatorError("还原剂百分比不能为负数。")
    if config.marker_volume_ul < 0:
        raise WBLoadingCalculatorError("Marker 体积不能为负数。")
    if config.min_pipette_volume_ul < 0:
        raise WBLoadingCalculatorError("低体积 warning 阈值不能为负数。")
    if config.lane_count_mode not in ("auto", "fixed"):
        raise WBLoadingCalculatorError("Lane 数模式必须为 auto 或 fixed。")
    if config.lane_count_mode == "fixed" and config.fixed_lane_count not in SUPPORTED_FIXED_LANE_COUNTS:
        raise WBLoadingCalculatorError("固定 lane 数仅支持 10、12 或 15。")


def _calculate_row(config: WBLoadingConfig, sample: WBSampleInput, sample_index: int) -> WBLoadingResultRow:
    errors: list[str] = []
    warnings: list[str] = []
    sample_name = sample.sample_name.strip()
    if not sample_name:
        sample_name = f"未命名样本 {sample_index}"
        errors.append("样本名不能为空。")

    concentration = sample.concentration_ug_per_ul
    if concentration <= 0:
        errors.append("样本浓度必须大于 0 µg/µL。")
        sample_volume = 0.0
    else:
        sample_volume = config.target_protein_ug / concentration

    loading_buffer_volume = config.final_volume_ul / config.loading_buffer_factor
    reducing_agent_volume = _reducing_agent_volume(config)
    diluent_volume = config.final_volume_ul - sample_volume - loading_buffer_volume - reducing_agent_volume

    if sample_volume > config.final_volume_ul:
        errors.append("样本浓度不足：所需样本体积超过目标终体积。")
    if diluent_volume < 0:
        errors.append("补足液体积为负，请降低目标上样量、增加终体积或重新检查样本浓度。")
    if sample_volume + loading_buffer_volume + reducing_agent_volume > config.final_volume_ul:
        errors.append("样本体积、loading buffer 和还原剂之和超过目标终体积。")

    for label, volume in (
        ("样本体积", sample_volume),
        ("loading buffer 体积", loading_buffer_volume),
        ("还原剂体积", reducing_agent_volume),
        (f"{config.diluent_name or '补足液'}体积", diluent_volume),
    ):
        if 0 < volume < config.min_pipette_volume_ul:
            warnings.append(f"{label} {_fmt(volume)} µL 低于 {_fmt(config.min_pipette_volume_ul)} µL，可能存在较大移液误差。")

    return WBLoadingResultRow(
        sample_name=sample_name,
        concentration_ug_per_ul=concentration,
        target_protein_ug=config.target_protein_ug,
        sample_volume_ul=sample_volume,
        loading_buffer_volume_ul=loading_buffer_volume,
        reducing_agent_volume_ul=reducing_agent_volume,
        diluent_volume_ul=diluent_volume,
        final_volume_ul=config.final_volume_ul,
        warnings=tuple(warnings),
        errors=tuple(errors),
        note=sample.note,
    )


def _reducing_agent_volume(config: WBLoadingConfig) -> float:
    if config.reducing_agent_mode == "none":
        return 0.0
    if config.reducing_agent_mode == "fixed_volume":
        return config.reducing_agent_fixed_volume_ul
    return config.final_volume_ul * config.reducing_agent_percent / 100


def _build_lanes(config: WBLoadingConfig, rows: tuple[WBLoadingResultRow, ...]) -> tuple[tuple[WBLane, ...], list[str], list[str]]:
    lanes: list[WBLane] = []
    warnings: list[str] = []
    errors: list[str] = []

    if config.lane_count_mode == "auto":
        lane_count = len(rows) + (1 if config.marker_enabled else 0)
    else:
        lane_count = config.fixed_lane_count
        capacity = lane_count - (1 if config.marker_enabled else 0)
        if len(rows) > capacity:
            errors.append("固定 lane 数不足，部分样本无法放入当前胶孔布局。")

    lane_index = 1
    if config.marker_enabled:
        lanes.append(
            WBLane(
                lane_index=lane_index,
                lane_label=f"Lane {lane_index}",
                lane_type="marker",
                sample_name=config.marker_name or "Protein Marker",
                marker_volume_ul=config.marker_volume_ul,
                note="Marker lane 不参与蛋白样本计算。",
            )
        )
        lane_index += 1

    for row in rows[: max(0, lane_count - len(lanes))]:
        lanes.append(
            WBLane(
                lane_index=lane_index,
                lane_label=f"Lane {lane_index}",
                lane_type="sample",
                sample_name=row.sample_name,
                result_row=row,
                warnings=row.warnings,
                errors=row.errors,
                note=row.note,
            )
        )
        lane_index += 1

    while len(lanes) < lane_count:
        lanes.append(WBLane(lane_index=lane_index, lane_label=f"Lane {lane_index}", lane_type="empty", sample_name="Empty"))
        lane_index += 1

    return tuple(lanes), warnings, errors


def _build_lane_layout_table(config: WBLoadingConfig, lanes: tuple[WBLane, ...]) -> tuple[tuple[str, ...], ...]:
    reducing_label = _reducing_label(config)
    rows: list[tuple[str, ...]] = [
        tuple(["项目", *(lane.lane_label for lane in lanes)]),
        tuple(["类型", *(_lane_type_label(lane) for lane in lanes)]),
        tuple(["样本", *(_lane_sample_label(lane) for lane in lanes)]),
        tuple(["样本体积", *(_lane_sample_volume(lane) for lane in lanes)]),
        tuple([f"{_fmt(config.loading_buffer_factor)}X loading buffer", *(_lane_row_volume(lane, "loading") for lane in lanes)]),
        tuple([reducing_label, *(_lane_row_volume(lane, "reducing") for lane in lanes)]),
        tuple([config.diluent_name or "补足液", *(_lane_row_volume(lane, "diluent") for lane in lanes)]),
        tuple(["状态", *(_lane_status(lane) for lane in lanes)]),
    ]
    return tuple(rows)


def _lane_type_label(lane: WBLane) -> str:
    if lane.lane_type == "marker":
        return "Marker"
    if lane.lane_type == "sample":
        return "Sample"
    return "Empty"


def _lane_sample_label(lane: WBLane) -> str:
    if lane.lane_type == "empty":
        return "-"
    return lane.sample_name


def _lane_sample_volume(lane: WBLane) -> str:
    if lane.lane_type == "marker":
        return f"{_fmt(lane.marker_volume_ul)} µL"
    if lane.result_row is None:
        return "-"
    return f"{_fmt(lane.result_row.sample_volume_ul)} µL"


def _lane_row_volume(lane: WBLane, field: str) -> str:
    if lane.result_row is None:
        return "-"
    row = lane.result_row
    if field == "loading":
        return f"{_fmt(row.loading_buffer_volume_ul)} µL"
    if field == "reducing":
        return f"{_fmt(row.reducing_agent_volume_ul)} µL"
    if row.diluent_volume_ul < 0:
        return "Error"
    return f"{_fmt(row.diluent_volume_ul)} µL"


def _lane_status(lane: WBLane) -> str:
    if lane.lane_type == "marker":
        return "Marker"
    if lane.lane_type == "empty":
        return "Empty"
    if lane.errors:
        return "Error"
    if lane.warnings:
        return "Warning"
    return "OK"


def _reducing_label(config: WBLoadingConfig) -> str:
    if config.reducing_agent_mode == "none":
        return "还原剂"
    return config.reducing_agent_name.strip() or "还原剂"


def _build_steps(config: WBLoadingConfig) -> tuple[str, ...]:
    steps = [
        "1. 按横向 lane layout 确认上样顺序。",
    ]
    next_index = 2
    if config.marker_enabled:
        steps.append(f"{next_index}. Marker 加入 Lane 1：{config.marker_name or 'Protein Marker'}，{_fmt(config.marker_volume_ul)} µL。")
        next_index += 1
    steps.extend(
        [
            f"{next_index}. 按计算表为每个样本加入对应体积的蛋白样本。",
            f"{next_index + 1}. 加入 {_fmt(config.loading_buffer_factor)}X loading buffer。",
        ]
    )
    next_index += 2
    if config.reducing_agent_mode != "none":
        steps.append(f"{next_index}. 如设置还原剂，按表格加入 {config.reducing_agent_name or '还原剂'}。")
        next_index += 1
    steps.extend(
        [
            f"{next_index}. 使用 {config.diluent_name or '补足液'} 补至目标终体积。",
            f"{next_index + 1}. 混匀并短暂离心。",
            f"{next_index + 2}. 按实验室 SOP 进行变性和上样。",
        ]
    )
    return tuple(steps)


def _fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")
