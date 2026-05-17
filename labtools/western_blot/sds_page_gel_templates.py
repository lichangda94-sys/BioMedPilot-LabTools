from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
from xml.sax.saxutils import escape


LABTOOLS_SDS_PAGE_GEL_TEMPLATE_STORE_SCHEMA_VERSION = "labtools_sds_page_gel_template_store.v1"
SDS_PAGE_GEL_TEMPLATE_EXPORT_TYPE = "labtools_sds_page_gel_template"
SOFTWARE_CHANNEL = "Developer Preview / testing"
GEL_REVIEW_STATUS = "manual_review_required"
GEL_REVIEW_NOTICE = "结果为实验辅助计算草稿，使用前请按试剂盒说明书和实验室 SOP 人工核对"
GEL_TEMPLATE_CONTEXT_NOTICE = "基于用户录入的试剂盒/实验室模板进行批量换算"
GEL_SAFETY_NOTE = (
    "本地模板仅保存用户录入的 SDS-PAGE 配胶模板字段；不内置通用配方、不自动推荐胶浓度、"
    "不生成操作步骤。"
)
GEL_PERSISTENCE_NOTE = "仅在用户明确选择本地 JSON 路径后写盘；不自动保存、不进数据库、不云同步。"
SUPPORTED_GEL_COMPONENT_UNITS = ("µL", "mL", "mg", "g")
DEFAULT_OVERAGE_PERCENT = 3.0


class SdsPageGelTemplateError(ValueError):
    pass


@dataclass(frozen=True)
class GelComponent:
    component_name: str
    amount_per_gel: float
    unit: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_name": self.component_name,
            "amount_per_gel": self.amount_per_gel,
            "unit": self.unit,
            "note": self.note,
        }


@dataclass(frozen=True)
class GelSection:
    section_name: str
    components: tuple[GelComponent, ...] = ()
    is_used: bool = True
    note: str = ""

    @property
    def active_components(self) -> tuple[GelComponent, ...]:
        if not self.is_used:
            return ()
        return tuple(component for component in self.components if component.amount_per_gel > 0)

    @property
    def is_active(self) -> bool:
        return bool(self.active_components)

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_name": self.section_name,
            "is_used": self.is_used,
            "note": self.note,
            "components": [component.to_dict() for component in self.components],
        }


@dataclass(frozen=True)
class SdsPageGelTemplate:
    template_id: str
    template_name: str
    template_version: str
    gel_concentration: str
    gel_thickness: str
    well_count: str
    gel_format_or_note: str
    kit_or_sop_source: str
    resolving_gel_section: GelSection
    stacking_gel_section: GelSection
    created_at: str = ""
    updated_at: str = ""
    review_status: str = GEL_REVIEW_STATUS
    safety_note: str = GEL_SAFETY_NOTE

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at or _utc_now()
        updated_at = self.updated_at or created_at
        return {
            "template_id": self.template_id,
            "template_name": self.template_name,
            "template_version": self.template_version,
            "gel_concentration": self.gel_concentration,
            "gel_thickness": self.gel_thickness,
            "well_count": self.well_count,
            "gel_format_or_note": self.gel_format_or_note,
            "kit_or_sop_source": self.kit_or_sop_source,
            "created_at": created_at,
            "updated_at": updated_at,
            "review_status": self.review_status,
            "safety_note": self.safety_note,
            "resolving_gel_section": self.resolving_gel_section.to_dict(),
            "stacking_gel_section": self.stacking_gel_section.to_dict(),
        }


@dataclass(frozen=True)
class SdsPageGelCalculationInput:
    template: SdsPageGelTemplate
    gel_count: int
    overage_percent: float = DEFAULT_OVERAGE_PERCENT


@dataclass(frozen=True)
class GelComponentCalculationRow:
    component_name: str
    amount_per_gel: float
    unit: str
    gel_count: int
    overage_percent: float
    total_amount: float
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_name": self.component_name,
            "amount_per_gel": self.amount_per_gel,
            "unit": self.unit,
            "gel_count": self.gel_count,
            "overage_percent": self.overage_percent,
            "total_amount": self.total_amount,
            "note": self.note,
        }


@dataclass(frozen=True)
class GelSectionCalculationResult:
    section_name: str
    rows: tuple[GelComponentCalculationRow, ...]
    section_note: str = ""

    @property
    def is_used(self) -> bool:
        return bool(self.rows)


