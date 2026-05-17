from __future__ import annotations

from labtools.calculators.calculator_models import CalculationError, CalculationResult
from labtools.calculators.unit_conversion import (
    canonical_unit,
    format_number,
    g_to_mass,
    mass_concentration_to_g_per_l,
    molarity_to_m,
    parse_number,
    unit_kind,
    validate_molecular_weight,
    volume_to_l,
)


def calculate_solution_preparation(
    concentration: object,
    concentration_unit: str,
    target_volume: object,
    volume_unit: str,
    *,
    molecular_weight: object | None = None,
    output_mass_unit: str = "mg",
) -> CalculationResult:
    source_concentration_unit = canonical_unit(concentration_unit)
    source_volume_unit = canonical_unit(volume_unit)
    target_mass_unit = canonical_unit(output_mass_unit)
    concentration_kind = unit_kind(source_concentration_unit)
    if concentration_kind not in {"mass_concentration", "molarity"}:
        raise CalculationError("目标浓度单位必须是质量浓度或摩尔浓度单位。")
    if unit_kind(target_mass_unit) != "mass":
        raise CalculationError("输出质量单位必须是质量单位。")

    concentration_value = parse_number(concentration, "目标浓度")
    volume_value = parse_number(target_volume, "目标体积", allow_zero=False)
    volume_l = volume_to_l(volume_value, source_volume_unit)

    input_summary = [
        f"目标浓度：{format_number(concentration_value)} {source_concentration_unit}",
        f"目标体积：{format_number(volume_value)} {source_volume_unit}",
    ]
    if concentration_kind == "mass_concentration":
        g_per_l = mass_concentration_to_g_per_l(concentration_value, source_concentration_unit)
        mass_g = g_per_l * volume_l
        formula = (
            "需要称量质量 = 质量浓度 x 目标体积",
            f"{source_concentration_unit} -> g/L；{source_volume_unit} -> L；g -> {target_mass_unit}",
        )
        molecular_weight_value = None
    else:
        molecular_weight_value = validate_molecular_weight(molecular_weight)
        input_summary.append(f"分子量：{format_number(molecular_weight_value)} g/mol")
        molarity_m = molarity_to_m(concentration_value, source_concentration_unit)
        mass_g = molarity_m * volume_l * molecular_weight_value
        formula = (
            "需要称量质量 = 摩尔浓度 x 目标体积 x 分子量",
            f"{source_concentration_unit} -> M；{source_volume_unit} -> L；g -> {target_mass_unit}",
        )

    mass_value = g_to_mass(mass_g, target_mass_unit)
    return CalculationResult(
        title="溶液配制计算",
        input_summary=tuple(input_summary),
        formula=formula,
        result_lines=(
            f"需要称量质量：{format_number(mass_value)} {target_mass_unit}",
            f"需要溶剂补足体积：{format_number(volume_value)} {source_volume_unit}",
        ),
        result_value=mass_value,
        result_unit=target_mass_unit,
        record_inputs={
            "concentration": concentration_value,
            "concentration_unit": source_concentration_unit,
            "target_volume": volume_value,
            "volume_unit": source_volume_unit,
            "molecular_weight_g_per_mol": molecular_weight_value,
            "output_mass_unit": target_mass_unit,
        },
        record_outputs={
            "mass": mass_value,
            "mass_unit": target_mass_unit,
            "solvent_to_final_volume": volume_value,
            "volume_unit": source_volume_unit,
        },
    )
