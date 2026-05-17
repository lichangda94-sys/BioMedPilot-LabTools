from __future__ import annotations

import json
import zipfile
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree

import pytest

from labtools.western_blot import (
    DEFAULT_OVERAGE_PERCENT,
    GEL_REVIEW_NOTICE,
    LABTOOLS_SDS_PAGE_GEL_TEMPLATE_STORE_SCHEMA_VERSION,
    SUPPORTED_GEL_COMPONENT_UNITS,
    GelComponent,
    GelSection,
    SdsPageGelCalculationInput,
    SdsPageGelTemplate,
    SdsPageGelTemplateError,
    SdsPageGelTemplateStore,
    calculate_sds_page_gel_batch,
    load_sds_page_gel_template_json,
    save_sds_page_gel_calculation_xlsx,
    save_sds_page_gel_template_json,
)


def _template(*, stacking_used: bool = True) -> SdsPageGelTemplate:
    return SdsPageGelTemplate(
        template_id="lab_template_10pct",
        template_name="实验室 10% 胶模板",
        template_version="v1",
        gel_concentration="10%",
        gel_thickness="1.0 mm",
        well_count="10 wells",
        gel_format_or_note="用户录入 mini gel 模板",
        kit_or_sop_source="用户录入的试剂盒说明书",
        resolving_gel_section=GelSection(
            "分离胶",
            (
                GelComponent("Acrylamide mix", 2.5, "mL", "用户记录：避光"),
                GelComponent("APS", 50, "µL", "最后加入"),
            ),
        ),
        stacking_gel_section=GelSection(
            "浓缩胶",
            (GelComponent("Stacking buffer", 1.0, "mL", "用户记录"),) if stacking_used else (),
            is_used=stacking_used,
        ),
    )


def _xlsx_sheet_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    return [sheet.attrib["name"] for sheet in workbook.findall(".//main:sheet", ns)]


def _xlsx_text(path: Path) -> str:
    values: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.startswith("xl/worksheets/sheet"):
                values.append(archive.read(name).decode("utf-8"))
    return "\n".join(values)


def test_create_valid_template_contains_required_sections() -> None:
    template = _template()

    assert template.template_name == "实验室 10% 胶模板"
    assert template.resolving_gel_section.section_name == "分离胶"
    assert template.stacking_gel_section.section_name == "浓缩胶"
    assert "resolving_gel_section" in template.to_dict()
    assert "stacking_gel_section" in template.to_dict()


def test_section_can_be_marked_zero_or_not_used() -> None:
    template = _template(stacking_used=False)
    result = calculate_sds_page_gel_batch(SdsPageGelCalculationInput(template=template, gel_count=1))

    assert result.resolving_gel.is_used
    assert not result.stacking_gel.is_used


def test_supported_units_and_default_overage() -> None:
    assert SUPPORTED_GEL_COMPONENT_UNITS == ("µL", "mL", "mg", "g")
    assert DEFAULT_OVERAGE_PERCENT == 3.0

    for unit in SUPPORTED_GEL_COMPONENT_UNITS:
        template = SdsPageGelTemplate(
            template_id=f"unit_{unit}",
            template_name=f"unit {unit}",
            template_version="v1",
            gel_concentration="用户录入",
            gel_thickness="0.75 mm",
            well_count="12 wells",
            gel_format_or_note="",
            kit_or_sop_source="用户模板",
            resolving_gel_section=GelSection("分离胶", (GelComponent("component", 1, unit, "备注"),)),
            stacking_gel_section=GelSection("浓缩胶", (), is_used=False),
        )
        result = calculate_sds_page_gel_batch(SdsPageGelCalculationInput(template=template, gel_count=1))
        assert result.resolving_gel.rows[0].unit == unit
        assert result.resolving_gel.rows[0].total_amount == pytest.approx(1.03)


def test_calculates_one_and_ten_gels_correctly() -> None:
    one = calculate_sds_page_gel_batch(SdsPageGelCalculationInput(template=_template(), gel_count=1))
    ten = calculate_sds_page_gel_batch(SdsPageGelCalculationInput(template=_template(), gel_count=10))

    assert one.resolving_gel.rows[0].total_amount == pytest.approx(2.575)
    assert one.resolving_gel.rows[1].total_amount == pytest.approx(51.5)
    assert ten.resolving_gel.rows[0].total_amount == pytest.approx(25.75)
    assert ten.resolving_gel.rows[1].total_amount == pytest.approx(515)


