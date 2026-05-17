from __future__ import annotations

from dataclasses import dataclass

from labtools.calculators.calculator_models import CalculationError
from labtools.calculators.unit_conversion import (
    canonical_unit,
    format_number,
    g_to_mass,
    mass_concentration_to_g_per_l,
    molarity_to_m,
    parse_number,
    unit_kind,
    volume_to_l,
    l_to_volume,
)


CALCULATION_REVIEW_NOTICE = (
    "计算结果为实验辅助草稿，使用前需结合实验 SOP、试剂说明书和人工复核；"
    "不构成临床、诊断或安全操作建议。"
)


@dataclass(frozen=True)
class DilutionInput:
    stock_concentration: object
    stock_unit: str
    target_concentration: object
    target_unit: str
    final_volume: object
    final_volume_unit: str


@dataclass(frozen=True)
class DilutionResult:
    valid: bool
    stock_volume: float | None
    stock_volume_unit: str
    solvent_volume: float | None
    solvent_volume_unit: str
    final_volume: float | None
    final_volume_unit: str
    dilution_factor: float | None
    summary: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def as_text(self) -> str:
        return _result_text(
            "溶液稀释 C1V1=C2V2",
            self.valid,
            (
                f"所需 stock 体积：{format_number(self.stock_volume or 0)} {self.stock_volume_unit}",
                f"所需溶剂体积：{format_number(self.solvent_volume or 0)} {self.solvent_volume_unit}",
                f"稀释倍数：{format_number(self.dilution_factor or 0)}",
            ),
            self.summary,
            self.warnings,
            self.errors,
        )


def format_dilution_copy_text(input_data: DilutionInput, result: DilutionResult) -> str:
    if not result.valid:
        return ""
    stock_unit = _safe_unit(input_data.stock_unit)
    target_unit = _safe_unit(input_data.target_unit)
    final_volume_unit = _safe_unit(input_data.final_volume_unit)
    return "\n".join(
        [
            "工具：溶液稀释 C1V1=C2V2",
            f"输入：stock {input_data.stock_concentration} {stock_unit}；target {input_data.target_concentration} {target_unit}；final volume {input_data.final_volume} {final_volume_unit}",
            "计算结果：",
            f"- stock volume / stock 体积：{format_number(result.stock_volume or 0)} {result.stock_volume_unit}",
            f"- solvent volume / 溶剂体积：{format_number(result.solvent_volume or 0)} {result.solvent_volume_unit}",
            f"- dilution factor / 稀释倍数：{format_number(result.dilution_factor or 0)}",
            "人工核对提示：实验辅助计算草稿，不替代实验 SOP；使用前请核对单位、移液范围、溶剂兼容性和实验设计。",
        ]
    )


@dataclass(frozen=True)
class MassMolarityInput:
    molecular_weight: object
    target_concentration: object
    concentration_unit: str
    final_volume: object
    volume_unit: str
    output_mass_unit: str


@dataclass(frozen=True)
class MassMolarityResult:
    valid: bool
    required_mass: float | None
    required_mass_unit: str
    moles: float | None
    summary: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def as_text(self) -> str:
        return _result_text(
            "摩尔浓度 / 称量质量换算",
            self.valid,
            (
                f"所需称量质量：{format_number(self.required_mass or 0)} {self.required_mass_unit}",
                f"物质的量：{format_number(self.moles or 0)} mol",
            ),
            self.summary,
            self.warnings,
            self.errors,
        )


def format_mass_molarity_copy_text(input_data: MassMolarityInput, result: MassMolarityResult) -> str:
    if not result.valid:
        return ""
    concentration_unit = _safe_unit(input_data.concentration_unit)
    volume_unit = _safe_unit(input_data.volume_unit)
    return "\n".join(
        [
            "工具：摩尔浓度 / 称量质量换算",
            f"输入：MW {input_data.molecular_weight} g/mol；concentration {input_data.target_concentration} {concentration_unit}；volume {input_data.final_volume} {volume_unit}",
            "计算结果：",
            f"- required mass / 称量质量：{format_number(result.required_mass or 0)} {result.required_mass_unit}",
            f"- moles / 物质的量：{format_number(result.moles or 0)} mol",
            "人工核对提示：实验辅助计算草稿，不替代实验 SOP；使用前请核对试剂纯度、盐型/水合物形式、有效含量和实验设计。",
        ]
    )


