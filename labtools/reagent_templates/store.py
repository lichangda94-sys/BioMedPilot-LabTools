from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from labtools.reagent_templates.calculator import detect_template_cycles, validate_template
from labtools.reagent_templates.models import (
    LABTOOLS_REAGENT_TEMPLATE_STORE_SCHEMA_VERSION,
    ReagentTemplate,
    ReagentTemplateError,
    utc_now,
)
from labtools.shared.storage import default_storage_root


def default_reagent_template_store_path() -> Path:
    return default_storage_root() / "labtools" / "reagent_templates.json"


@dataclass
class ReagentTemplateStore:
    path: Path | None = None

    def resolved_path(self) -> Path:
        return self.path or default_reagent_template_store_path()

    def list_templates(self) -> tuple[ReagentTemplate, ...]:
        return self.load()

    def load(self) -> tuple[ReagentTemplate, ...]:
        path = self.resolved_path()
        if not path.exists():
            return ()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ReagentTemplateError("试剂模板 JSON 不是有效 JSON。") from exc
        except OSError as exc:
            raise ReagentTemplateError("无法读取试剂模板 JSON。") from exc
        if payload.get("schema_version") != LABTOOLS_REAGENT_TEMPLATE_STORE_SCHEMA_VERSION:
            raise ReagentTemplateError("试剂模板 JSON schema 不匹配。")
        raw_templates = payload.get("templates")
        if not isinstance(raw_templates, list):
            raise ReagentTemplateError("试剂模板 JSON 缺少 templates 列表。")
        templates = tuple(ReagentTemplate.from_dict(item).normalized_for_storage() for item in raw_templates)
        self._validate_all(templates)
        return templates

    def save_all(self, templates: tuple[ReagentTemplate, ...]) -> Path:
        templates = tuple(template.normalized_for_storage() for template in templates)
        self._validate_all(templates)
        path = self.resolved_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": LABTOOLS_REAGENT_TEMPLATE_STORE_SCHEMA_VERSION,
            "updated_at": utc_now(),
            "templates": [template.to_dict() for template in templates],
        }
        try:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError as exc:
            raise ReagentTemplateError("无法写入试剂模板 JSON，请检查路径权限。") from exc
        return path

    def upsert_template(self, template: ReagentTemplate) -> ReagentTemplate:
        templates = list(self.load())
        updated = template.normalized_for_storage().with_updated_timestamp()
        for index, existing in enumerate(templates):
            if existing.template_id == template.template_id:
                templates[index] = updated
                self.save_all(tuple(templates))
                return updated
        templates.append(updated)
        self.save_all(tuple(templates))
        return updated

    def copy_template(self, template_id: str) -> ReagentTemplate:
        templates = list(self.load())
        source = self._get_from_list(templates, template_id)
        copied = source.renamed_copy()
        templates.append(copied)
        self.save_all(tuple(templates))
        return copied

    def delete_template(self, template_id: str, *, confirmed: bool = False) -> tuple[ReagentTemplate, ...]:
        if not confirmed:
            raise ReagentTemplateError("删除模板前需要确认。")
        templates = list(self.load())
        if not any(template.template_id == template_id for template in templates):
            raise ReagentTemplateError("要删除的模板不存在。")
        remaining = tuple(template for template in templates if template.template_id != template_id)
        self.save_all(remaining)
        return remaining

    def _validate_all(self, templates: tuple[ReagentTemplate, ...]) -> None:
        ids: set[str] = set()
        for template in templates:
            if template.template_id in ids:
                raise ReagentTemplateError("试剂模板 template_id 重复。")
            ids.add(template.template_id)
            validate_template(template)
        _validate_references(templates)
        detect_template_cycles(templates)

    def _get_from_list(self, templates: list[ReagentTemplate], template_id: str) -> ReagentTemplate:
        for template in templates:
            if template.template_id == template_id:
                return template
        raise ReagentTemplateError("模板不存在。")


def _validate_references(templates: tuple[ReagentTemplate, ...]) -> None:
    ids = {template.template_id for template in templates}
    for template in templates:
        for component in template.components:
            if component.component_type == "self_prepared_template" and component.referenced_template_id and component.referenced_template_id not in ids:
                raise ReagentTemplateError(f"{template.name} 的组分 {component.name} 引用了不存在的子模板。")


def reagent_template_store_payload_from_dict(payload: Any) -> tuple[ReagentTemplate, ...]:
    if not isinstance(payload, dict):
        raise ReagentTemplateError("试剂模板 payload 必须是 JSON object。")
    if payload.get("schema_version") != LABTOOLS_REAGENT_TEMPLATE_STORE_SCHEMA_VERSION:
        raise ReagentTemplateError("试剂模板 JSON schema 不匹配。")
    raw_templates = payload.get("templates")
    if not isinstance(raw_templates, list):
        raise ReagentTemplateError("试剂模板 JSON 缺少 templates 列表。")
    return tuple(ReagentTemplate.from_dict(item) for item in raw_templates)
