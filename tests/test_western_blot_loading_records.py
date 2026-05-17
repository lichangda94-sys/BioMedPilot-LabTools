from __future__ import annotations

import csv
from io import StringIO

import pytest

from labtools.western_blot import (
    WBLoadingConfig,
    WBLoadingRecord,
    WBLoadingRecordError,
    WBLoadingRecordStore,
    WBSampleInput,
    calculate_wb_loading,
    wb_loading_record_csv,
    wb_loading_record_markdown,
)


def _test_a_record() -> WBLoadingRecord:
    samples = (
        WBSampleInput("S1", 2.0),
        WBSampleInput("S2", 1.5),
        WBSampleInput("S3", 1.0),
        WBSampleInput("S4", 0.8),
        WBSampleInput("S5", 4.0),
    )
    result = calculate_wb_loading(
        WBLoadingConfig(
            experiment_name="WB test A",
            target_protein_ug=20,
            final_volume_ul=20,
            loading_buffer_factor=4,
            reducing_agent_mode="none",
            diluent_name="ddH2O",
        ),
        samples,
    )
    return WBLoadingRecord.from_result(result, samples, operator_name="Tester", project_name="L4.2", notes="acceptance")


def test_wb_loading_record_model_captures_result_snapshot() -> None:
    record = _test_a_record()

    assert record.schema_version == "western_blot_loading_record.v1"
    assert record.record_id
    assert record.created_at
    assert record.updated_at
    assert record.experiment_name == "WB test A"
    assert record.config_snapshot["target_protein_ug"] == 20
    assert len(record.sample_inputs_snapshot) == 5
    assert len(record.result_snapshot["rows"]) == 5
    assert len(record.result_snapshot["lanes"]) == 6
    assert record.lane_layout_snapshot[0][1] == "Lane 1"
    assert record.result_snapshot["steps"]
    assert "人工复核" in record.result_snapshot["review_notice"]
    assert record.summary_status == "Error"


def test_wb_loading_record_store_saves_reads_reloads_and_deletes(tmp_path) -> None:
    store = WBLoadingRecordStore(tmp_path / "loading_records.json")
    record = _test_a_record()

    assert store.list_records() == ()
    saved = store.save_record(record)
    assert store.list_records()[0].record_id == saved.record_id
    assert store.get_record(saved.record_id).experiment_name == "WB test A"

    reloaded = WBLoadingRecordStore(tmp_path / "loading_records.json")
    assert reloaded.get_record(saved.record_id).result_snapshot["rows"][0]["sample_name"] == "S1"

    reloaded.delete_record(saved.record_id, confirmed=True)
    assert reloaded.list_records() == ()


def test_wb_loading_record_store_rejects_bad_json(tmp_path) -> None:
    path = tmp_path / "loading_records.json"
    path.write_text("{bad json", encoding="utf-8")

    with pytest.raises(WBLoadingRecordError, match="不是有效 JSON"):
        WBLoadingRecordStore(path).list_records()


def test_wb_loading_markdown_formatter_contains_sections_and_boundaries() -> None:
    markdown = wb_loading_record_markdown(_test_a_record())

    assert "# Western Blot 上样记录" in markdown
    assert "实验名称：WB test A" in markdown
    assert "目标蛋白量：20 µg/lane" in markdown
    assert "Loading buffer：4X" in markdown
    for sample_name in ("S1", "S2", "S3", "S4", "S5"):
        assert sample_name in markdown
    assert "## 横向 Lane Layout" in markdown
    assert "Lane 1" in markdown
    assert "Protein Marker" in markdown
    assert "Lane 2" in markdown
    assert "Error" in markdown
    assert "## 人工复核提示" in markdown
    for forbidden in ("图像分析已启用", "自动条带识别已启用", "灰度定量已启用", "自动 ROI 已启用", "ImageJ-assisted 已可用于真实定量"):
        assert forbidden not in markdown


def test_wb_loading_csv_formatter_contains_rows_and_lane_layout() -> None:
    text = wb_loading_record_csv(_test_a_record())
    rows = list(csv.reader(StringIO(text)))

    header = rows[0]
    assert "sample_name" in header
    assert "sample_volume_ul" in header
    assert "loading_buffer_volume_ul" in header
    assert "diluent_volume_ul" in header
    assert "status" in header
    s1 = next(row for row in rows if len(row) > 1 and row[1] == "S1")
    assert s1[header.index("sample_volume_ul")] == "10.0"
    assert s1[header.index("loading_buffer_volume_ul")] == "5.0"
    assert s1[header.index("diluent_volume_ul")] == "5.0"
    assert s1[header.index("status")] == "OK"
    assert any(len(row) > 1 and row[1] == "S3" and "Error" in row for row in rows)
    assert any(row == ["lane_layout"] for row in rows)


def test_wb_loading_record_export_writes_markdown_and_csv(tmp_path) -> None:
    store = WBLoadingRecordStore(tmp_path / "loading_records.json")
    record = _test_a_record()
    md_path = store.export_record_markdown(record, tmp_path / "record.md")
    csv_path = store.export_record_csv(record, tmp_path / "record.csv")
    second_md_path = store.export_record_markdown(record, tmp_path / "record.md")

    assert md_path.read_text(encoding="utf-8").startswith("# Western Blot 上样记录")
    assert "sample_name" in csv_path.read_text(encoding="utf-8")
    assert second_md_path.name == "record_1.md"


def test_wb_loading_summary_status_ok_warning_error() -> None:
    ok = WBLoadingRecord.from_result(calculate_wb_loading(WBLoadingConfig(), (WBSampleInput("S1", 2),)), (WBSampleInput("S1", 2),))
    warning = WBLoadingRecord.from_result(
        calculate_wb_loading(WBLoadingConfig(target_protein_ug=1, min_pipette_volume_ul=0.5), (WBSampleInput("High", 10),)),
        (WBSampleInput("High", 10),),
    )
    error = _test_a_record()

    assert ok.summary_status == "OK"
    assert warning.summary_status == "Warning"
    assert error.summary_status == "Error"
