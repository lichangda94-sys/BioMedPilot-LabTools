from __future__ import annotations

import math
import re

from labtools.calculators.calculator_models import CalculationError
from labtools.calculators.unit_conversion import canonical_unit, format_number, l_to_volume, unit_kind, volume_to_l
from labtools.reagent_templates.models import (
    COMPONENT_TYPES,
    SOLVENT_INITIAL_ADDITION_MODES,
    SUPPORTED_TEMPLATE_UNITS,
    PHRecord,
    PreparationComponentResult,
    PreparationRequest,
    PreparationResult,
    PreparationTreeNode,
    ReagentComponent,
    ReagentTemplate,
    ReagentTemplateError,
)


def validate_template(template: ReagentTemplate, templates: tuple[ReagentTemplate, ...] = ()) -> None:
    template = template.normalized_for_storage()
    if not template.template_id.strip():
        raise ReagentTemplateError("模板缺少 template_id。")
    if not template.name.strip():
        raise ReagentTemplateError("请填写模板名称。")
    if template.default_volume <= 0:
        raise ReagentTemplateError("默认配制体积必须大于 0。")
    _canonical_template_unit(template.default_volume_unit)
    _parse_strength(template.default_strength, "默认倍数或浓度")
    auto_fill_count = sum(1 for component in template.components if component.auto_fill_to_final_volume)
    if auto_fill_count > 1:
        raise ReagentTemplateError("每个模板最多只能有一个自动补足至最终体积的组分。")
    for component in template.components:
        _validate_component(component)
    _validate_ph_record(template.ph_record)
    if templates:
        detect_template_cycles(templates)


def detect_template_cycles(templates: tuple[ReagentTemplate, ...]) -> None:
    templates = tuple(template.normalized_for_storage() for template in templates)
    template_map = {template.template_id: template for template in templates}
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(template_id: str) -> None:
        if template_id in visiting:
            cycle = visiting[visiting.index(template_id) :] + [template_id]
            names = [template_map[item].name for item in cycle if item in template_map]
            raise ReagentTemplateError("检测到模板循环引用：" + " -> ".join(names or cycle))
        if template_id in visited or template_id not in template_map:
            return
        visiting.append(template_id)
        for component in template_map[template_id].components:
            if component.component_type == "self_prepared_template" and component.referenced_template_id:
                visit(component.referenced_template_id)
        visiting.pop()
        visited.add(template_id)

    for template in templates:
        visit(template.template_id)


def calculate_preparation(request: PreparationRequest, templates: tuple[ReagentTemplate, ...]) -> PreparationResult:
    templates = tuple(template.normalized_for_storage() for template in templates)
    template_map = {template.template_id: template for template in templates}
    if request.template_id not in template_map:
        raise ReagentTemplateError("请选择有效试剂模板。")
    if request.target_volume <= 0:
        raise ReagentTemplateError("本次目标体积必须大于 0。")
    if request.overage_percent < 0:
        raise ReagentTemplateError("损耗系数不能为负数。")
    for template in templates:
        validate_template(template)
    detect_template_cycles(templates)

    root = _calculate_node(
        template_map[request.template_id],
        template_map,
        target_volume=request.target_volume,
        target_volume_unit=request.target_volume_unit,
        target_strength=request.target_strength,
        overage_percent=request.overage_percent,
        expand_subtemplates=request.expand_subtemplates,
        stack=(),
    )
    warnings = tuple(_collect_warnings(root))
    steps = _build_steps(root)
    return PreparationResult(
        title=f"{root.template_name} 本次配制清单",
        template_id=root.template_id,
        template_name=root.template_name,
        target_volume=request.target_volume,
        target_volume_unit=_canonical_template_unit(request.target_volume_unit),
        suggested_volume=root.suggested_volume,
        suggested_volume_unit=root.suggested_volume_unit,
        target_strength=request.target_strength,
        overage_percent=request.overage_percent,
        direct_components=root.components,
        tree=root,
        warnings=warnings,
        steps=steps,
        ph_record=root.ph_record,
    )


