from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from typing import Any


BCA_REVIEW_NOTICE = "结果为 BCA 蛋白浓度测定辅助计算草稿。使用前请结合试剂盒说明书、标准曲线质量、重复孔一致性和实验室 SOP 人工核对。"
BCA_CV_WARNING_THRESHOLD = 15.0
BCA_R2_WARNING_THRESHOLD = 0.98
BCA_HIGH_OD_WARNING_THRESHOLD = 4.0
BCA_SUPPORTED_CONCENTRATION_UNITS = ("µg/mL", "mg/mL")
BCA_WELL_TYPES = ("Blank", "Standard", "Sample", "Unused")
BCA_ROWS = tuple("ABCDEFGH")
BCA_COLUMNS = tuple(range(1, 13))


class BcaAssayError(ValueError):
    pass


@dataclass(frozen=True)
class BcaWellAnnotation:
    well: str
    well_type: str
    name: str = ""
    standard_concentration: float | None = None
    concentration_unit: str = "µg/mL"
    dilution_factor: float = 1.0
    note: str = ""
    include_in_calculation: bool = True


@dataclass(frozen=True)
class BcaPlateMatrix:
    values: dict[str, float | None]
    warnings: tuple[str, ...] = ()

    def value(self, well: str) -> float | None:
        return self.values.get(normalize_well(well))


@dataclass(frozen=True)
class BcaRawDataRow:
    well: str
    well_type: str
    name: str
    raw_od: float | None
    blank_corrected_od: float | None
    include_in_calculation: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class BcaStandardCurveRow:
    standard_name: str
    standard_concentration: float
    concentration_unit: str
    wells: tuple[str, ...]
    mean_od: float | None
    sd: float | None
    cv_percent: float | None
    used_for_fit: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class BcaSampleResultRow:
    sample_name: str
    wells: tuple[str, ...]
    dilution_factor: float
    mean_od: float | None
    sd: float | None
    cv_percent: float | None
    measured_concentration: float | None
    original_sample_concentration: float | None
    unit: str
    out_of_standard_range: bool
    warnings: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class BcaFitResult:
    slope: float | None
    intercept: float | None
    r_squared: float | None
    standard_od_range: tuple[float, float] | None
    standard_concentration_range: tuple[float, float] | None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class BcaAnalysisResult:
    blank_subtraction_enabled: bool
    blank_mean_od: float | None
    raw_data: tuple[BcaRawDataRow, ...]
    standard_curve: tuple[BcaStandardCurveRow, ...]
    sample_results: tuple[BcaSampleResultRow, ...]
    fit: BcaFitResult
    warnings: tuple[str, ...]
    review_notice: str = BCA_REVIEW_NOTICE

    def to_dict(self) -> dict[str, Any]:
        return {
            "blank_subtraction_enabled": self.blank_subtraction_enabled,
            "blank_mean_od": self.blank_mean_od,
            "raw_data": [row.__dict__ for row in self.raw_data],
            "standard_curve": [row.__dict__ for row in self.standard_curve],
            "sample_results": [row.__dict__ for row in self.sample_results],
            "fit": self.fit.__dict__,
            "warnings": list(self.warnings),
            "review_notice": self.review_notice,
        }

    def copy_text(self) -> str:
        return build_bca_copy_text(self)


def parse_bca_od_matrix(text: str) -> BcaPlateMatrix:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        raise BcaAssayError("OD 矩阵为空")

    rows: list[list[str]] = []
    warnings: list[str] = []
    for line in lines:
        tokens = [token.strip() for token in re.split(r"\t|,|\s+", line) if token.strip()]
        if not tokens:
            continue
        if _is_header_row(tokens):
            continue
        if tokens[0].upper() in BCA_ROWS:
            tokens = tokens[1:]
        rows.append(tokens)

    if len(rows) != 8 or any(len(row) != 12 for row in rows):
        raise BcaAssayError("OD 矩阵需要为 8×12")

    values: dict[str, float | None] = {}
    for row_index, tokens in enumerate(rows):
        row_name = BCA_ROWS[row_index]
        for col_index, token in enumerate(tokens, start=1):
            well = f"{row_name}{col_index}"
            try:
                values[well] = float(token)
            except ValueError:
                values[well] = None
                warnings.append(f"{well}: 缺失值或非数值，需人工核对")
    return BcaPlateMatrix(values=values, warnings=tuple(warnings))