def test_validation_errors_are_user_facing() -> None:
    with pytest.raises(SdsPageGelTemplateError, match="需要填写模板名称"):
        calculate_sds_page_gel_batch(SdsPageGelCalculationInput(template=replace(_template(), template_name=""), gel_count=1))
    with pytest.raises(SdsPageGelTemplateError, match="胶数量需要为正整数"):
        calculate_sds_page_gel_batch(SdsPageGelCalculationInput(template=_template(), gel_count=0))
    with pytest.raises(SdsPageGelTemplateError, match="余量百分比不能小于 0"):
        calculate_sds_page_gel_batch(SdsPageGelCalculationInput(template=_template(), gel_count=1, overage_percent=-1))
    with pytest.raises(SdsPageGelTemplateError, match="至少需要一个有效的胶 section"):
        calculate_sds_page_gel_batch(
            SdsPageGelCalculationInput(
                template=SdsPageGelTemplate(
                    template_id="empty",
                    template_name="empty",
                    template_version="v1",
                    gel_concentration="",
                    gel_thickness="1.0 mm",
                    well_count="10 wells",
                    gel_format_or_note="",
                    kit_or_sop_source="",
                    resolving_gel_section=GelSection("分离胶", (), is_used=False),
                    stacking_gel_section=GelSection("浓缩胶", (), is_used=False),
                ),
                gel_count=1,
            )
        )


def test_component_validation_errors_are_user_facing() -> None:
    base = _template()
    with pytest.raises(SdsPageGelTemplateError, match="需要填写组分名称"):
        calculate_sds_page_gel_batch(
            SdsPageGelCalculationInput(
                template=replace(base, resolving_gel_section=GelSection("分离胶", (GelComponent("", 1, "mL"),))),
                gel_count=1,
            )
        )
    with pytest.raises(SdsPageGelTemplateError, match="组分用量不能小于 0"):
        calculate_sds_page_gel_batch(
            SdsPageGelCalculationInput(
                template=replace(base, resolving_gel_section=GelSection("分离胶", (GelComponent("x", -1, "mL"),))),
                gel_count=1,
            )
        )
    with pytest.raises(SdsPageGelTemplateError, match="暂不支持该单位"):
        calculate_sds_page_gel_batch(
            SdsPageGelCalculationInput(
                template=replace(base, resolving_gel_section=GelSection("分离胶", (GelComponent("x", 1, "L"),))),
                gel_count=1,
            )
        )


def test_json_export_contains_schema_and_import_restores_template(tmp_path: Path) -> None:
    path = save_sds_page_gel_template_json(_template(), tmp_path / "template.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == LABTOOLS_SDS_PAGE_GEL_TEMPLATE_STORE_SCHEMA_VERSION
    assert payload["template"]["template_name"] == "实验室 10% 胶模板"
    restored = load_sds_page_gel_template_json(path)
    assert restored.template_id == "lab_template_10pct"
    assert restored.resolving_gel_section.components[1].unit == "µL"


def test_json_conflict_never_overwrites_and_copy_imports() -> None:
    store = SdsPageGelTemplateStore((_template(),))

    skipped = store.import_template(_template(), conflict_policy="skip")
    assert skipped.action == "skipped"
    assert skipped.conflict_detected
    assert len(store.list_templates()) == 1

    copied = store.import_template(_template(), conflict_policy="copy")
    assert copied.action == "copied"
    assert copied.template is not None
    assert copied.template.template_id != "lab_template_10pct"
    assert len(store.list_templates()) == 2


def test_invalid_json_does_not_affect_existing_store(tmp_path: Path) -> None:
    store = SdsPageGelTemplateStore((_template(),))
    path = tmp_path / "invalid.json"
    path.write_text("{bad", encoding="utf-8")

    with pytest.raises(SdsPageGelTemplateError, match="模板 JSON 无效，无法导入"):
        load_sds_page_gel_template_json(path)
    assert len(store.list_templates()) == 1


def test_xlsx_export_generates_three_sheets_and_review_fields(tmp_path: Path) -> None:
    result = calculate_sds_page_gel_batch(SdsPageGelCalculationInput(template=_template(), gel_count=10))
    path = save_sds_page_gel_calculation_xlsx(result, tmp_path / "gel.xlsx")

    assert path.suffix == ".xlsx"
    assert _xlsx_sheet_names(path) == ["Summary", "分离胶", "浓缩胶"]
    text = _xlsx_text(path)
    assert "人工核对提示" in text
    assert GEL_REVIEW_NOTICE in text
    assert "正式 SOP" not in text
    assert "无需人工复核" not in text
