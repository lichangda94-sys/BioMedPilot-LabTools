from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEFAULT_LOADING_OVERAGE_PERCENT = 3.0
PROTEIN_LOADING_REVIEW_NOTICE = (
    "结果为 Western Blot 上样体系辅助计算草稿。使用前请人工核对蛋白浓度测定方法、"
    "样本稀释状态、loading buffer 倍数、还原剂使用要求、加热变性条件和实验室 SOP。"
)
REDUCING_AGENT_NOTICE = (
    "请确认所用 loading buffer 是否已包含 DTT、β-ME 或其他还原剂；如未包含，"
    "请按试剂盒说明书或实验室 SOP 另行处理。"
)
SUPPORTED_PROTEIN_CONCENTRATION_UNITS = ("µg/µL", "ug/uL", "mg/mL", "µg/mL", "ug/mL")


class ProteinLoadingError(ValueError):
    pass


@dataclass(frozen=True)
class ProteinLoadingSampleInput:
    sample_name: str
    protein_concentration: float
    concentration_unit: str


@dataclass(frozen=True)
class ProteinLoadingSettings:
    target_protein_ug: float
    final_loading_volume_ul: float
    loading_buffer_multiple: float
    loading_buffer_target_concentration: float = 1.0
    overage_percent: float = DEFAULT_LOADING_OVERAGE_PERCENT


@dataclass(frozen=True)
class ProteinLoadingSampleResult:
    sample_name: str
    protein_concentration: float
    concentration_unit: str
    concentration_ug_per_ul: float
    target_protein_ug: float
    sample_volume_ul: float
    loading_buffer_volume_ul: float
    water_volume_ul: float
    final_loading_volume_ul: float
    overage_percent: float
    total_sample_volume_ul: float
    total_loading_buffer_volume_ul: float
    total_water_volume_ul: float
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_name": self.sample_name,
            "protein_concentration": self.protein_concentration,
            "concentration_unit": self.concentration_unit,
            "concentration_ug_per_ul": self.concentration_ug_per_ul,
            "target_protein_ug": self.target_protein_ug,
            "sample_volume_ul": self.sample_volume_ul,
            "loading_buffer_volume_ul": self.loading_buffer_volume_ul,
            "water_volume_ul": self.water_volume_ul,
            "final_loading_volume_ul": self.final_loading_volume_ul,
            "overage_percent": self.overage_percent,
            "total_sample_volume_ul": self.total_sample_volume_ul,
            "total_loading_buffer_volume_ul": self.total_loading_buffer_volume_ul,
            "total_water_volume_ul": self.total_water_volume_ul,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ProteinLoadingResult:
    settings: ProteinLoadingSettings
    samples: tuple[ProteinLoadingSampleResult, ...]
    total_sample_volume_ul: float
    total_loading_buffer_volume_ul: float
    total_water_volume_ul: float
    warnings: tuple[str, ...]
    review_notice: str = PROTEIN_LOADING_REVIEW_NOTICE
    reducing_agent_notice: str = REDUCING_AGENT_NOTICE

    def to_dict(self) -> dict[str, Any]:
        return {
            "settings": {
                "target_protein_ug": self.settings.target_protein_ug,
                "final_loading_volume_ul": self.settings.final_loading_volume_ul,
                "loading_buffer_multiple": self.settings.loading_buffer_multiple,
                "loading_buffer_target_concentration": self.settings.loading_buffer_target_concentration,
                "overage_percent": self.settings.overage_percent,
            },
            "samples": [sample.to_dict() for sample in self.samples],
            "total_sample_volume_ul": self.total_sample_volume_ul,
            "total_loading_buffer_volume_ul": self.total_loading_buffer_volume_ul,
            "total_water_volume_ul": self.total_water_volume_ul,
            "warnings": list(self.warnings),
            "review_notice": self.review_notice,
            "reducing_agent_notice": self.reducing_agent_notice,
        }

    def copy_text(self) -> str:
        return build_protein_loading_copy_text(self)


