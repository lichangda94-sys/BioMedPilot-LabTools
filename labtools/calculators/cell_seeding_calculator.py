from __future__ import annotations

from labtools.calculators.calculator_models import CalculationError, CalculationResult
from labtools.calculators.unit_conversion import canonical_unit, format_number, parse_number, unit_kind


def calculate_cell_seeding(
    cell_density: object,
    density_unit: str,
    target_cells_per_well: object,
    wells: object,
    *,
    loss_percent: object = 10,
) -> CalculationResult:
    source_density_unit = canonical_unit(density_unit)
    if unit_kind(source_density_unit) != "cell_density":
        raise CalculationError("细胞悬液浓度单位必须是 cells/mL。")
    density_value = parse_number(cell_density, "当前细胞悬液浓度", allow_zero=False)
    target_cells_value = parse_number(target_cells_per_well, "目标每孔细胞数", allow_zero=False)
    well_count = parse_number(wells, "孔数", allow_zero=False)
    loss_value = parse_number(loss_percent, "额外损耗比例")

    loss_factor = 1 + loss_value / 100
    total_cells_without_loss = target_cells_value * well_count
    total_cells_with_loss = total_cells_without_loss * loss_factor
    required_suspension_ml = total_cells_with_loss / density_value
    per_well_ml = required_suspension_ml / well_count
    required_suspension_ul = required_suspension_ml * 1000
    per_well_ul = per_well_ml * 1000

    warning = "建议补足总体积为满足细胞数的最低工作体积；如实验 SOP 规定每孔总体积，请按 SOP 补足培养基并复核。"
    return CalculationResult(
        title="细胞接种计算",
        input_summary=(
            f"当前细胞悬液浓度：{format_number(density_value)} {source_density_unit}",
            f"目标每孔细胞数：{format_number(target_cells_value)} cells",
            f"孔数：{format_number(well_count)}",
            f"额外损耗比例：{format_number(loss_value)}%",
        ),
        formula=(
            "总细胞数 = 目标每孔细胞数 x 孔数 x (1 + 损耗比例)",
            "所需细胞悬液体积 = 总细胞数 / 当前细胞悬液浓度",
            "每孔加样体积 = 所需细胞悬液体积 / 孔数",
        ),
        result_lines=(
            f"总细胞数：{format_number(total_cells_with_loss)} cells",
            f"所需细胞悬液体积：{format_number(required_suspension_ul)} µL",
            f"建议补足总体积：{format_number(required_suspension_ul)} µL",
            f"每孔加样体积：{format_number(per_well_ul)} µL",
        ),
        result_value=required_suspension_ul,
        result_unit="µL",
        warnings=(warning,),
        record_inputs={
            "cell_density": density_value,
            "density_unit": source_density_unit,
            "target_cells_per_well": target_cells_value,
            "wells": well_count,
            "loss_percent": loss_value,
        },
        record_outputs={
            "total_cells": total_cells_with_loss,
            "required_suspension_volume_uL": required_suspension_ul,
            "suggested_final_volume_uL": required_suspension_ul,
            "per_well_volume_uL": per_well_ul,
        },
    )