@dataclass(frozen=True)
class CellSeedingInput:
    current_cell_concentration: object
    concentration_unit: str
    target_cells_per_well: object
    well_count: object
    volume_per_well: object
    volume_unit: str
    overage_percentage: object = 10


@dataclass(frozen=True)
class CellSeedingResult:
    valid: bool
    required_cell_suspension_volume: float | None
    required_cell_suspension_volume_unit: str
    required_medium_volume: float | None
    required_medium_volume_unit: str
    total_final_volume: float | None
    total_final_volume_unit: str
    total_cells_required: float | None
    overage_percentage: float | None
    summary: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def as_text(self) -> str:
        return _result_text(
            "细胞接种密度计算",
            self.valid,
            (
                f"总细胞需求量：{format_number(self.total_cells_required or 0)} cells",
                (
                    "所需细胞悬液体积："
                    f"{format_number(self.required_cell_suspension_volume or 0)} "
                    f"{self.required_cell_suspension_volume_unit}"
                ),
                f"所需培养基体积：{format_number(self.required_medium_volume or 0)} {self.required_medium_volume_unit}",
                f"总终体积：{format_number(self.total_final_volume or 0)} {self.total_final_volume_unit}",
            ),
            self.summary,
            self.warnings,
            self.errors,
        )


def format_cell_seeding_copy_text(input_data: CellSeedingInput, result: CellSeedingResult) -> str:
    if not result.valid:
        return ""
    concentration_unit = _safe_unit(input_data.concentration_unit)
    volume_unit = _safe_unit(input_data.volume_unit)
    return "\n".join(
        [
            "工具：细胞接种密度计算",
            f"输入：current concentration {input_data.current_cell_concentration} {concentration_unit}；target {input_data.target_cells_per_well} cells/well；wells {input_data.well_count}；volume {input_data.volume_per_well} {volume_unit}/well；overage {input_data.overage_percentage}%",
            "计算结果：",
            f"- total cells / 总细胞需求量：{format_number(result.total_cells_required or 0)} cells",
            f"- suspension volume / 细胞悬液体积：{format_number(result.required_cell_suspension_volume or 0)} {result.required_cell_suspension_volume_unit}",
            f"- medium volume / 培养基体积：{format_number(result.required_medium_volume or 0)} {result.required_medium_volume_unit}",
            f"- total final volume / 总终体积：{format_number(result.total_final_volume or 0)} {result.total_final_volume_unit}",
            "人工核对提示：实验辅助计算草稿，不替代实验 SOP；实际接种前请核对细胞活率、混匀状态、计数误差、孔板设计和实验设计。",
        ]
    )


@dataclass(frozen=True)
class QpcrMixInput:
    reactions: object
    reaction_volume_ul: object
    master_mix_value: object
    forward_primer_ul: object
    reverse_primer_ul: object
    template_ul: object
    master_mix_mode: str = "volume"
    overage_percentage: object = 10


@dataclass(frozen=True)
class QpcrMixResult:
    valid: bool
    per_reaction_ul: dict[str, float]
    total_ul: dict[str, float]
    total_with_overage_ul: dict[str, float]
    total_reaction_volume_with_overage_ul: float | None
    overage_percentage: float | None
    summary: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def as_text(self) -> str:
        lines = tuple(
            f"{label}：单反应 {format_number(self.per_reaction_ul.get(key, 0))} µL；"
            f"总用量 {format_number(self.total_ul.get(key, 0))} µL；"
            f"含 overage {format_number(self.total_with_overage_ul.get(key, 0))} µL"
            for key, label in _QPCR_LABELS.items()
        )
        return _result_text("qPCR 配液计算", self.valid, lines, self.summary, self.warnings, self.errors)


@dataclass(frozen=True)
class WesternBlotLoadingInput:
    protein_concentration: object
    concentration_unit: str
    target_protein_mass_ug: object
    final_loading_volume: object
    volume_unit: str
    loading_buffer_x: object