def calculate_protein_loading(
    samples: tuple[ProteinLoadingSampleInput, ...] | list[ProteinLoadingSampleInput],
    settings: ProteinLoadingSettings,
) -> ProteinLoadingResult:
    if settings.target_protein_ug <= 0:
        raise ProteinLoadingError("目标每孔蛋白量需要大于 0")
    if settings.final_loading_volume_ul <= 0:
        raise ProteinLoadingError("最终上样体积需要大于 0")
    if settings.loading_buffer_multiple <= settings.loading_buffer_target_concentration:
        raise ProteinLoadingError("请检查 loading buffer 设置")
    if settings.overage_percent < 0:
        raise ProteinLoadingError("余量百分比不能小于 0")
    if not samples:
        raise ProteinLoadingError("至少需要一个样本")

    loading_buffer_volume = (
        settings.final_loading_volume_ul
        * settings.loading_buffer_target_concentration
        / settings.loading_buffer_multiple
    )
    factor = 1 + settings.overage_percent / 100
    rows: list[ProteinLoadingSampleResult] = []
    all_warnings: list[str] = []

    for index, sample in enumerate(samples, start=1):
        name = sample.sample_name.strip() or f"Sample {index}"
        concentration = concentration_to_ug_per_ul(sample.protein_concentration, sample.concentration_unit)
        sample_volume = settings.target_protein_ug / concentration
        water_volume = settings.final_loading_volume_ul - sample_volume - loading_buffer_volume
        if water_volume < 0:
            raise ProteinLoadingError("组分体积超过最终上样体积，无法计算")

        warnings: list[str] = []
        if sample_volume < 1:
            warnings.append("蛋白样品体积 < 1 µL，移液体积过小，建议预稀释或人工核对")
        if water_volume < 1:
            warnings.append("补水体积 < 1 µL，移液可行性需人工核对")
        all_warnings.extend(f"{name}: {warning}" for warning in warnings)

        rows.append(
            ProteinLoadingSampleResult(
                sample_name=name,
                protein_concentration=sample.protein_concentration,
                concentration_unit=sample.concentration_unit,
                concentration_ug_per_ul=concentration,
                target_protein_ug=settings.target_protein_ug,
                sample_volume_ul=sample_volume,
                loading_buffer_volume_ul=loading_buffer_volume,
                water_volume_ul=water_volume,
                final_loading_volume_ul=settings.final_loading_volume_ul,
                overage_percent=settings.overage_percent,
                total_sample_volume_ul=sample_volume * factor,
                total_loading_buffer_volume_ul=loading_buffer_volume * factor,
                total_water_volume_ul=water_volume * factor,
                warnings=tuple(warnings),
            )
        )

    return ProteinLoadingResult(
        settings=settings,
        samples=tuple(rows),
        total_sample_volume_ul=sum(row.sample_volume_ul for row in rows) * factor,
        total_loading_buffer_volume_ul=sum(row.loading_buffer_volume_ul for row in rows) * factor,
        total_water_volume_ul=sum(row.water_volume_ul for row in rows) * factor,
        warnings=tuple(all_warnings),
    )


def concentration_to_ug_per_ul(value: float, unit: str) -> float:
    if value <= 0:
        raise ProteinLoadingError("蛋白浓度需要大于 0")
    normalized = unit.strip()
    if normalized not in SUPPORTED_PROTEIN_CONCENTRATION_UNITS:
        raise ProteinLoadingError("暂不支持该浓度单位")
    if normalized in ("µg/µL", "ug/uL", "mg/mL"):
        return value
    return value / 1000


def build_protein_loading_copy_text(result: ProteinLoadingResult) -> str:
    lines = [
        "Western Blot 蛋白上样体系辅助计算",
        f"目标每孔蛋白量：{_fmt(result.settings.target_protein_ug)} µg",
        f"最终上样体积：{_fmt(result.settings.final_loading_volume_ul)} µL",
        f"Loading buffer：{_fmt(result.settings.loading_buffer_multiple)}× 配至 {_fmt(result.settings.loading_buffer_target_concentration)}×",
        f"余量百分比：{_fmt(result.settings.overage_percent)}%",
        "",
        "样本结果：",
    ]
    for row in result.samples:
        lines.extend(
            [
                f"- {row.sample_name}",
                f"  蛋白样品浓度：{_fmt(row.protein_concentration)} {row.concentration_unit}",
                f"  每孔蛋白样品体积：{_fmt(row.sample_volume_ul)} µL",
                f"  每孔 loading buffer 体积：{_fmt(row.loading_buffer_volume_ul)} µL",
                f"  每孔补水体积：{_fmt(row.water_volume_ul)} µL",
                f"  每孔最终上样体积：{_fmt(row.final_loading_volume_ul)} µL",
                f"  总蛋白样品体积：{_fmt(row.total_sample_volume_ul)} µL",
                f"  总 loading buffer 体积：{_fmt(row.total_loading_buffer_volume_ul)} µL",
                f"  总补水体积：{_fmt(row.total_water_volume_ul)} µL",
            ]
        )
        for warning in row.warnings:
            lines.append(f"  警告：{warning}")
    lines.extend(
        [
            "",
            "总量：",
            f"- 总蛋白样品体积：{_fmt(result.total_sample_volume_ul)} µL",
            f"- 总 loading buffer 体积：{_fmt(result.total_loading_buffer_volume_ul)} µL",
            f"- 总补水体积：{_fmt(result.total_water_volume_ul)} µL",
            "",
            "警告：",
        ]
    )
    lines.extend(f"- {warning}" for warning in result.warnings)
    if not result.warnings:
        lines.append("- 无自动警告；仍需人工复核。")
    lines.extend(["", result.reducing_agent_notice, result.review_notice])
    return "\n".join(lines)


def _fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")
