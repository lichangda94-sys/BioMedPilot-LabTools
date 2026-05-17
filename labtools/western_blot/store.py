from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from labtools.western_blot.exporter import export_wb_loading_record_csv, export_wb_loading_record_markdown
from labtools.western_blot.models import WBLoadingRecord, WBLoadingRecordError, utc_now
from labtools.shared.storage import default_storage_root


WB_LOADING_RECORD_STORE_SCHEMA_VERSION = "western_blot_loading_record_store.v1"


def default_wb_loading_record_store_path() -> Path:
    return default_storage_root() / "labtools" / "western_blot" / "loading_records.json"


@dataclass
class WBLoadingRecordStore:
    path: Path | None = None

    def resolved_path(self) -> Path:
        return self.path or default_wb_loading_record_store_path()

    def list_records(self) -> tuple[WBLoadingRecord, ...]:
        return self.load()

    def load(self) -> tuple[WBLoadingRecord, ...]:
        path = self.resolved_path()
        if not path.exists():
            return ()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise WBLoadingRecordError("Western Blot 上样记录 JSON 不是有效 JSON。") from exc
        except OSError as exc:
            raise WBLoadingRecordError("无法读取 Western Blot 上样记录 JSON。") from exc
        return records_from_store_payload(payload)

    def save_record(self, record: WBLoadingRecord) -> WBLoadingRecord:
        records = list(self.load())
        updated = record.with_updated_timestamp()
        for index, existing in enumerate(records):
            if existing.record_id == record.record_id:
                records[index] = updated
                self.save_all(tuple(records))
                return updated
        records.append(updated)
        self.save_all(tuple(records))
        return updated

    def save_all(self, records: tuple[WBLoadingRecord, ...]) -> Path:
        path = self.resolved_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": WB_LOADING_RECORD_STORE_SCHEMA_VERSION,
            "updated_at": utc_now(),
            "records": [record.to_dict() for record in records],
        }
        try:
            _atomic_write_json(path, payload)
        except OSError as exc:
            raise WBLoadingRecordError("无法写入 Western Blot 上样记录 JSON，请检查路径权限。") from exc
        return path

    def get_record(self, record_id: str) -> WBLoadingRecord:
        for record in self.load():
            if record.record_id == record_id:
                return record
        raise WBLoadingRecordError("Western Blot 上样记录不存在。")

    def delete_record(self, record_id: str, *, confirmed: bool = False) -> tuple[WBLoadingRecord, ...]:
        if not confirmed:
            raise WBLoadingRecordError("删除 Western Blot 上样记录前需要确认。")
        records = self.load()
        if not any(record.record_id == record_id for record in records):
            raise WBLoadingRecordError("Western Blot 上样记录不存在。")
        remaining = tuple(record for record in records if record.record_id != record_id)
        self.save_all(remaining)
        return remaining

    def export_record_markdown(self, record: WBLoadingRecord, output_path: str | Path) -> Path:
        return export_wb_loading_record_markdown(record, output_path)

    def export_record_csv(self, record: WBLoadingRecord, output_path: str | Path) -> Path:
        return export_wb_loading_record_csv(record, output_path)


def records_from_store_payload(payload: Any) -> tuple[WBLoadingRecord, ...]:
    if not isinstance(payload, dict):
        raise WBLoadingRecordError("Western Blot 上样记录 payload 必须是 JSON object。")
    if payload.get("schema_version") != WB_LOADING_RECORD_STORE_SCHEMA_VERSION:
        raise WBLoadingRecordError("Western Blot 上样记录 store schema 不匹配。")
    raw_records = payload.get("records")
    if not isinstance(raw_records, list):
        raise WBLoadingRecordError("Western Blot 上样记录 JSON 缺少 records 列表。")
    return tuple(WBLoadingRecord.from_dict(item) for item in raw_records)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)