@dataclass(frozen=True)
class WesternBlotLoadingResult:
    valid: bool
    sample_volume: float | None
    sample_volume_unit: str
    loading_buffer_volume: float | None
    loading_buffer_volume_unit: str
    water_volume: float | None
    water_volume_unit: str
    final_loading_volume: float | None
    final_loading_volume_unit: str
    target_protein_mass_ug: float | None
    summary: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def as_text(self) -> str:
        return _result_text(
            "Western blot / SDS-PAGE 上样计算",
            self.valid,
            (
                f"样品体积：{format_number(self.sample_volume or 0)} {self.sample_volume_unit}",
                f"loading buffer 体积：{format_number(self.loading_buffer_volume or 0)} {self.loading_buffer_volume_unit}",
                f"补水体积：{format_number(self.water_volume or 0)} {self.water_volume_unit}",
                f"终上样体积：{format_number(self.final_loading_volume or 0)} {self.final_loading_volume_unit}",
            ),
            self.summary,
            self.warnings,
            self.errors,
        )


def calculate_dilution_v1(input_data: DilutionInput) -> DilutionResult:
    try:
        stock_unit = canonical_unit(input_data.stock_unit)
        target_unit = canonical_unit(input_data.target_unit)
        final_volume_unit = canonical_unit(input_data.final_volume_unit)
        stock_kind = unit_kind(stock_unit)
        target_kind = unit_kind(target_unit)
        if stock_kind not in {"molarity", "mass_concentration"}:
            raise CalculationError("stock 浓度单位必须是物质的量浓度或质量浓度单位。")
        if target_kind not in {"molarity", "mass_concentration"}:
            raise CalculationError("目标浓度单位必须是物质的量浓度或质量浓度单位。")
        if stock_kind != target_kind:
            raise CalculationError("stock 和目标浓度单位维度不同；L5B 稀释计算不混合摩尔浓度与质量浓度。")
        if unit_kind(final_volume_unit) != "volume":
            raise CalculationError("终体积单位必须是体积单位。")

        stock_value = parse_number(input_data.stock_concentration, "stock 浓度", allow_zero=False)
        target_value = parse_number(input_data.target_concentration, "目标浓度", allow_zero=False)
        final_volume_value = parse_number(input_data.final_volume, "终体积", allow_zero=False)
        stock_base = _concentration_to_base(stock_value, stock_unit)
        target_base = _concentration_to_base(target_value, target_unit)
        if target_base > stock_base:
            raise CalculationError("目标浓度不能高于 stock 浓度，不能通过稀释获得。")

        final_volume_l = volume_to_l(final_volume_value, final_volume_unit)
        dilution_factor = stock_base / target_base
        stock_volume_l = final_volume_l / dilution_factor
        if stock_volume_l > final_volume_l:
            raise CalculationError("所需 stock 体积大于终体积，请检查输入浓度。")
        solvent_volume_l = final_volume_l - stock_volume_l
        stock_volume = l_to_volume(stock_volume_l, final_volume_unit)
        solvent_volume = l_to_volume(solvent_volume_l, final_volume_unit)
        return DilutionResult(
            valid=True,
            stock_volume=stock_volume,
            stock_volume_unit=final_volume_unit,
            solvent_volume=solvent_volume,
            solvent_volume_unit=final_volume_unit,
            final_volume=final_volume_value,
            final_volume_unit=final_volume_unit,
            dilution_factor=dilution_factor,
            summary=(
                "按 C1V1=C2V2 估算 stock 与溶剂体积。"
                "结果为实验辅助草稿，使用前需人工核对移液范围、溶剂兼容性和实验 SOP。"
            ),
            warnings=(CALCULATION_REVIEW_NOTICE,),
        )
    except CalculationError as exc:
        unit = _safe_unit(input_data.final_volume_unit)
        return DilutionResult(
            valid=False,
            stock_volume=None,
            stock_volume_unit=unit,
            solvent_volume=None,
            solvent_volume_unit=unit,
            final_volume=None,
            final_volume_unit=unit,
            dilution_factor=None,
            summary="稀释计算未生成结果。",
            errors=(str(exc),),
        )