@dataclass(frozen=True)
class SdsPageGelCalculationResult:
    template: SdsPageGelTemplate
    gel_count: int
    overage_percent: float
    calculated_at: str
    resolving_gel: GelSectionCalculationResult
    stacking_gel: GelSectionCalculationResult
    review_notice: str = GEL_REVIEW_NOTICE
    context_notice: str = GEL_TEMPLATE_CONTEXT_NOTICE

    def to_dict(self) -> dict[str, Any]:
        return {
            "template": self.template.to_dict(),
            "gel_count": self.gel_count,
            "overage_percent": self.overage_percent,
            "calculated_at": self.calculated_at,
            "review_notice": self.review_notice,
            "context_notice": self.context_notice,
            "resolving_gel": [row.to_dict() for row in self.resolving_gel.rows],
            "stacking_gel": [row.to_dict() for row in self.stacking_gel.rows],
        }


@dataclass(frozen=True)
class GelTemplateImportResult:
    action: str
    template: SdsPageGelTemplate | None
    conflict_detected: bool
    message: str


@dataclass
class SdsPageGelTemplateStore:
    templates: tuple[SdsPageGelTemplate, ...] = ()

    def list_templates(self) -> tuple[SdsPageGelTemplate, ...]:
        return self.templates

    def has_conflict(self, template: SdsPageGelTemplate) -> bool:
        return any(
            current.template_id == template.template_id or current.template_name == template.template_name
            for current in self.templates
        )

    def import_template(self, template: SdsPageGelTemplate, *, conflict_policy: str = "skip") -> GelTemplateImportResult:
        conflict = self.has_conflict(template)
        if conflict and conflict_policy == "skip":
            return GelTemplateImportResult(
                action="skipped",
                template=None,
                conflict_detected=True,
                message="检测到同名或同 ID 模板，可跳过或作为副本导入",
            )
        imported = clone_template_as_copy(template) if conflict else template
        self.templates = self.templates + (imported,)
        return GelTemplateImportResult(
            action="copied" if conflict else "imported",
            template=imported,
            conflict_detected=conflict,
            message="作为副本导入" if conflict else "导入成功",
        )


def calculate_sds_page_gel_batch(input_data: SdsPageGelCalculationInput) -> SdsPageGelCalculationResult:
    validate_template(input_data.template)
    gel_count = input_data.gel_count
    if not isinstance(gel_count, int) or gel_count <= 0:
        raise SdsPageGelTemplateError("胶数量需要为正整数")
    if input_data.overage_percent < 0:
        raise SdsPageGelTemplateError("余量百分比不能小于 0")
    return SdsPageGelCalculationResult(
        template=input_data.template,
        gel_count=gel_count,
        overage_percent=input_data.overage_percent,
        calculated_at=_utc_now(),
        resolving_gel=_calculate_section(input_data.template.resolving_gel_section, gel_count, input_data.overage_percent),
        stacking_gel=_calculate_section(input_data.template.stacking_gel_section, gel_count, input_data.overage_percent),
    )


def validate_template(template: SdsPageGelTemplate) -> None:
    if not template.template_name.strip():
        raise SdsPageGelTemplateError("需要填写模板名称")
    _validate_section(template.resolving_gel_section)
    _validate_section(template.stacking_gel_section)
    if not template.resolving_gel_section.is_active and not template.stacking_gel_section.is_active:
        raise SdsPageGelTemplateError("至少需要一个有效的胶 section")


def build_sds_page_gel_template_payload(template: SdsPageGelTemplate) -> dict[str, Any]:
    validate_template(template)
    return {
        "schema_version": LABTOOLS_SDS_PAGE_GEL_TEMPLATE_STORE_SCHEMA_VERSION,
        "export_type": SDS_PAGE_GEL_TEMPLATE_EXPORT_TYPE,
        "created_at": _utc_now(),
        "software_channel": SOFTWARE_CHANNEL,
        "review_status": GEL_REVIEW_STATUS,
        "template": template.to_dict(),
        "safety_note": GEL_SAFETY_NOTE,
        "persistence_note": GEL_PERSISTENCE_NOTE,
        "review_notice": GEL_REVIEW_NOTICE,
        "context_notice": GEL_TEMPLATE_CONTEXT_NOTICE,
    }


def save_sds_page_gel_template_json(template: SdsPageGelTemplate, output_path: str | Path | None) -> Path:
    path = _resolve_output_file(output_path, ".json", "sds_page_gel_template")
    payload = build_sds_page_gel_template_payload(template)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    except FileExistsError as exc:
        raise SdsPageGelTemplateError("保存目标文件已存在，已停止以避免覆盖。") from exc
    except OSError as exc:
        raise SdsPageGelTemplateError("无法写入 SDS-PAGE 配胶模板 JSON，请检查路径权限。") from exc
    return path


