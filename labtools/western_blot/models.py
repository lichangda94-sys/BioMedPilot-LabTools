from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from labtools.shared.version import APP_VERSION


ReducingAgentMode = Literal["none", "fixed_volume", "percent_of_final"]
LaneCountMode = Literal["auto", "fixed"]
LaneType = Literal["marker", "sample", "empty"]
WB_LOADING_RECORD_SCHEMA_VERSION = "western_blot_loading_record.v1"

WB_LOADING_REVIEW_NOTICE = (
    "本结果仅用于 Western Blot 上样体系计算。请根据实验室 SOP、试剂说明书和安全规范人工复核；"
    "本工具不判断实验设计合理性，也不进行图像分析或结果解释。"
)


class WBLoadingCalculatorError(ValueError):
    pass


class WBLoadingRecordError(ValueError):
    pass


@dataclass(frozen=True)
class WBLoadingConfig:
    experiment_name: str = "WB loading"
    target_protein_ug: float = 20
    final_volume_ul: float = 20
    loading_buffer_factor: float = 4
    reducing_agent_mode: ReducingAgentMode = "none"
    reducing_agent_name: str = ""
    reducing_agent_fixed_volume_ul: float = 0
    reducing_agent_percent: float = 0
    diluent_name: str = "ddH2O"
    marker_enabled: bool = True
    marker_name: str = "Protein Marker"
    marker_volume_ul: float = 5
    lane_count_mode: LaneCountMode = "auto"
    fixed_lane_count: int = 10
    min_pipette_volume_ul: float = 0.5


@dataclass(frozen=True)
class WBSampleInput:
    sample_name: str
    concentration_ug_per_ul: float
    note: str = ""


@dataclass(frozen=True)
class WBLoadingResultRow:
    sample_name: str
    concentration_ug_per_ul: float
    target_protein_ug: float
    sample_volume_ul: float
    loading_buffer_volume_ul: float
    reducing_agent_volume_ul: float
    diluent_volume_ul: float
    final_volume_ul: float
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    note: str = ""

    @property
    def status(self) -> str:
        if self.errors:
            return "Error"
        if self.warnings:
            return "Warning"
        return "OK"


@dataclass(frozen=True)
class WBLane:
    lane_index: int
    lane_label: str
    lane_type: LaneType
    sample_name: str = ""
    marker_volume_ul: float = 0
    result_row: WBLoadingResultRow | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class WBLoadingResult:
    config: WBLoadingConfig
    rows: tuple[WBLoadingResultRow, ...]
    lanes: tuple[WBLane, ...]
    lane_layout_table: tuple[tuple[str, ...], ...]
    steps: tuple[str, ...]
    review_notice: str
    summary_warnings: tuple[str, ...]
    summary_errors: tuple[str, ...]

    def as_text(self) -> str:
        lines = [
            f"{self.config.experiment_name} Western Blot 上样计算器",
            "Western Blot 上样体系辅助计算草稿",
            f"目标上样蛋白量：{_fmt(self.config.target_protein_ug)} µg / lane",
            f"目标终体积：{_fmt(self.config.final_volume_ul)} µL / lane",
            f"{_fmt(self.config.loading_buffer_factor)}X loading buffer：{_fmt(self.config.final_volume_ul / self.config.loading_buffer_factor)} µL / lane",
            f"总 loading buffer 体积：{_fmt(sum(row.loading_buffer_volume_ul for row in self.rows))} µL",
            "",
            "纵向计算明细表",
            "样本\t浓度(µg/µL)\t目标蛋白(µg)\t样本体积(µL)\tLoading buffer(µL)\t还原剂(µL)\t补足液(µL)\t终体积(µL)\t状态",
        ]
        for row in self.rows:
            lines.append(
                "\t".join(
                    (
                        row.sample_name,
                        _fmt(row.concentration_ug_per_ul),
                        _fmt(row.target_protein_ug),
                        _fmt(row.sample_volume_ul),
                        _fmt(row.loading_buffer_volume_ul),
                        _fmt(row.reducing_agent_volume_ul),
                        _fmt(row.diluent_volume_ul),
                        _fmt(row.final_volume_ul),
                        row.status,
                    )
                )
            )
            for warning in row.warnings:
                lines.append(f"  警告：{warning}")
            for error in row.errors:
                lines.append(f"  错误：{error}")
        lines.extend(["", "横向 lane layout"])
        lines.extend("\t".join(item for item in row) for row in self.lane_layout_table)
        if self.summary_warnings:
            lines.extend(["", "汇总 warning", *self.summary_warnings])
        if self.summary_errors:
            lines.extend(["", "汇总 error", *self.summary_errors])
        lines.extend(["", "通用步骤", *self.steps, "", "复核提示", self.review_notice])
        return "\n".join(lines)