def calculate_mass_molarity_v1(input_data: MassMolarityInput) -> MassMolarityResult:
    try:
        concentration_unit = canonical_unit(input_data.concentration_unit)
        volume_unit = canonical_unit(input_data.volume_unit)
        output_mass_unit = canonical_unit(input_data.output_mass_unit)
        if unit_kind(concentration_unit) != "molarity":
            raise CalculationError("目标浓度必须使用 M、mM、µM/uM 或 nM。")
        if unit_kind(volume_unit) != "volume":
            raise CalculationError("终体积单位必须是体积单位。")
        if unit_kind(output_mass_unit) != "mass":
            raise CalculationError("输出质量单位必须是 g、mg、µg/ug 或 ng。")
        molecular_weight = parse_number(input_data.molecular_weight, "分子量", allow_zero=False)
        concentration = parse_number(input_data.target_concentration, "目标摩尔浓度", allow_zero=False)
        final_volume = parse_number(input_data.final_volume, "终体积", allow_zero=False)

        concentration_m = molarity_to_m(concentration, concentration_unit)
        volume_l = volume_to_l(final_volume, volume_unit)
        moles = concentration_m * volume_l
        mass_g = moles * molecular_weight
        required_mass = g_to_mass(mass_g, output_mass_unit)
        return MassMolarityResult(
            valid=True,
            required_mass=required_mass,
            required_mass_unit=output_mass_unit,
            moles=moles,
            summary=(
                "按分子量和目标摩尔浓度估算称量质量，需人工核对试剂纯度、"
                "盐型/水合物形式、有效含量和实验 SOP。"
            ),
            warnings=(CALCULATION_REVIEW_NOTICE,),
        )
    except CalculationError as exc:
        return MassMolarityResult(
            valid=False,
            required_mass=None,
            required_mass_unit=_safe_unit(input_data.output_mass_unit),
            moles=None,
            summary="摩尔浓度 / 称量质量换算未生成结果。",
            errors=(str(exc),),
        )


def calculate_cell_seeding_v1(input_data: CellSeedingInput) -> CellSeedingResult:
    try:
        concentration_unit = canonical_unit(input_data.concentration_unit)
        volume_unit = canonical_unit(input_data.volume_unit)
        if unit_kind(concentration_unit) != "cell_density":
            raise CalculationError("当前细胞悬液浓度单位必须是 cells/mL 或 cells/µL/uL。")
        if unit_kind(volume_unit) != "volume":
            raise CalculationError("每孔体积单位必须是体积单位。")
        concentration = parse_number(input_data.current_cell_concentration, "当前细胞悬液浓度", allow_zero=False)
        target_cells = parse_number(input_data.target_cells_per_well, "目标每孔细胞数", allow_zero=False)
        well_count_value = _parse_positive_int(input_data.well_count, "孔数")
        volume_per_well = parse_number(input_data.volume_per_well, "每孔体积", allow_zero=False)
        overage = parse_number(input_data.overage_percentage, "overage 比例")

        concentration_cells_per_ml = _cell_density_to_cells_per_ml(concentration, concentration_unit)
        factor = 1 + overage / 100
        total_cells = target_cells * well_count_value * factor
        total_final_volume_l = volume_to_l(volume_per_well, volume_unit) * well_count_value * factor
        suspension_volume_ml = total_cells / concentration_cells_per_ml
        suspension_volume_l = suspension_volume_ml / 1000
        if suspension_volume_l > total_final_volume_l:
            raise CalculationError("当前细胞悬液浓度不足以在目标终体积内达到目标接种密度。")
        medium_volume_l = total_final_volume_l - suspension_volume_l
        return CellSeedingResult(
            valid=True,
            required_cell_suspension_volume=l_to_volume(suspension_volume_l, volume_unit),
            required_cell_suspension_volume_unit=volume_unit,
            required_medium_volume=l_to_volume(medium_volume_l, volume_unit),
            required_medium_volume_unit=volume_unit,
            total_final_volume=l_to_volume(total_final_volume_l, volume_unit),
            total_final_volume_unit=volume_unit,
            total_cells_required=total_cells,
            overage_percentage=overage,
            summary=(
                "细胞接种结果为辅助计算草稿，实际接种前需人工核对细胞活率、"
                "混匀状态、计数误差、孔板设计和实验 SOP。"
            ),
            warnings=(CALCULATION_REVIEW_NOTICE,),
        )
    except CalculationError as exc:
        unit = _safe_unit(input_data.volume_unit)
        return CellSeedingResult(
            valid=False,
            required_cell_suspension_volume=None,
            required_cell_suspension_volume_unit=unit,
            required_medium_volume=None,
            required_medium_volume_unit=unit,
            total_final_volume=None,
            total_final_volume_unit=unit,
            total_cells_required=None,
            overage_percentage=None,
            summary="细胞接种密度计算未生成结果。",
            errors=(str(exc),),
        )