def load_sds_page_gel_template_json(input_path: str | Path | None) -> SdsPageGelTemplate:
    path = _input_file(input_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SdsPageGelTemplateError("模板 JSON 无效，无法导入") from exc
    except OSError as exc:
        raise SdsPageGelTemplateError("模板 JSON 无效，无法导入") from exc
    if payload.get("schema_version") != LABTOOLS_SDS_PAGE_GEL_TEMPLATE_STORE_SCHEMA_VERSION:
        raise SdsPageGelTemplateError("模板 JSON 无效，无法导入")
    template = _template_from_dict(payload.get("template"))
    validate_template(template)
    return template


def clone_template_as_copy(template: SdsPageGelTemplate) -> SdsPageGelTemplate:
    timestamp = _utc_now()
    return replace(
        template,
        template_id=f"{template.template_id}_copy_{uuid4().hex[:8]}",
        template_name=f"{template.template_name} 副本",
        created_at=timestamp,
        updated_at=timestamp,
    )


def save_sds_page_gel_calculation_xlsx(result: SdsPageGelCalculationResult, output_path: str | Path | None) -> Path:
    path = _resolve_output_file(output_path, ".xlsx", "sds_page_gel_calculation")
    workbook = _build_xlsx_workbook(
        {
            "Summary": _summary_rows(result),
            "分离胶": _section_rows(result.resolving_gel, result.gel_count, result.overage_percent),
            "浓缩胶": _section_rows(result.stacking_gel, result.gel_count, result.overage_percent),
        }
    )
    try:
        with path.open("xb") as handle:
            handle.write(workbook)
    except FileExistsError as exc:
        raise SdsPageGelTemplateError("导出失败，请检查目标文件夹是否可写") from exc
    except OSError as exc:
        raise SdsPageGelTemplateError("导出失败，请检查目标文件夹是否可写") from exc
    return path


def _validate_section(section: GelSection) -> None:
    if not section.is_used:
        return
    for component in section.components:
        if not component.component_name.strip():
            raise SdsPageGelTemplateError("需要填写组分名称")
        if component.amount_per_gel < 0:
            raise SdsPageGelTemplateError("组分用量不能小于 0")
        if component.unit not in SUPPORTED_GEL_COMPONENT_UNITS:
            raise SdsPageGelTemplateError("暂不支持该单位")


def _calculate_section(section: GelSection, gel_count: int, overage_percent: float) -> GelSectionCalculationResult:
    rows = tuple(
        GelComponentCalculationRow(
            component_name=component.component_name,
            amount_per_gel=component.amount_per_gel,
            unit=component.unit,
            gel_count=gel_count,
            overage_percent=overage_percent,
            total_amount=component.amount_per_gel * gel_count * (1 + overage_percent / 100),
            note=component.note,
        )
        for component in section.active_components
    )
    return GelSectionCalculationResult(section_name=section.section_name, rows=rows, section_note=section.note)


def _template_from_dict(payload: Any) -> SdsPageGelTemplate:
    if not isinstance(payload, dict):
        raise SdsPageGelTemplateError("模板 JSON 无效，无法导入")
    return SdsPageGelTemplate(
        template_id=str(payload.get("template_id") or f"sds_page_gel_template_{uuid4().hex[:8]}"),
        template_name=str(payload.get("template_name") or ""),
        template_version=str(payload.get("template_version") or "v1"),
        gel_concentration=str(payload.get("gel_concentration") or ""),
        gel_thickness=str(payload.get("gel_thickness") or "1.0 mm"),
        well_count=str(payload.get("well_count") or "10 wells"),
        gel_format_or_note=str(payload.get("gel_format_or_note") or ""),
        kit_or_sop_source=str(payload.get("kit_or_sop_source") or ""),
        created_at=str(payload.get("created_at") or _utc_now()),
        updated_at=str(payload.get("updated_at") or _utc_now()),
        review_status=str(payload.get("review_status") or GEL_REVIEW_STATUS),
        safety_note=str(payload.get("safety_note") or GEL_SAFETY_NOTE),
        resolving_gel_section=_section_from_dict(payload.get("resolving_gel_section"), "分离胶"),
        stacking_gel_section=_section_from_dict(payload.get("stacking_gel_section"), "浓缩胶"),
    )


def _section_from_dict(payload: Any, default_name: str) -> GelSection:
    if not isinstance(payload, dict):
        return GelSection(section_name=default_name, components=(), is_used=False)
    raw_components = payload.get("components") or ()
    if not isinstance(raw_components, list):
        raise SdsPageGelTemplateError("模板 JSON 无效，无法导入")
    return GelSection(
        section_name=str(payload.get("section_name") or default_name),
        is_used=bool(payload.get("is_used", True)),
        note=str(payload.get("note") or ""),
        components=tuple(_component_from_dict(item) for item in raw_components),
    )


def _component_from_dict(payload: Any) -> GelComponent:
    if not isinstance(payload, dict):
        raise SdsPageGelTemplateError("模板 JSON 无效，无法导入")
    try:
        amount = float(payload.get("amount_per_gel"))
    except (TypeError, ValueError) as exc:
        raise SdsPageGelTemplateError("模板 JSON 无效，无法导入") from exc
    return GelComponent(
        component_name=str(payload.get("component_name") or ""),
        amount_per_gel=amount,
        unit=str(payload.get("unit") or ""),
        note=str(payload.get("note") or ""),
    )


def _summary_rows(result: SdsPageGelCalculationResult) -> list[list[Any]]:
    template = result.template
    return [
        ["字段", "值"],
        ["模板名称", template.template_name],
        ["模板版本", template.template_version],
        ["胶浓度", template.gel_concentration],
        ["胶厚度", template.gel_thickness],
        ["孔数", template.well_count],
        ["胶数量", result.gel_count],
        ["余量百分比", result.overage_percent],
        ["计算时间", result.calculated_at],
        ["模板来源", template.kit_or_sop_source],
        ["人工核对提示", result.review_notice],
        ["备注", template.gel_format_or_note],
    ]


def _section_rows(section: GelSectionCalculationResult, gel_count: int, overage_percent: float) -> list[list[Any]]:
    rows: list[list[Any]] = [["组分名称", "每块胶用量", "单位", "胶数量", "余量百分比", "总量含余量", "备注"]]
    rows.extend(
        [
            row.component_name,
            row.amount_per_gel,
            row.unit,
            gel_count,
            overage_percent,
            row.total_amount,
            row.note,
        ]
        for row in section.rows
    )
    return rows


def _build_xlsx_workbook(sheets: dict[str, list[list[Any]]]) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml(len(sheets)))
        archive.writestr("_rels/.rels", _root_rels_xml())
        archive.writestr("docProps/core.xml", _core_xml())
        archive.writestr("docProps/app.xml", _app_xml())
        archive.writestr("xl/workbook.xml", _workbook_xml(tuple(sheets)))
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml(len(sheets)))
        for index, rows in enumerate(sheets.values(), start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _worksheet_xml(rows))
    return buffer.getvalue()


