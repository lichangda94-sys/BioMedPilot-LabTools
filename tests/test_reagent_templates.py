from __future__ import annotations

import json

import pytest

from labtools.reagent_templates import (
    LABTOOLS_REAGENT_TEMPLATE_STORE_SCHEMA_VERSION,
    CommercialReagentInfo,
    PHRecord,
    PreparationRequest,
    ReagentComponent,
    ReagentTemplate,
    ReagentTemplateError,
    ReagentTemplateStore,
    calculate_preparation,
)


def _component(
    name: str,
    amount: float,
    unit: str,
    *,
    component_type: str = "liquid",
    scale_with_volume: bool = True,
    scale_with_strength: bool = False,
    contributes_to_final_volume: bool = False,
    auto_fill: bool = False,
    referenced_template_id: str = "",
    initial_addition_mode: str = "none",
    initial_addition_percent: float = 0,
) -> ReagentComponent:
    return ReagentComponent(
        name=name,
        component_type=component_type,
        base_amount=amount,
        unit=unit,
        scale_with_volume=scale_with_volume,
        scale_with_strength=scale_with_strength,
        contributes_to_final_volume=contributes_to_final_volume,
        auto_fill_to_final_volume=auto_fill,
        referenced_template_id=referenced_template_id,
        initial_addition_mode=initial_addition_mode,
        initial_addition_percent=initial_addition_percent,
    )


def _template_a(*, child_id: str = "") -> ReagentTemplate:
    components = [
        _component("B", 10, "mL", contributes_to_final_volume=True),
        _component("D 固定添加剂", 2, "mg", scale_with_volume=False, component_type="powder"),
        ReagentComponent(
            name="商品化 E",
            component_type="commercial_reagent",
            base_amount=8,
            unit="mL",
            contributes_to_final_volume=True,
            commercial_info=CommercialReagentInfo(concentration="10X", lot_number="L001", supplier="Vendor", storage_condition="4C"),
        ),
        _component("水", 0, "mL", component_type="solvent", auto_fill=True),
    ]
    if child_id:
        components.insert(
            1,
            _component("试剂 C", 8, "mL", component_type="self_prepared_template", contributes_to_final_volume=True, referenced_template_id=child_id),
        )
    return ReagentTemplate.create(name="试剂 A", default_volume=100, components=tuple(components), notes="用户模板")


def _template_c() -> ReagentTemplate:
    return ReagentTemplate.create(
        name="试剂 C",
        default_volume=100,
        components=(
            _component("C1", 20, "mL", contributes_to_final_volume=True),
            _component("C powder", 1, "g", component_type="powder"),
            _component("C water", 0, "mL", component_type="solvent", auto_fill=True),
        ),
    )


def _pbs_template() -> ReagentTemplate:
    return ReagentTemplate.create(
        name="1X PBS pH 7.4",
        default_volume=1000,
        default_volume_unit="mL",
        default_strength="1X",
        components=(
            _component("NaCl", 8.0, "g", component_type="powder"),
            _component("KCl", 0.2, "g", component_type="powder"),
            _component("Na2HPO4", 1.44, "g", component_type="powder"),
            _component("KH2PO4", 0.24, "g", component_type="powder"),
            _component(
                "ddH2O",
                0,
                "mL",
                component_type="solvent",
                contributes_to_final_volume=True,
                auto_fill=True,
                initial_addition_mode="percent_of_final",
                initial_addition_percent=80,
            ),
        ),
        ph_record=PHRecord(
            target_ph="7.4",
            adjustment_note="使用 HCl 或 NaOH 调整，需 pH meter 实测",
            include_in_steps=True,
        ),
    )