def calculate_qpcr_mix_v1(input_data: QpcrMixInput) -> QpcrMixResult:
    try:
        reaction_count = parse_number(input_data.reactions, "反应数", allow_zero=False)
        reaction_volume = parse_number(input_data.reaction_volume_ul, "单反应总体积", allow_zero=False)
        master_value = parse_number(input_data.master_mix_value, "master mix 体积或比例", allow_zero=False)
        forward = parse_number(input_data.forward_primer_ul, "forward primer 体积")
        reverse = parse_number(input_data.reverse_primer_ul, "reverse primer 体积")
        template = parse_number(input_data.template_ul, "template 体积")
        overage = parse_number(input_data.overage_percentage, "overage 比例")
        if input_data.master_mix_mode == "volume":
            master_mix = master_value
        elif input_data.master_mix_mode == "ratio":
            if master_value > 100:
                raise CalculationError("master mix 比例不能超过 100%。")
            master_mix = reaction_volume * master_value / 100
        else:
            raise CalculationError("master mix 模式必须是 volume 或 ratio。")
        component_total = master_mix + forward + reverse + template
        if component_total > reaction_volume:
            raise CalculationError("组分体积总和超过单反应总体积，请调整输入。")
        water = reaction_volume - component_total
        factor = 1 + overage / 100
        per_reaction = {
            "master_mix_uL": master_mix,
            "forward_primer_uL": forward,
            "reverse_primer_uL": reverse,
            "template_uL": template,
            "nuclease_free_water_uL": water,
        }
        total = {key: value * reaction_count for key, value in per_reaction.items()}
        total_with_overage = {key: value * factor for key, value in total.items()}
        warnings = []
        if water == 0:
            warnings.append("nuclease-free water 为 0 µL，请确认该配方符合实验设计。")
        warnings.append(CALCULATION_REVIEW_NOTICE)
        return QpcrMixResult(
            valid=True,
            per_reaction_ul=per_reaction,
            total_ul=total,
            total_with_overage_ul=total_with_overage,
            total_reaction_volume_with_overage_ul=reaction_volume * reaction_count * factor,
            overage_percentage=overage,
            summary=(
                "qPCR 配液结果为实验辅助草稿，使用前需人工核对 master mix 类型、"
                "primer/template 浓度、重复数、阴阳性对照和实验 SOP。"
            ),
            warnings=tuple(warnings),
        )
    except CalculationError as exc:
        return QpcrMixResult(
            valid=False,
            per_reaction_ul={},
            total_ul={},
            total_with_overage_ul={},
            total_reaction_volume_with_overage_ul=None,
            overage_percentage=None,
            summary="qPCR 配液计算未生成结果。",
            errors=(str(exc),),
        )