def annotate_well(
    annotations: dict[str, BcaWellAnnotation],
    well: str,
    well_type: str,
    *,
    name: str = "",
    standard_concentration: float | None = None,
    concentration_unit: str = "µg/mL",
    dilution_factor: float = 1.0,
    note: str = "",
    include_in_calculation: bool = True,
) -> dict[str, BcaWellAnnotation]:
    well_id = normalize_well(well)
    _validate_well_type(well_type)
    if concentration_unit not in BCA_SUPPORTED_CONCENTRATION_UNITS:
        raise BcaAssayError("暂不支持该浓度单位")
    if dilution_factor <= 0:
        raise BcaAssayError("稀释倍数需要为正数")
    updated = dict(annotations)
    updated[well_id] = BcaWellAnnotation(
        well=well_id,
        well_type=well_type,
        name=name,
        standard_concentration=standard_concentration,
        concentration_unit=concentration_unit,
        dilution_factor=dilution_factor,
        note=note,
        include_in_calculation=include_in_calculation,
    )
    return updated


def annotate_well_range(
    annotations: dict[str, BcaWellAnnotation],
    start_well: str,
    end_well: str,
    well_type: str,
    *,
    name: str = "",
    standard_concentration: float | None = None,
    concentration_unit: str = "µg/mL",
    dilution_factor: float = 1.0,
    note: str = "",
    include_in_calculation: bool = True,
) -> dict[str, BcaWellAnnotation]:
    updated = dict(annotations)
    for well in wells_in_range(start_well, end_well):
        updated = annotate_well(
            updated,
            well,
            well_type,
            name=name,
            standard_concentration=standard_concentration,
            concentration_unit=concentration_unit,
            dilution_factor=dilution_factor,
            note=note,
            include_in_calculation=include_in_calculation,
        )
    return updated