def _worksheet_xml(rows: list[list[Any]]) -> str:
    row_xml: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: list[str] = []
        for column_index, value in enumerate(row, start=1):
            ref = f"{_column_name(column_index)}{row_index}"
            if isinstance(value, int | float) and not isinstance(value, bool):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData></worksheet>'
    )


def _workbook_xml(sheet_names: tuple[str, ...]) -> str:
    sheets = "".join(
        f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, name in enumerate(sheet_names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheets}</sheets></workbook>"
    )


def _content_types_xml(sheet_count: int) -> str:
    sheet_types = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        f"{sheet_types}</Types>"
    )


def _root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )


def _workbook_rels_xml(sheet_count: int) -> str:
    rels = "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>'
    )


def _core_xml() -> str:
    now = _utc_now().replace("+00:00", "Z")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:creator>LabTools</dc:creator><dc:title>SDS-PAGE gel calculation</dc:title>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def _app_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>LabTools</Application></Properties>"
    )


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _resolve_output_file(output_path: str | Path | None, suffix: str, default_stem: str) -> Path:
    if output_path is None or str(output_path).strip() == "":
        raise SdsPageGelTemplateError("请选择保存路径。")
    requested = Path(output_path).expanduser()
    if requested.exists() and requested.is_dir():
        requested = requested / f"{default_stem}{suffix}"
    if requested.suffix.lower() != suffix:
        requested = requested.with_suffix(suffix)
    parent = requested.parent
    if not parent.exists() or not parent.is_dir():
        raise SdsPageGelTemplateError("导出失败，请检查目标文件夹是否可写")
    return _non_overwriting_path(requested, default_stem)


def _input_file(input_path: str | Path | None) -> Path:
    if input_path is None or str(input_path).strip() == "":
        raise SdsPageGelTemplateError("模板 JSON 无效，无法导入")
    path = Path(input_path).expanduser()
    if not path.exists() or not path.is_file():
        raise SdsPageGelTemplateError("模板 JSON 无效，无法导入")
    return path


def _non_overwriting_path(path: Path, default_stem: str) -> Path:
    safe_name = _sanitize_filename(path.stem, default_stem)
    candidate = path.with_name(f"{safe_name}{path.suffix}")
    for index in range(1000):
        numbered = candidate if index == 0 else candidate.with_name(f"{safe_name}_{index:03d}{path.suffix}")
        if not numbered.exists():
            return numbered
    raise SdsPageGelTemplateError("导出失败，请检查目标文件夹是否可写")


def _sanitize_filename(value: str, default_stem: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._-")
    return sanitized[:96] or default_stem


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