def _pbs_stock_template() -> ReagentTemplate:
    return ReagentTemplate.create(
        name="10X PBS stock",
        default_volume=1000,
        default_volume_unit="mL",
        default_strength="10X",
        components=(
            _component("NaCl", 80.0, "g", component_type="powder"),
            _component("KCl", 2.0, "g", component_type="powder"),
            _component("Na2HPO4", 14.4, "g", component_type="powder"),
            _component("KH2PO4", 2.4, "g", component_type="powder"),
            _component("ddH2O", 0, "mL", component_type="solvent", contributes_to_final_volume=True, auto_fill=True),
        ),
        ph_record=PHRecord(target_ph="7.4", adjustment_note="按实验室 SOP 处理", include_in_steps=True),
    )


def _pbs_from_stock_template(stock_id: str, *, commercial: bool = False) -> ReagentTemplate:
    return ReagentTemplate.create(
        name="1X PBS from 10X stock",
        default_volume=100,
        default_volume_unit="mL",
        default_strength="1X",
        components=(
            _component(
                "10X PBS stock",
                10,
                "mL",
                component_type="commercial_reagent" if commercial else "self_prepared_template",
                contributes_to_final_volume=True,
                referenced_template_id="" if commercial else stock_id,
            ),
            _component("ddH2O", 0, "mL", component_type="solvent", contributes_to_final_volume=True, auto_fill=True),
        ),
    )


def test_reagent_template_model_serializes_schema_fields() -> None:
    template = _template_a()
    payload = template.to_dict()
    restored = ReagentTemplate.from_dict(payload)

    assert restored.template_id == template.template_id
    assert restored.name == "试剂 A"
    assert restored.default_volume == 100
    assert restored.default_strength == "1X"
    assert restored.components[2].commercial_info is not None
    assert restored.components[2].commercial_info.lot_number == "L001"


def test_ph_record_and_staged_solvent_serialize_without_ph_as_component(tmp_path) -> None:
    store = ReagentTemplateStore(tmp_path / "templates.json")
    saved = store.upsert_template(_pbs_template())
    loaded = store.load()[0]
    payload = json.loads((tmp_path / "templates.json").read_text(encoding="utf-8"))

    assert loaded.template_id == saved.template_id
    assert loaded.ph_record is not None
    assert loaded.ph_record.target_ph == "7.4"
    assert loaded.ph_record.adjustment_note == "使用 HCl 或 NaOH 调整，需 pH meter 实测"
    assert all(component.component_type not in {"ph_record", "ph_adjustment"} for component in loaded.components)
    assert all(component.unit != "pH" for component in loaded.components)
    assert payload["templates"][0]["ph_record"]["target_ph"] == "7.4"
    solvent = next(component for component in loaded.components if component.name == "ddH2O")
    assert solvent.initial_addition_mode == "percent_of_final"
    assert solvent.initial_addition_percent == 80


def test_legacy_ph_component_is_migrated_to_ph_record_on_read(tmp_path) -> None:
    legacy = ReagentTemplate.create(
        name="旧 pH 模板",
        default_volume=1000,
        components=(
            _component("NaCl", 8, "g", component_type="powder"),
            _component("pH 记录", 7.4, "mL", component_type="ph_adjustment", scale_with_volume=False),
        ),
    )
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": LABTOOLS_REAGENT_TEMPLATE_STORE_SCHEMA_VERSION,
                "updated_at": "2026-05-15T00:00:00+00:00",
                "templates": [legacy.to_dict()],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    loaded = ReagentTemplateStore(path).load()[0]

    assert loaded.ph_record is not None
    assert loaded.ph_record.target_ph == "7.4"
    assert all(component.component_type != "ph_adjustment" for component in loaded.components)