def _calculate_node(
    template: ReagentTemplate,
    template_map: dict[str, ReagentTemplate],
    *,
    target_volume: float,
    target_volume_unit: str,
    target_strength: str,
    overage_percent: float,
    expand_subtemplates: bool,
    stack: tuple[str, ...],
) -> PreparationTreeNode:
    if template.template_id in stack:
        raise ReagentTemplateError("检测到模板循环引用。")
    target_unit = _canonical_template_unit(target_volume_unit)
    target_l = volume_to_l(target_volume, target_unit)
    suggested_l = target_l * (1 + overage_percent / 100)
    suggested_volume = l_to_volume(suggested_l, target_unit)
    default_l = volume_to_l(template.default_volume, template.default_volume_unit)
    volume_factor = suggested_l / default_l
    strength_factor = _parse_strength(target_strength, "本次目标倍数") / _parse_strength(template.default_strength, "模板默认倍数")

    children: list[PreparationTreeNode] = []
    preliminary: list[PreparationComponentResult] = []
    volume_total_l = 0.0
    auto_fill_component: ReagentComponent | None = None

    for component in template.components:
        if component.auto_fill_to_final_volume:
            auto_fill_component = component
            continue
        result = _component_result(component, volume_factor=volume_factor, strength_factor=strength_factor)
        preliminary.append(result)
        if component.contributes_to_final_volume and result.amount is not None:
            volume_total_l += _volume_amount_to_l(result.amount, result.unit, component.name)
        if result.is_subtemplate and component.referenced_template_id not in template_map:
            raise ReagentTemplateError(f"{component.name} 引用的子模板不存在。")
        if result.is_subtemplate and result.amount is not None and expand_subtemplates:
            child_template = template_map.get(component.referenced_template_id)
            if child_template is None:
                raise ReagentTemplateError(f"{component.name} 引用的子模板不存在。")
            if unit_kind(_canonical_template_unit(result.unit)) != "volume":
                raise ReagentTemplateError(f"{component.name} 引用子模板时，本次需求量必须是体积单位。")
            children.append(
                _calculate_node(
                    child_template,
                    template_map,
                    target_volume=result.amount,
                    target_volume_unit=result.unit,
                    target_strength=child_template.default_strength,
                    overage_percent=0,
                    expand_subtemplates=expand_subtemplates,
                    stack=stack + (template.template_id,),
                )
            )

    if auto_fill_component is not None:
        remaining_l = suggested_l - volume_total_l
        if remaining_l < -1e-12:
            raise ReagentTemplateError("参与最终体积的组分总量已经超过建议配制体积，无法自动补足溶剂。")
        remaining_l = max(0.0, remaining_l)
        fill_unit = _canonical_template_unit(auto_fill_component.unit)
        fill_amount = l_to_volume(remaining_l, fill_unit)
        preliminary.append(
            PreparationComponentResult(
                name=auto_fill_component.name,
                component_type=auto_fill_component.component_type,
                amount=fill_amount,
                unit=fill_unit,
                display_amount=f"{format_number(fill_amount)} {fill_unit}",
                is_auto_fill=True,
                initial_addition_display=_initial_addition_display(auto_fill_component, suggested_l, fill_unit),
                initial_addition_detail=_initial_addition_detail(auto_fill_component, suggested_l, fill_unit, fill_amount),
                notes=auto_fill_component.notes or "自动补足至建议配制体积",
                warnings=tuple(_initial_addition_warnings(auto_fill_component, suggested_l)),
            )
        )

    return PreparationTreeNode(
        template_id=template.template_id,
        template_name=template.name,
        target_volume=target_volume,
        target_volume_unit=target_unit,
        suggested_volume=suggested_volume,
        suggested_volume_unit=target_unit,
        components=tuple(preliminary),
        ph_record=template.ph_record,
        children=tuple(children),
    )


def _component_result(component: ReagentComponent, *, volume_factor: float, strength_factor: float) -> PreparationComponentResult:
    component = component.normalized_for_storage()
    factor = 1.0
    if component.scale_with_volume:
        factor *= volume_factor
    if component.scale_with_strength:
        factor *= strength_factor
    amount = component.base_amount * factor
    unit = _canonical_template_unit(component.unit)
    warnings: list[str] = []
    if component.contributes_to_final_volume and unit_kind(unit) != "volume":
        warnings.append("该组分标记为参与最终体积，但单位不是体积单位，已排除自动补足计算。")
    if component.component_type == "self_prepared_template" and not component.referenced_template_id:
        raise ReagentTemplateError(f"{component.name} 是自配试剂模板组分，但未引用子模板。")
    return PreparationComponentResult(
        name=component.name,
        component_type=component.component_type,
        amount=amount,
        unit=unit,
        display_amount=f"{format_number(amount)} {unit}",
        is_commercial=component.component_type == "commercial_reagent",
        is_subtemplate=component.component_type == "self_prepared_template" and bool(component.referenced_template_id),
        referenced_template_id=component.referenced_template_id,
        notes=component.notes,
        warnings=tuple(warnings),
    )