@dataclass(frozen=True)
class WBLoadingRecord:
    record_id: str
    created_at: str
    updated_at: str
    experiment_name: str
    operator_name: str
    project_name: str
    notes: str
    config_snapshot: dict[str, Any]
    sample_inputs_snapshot: tuple[dict[str, Any], ...]
    result_snapshot: dict[str, Any]
    lane_layout_snapshot: tuple[tuple[str, ...], ...]
    app_version: str = APP_VERSION
    schema_version: str = WB_LOADING_RECORD_SCHEMA_VERSION

    @classmethod
    def from_result(
        cls,
        result: WBLoadingResult,
        sample_inputs: tuple[WBSampleInput, ...] | list[WBSampleInput],
        *,
        operator_name: str = "",
        project_name: str = "",
        notes: str = "",
        record_id: str | None = None,
        created_at: str | None = None,
    ) -> "WBLoadingRecord":
        now = utc_now()
        return cls(
            record_id=record_id or f"wb_loading_{uuid4().hex}",
            created_at=created_at or now,
            updated_at=now,
            experiment_name=result.config.experiment_name,
            operator_name=operator_name,
            project_name=project_name,
            notes=notes,
            config_snapshot=wb_loading_config_to_dict(result.config),
            sample_inputs_snapshot=tuple(wb_sample_input_to_dict(sample) for sample in sample_inputs),
            result_snapshot=wb_loading_result_to_dict(result),
            lane_layout_snapshot=tuple(tuple(row) for row in result.lane_layout_table),
        )

    @property
    def summary_status(self) -> str:
        rows = self.result_snapshot.get("rows", [])
        summary_errors = self.result_snapshot.get("summary_errors", [])
        summary_warnings = self.result_snapshot.get("summary_warnings", [])
        if summary_errors or any(row.get("errors") for row in rows if isinstance(row, dict)):
            return "Error"
        if summary_warnings or any(row.get("warnings") for row in rows if isinstance(row, dict)):
            return "Warning"
        return "OK"

    def with_updated_timestamp(self) -> "WBLoadingRecord":
        return WBLoadingRecord(
            record_id=self.record_id,
            created_at=self.created_at,
            updated_at=utc_now(),
            experiment_name=self.experiment_name,
            operator_name=self.operator_name,
            project_name=self.project_name,
            notes=self.notes,
            config_snapshot=dict(self.config_snapshot),
            sample_inputs_snapshot=tuple(dict(item) for item in self.sample_inputs_snapshot),
            result_snapshot=dict(self.result_snapshot),
            lane_layout_snapshot=tuple(tuple(row) for row in self.lane_layout_snapshot),
            app_version=self.app_version,
            schema_version=self.schema_version,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "experiment_name": self.experiment_name,
            "operator_name": self.operator_name,
            "project_name": self.project_name,
            "notes": self.notes,
            "config_snapshot": self.config_snapshot,
            "sample_inputs_snapshot": list(self.sample_inputs_snapshot),
            "result_snapshot": self.result_snapshot,
            "lane_layout_snapshot": [list(row) for row in self.lane_layout_snapshot],
            "app_version": self.app_version,
            "summary_status": self.summary_status,
        }

    @classmethod
    def from_dict(cls, payload: Any) -> "WBLoadingRecord":
        if not isinstance(payload, dict):
            raise WBLoadingRecordError("WB loading record payload 必须是 JSON object。")
        if payload.get("schema_version") != WB_LOADING_RECORD_SCHEMA_VERSION:
            raise WBLoadingRecordError("WB loading record schema 不匹配。")
        result_snapshot = payload.get("result_snapshot")
        if not isinstance(result_snapshot, dict):
            raise WBLoadingRecordError("WB loading record 缺少 result_snapshot。")
        return cls(
            record_id=str(payload.get("record_id") or ""),
            created_at=str(payload.get("created_at") or ""),
            updated_at=str(payload.get("updated_at") or ""),
            experiment_name=str(payload.get("experiment_name") or ""),
            operator_name=str(payload.get("operator_name") or ""),
            project_name=str(payload.get("project_name") or ""),
            notes=str(payload.get("notes") or ""),
            config_snapshot=_dict_or_empty(payload.get("config_snapshot")),
            sample_inputs_snapshot=tuple(_dict_or_empty(item) for item in _list_or_empty(payload.get("sample_inputs_snapshot"))),
            result_snapshot=result_snapshot,
            lane_layout_snapshot=tuple(tuple(str(cell) for cell in row) for row in _list_or_empty(payload.get("lane_layout_snapshot")) if isinstance(row, list | tuple)),
            app_version=str(payload.get("app_version") or ""),
            schema_version=str(payload.get("schema_version") or WB_LOADING_RECORD_SCHEMA_VERSION),
        )


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def wb_loading_config_to_dict(config: WBLoadingConfig) -> dict[str, Any]:
    return {
        "experiment_name": config.experiment_name,
        "target_protein_ug": config.target_protein_ug,
        "final_volume_ul": config.final_volume_ul,
        "loading_buffer_factor": config.loading_buffer_factor,
        "reducing_agent_mode": config.reducing_agent_mode,
        "reducing_agent_name": config.reducing_agent_name,
        "reducing_agent_fixed_volume_ul": config.reducing_agent_fixed_volume_ul,
        "reducing_agent_percent": config.reducing_agent_percent,
        "diluent_name": config.diluent_name,
        "marker_enabled": config.marker_enabled,
        "marker_name": config.marker_name,
        "marker_volume_ul": config.marker_volume_ul,
        "lane_count_mode": config.lane_count_mode,
        "fixed_lane_count": config.fixed_lane_count,
        "min_pipette_volume_ul": config.min_pipette_volume_ul,
    }


