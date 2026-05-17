from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

from labtools.western_blot.models import WBLoadingRecord


def wb_loading_record_markdown(record: WBLoadingRecord) -> str:
    config = record.config_snapshot
    result = record.result_snapshot
    rows = _list(result.get("rows"))
    lane_layout = record.lane_layout_snapshot or tuple(tuple(str(cell) for cell in row) for row in _list(result.get("lane_layout_table")) if isinstance(row, list | tuple))
    lines = [
        "# Western Blot 上样记录",
        "",
        f"实验名称：{record.experiment_name}",
        f"创建时间：{record.created_at}",
        f"目标蛋白量：{_fmt(config.get('target_protein_ug'))} µg/lane",
        f"目标终体积：{_fmt(config.get('final_volume_ul'))} µL/lane",
        f"Loading buffer：{_fmt(config.get('loading_buffer_factor'))}X",
        f"还原剂：{_reducing_text(config)}",
        f"补足液：{config.get('diluent_name') or 'ddH2O'}",
        f"Marker：{_marker_text(config)}",
        f"状态：{record.summary_status}",
        "",
        "## 样本计算明细",
        "",
        f"| 样本 | 浓度 (µg/µL) | 样本体积 (µL) | Loading buffer (µL) | 还原剂 (µL) | {config.get('diluent_name') or '补足液'} (µL) | 状态 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row.get("sample_name") or ""),
                    _fmt(row.get("concentration_ug_per_ul")),
                    _fmt(row.get("sample_volume_ul")),
                    _fmt(row.get("loading_buffer_volume_ul")),
                    _fmt(row.get("reducing_agent_volume_ul")),
                    _fmt(row.get("diluent_volume_ul")),
                    str(row.get("status") or ""),
                )
            )
            + " |"
        )
    lines.extend(["", "## 横向 Lane Layout", ""])
    if lane_layout:
        header = tuple(lane_layout[0])
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join("---" for _ in header) + "|")
        for layout_row in lane_layout[1:]:
            lines.append("| " + " | ".join(layout_row) + " |")
    lines.extend(["", "## Warning / Error", ""])
    warnings_errors = _warnings_errors(rows, result)
    if warnings_errors:
        lines.extend(f"- {item}" for item in warnings_errors)
    else:
        lines.append("- 无")
    lines.extend(["", "## 操作步骤", ""])
    lines.extend(str(step) for step in _list(result.get("steps")))
    lines.extend(["", "## 人工复核提示", "", str(result.get("review_notice") or "")])
    if record.notes:
        lines.extend(["", "## 备注", "", record.notes])
    return "\n".join(lines).rstrip() + "\n"


def wb_loading_record_csv(record: WBLoadingRecord) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        (
            "experiment_name",
            "sample_name",
            "concentration_ug_per_ul",
            "target_protein_ug",
            "sample_volume_ul",
            "loading_buffer_volume_ul",
            "reducing_agent_name",
            "reducing_agent_volume_ul",
            "diluent_name",
            "diluent_volume_ul",
            "final_volume_ul",
            "status",
            "warnings",
            "errors",
        )
    )
    config = record.config_snapshot
    reducing_name = str(config.get("reducing_agent_name") or "")
    diluent_name = str(config.get("diluent_name") or "ddH2O")
    for row in _list(record.result_snapshot.get("rows")):
        if not isinstance(row, dict):
            continue
        writer.writerow(
            (
                record.experiment_name,
                row.get("sample_name", ""),
                row.get("concentration_ug_per_ul", ""),
                row.get("target_protein_ug", ""),
                row.get("sample_volume_ul", ""),
                row.get("loading_buffer_volume_ul", ""),
                reducing_name,
                row.get("reducing_agent_volume_ul", ""),
                diluent_name,
                row.get("diluent_volume_ul", ""),
                row.get("final_volume_ul", ""),
                row.get("status", ""),
                "; ".join(str(item) for item in _list(row.get("warnings"))),
                "; ".join(str(item) for item in _list(row.get("errors"))),
            )
        )
    writer.writerow(())
    writer.writerow(("lane_layout",))
    writer.writerow(
        (
            "lane_index",
            "lane_type",
            "lane_label",
            "sample_name",
            "sample_volume_ul",
            "loading_buffer_volume_ul",
            "reducing_agent_volume_ul",
            "diluent_volume_ul",
            "status",
            "warnings",
            "errors",
        )
    )
    for lane in _list(record.result_snapshot.get("lanes")):
        if not isinstance(lane, dict):
            continue
        result_row = lane.get("result_row") if isinstance(lane.get("result_row"), dict) else {}
        writer.writerow(
            (
                lane.get("lane_index", ""),
                lane.get("lane_type", ""),
                lane.get("lane_label", ""),
                lane.get("sample_name", ""),
                result_row.get("sample_volume_ul", "") if result_row else lane.get("marker_volume_ul", ""),
                result_row.get("loading_buffer_volume_ul", "") if result_row else "",
                result_row.get("reducing_agent_volume_ul", "") if result_row else "",
                result_row.get("diluent_volume_ul", "") if result_row else "",
                lane.get("status", ""),
                "; ".join(str(item) for item in _list(lane.get("warnings"))),
                "; ".join(str(item) for item in _list(lane.get("errors"))),
            )
        )
    return output.getvalue()


def export_wb_loading_record_markdown(record: WBLoadingRecord, output_path: str | Path) -> Path:
    path = _available_path(_resolve_output_path(output_path, ".md"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(wb_loading_record_markdown(record), encoding="utf-8")
    return path


def export_wb_loading_record_csv(record: WBLoadingRecord, output_path: str | Path) -> Path:
    path = _available_path(_resolve_output_path(output_path, ".csv"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(wb_loading_record_csv(record), encoding="utf-8", newline="")
    return path


def _resolve_output_path(output_path: str | Path, suffix: str) -> Path:
    path = Path(output_path)
    if path.suffix.lower() != suffix:
        path = path.with_suffix(suffix)
    return path


def _available_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(1, 1000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError("无法生成不覆盖已有文件的导出路径。")


def _reducing_text(config: dict[str, Any]) -> str:
    mode = str(config.get("reducing_agent_mode") or "none")
    if mode == "none":
        return "none"
    name = str(config.get("reducing_agent_name") or "还原剂")
    if mode == "fixed_volume":
        return f"{name}, {_fmt(config.get('reducing_agent_fixed_volume_ul'))} µL"
    return f"{name}, {_fmt(config.get('reducing_agent_percent'))}% final volume"


def _marker_text(config: dict[str, Any]) -> str:
    if not config.get("marker_enabled"):
        return "disabled"
    return f"{config.get('marker_name') or 'Protein Marker'}, {_fmt(config.get('marker_volume_ul'))} µL"


def _warnings_errors(rows: list[Any], result: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("sample_name") or "样本")
        for warning in _list(row.get("warnings")):
            items.append(f"{name}: {warning}")
        for error in _list(row.get("errors")):
            items.append(f"{name}: {error}")
    items.extend(str(item) for item in _list(result.get("summary_warnings")))
    items.extend(str(item) for item in _list(result.get("summary_errors")))
    return items


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []


def _fmt(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{float(value):.3f}".rstrip("0").rstrip(".")
    if value is None:
        return ""
    return str(value)