def _build_steps(root: PreparationTreeNode) -> tuple[str, ...]:
    has_child = bool(root.children)
    auto_fill = next((component for component in root.components if component.is_auto_fill), None)
    staged = next((component for component in root.components if component.initial_addition_display), None)
    has_commercial = any(component.is_commercial for component in root.components)
    steps = [
        "准备合适容器并核对模板名称、日期、操作者和目标体积。",
    ]
    if staged is not None:
        steps.append(f"先加入约 {staged.initial_addition_display} {staged.name}，保留最终补足空间。")
    else:
        steps.append("先加入部分溶剂或基础液体，保留补足空间。")
    if has_child:
        steps.append("需要时先按完整展开清单配制自配子试剂，并记录其批次或配制日期。")
    if has_commercial:
        steps.append("核对商品化试剂名称、浓度、批号、供应商和保存条件后再加入。")
    steps.extend(["按一级配制清单加入非补足组分。", "混匀，确保粉末或其他组分充分溶解。"])
    if root.ph_record is not None and root.ph_record.include_in_steps:
        steps.append(_ph_step(root.ph_record))
    if auto_fill is not None:
        steps.append(f"最后用 {auto_fill.name} 补足至建议配制体积 {format_number(root.suggested_volume)} {root.suggested_volume_unit}。")
    steps.extend(
        [
            "标记名称、浓度/倍数、日期、操作者、保存条件和人工复核状态。",
            "本步骤为通用准备清单，不替代实验室 SOP、SDS 或试剂说明书。",
        ]
    )
    return tuple(steps)


def _collect_warnings(node: PreparationTreeNode) -> list[str]:
    warnings: list[str] = []
    for component in node.components:
        warnings.extend(component.warnings)
    for child in node.children:
        warnings.extend(_collect_warnings(child))
    return warnings


def _validate_component(component: ReagentComponent) -> None:
    if not component.name.strip():
        raise ReagentTemplateError("组分名称不能为空。")
    if component.component_type not in COMPONENT_TYPES:
        raise ReagentTemplateError(f"暂不支持组分类型：{component.component_type}。")
    if component.component_type in {"ph_record", "ph_adjustment"}:
        raise ReagentTemplateError("pH 调节记录请使用独立 pH 记录字段，不应作为普通组分保存。")
    if component.base_amount < 0 or not math.isfinite(component.base_amount):
        raise ReagentTemplateError("组分基准用量必须是非负数字。")
    unit = _canonical_template_unit(component.unit)
    if component.auto_fill_to_final_volume and unit_kind(unit) != "volume":
        raise ReagentTemplateError("自动补足组分必须使用体积单位。")
    _validate_initial_addition(component)
    if component.component_type == "self_prepared_template" and not component.referenced_template_id.strip():
        raise ReagentTemplateError("自配试剂模板组分必须引用子模板。")


def _validate_initial_addition(component: ReagentComponent) -> None:
    if component.initial_addition_mode not in SOLVENT_INITIAL_ADDITION_MODES:
        raise ReagentTemplateError(f"暂不支持初始溶剂加入模式：{component.initial_addition_mode}。")
    if component.initial_addition_mode == "none":
        return
    if not component.auto_fill_to_final_volume:
        raise ReagentTemplateError("初始溶剂加入字段只能用于自动补足溶剂。")
    if component.initial_addition_mode == "percent_of_final":
        if component.initial_addition_percent <= 0 or component.initial_addition_percent >= 100:
            raise ReagentTemplateError("初始加入比例必须大于 0 且小于 100。")
    if component.initial_addition_mode == "fixed_amount":
        if component.initial_addition_amount <= 0:
            raise ReagentTemplateError("固定初始加入量必须大于 0。")
        unit = _canonical_template_unit(component.initial_addition_unit)
        if unit_kind(unit) != "volume":
            raise ReagentTemplateError("固定初始加入量必须使用体积单位。")