def test_non_reference_components_clear_stale_referenced_template_id_in_store(tmp_path) -> None:
    stock = _pbs_stock_template()
    contaminated = ReagentTemplate.create(
        name="残留引用模板",
        default_volume=100,
        components=(
            _component("10X PBS stock", 10, "mL", component_type="self_prepared_template", contributes_to_final_volume=True, referenced_template_id=stock.template_id),
            _component("ddH2O", 0, "mL", component_type="solvent", contributes_to_final_volume=True, auto_fill=True, referenced_template_id=stock.template_id),
            _component("已有 10X stock", 10, "mL", component_type="commercial_reagent", contributes_to_final_volume=True, referenced_template_id=stock.template_id),
        ),
    )
    store = ReagentTemplateStore(tmp_path / "templates.json")

    store.save_all((stock, contaminated))
    loaded = {template.name: template for template in store.load()}

    components = {component.name: component for component in loaded["残留引用模板"].components}
    assert components["10X PBS stock"].referenced_template_id == stock.template_id
    assert components["ddH2O"].referenced_template_id == ""
    assert components["已有 10X stock"].referenced_template_id == ""


def test_reagent_template_store_saves_loads_copies_and_requires_delete_confirmation(tmp_path) -> None:
    store = ReagentTemplateStore(tmp_path / "templates.json")
    template = _template_a()

    saved = store.upsert_template(template)
    loaded = store.load()

    assert loaded[0].template_id == saved.template_id
    assert json.loads((tmp_path / "templates.json").read_text(encoding="utf-8"))["schema_version"] == LABTOOLS_REAGENT_TEMPLATE_STORE_SCHEMA_VERSION

    copied = store.copy_template(saved.template_id)
    assert copied.template_id != saved.template_id
    assert copied.name.endswith("副本")
    with pytest.raises(ReagentTemplateError, match="确认"):
        store.delete_template(saved.template_id)
    remaining = store.delete_template(saved.template_id, confirmed=True)
    assert [template.template_id for template in remaining] == [copied.template_id]