def analyze_bca_assay(
    plate: BcaPlateMatrix,
    annotations: dict[str, BcaWellAnnotation],
    *,
    blank_subtraction_enabled: bool = False,
) -> BcaAnalysisResult:
    warnings = list(plate.warnings)
    normalized_annotations = {normalize_well(well): replace(annotation, well=normalize_well(annotation.well)) for well, annotation in annotations.items()}
    blank_values = [
        plate.value(annotation.well)
        for annotation in normalized_annotations.values()
        if annotation.well_type == "Blank" and _valid_number(plate.value(annotation.well))
    ]
    blank_mean = mean(blank_values) if blank_subtraction_enabled and blank_values else None
    if blank_subtraction_enabled and not blank_values:
        warnings.append("已启用 blank 扣除，但未找到有效 Blank 孔")
    if not blank_values and _has_zero_standard(normalized_annotations):
        warnings.append("未标注 Blank；可考虑使用 0 浓度标准作为 blank，但不会自动扣除")

    raw_rows: list[BcaRawDataRow] = []
    corrected_by_well: dict[str, float] = {}
    for well in _all_plate_wells():
        annotation = normalized_annotations.get(well, BcaWellAnnotation(well=well, well_type="Unused"))
        raw = plate.value(well)
        row_warnings = _od_warnings(well, raw)
        corrected = raw - blank_mean if _valid_number(raw) and blank_mean is not None else raw
        if _valid_number(corrected):
            corrected_by_well[well] = corrected
            if corrected < 0:
                row_warnings.append("扣 blank 后 OD < 0，需人工核对")
        raw_rows.append(
            BcaRawDataRow(
                well=well,
                well_type=annotation.well_type,
                name=annotation.name,
                raw_od=raw,
                blank_corrected_od=corrected if blank_subtraction_enabled else None,
                include_in_calculation=annotation.include_in_calculation and annotation.well_type != "Unused",
                warnings=tuple(row_warnings),
            )
        )

    standard_rows = _build_standard_rows(normalized_annotations, corrected_by_well)
    sample_rows: list[BcaSampleResultRow] = []
    fit = _fit_standard_curve(standard_rows)
    warnings.extend(fit.warnings)
    if fit.r_squared is not None and fit.r_squared < BCA_R2_WARNING_THRESHOLD:
        warnings.append("标准曲线拟合质量需人工核对")
    warnings.extend(_collect_standard_warnings(standard_rows))

    sample_rows = _build_sample_rows(normalized_annotations, corrected_by_well, fit)
    warnings.extend(_collect_sample_warnings(sample_rows))
    warnings.extend(_collect_raw_warnings(raw_rows))

    return BcaAnalysisResult(
        blank_subtraction_enabled=blank_subtraction_enabled,
        blank_mean_od=blank_mean,
        raw_data=tuple(raw_rows),
        standard_curve=tuple(standard_rows),
        sample_results=tuple(sample_rows),
        fit=fit,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def build_bca_copy_text(result: BcaAnalysisResult) -> str:
    fit = result.fit
    formula = "标准曲线无效"
    if fit.slope is not None and fit.intercept is not None:
        formula = f"OD = {_fmt(fit.slope)} × concentration + {_fmt(fit.intercept)}"
    lines = [
        "BCA 蛋白浓度测定辅助计算摘要",
        f"Blank 扣除：{'启用' if result.blank_subtraction_enabled else '未启用'}",
        f"Blank 平均 OD：{_fmt(result.blank_mean_od) if result.blank_mean_od is not None else '无'}",
        f"标准曲线公式：{formula}",
        f"R²：{_fmt(fit.r_squared) if fit.r_squared is not None else '无'}",
        "",
        "样本结果：",
    ]
    for row in result.sample_results:
        lines.append(
            f"- {row.sample_name}: 孔位 {', '.join(row.wells)}; 稀释倍数 {_fmt(row.dilution_factor)}; "
            f"平均 OD {_fmt(row.mean_od)}; 测定孔浓度 {_fmt(row.measured_concentration)} {row.unit}; "
            f"稀释修正后原始样本浓度 {_fmt(row.original_sample_concentration)} {row.unit}"
        )
        for warning in row.warnings:
            lines.append(f"  警告：{warning}")
    lines.append("")
    lines.append("警告列表：")
    lines.extend(f"- {warning}" for warning in result.warnings)
    if not result.warnings:
        lines.append("- 无自动警告；仍需人工复核。")
    lines.extend(["", result.review_notice])
    return "\n".join(lines)


def normalize_well(well: str) -> str:
    match = re.fullmatch(r"\s*([A-Ha-h])\s*0?([1-9]|1[0-2])\s*", well)
    if not match:
        raise BcaAssayError("孔位需要为 A1-H12")
    return f"{match.group(1).upper()}{int(match.group(2))}"


def wells_in_range(start_well: str, end_well: str) -> tuple[str, ...]:
    start = normalize_well(start_well)
    end = normalize_well(end_well)
    start_row, start_col = BCA_ROWS.index(start[0]), int(start[1:])
    end_row, end_col = BCA_ROWS.index(end[0]), int(end[1:])
    row_min, row_max = sorted((start_row, end_row))
    col_min, col_max = sorted((start_col, end_col))
    return tuple(f"{BCA_ROWS[row]}{col}" for row in range(row_min, row_max + 1) for col in range(col_min, col_max + 1))


def mean(values: list[float] | tuple[float, ...]) -> float:
    if not values:
        raise BcaAssayError("无法计算空列表均值")
    return sum(values) / len(values)


def sample_sd(values: list[float] | tuple[float, ...]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def cv_percent(values: list[float] | tuple[float, ...]) -> float | None:
    avg = mean(values)
    if avg == 0:
        return None
    return sample_sd(values) / abs(avg) * 100


def _build_standard_rows(annotations: dict[str, BcaWellAnnotation], corrected_by_well: dict[str, float]) -> list[BcaStandardCurveRow]:
    grouped: dict[tuple[str, float, str], list[str]] = {}
    for annotation in annotations.values():
        if annotation.well_type != "Standard" or not annotation.include_in_calculation:
            continue
        concentration = _standard_concentration_ug_per_ml(annotation)
        grouped.setdefault((annotation.name or "Standard", concentration, "µg/mL"), []).append(annotation.well)

    rows: list[BcaStandardCurveRow] = []
    for (name, concentration, unit), wells in sorted(grouped.items(), key=lambda item: item[0][1]):
        values = [corrected_by_well[well] for well in wells if well in corrected_by_well]
        warnings: list[str] = []
        avg = mean(values) if values else None
        sd_value = sample_sd(values) if values else None
        cv_value = cv_percent(values) if values else None
        if cv_value is not None and cv_value > BCA_CV_WARNING_THRESHOLD:
            warnings.append("标准品重复孔差异较大")
        rows.append(
            BcaStandardCurveRow(
                standard_name=name,
                standard_concentration=concentration,
                concentration_unit=unit,
                wells=tuple(wells),
                mean_od=avg,
                sd=sd_value,
                cv_percent=cv_value,
                used_for_fit=bool(values),
                warnings=tuple(warnings),
            )
        )
    return rows


def _fit_standard_curve(rows: list[BcaStandardCurveRow]) -> BcaFitResult:
    fit_rows = [row for row in rows if row.used_for_fit and row.mean_od is not None]
    warnings: list[str] = []
    if len(fit_rows) < 3:
        warnings.append("标准曲线点数不足")
        return BcaFitResult(None, None, None, None, None, tuple(warnings))
    x_values = [row.standard_concentration for row in fit_rows]
    y_values = [row.mean_od for row in fit_rows if row.mean_od is not None]
    x_avg = mean(x_values)
    y_avg = mean(y_values)
    denominator = sum((x - x_avg) ** 2 for x in x_values)
    if denominator == 0:
        warnings.append("标准曲线无效")
        return BcaFitResult(None, None, None, None, None, tuple(warnings))
    slope = sum((x - x_avg) * (y - y_avg) for x, y in zip(x_values, y_values, strict=True)) / denominator
    intercept = y_avg - slope * x_avg
    if slope <= 0:
        warnings.append("标准曲线无效")
    predicted = [slope * x + intercept for x in x_values]
    ss_res = sum((y - y_hat) ** 2 for y, y_hat in zip(y_values, predicted, strict=True))
    ss_tot = sum((y - y_avg) ** 2 for y in y_values)
    r_squared = 1 - ss_res / ss_tot if ss_tot else 0.0
    return BcaFitResult(
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        standard_od_range=(min(y_values), max(y_values)),
        standard_concentration_range=(min(x_values), max(x_values)),
        warnings=tuple(warnings),
    )


def _build_sample_rows(
    annotations: dict[str, BcaWellAnnotation],
    corrected_by_well: dict[str, float],
    fit: BcaFitResult,
) -> list[BcaSampleResultRow]:
    grouped: dict[tuple[str, float, str, str], list[str]] = {}
    for annotation in annotations.values():
        if annotation.well_type != "Sample" or not annotation.include_in_calculation:
            continue
        grouped.setdefault((annotation.name or "Sample", annotation.dilution_factor, "µg/mL", annotation.note), []).append(annotation.well)

    rows: list[BcaSampleResultRow] = []
    for (name, dilution, unit, note), wells in sorted(grouped.items(), key=lambda item: item[0][0]):
        values = [corrected_by_well[well] for well in wells if well in corrected_by_well]
        warnings: list[str] = []
        avg = mean(values) if values else None
        sd_value = sample_sd(values) if values else None
        cv_value = cv_percent(values) if values else None
        if cv_value is not None and cv_value > BCA_CV_WARNING_THRESHOLD:
            warnings.append("样本重复孔差异较大")
        measured = None
        original = None
        out_of_range = False
        if avg is not None and fit.slope is not None and fit.intercept is not None and fit.slope > 0:
            measured = (avg - fit.intercept) / fit.slope
            original = measured * dilution
            if measured < 0:
                warnings.append("样本浓度计算为负数，结果不可直接解释")
            if fit.standard_od_range and (avg < fit.standard_od_range[0] or avg > fit.standard_od_range[1]):
                out_of_range = True
                warnings.append("样本 OD 超出标准曲线 OD 范围，建议重新稀释或复测")
            if fit.standard_concentration_range and (measured < fit.standard_concentration_range[0] or measured > fit.standard_concentration_range[1]):
                out_of_range = True
                warnings.append("样本计算浓度超出标准浓度范围，建议重新稀释或复测")
        else:
            warnings.append("标准曲线无效，无法解释样本浓度")
        rows.append(
            BcaSampleResultRow(
                sample_name=name,
                wells=tuple(wells),
                dilution_factor=dilution,
                mean_od=avg,
                sd=sd_value,
                cv_percent=cv_value,
                measured_concentration=measured,
                original_sample_concentration=original,
                unit=unit,
                out_of_standard_range=out_of_range,
                warnings=tuple(dict.fromkeys(warnings)),
                note=note,
            )
        )
    return rows


def _standard_concentration_ug_per_ml(annotation: BcaWellAnnotation) -> float:
    if annotation.standard_concentration is None:
        raise BcaAssayError("标准品需要填写标准浓度")
    if annotation.standard_concentration < 0:
        raise BcaAssayError("标准浓度不能小于 0")
    if annotation.concentration_unit == "µg/mL":
        return annotation.standard_concentration
    if annotation.concentration_unit == "mg/mL":
        return annotation.standard_concentration * 1000
    raise BcaAssayError("暂不支持该浓度单位")


def _od_warnings(well: str, value: float | None) -> list[str]:
    if value is None:
        return [f"{well}: 缺失值或非数值，需人工核对"]
    warnings: list[str] = []
    if value < 0:
        warnings.append("负 OD，需人工核对")
    if value > BCA_HIGH_OD_WARNING_THRESHOLD:
        warnings.append("异常高 OD，需人工核对")
    return warnings


def _collect_standard_warnings(rows: list[BcaStandardCurveRow]) -> list[str]:
    warnings: list[str] = []
    for row in rows:
        warnings.extend(f"{row.standard_name} {row.standard_concentration:g} {row.concentration_unit}: {warning}" for warning in row.warnings)
    return warnings


def _collect_sample_warnings(rows: list[BcaSampleResultRow]) -> list[str]:
    warnings: list[str] = []
    for row in rows:
        warnings.extend(f"{row.sample_name}: {warning}" for warning in row.warnings)
    return warnings


def _collect_raw_warnings(rows: list[BcaRawDataRow]) -> list[str]:
    warnings: list[str] = []
    for row in rows:
        warnings.extend(f"{row.well}: {warning}" for warning in row.warnings)
    return warnings


def _has_zero_standard(annotations: dict[str, BcaWellAnnotation]) -> bool:
    return any(annotation.well_type == "Standard" and annotation.standard_concentration == 0 for annotation in annotations.values())


def _all_plate_wells() -> tuple[str, ...]:
    return tuple(f"{row}{column}" for row in BCA_ROWS for column in BCA_COLUMNS)


def _valid_number(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _validate_well_type(well_type: str) -> None:
    if well_type not in BCA_WELL_TYPES:
        raise BcaAssayError("孔类型需要为 Blank / Standard / Sample / Unused")


def _is_header_row(tokens: list[str]) -> bool:
    if tokens[0] == "" and len(tokens) > 1:
        tokens = tokens[1:]
    if len(tokens) == 12 and all(token.isdigit() for token in tokens):
        return [int(token) for token in tokens] == list(BCA_COLUMNS)
    if len(tokens) == 13 and tokens[0].upper() not in BCA_ROWS and all(token.isdigit() for token in tokens[1:]):
        return [int(token) for token in tokens[1:]] == list(BCA_COLUMNS)
    return False


def _fmt(value: float | None) -> str:
    if value is None:
        return "无"
    return f"{value:.4f}".rstrip("0").rstrip(".")
