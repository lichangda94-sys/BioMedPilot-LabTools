from __future__ import annotations

from labtools.calculators.calculator_models import CalculationError, CalculationResult
from labtools.calculators.unit_conversion import format_number, parse_number


def calculate_qpcr_mix(
    reactions: object,
    reaction_volume_ul: object,
    master_mix_value: object,
    forward_primer_ul: object,
    reverse_primer_ul: object,
    template_ul: object,
    *,
    master_mix_mode: str = "volume",
    loss_percent: object = 10,
) -> CalculationResult:
    reaction_count = parse_number(reactions, "反应数", allow_zero=False)
    total_volume = parse_number(reaction_volume_ul, "单反应总体积", allow_zero=False)
    master_value = parse_number(master_mix_value, "master mix 体积或比例", allow_zero=False)
    forward_value = parse_number(forward_primer_ul, "forward primer 体积")
    reverse_value = parse_number(reverse_primer_ul, "reverse primer 体积")
    template_value = parse_number(template_ul, "template 体积")
    loss_value = parse_number(loss_percent, "损耗比例")

    if master_mix_mode == "volume":
        master_mix_ul = master_value
        master_mix_label = f"{format_number(master_value)} µL"
    elif master_mix_mode == "ratio":
        if master_value > 100:
            raise CalculationError("master mix 比例不能超过 100%。")
        master_mix_ul = total_volume * master_value / 100
        master_mix_label = f"{format_number(master_value)}%"
    else:
        raise CalculationError("master mix 模式必须是体积或比例。")

    component_total = master_mix_ul + forward_value + reverse_value + template_value
    if component_total > total_volume:
        raise CalculationError("组分体积总和超过单反应总体积，请调整输入。")

    water_ul = total_volume - component_total
    loss_factor = 1 + loss_value / 100
    components = {
        "master_mix_uL": master_mix_ul,
        "forward_primer_uL": forward_value,
        "reverse_primer_uL": reverse_value,
        "template_uL": template_value,
        "nuclease_free_water_uL": water_ul,
    }
    total_without_loss = {key: value * reaction_count for key, value in components.items()}
    total_with_loss = {key: value * reaction_count * loss_factor for key, value in components.items()}
    warnings = ()
    if water_ul == 0:
        warnings = ("nuclease-free water 为 0 µL，请确认该配方符合实验设计。",)

    labels = {
        "master_mix_uL": "master mix",
        "forward_primer_uL": "forward primer",
        "reverse_primer_uL": "reverse primer",
        "template_uL": "template",
        "nuclease_free_water_uL": "nuclease-free water",
    }
    result_lines = tuple(
        f"{label}：单反应 {format_number(components[key])} µL；"
        f"总用量 {format_number(total_without_loss[key])} µL；"
        f"加损耗 {format_number(total_with_loss[key])} µL"
        for key, label in labels.items()
    )

    return CalculationResult(
        title="qPCR 配液计算",
        input_summary=(
            f"反应数：{format_number(reaction_count)}",
            f"单反应总体积：{format_number(total_volume)} µL",
            f"master mix：{master_mix_label}",
            f"forward primer：{format_number(forward_value)} µL",
            f"reverse primer：{format_number(reverse_value)} µL",
            f"template：{format_number(template_value)} µL",
            f"损耗比例：{format_number(loss_value)}%",
        ),
        formula=(
            "nuclease-free water = 单反应总体积 - 已输入组分体积总和",
            "总用量 = 单反应用量 x 反应数",
            "加损耗后的总用量 = 总用量 x (1 + 损耗比例)",
        ),
        result_lines=result_lines,
        result_value=sum(total_with_loss.values()),
        result_unit="µL",
        warnings=warnings,
        record_inputs={
            "reactions": reaction_count,
            "reaction_volume_uL": total_volume,
            "master_mix_value": master_value,
            "master_mix_mode": master_mix_mode,
            "forward_primer_uL": forward_value,
            "reverse_primer_uL": reverse_value,
            "template_uL": template_value,
            "loss_percent": loss_value,
        },
        record_outputs={
            "per_reaction_uL": components,
            "total_uL": total_without_loss,
            "total_with_loss_uL": total_with_loss,
        },
    )
