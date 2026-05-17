from __future__ import annotations

from labtools.calculators.calculator_models import CalculationError, CalculationResult
from labtools.calculators.concentration_calculator import convert_concentration
from labtools.calculators.unit_conversion import (
    canonical_unit,
    format_number,
    l_to_volume,
    parse_number,
    unit_kind,
    volume_to_l,
)


def calculate_dilution(
    stock_concentration: object,
    stock_unit: str,
    target_concentration: object,
    target_unit: str,
    target_volume: object,
    volume_unit: str,
    *,
    molecular_weight: object | None = None,
    output_volume_unit: str | None = None,
) -> CalculationResult:
    source_stock_unit = canonical_unit(stock_unit)
    source_target_unit = canonical_unit(target_unit)
    source_volume_unit = canonical_unit(volume_unit)
    output_unit = canonical_unit(output_volume_unit or source_volume_unit)
    if unit_kind(source_stock_unit) not in {"molarity", "mass_concentration"}:
        raise CalculationError("原液浓度单位必须是浓度单位。")
    if unit_kind(source_target_unit) not in {"molarity", "mass_concentration"}:
        raise CalculationError("目标浓度单位必须是浓度单位。")
    if unit_kind(output_unit) != "volume":
        raise CalculationError("输出单位必须是体积单位。")

    stock_value = parse_number(stock_concentration, "原液浓度", allow_zero=False)
    target_value = parse_number(target_concentration, "目标浓度")
    target_volume_value = parse_number(target_volume, "目标体积", allow_zero=False)

    stock_as_target = convert_concentration(
        stock_value,
        source_stock_unit,
        source_target_unit,
        molecular_weight=molecular_weight,
    ).result_value
    if stock_as_target is None:
        raise CalculationError("无法换算原液浓度。")
    if stock_as_target == 0:
        raise CalculationError("原液浓度必须大于 0。")
    if target_value > stock_as_target:
        raise CalculationError("目标浓度高于原液浓度，不能通过稀释获得。")

    target_volume_l = volume_to_l(target_volume_value, source_volume_unit)
    stock_volume_l = target_value * target_volume_l / stock_as_target
    solvent_volume_l = target_volume_l - stock_volume_l
    stock_volume = l_to_volume(stock_volume_l, output_unit)
    solvent_volume = l_to_volume(solvent_volume_l, output_unit)

    stock_summary = f"{format_number(stock_value)} {source_stock_unit}"
    if source_stock_unit != source_target_unit:
        stock_summary = f"{stock_summary}（按 {format_number(stock_as_target)} {source_target_unit} 计算）"

    return CalculationResult(
        title="C1V1 = C2V2 稀释计算",
        input_summary=(
            f"原液浓度：{stock_summary}",
            f"目标浓度：{format_number(target_value)} {source_target_unit}",
            f"目标体积：{format_number(target_volume_value)} {source_volume_unit}",
        ),
        formula=("C1V1 = C2V2", "V1 = C2 x V2 / C1", "溶剂体积 = 目标体积 - 所需原液体积"),
        result_lines=(
            f"所需原液体积：{format_number(stock_volume)} {output_unit}",
            f"所需溶剂体积：{format_number(solvent_volume)} {output_unit}",
        ),
        result_value=stock_volume,
        result_unit=output_unit,
    )