def _validate_ph_record(ph_record: PHRecord | None) -> None:
    if ph_record is None:
        return
    if not ph_record.target_ph.strip() and not ph_record.adjustment_note.strip() and not ph_record.measured_ph.strip():
        raise ReagentTemplateError("pH 记录至少需要目标 pH、实测 pH 或调节说明之一。")


def _canonical_template_unit(unit: str) -> str:
    text = str(unit or "").strip()
    alias = {"uL": "µL", "ul": "µL", "μL": "µL", "ug": "µg", "μg": "µg", "uM": "µM", "μM": "µM", "x": "X", "×": "X"}
    canonical = alias.get(text, text)
    if canonical in {"%", "X"}:
        return canonical
    try:
        normalized = canonical_unit(canonical)
    except CalculationError as exc:
        raise ReagentTemplateError(str(exc)) from exc
    if normalized not in SUPPORTED_TEMPLATE_UNITS:
        raise ReagentTemplateError(f"L3 试剂模板暂不支持单位：{text}。")
    return normalized


def _parse_strength(value: str, field_name: str) -> float:
    text = str(value or "").strip()
    if not text or text in {"原液", "stock", "Stock"}:
        return 1.0
    normalized = text.replace("×", "X").replace("x", "X")
    if normalized.endswith("X"):
        number = normalized[:-1].strip()
        return _positive_float(number, field_name)
    if normalized.endswith("%"):
        number = normalized[:-1].strip()
        return _positive_float(number, field_name) / 100
    return _positive_float(normalized, field_name)


def _positive_float(value: str, field_name: str) -> float:
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value or ""):
        raise ReagentTemplateError(f"{field_name}必须是 1X、0.5X、100% 或数字。")
    number = float(value)
    if number <= 0:
        raise ReagentTemplateError(f"{field_name}必须大于 0。")
    return number


def _volume_amount_to_l(amount: float, unit: str, component_name: str) -> float:
    if unit_kind(_canonical_template_unit(unit)) != "volume":
        raise ReagentTemplateError(f"{component_name} 参与最终体积但单位不是体积单位。")
    return volume_to_l(amount, unit)


def _initial_addition_display(component: ReagentComponent, suggested_l: float, output_unit: str) -> str:
    if component.initial_addition_mode == "percent_of_final":
        amount = l_to_volume(suggested_l * component.initial_addition_percent / 100, output_unit)
        return f"{format_number(amount)} {output_unit}"
    if component.initial_addition_mode == "fixed_amount":
        unit = _canonical_template_unit(component.initial_addition_unit)
        return f"{format_number(component.initial_addition_amount)} {unit}"
    return ""


def _initial_addition_detail(component: ReagentComponent, suggested_l: float, output_unit: str, fill_amount: float) -> str:
    if component.initial_addition_mode == "percent_of_final":
        initial = _initial_addition_display(component, suggested_l, output_unit)
        return (
            f"初始加入约 {initial}（{format_number(component.initial_addition_percent)}% 建议配制体积）；"
            f"最终补足至 {format_number(fill_amount)} {output_unit}"
        )
    if component.initial_addition_mode == "fixed_amount":
        initial = _initial_addition_display(component, suggested_l, output_unit)
        return f"初始加入约 {initial}（固定量，不随目标体积缩放）；最终补足至 {format_number(fill_amount)} {output_unit}"
    if component.initial_addition_mode == "note_only":
        return component.initial_addition_note or "初始加入量按备注执行；最终补足至建议配制体积"
    return ""


def _initial_addition_warnings(component: ReagentComponent, suggested_l: float) -> list[str]:
    warnings: list[str] = []
    if component.initial_addition_mode == "fixed_amount":
        warnings.append(f"{component.name} 使用固定初始加入量，不会随目标体积缩放，可能不适合小体积配制。")
        fixed_l = volume_to_l(component.initial_addition_amount, component.initial_addition_unit)
        if fixed_l > suggested_l:
            warnings.append(f"{component.name} 固定初始加入量已超过建议配制体积。")
    return warnings


def _ph_step(ph_record: PHRecord) -> str:
    target = f"至目标 pH {ph_record.target_ph}" if ph_record.target_ph else "并记录 pH"
    note = ph_record.adjustment_note or "按实验室 SOP 调整，需 pH meter 实测。"
    return f"调节或记录 pH {target}；{note}；软件不预测酸碱加入量。"