def wb_sample_input_to_dict(sample: WBSampleInput) -> dict[str, Any]:
    return {
        "sample_name": sample.sample_name,
        "concentration_ug_per_ul": sample.concentration_ug_per_ul,
        "note": sample.note,
    }


def wb_loading_result_row_to_dict(row: WBLoadingResultRow) -> dict[str, Any]:
    return {
        "sample_name": row.sample_name,
        "concentration_ug_per_ul": row.concentration_ug_per_ul,
        "target_protein_ug": row.target_protein_ug,
        "sample_volume_ul": row.sample_volume_ul,
        "loading_buffer_volume_ul": row.loading_buffer_volume_ul,
        "reducing_agent_volume_ul": row.reducing_agent_volume_ul,
        "diluent_volume_ul": row.diluent_volume_ul,
        "final_volume_ul": row.final_volume_ul,
        "warnings": list(row.warnings),
        "errors": list(row.errors),
        "note": row.note,
        "status": row.status,
    }


def wb_lane_to_dict(lane: WBLane) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "lane_index": lane.lane_index,
        "lane_label": lane.lane_label,
        "lane_type": lane.lane_type,
        "sample_name": lane.sample_name,
        "marker_volume_ul": lane.marker_volume_ul,
        "warnings": list(lane.warnings),
        "errors": list(lane.errors),
        "note": lane.note,
        "status": _lane_status(lane),
    }
    if lane.result_row is not None:
        payload["result_row"] = wb_loading_result_row_to_dict(lane.result_row)
    return payload


def wb_loading_result_to_dict(result: WBLoadingResult) -> dict[str, Any]:
    return {
        "config": wb_loading_config_to_dict(result.config),
        "rows": [wb_loading_result_row_to_dict(row) for row in result.rows],
        "lanes": [wb_lane_to_dict(lane) for lane in result.lanes],
        "lane_layout_table": [list(row) for row in result.lane_layout_table],
        "steps": list(result.steps),
        "review_notice": result.review_notice,
        "summary_warnings": list(result.summary_warnings),
        "summary_errors": list(result.summary_errors),
        "summary_status": result_summary_status(result),
    }


def result_summary_status(result: WBLoadingResult) -> str:
    if result.summary_errors or any(row.errors for row in result.rows):
        return "Error"
    if result.summary_warnings or any(row.warnings for row in result.rows):
        return "Warning"
    return "OK"


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


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []


def _fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")
