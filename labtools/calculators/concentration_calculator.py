from __future__ import annotations

from labtools.calculators.calculator_models import CalculationError, CalculationResult
from labtools.calculators.unit_conversion import (
    canonical_unit,
    format_number,
    g_per_l_to_mass_concentration,
    g_to_mass,
    mass_concentration_to_g_per_l,
    mass_to_g,
    m_to_molarity,
    molarity_to_m,
    parse_number,
    unit_kind,
    validate_molecular_weight,
    volume_to_l,
)


def convert_concentration(
    value: object,
    from_unit: str,
    to_unit: str,
    *,
    molecular_weight: object | None = None,
) -> CalculationResult:
    source_unit = canonical_unit(from_unit)
    target_unit = canonical_unit(to_unit)
    source_kind = unit_kind(source_unit)
    target_kind = unit_kind(target_unit)
    if source_kind not in {"molarity", "mass_concentration"} or target_kind not in {"molarity", "mass_concentration"}:
        raise CalculationError("请选择浓度单位进行换算。")

    concentration_value = parse_number(value, "浓度")
    molecular_weight_value: float | None = None

    if source_kind == "molarity":
        value_m = molarity_to_m(concentration_value, source_unit)
        if target_kind == "molarity":
            converted = m_to_molarity(value_m, target_unit)
            formula = (f"{format_number(concentration_value)} {source_unit} -> M -> {target_unit}",)
        else:
            molecular_weight_value = validate_molecular_weight(molecular_weight)
            g_per_l = value_m * molecular_weight_value
            converted = g_per_l_to_mass_concentration(g_per_l, target_unit)
            formula = ("质量浓度 = 摩尔浓度 x 分子量", f"{source_unit} -> M；g/L -> {target_unit}")
    else:
        value_g_per_l = mass_concentration_to_g_per_l(concentration_value, source_unit)
        if target_kind == "mass_concentration":
            converted = g_per_l_to_mass_concentration(value_g_per_l, target_unit)
            formula = (f"{format_number(concentration_value)} {source_unit} -> g/L -> {target_unit}",)
        else:
            molecular_weight_value = validate_molecular_weight(molecular_weight)
            value_m = value_g_per_l / molecular_weight_value
            converted = m_to_molarity(value_m, target_unit)
            formula = ("摩尔浓度 = 质量浓度 / 分子量", f"{source_unit} -> g/L；M -> {target_unit}")

    summary = [f"输入浓度：{format_number(concentration_value)} {source_unit}", f"目标单位：{target_unit}"]
    if molecular_weight_value is not None:
        summary.append(f"分子量：{format_number(molecular_weight_value)} g/mol")
    return CalculationResult(
        title="浓度单位换算",
        input_summary=tuple(summary),
        formula=formula,
        result_lines=(f"换算结果：{format_number(converted)} {target_unit}",),
        result_value=converted,
        result_unit=target_unit,
    )


def calculate_molar_concentration(
    mass: object,
    mass_unit: str,
    volume: object,
    volume_unit: str,
    molecular_weight: object,
    *,
    output_unit: str = "µM",
) -> CalculationResult:
    source_mass_unit = canonical_unit(mass_unit)
    source_volume_unit = canonical_unit(volume_unit)
    target_unit = canonical_unit(output_unit)
    if unit_kind(target_unit) != "molarity":
        raise CalculationError("输出单位必须是物质的量浓度单位。")

    mass_value = parse_number(mass, "质量")
    volume_value = parse_number(volume, "体积", allow_zero=False)
    molecular_weight_value = validate_molecular_weight(molecular_weight)

    mass_g = mass_to_g(mass_value, source_mass_unit)
    volume_l = volume_to_l(volume_value, source_volume_unit)
    moles = mass_g / molecular_weight_value
    molarity_m = moles / volume_l
    converted = m_to_molarity(molarity_m, target_unit)
    return CalculationResult(
        title="由质量和体积计算摩尔浓度",
        input_summary=(
            f"质量：{format_number(mass_value)} {source_mass_unit}",
            f"体积：{format_number(volume_value)} {source_volume_unit}",
            f"分子量：{format_number(molecular_weight_value)} g/mol",
        ),
        formula=("物质的量 n = 质量 / 分子量", "摩尔浓度 C = n / 体积"),
        result_lines=(f"摩尔浓度：{format_number(converted)} {target_unit}",),
        result_value=converted,
        result_unit=target_unit,
    )


def calculate_mass_for_molar_solution(
    concentration: object,
    concentration_unit: str,
    volume: object,
    volume_unit: str,
    molecular_weight: object,
    *,
    output_unit: str = "mg",
) -> CalculationResult:
    source_concentration_unit = canonical_unit(concentration_unit)
    source_volume_unit = canonical_unit(volume_unit)
    target_unit = canonical_unit(output_unit)
    if unit_kind(source_concentration_unit) != "molarity":
        raise CalculationError("浓度单位必须是物质的量浓度单位。")
    if unit_kind(target_unit) != "mass":
        raise CalculationError("输出单位必须是质量单位。")

    concentration_value = parse_number(concentration, "摩尔浓度")
    volume_value = parse_number(volume, "体积", allow_zero=False)
    molecular_weight_value = validate_molecular_weight(molecular_weight)

    concentration_m = molarity_to_m(concentration_value, source_concentration_unit)
    volume_l = volume_to_l(volume_value, source_volume_unit)
    mass_g = concentration_m * volume_l * molecular_weight_value
    converted = g_to_mass(mass_g, target_unit)
    return CalculationResult(
        title="由摩尔浓度和体积计算称量质量",
        input_summary=(
            f"目标浓度：{format_number(concentration_value)} {source_concentration_unit}",
            f"目标体积：{format_number(volume_value)} {source_volume_unit}",
            f"分子量：{format_number(molecular_weight_value)} g/mol",
        ),
        formula=("质量 = 摩尔浓度 x 体积 x 分子量", f"{source_concentration_unit} -> M；{source_volume_unit} -> L；g -> {target_unit}"),
        result_lines=(f"所需质量：{format_number(converted)} {target_unit}",),
        result_value=converted,
        result_unit=target_unit,
    )