def test_reagent_template_store_rejects_bad_json_and_schema(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{bad", encoding="utf-8")
    with pytest.raises(ReagentTemplateError, match="有效 JSON"):
        ReagentTemplateStore(path).load()

    path.write_text(json.dumps({"schema_version": "wrong", "templates": []}), encoding="utf-8")
    with pytest.raises(ReagentTemplateError, match="schema"):
        ReagentTemplateStore(path).load()


def test_preparation_scales_volume_fixed_amount_strength_and_overage() -> None:
    template = ReagentTemplate.create(
        name="倍数模板",
        default_volume=100,
        default_strength="1X",
        components=(
            _component("随体积液体", 10, "mL", contributes_to_final_volume=True),
            _component("固定粉末", 5, "mg", component_type="powder", scale_with_volume=False),
            _component("按倍数组分", 4, "mL", scale_with_strength=True, contributes_to_final_volume=True),
            _component("水", 0, "mL", component_type="solvent", auto_fill=True),
        ),
    )

    result = calculate_preparation(PreparationRequest(template.template_id, 75, "mL", "0.5X", 10), (template,))

    assert result.target_volume == 75
    assert result.suggested_volume == pytest.approx(82.5)
    amounts = {component.name: component.amount for component in result.direct_components}
    assert amounts["随体积液体"] == pytest.approx(8.25)
    assert amounts["固定粉末"] == pytest.approx(5)
    assert amounts["按倍数组分"] == pytest.approx(1.65)
    assert amounts["水"] == pytest.approx(72.6)
    assert "目标最终体积：75 mL" in result.as_text()
    assert "建议配制体积：82.5 mL" in result.as_text()


@pytest.mark.parametrize(
    ("target_volume", "overage", "expected"),
    (
        (
            75,
            0,
            {
                "suggested": 75,
                "NaCl": 0.6,
                "KCl": 0.015,
                "Na2HPO4": 0.108,
                "KH2PO4": 0.018,
                "ddH2O": 75,
                "initial": "60 mL",
            },
        ),
        (
            300,
            0,
            {
                "suggested": 300,
                "NaCl": 2.4,
                "KCl": 0.06,
                "Na2HPO4": 0.432,
                "KH2PO4": 0.072,
                "ddH2O": 300,
                "initial": "240 mL",
            },
        ),
        (
            75,
            10,
            {
                "suggested": 82.5,
                "NaCl": 0.66,
                "KCl": 0.0165,
                "Na2HPO4": 0.1188,
                "KH2PO4": 0.0198,
                "ddH2O": 82.5,
                "initial": "66 mL",
            },
        ),
    ),
)
def test_pbs_regression_ph_record_and_staged_solvent_outputs(target_volume, overage, expected) -> None:
    template = _pbs_template()
    result = calculate_preparation(PreparationRequest(template.template_id, target_volume, "mL", "1X", overage), (template,))
    amounts = {component.name: component.amount for component in result.direct_components}
    text = result.as_text()

    assert result.suggested_volume == pytest.approx(expected["suggested"])
    for component_name in ("NaCl", "KCl", "Na2HPO4", "KH2PO4", "ddH2O"):
        assert amounts[component_name] == pytest.approx(expected[component_name])
    assert result.ph_record is not None
    assert "pH / 调节记录" in text
    assert "目标 pH: 7.4" in text
    assert "pH 记录: 7.4 mL" not in text
    assert "初始加入约 " + expected["initial"] in text
    assert f"最终补足至 {expected['ddH2O']:g} mL" in text
    assert f"最后用 ddH2O 补足至建议配制体积 {expected['suggested']:g} mL" in text


def test_staged_solvent_1000_ml_initial_addition_is_800_ml() -> None:
    template = _pbs_template()
    result = calculate_preparation(PreparationRequest(template.template_id, 1000), (template,))
    text = result.as_text()

    assert "初始加入约 800 mL" in text
    assert "最终补足至 1000 mL" in text
    assert "调节或记录 pH 至目标 pH 7.4" in text


def test_auto_fill_rejects_overfilled_volume_and_multiple_fillers(tmp_path) -> None:
    overfilled = ReagentTemplate.create(
        name="超量模板",
        default_volume=100,
        components=(
            _component("液体", 120, "mL", contributes_to_final_volume=True),
            _component("水", 0, "mL", component_type="solvent", auto_fill=True),
        ),
    )
    with pytest.raises(ReagentTemplateError, match="超过建议配制体积"):
        calculate_preparation(PreparationRequest(overfilled.template_id, 100), (overfilled,))

    invalid = ReagentTemplate.create(
        name="双补足",
        default_volume=100,
        components=(
            _component("水", 0, "mL", component_type="solvent", auto_fill=True),
            _component("PBS", 0, "mL", component_type="solvent", auto_fill=True),
        ),
    )
    with pytest.raises(ReagentTemplateError, match="最多只能有一个"):
        ReagentTemplateStore(tmp_path / "templates.json").save_all((invalid,))


def test_l3_template_units_are_explicitly_limited_to_first_version_scope() -> None:
    unsupported = ReagentTemplate.create(
        name="暂不支持单位",
        default_volume=100,
        components=(_component("低浓度组分", 1, "nM"),),
    )

    with pytest.raises(ReagentTemplateError, match="暂不支持单位"):
        calculate_preparation(PreparationRequest(unsupported.template_id, 10), (unsupported,))


def test_10x_pbs_stock_and_1x_from_stock_regression_with_subtemplate_ph_display() -> None:
    stock = _pbs_stock_template()
    working = _pbs_from_stock_template(stock.template_id)
    result = calculate_preparation(PreparationRequest(working.template_id, 75, expand_subtemplates=True), (stock, working))
    amounts = {component.name: component.amount for component in result.direct_components}
    text = result.as_text()
    before_expand = text.split("完整展开清单", 1)[0]

    assert result.suggested_volume == pytest.approx(75)
    assert amounts["10X PBS stock"] == pytest.approx(7.5)
    assert amounts["ddH2O"] == pytest.approx(67.5)
    assert "pH / 调节记录" not in before_expand
    assert "pH 记录字段" not in before_expand
    assert "子模板 pH：目标 pH: 7.4；调节说明: 按实验室 SOP 处理" in text
    assert "子模板展开提示" in text
    assert "- NaCl: 0.6 g" in text
    assert "- KCl: 0.015 g" in text
    assert "- Na2HPO4: 0.108 g" in text
    assert "- KH2PO4: 0.018 g" in text
    assert "- ddH2O（溶剂补足）: 7.5 mL" in text


def test_commercial_existing_stock_path_does_not_expand_internal_template() -> None:
    stock = _pbs_stock_template()
    working = _pbs_from_stock_template(stock.template_id, commercial=True)
    result = calculate_preparation(PreparationRequest(working.template_id, 75, expand_subtemplates=True), (stock, working))
    text = result.as_text()
    amounts = {component.name: component.amount for component in result.direct_components}

    assert amounts["10X PBS stock"] == pytest.approx(7.5)
    assert amounts["ddH2O"] == pytest.approx(67.5)
    assert "完整展开清单" not in text
    assert "- NaCl: 0.6 g" not in text
    assert "子模板 pH" not in text


def test_10x_pbs_stock_1000_ml_regression() -> None:
    stock = _pbs_stock_template()
    result = calculate_preparation(PreparationRequest(stock.template_id, 1000, "mL", "10X"), (stock,))
    amounts = {component.name: component.amount for component in result.direct_components}
    text = result.as_text()

    assert amounts["NaCl"] == pytest.approx(80)
    assert amounts["KCl"] == pytest.approx(2)
    assert amounts["Na2HPO4"] == pytest.approx(14.4)
    assert amounts["KH2PO4"] == pytest.approx(2.4)
    assert amounts["ddH2O"] == pytest.approx(1000)
    assert "目标 pH: 7.4" in text
    assert "pH 记录: 7.4 mL" not in text


def test_subtemplate_expands_with_child_target_volume() -> None:
    child = _template_c()
    parent = _template_a(child_id=child.template_id)

    result = calculate_preparation(PreparationRequest(parent.template_id, 100, expand_subtemplates=True), (parent, child))

    child_node = result.tree.children[0]
    assert child_node.template_name == "试剂 C"
    assert child_node.suggested_volume == pytest.approx(8)
    child_amounts = {component.name: component.amount for component in child_node.components}
    assert child_amounts["C1"] == pytest.approx(1.6)
    assert child_amounts["C water"] == pytest.approx(6.4)
    assert "完整展开清单" in result.as_text()
    assert "试剂 C" in result.as_text()


def test_cycle_reference_is_blocked() -> None:
    a = ReagentTemplate.create(name="A", default_volume=100)
    c = ReagentTemplate.create(name="C", default_volume=100)
    a = ReagentTemplate(
        **{**a.to_dict(), "components": (_component("C", 1, "mL", component_type="self_prepared_template", referenced_template_id=c.template_id),)}
    )
    c = ReagentTemplate(
        **{**c.to_dict(), "components": (_component("A", 1, "mL", component_type="self_prepared_template", referenced_template_id=a.template_id),)}
    )

    with pytest.raises(ReagentTemplateError, match="循环引用"):
        calculate_preparation(PreparationRequest(a.template_id, 10), (a, c))


def test_preparation_steps_are_generic_and_include_review_notice() -> None:
    template = _template_a()
    result = calculate_preparation(PreparationRequest(template.template_id, 75), (template,))
    text = result.as_text()

    assert "准备合适容器" in text
    assert "按一级配制清单加入非补足组分" in text
    assert "混匀，确保粉末或其他组分充分溶解" in text
    assert "pH 记录字段" not in text
    assert "目标 pH:" not in text
    assert "实测 pH:" not in text
    assert "补足至建议配制体积" in text
    assert "人工复核提示" in text
    for forbidden in ("自动 pH 预测", "自动推荐最佳配方", "无需人工复核"):
        assert forbidden not in text