def calculate_western_blot_loading_v1(input_data: WesternBlotLoadingInput) -> WesternBlotLoadingResult:
    try:
        concentration_unit = canonical_unit(input_data.concentration_unit)
        volume_unit = canonical_unit(input_data.volume_unit)
        if unit_kind(concentration_unit) != "mass_concentration":
            raise CalculationError("蛋白浓度单位必须是 mg/mL 或 µg/µL。")
        if unit_kind(volume_unit) != "volume":
            raise CalculationError("上样体积单位必须是体积单位。")
        concentration = parse_number(input_data.protein_concentration, "蛋白浓度", allow_zero=False)
        target_mass = parse_number(input_data.target_protein_mass_ug, "目标上样蛋白量", allow_zero=False)
        final_volume = parse_number(input_data.final_loading_volume, "目标上样体积", allow_zero=False)
        buffer_x = parse_number(input_data.loading_buffer_x, "loading buffer 倍数", allow_zero=False)
        if buffer_x <= 1:
            raise CalculationError("loading buffer 倍数必须大于 1，例如 4× 或 5×。")

        concentration_ug_per_ul = _mass_concentration_to_ug_per_ul(concentration, concentration_unit)
        sample_volume_ul = target_mass / concentration_ug_per_ul
        final_volume_ul = l_to_volume(volume_to_l(final_volume, volume_unit), "µL")
        buffer_volume_ul = final_volume_ul / buffer_x
        water_volume_ul = final_volume_ul - sample_volume_ul - buffer_volume_ul
        if water_volume_ul < 0:
            raise CalculationError("样品体积加 loading buffer 已超过目标上样体积，请提高终体积或调整目标蛋白量。")
        return WesternBlotLoadingResult(
            valid=True,
            sample_volume=l_to_volume(volume_to_l(sample_volume_ul, "µL"), volume_unit),
            sample_volume_unit=volume_unit,
            loading_buffer_volume=l_to_volume(volume_to_l(buffer_volume_ul, "µL"), volume_unit),
            loading_buffer_volume_unit=volume_unit,
            water_volume=l_to_volume(volume_to_l(water_volume_ul, "µL"), volume_unit),
            water_volume_unit=volume_unit,
            final_loading_volume=final_volume,
            final_loading_volume_unit=volume_unit,
            target_protein_mass_ug=target_mass,
            summary=(
                "WB/SDS-PAGE 上样计算仅估算样品、loading buffer 和水的体积；"
                "使用前需人工核对蛋白定量方法、样品兼容性、还原/变性条件和实验 SOP。"
            ),
            warnings=(CALCULATION_REVIEW_NOTICE,),
        )
    except CalculationError as exc:
        unit = _safe_unit(input_data.volume_unit)
        return WesternBlotLoadingResult(
            valid=False,
            sample_volume=None,
            sample_volume_unit=unit,
            loading_buffer_volume=None,
            loading_buffer_volume_unit=unit,
            water_volume=None,
            water_volume_unit=unit,
            final_loading_volume=None,
            final_loading_volume_unit=unit,
            target_protein_mass_ug=None,
            summary="Western blot / SDS-PAGE 上样计算未生成结果。",
            errors=(str(exc),),
        )


def _concentration_to_base(value: float, unit: str) -> float:
    kind = unit_kind(unit)
    if kind == "molarity":
        return molarity_to_m(value, unit)
    if kind == "mass_concentration":
        return mass_concentration_to_g_per_l(value, unit)
    raise CalculationError("请选择有效浓度单位。")


def _cell_density_to_cells_per_ml(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical == "cells/mL":
        return value
    if canonical == "cells/µL":
        return value * 1000
    raise CalculationError("当前细胞悬液浓度单位必须是 cells/mL 或 cells/µL/uL。")


def _mass_concentration_to_ug_per_ul(value: float, unit: str) -> float:
    return mass_concentration_to_g_per_l(value, unit)


def _parse_positive_int(value: object, field_name: str) -> int:
    number = parse_number(value, field_name, allow_zero=False)
    if int(number) != number:
        raise CalculationError(f"{field_name}必须是正整数。")
    return int(number)


def _safe_unit(unit: str) -> str:
    try:
        return canonical_unit(unit)
    except CalculationError:
        return str(unit or "")


def _result_text(
    title: str,
    valid: bool,
    result_lines: tuple[str, ...],
    summary: str,
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
) -> str:
    if not valid:
        return "\n".join(["输入需要调整", *errors, "", "说明", summary])
    sections = [title, "", "结果", *result_lines, "", "说明", summary]
    if warnings:
        sections.extend(["", "人工核对提示", *warnings])
    return "\n".join(sections)


_QPCR_LABELS = {
    "master_mix_uL": "master mix",
    "forward_primer_uL": "forward primer",
    "reverse_primer_uL": "reverse primer",
    "template_uL": "template / cDNA",
    "nuclease_free_water_uL": "nuclease-free water",
}
