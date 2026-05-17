from __future__ import annotations

import pytest

from labtools.western_blot import (
    BCA_REVIEW_NOTICE,
    BcaWellAnnotation,
    analyze_bca_assay,
    annotate_well,
    annotate_well_range,
    parse_bca_od_matrix,
)


def _matrix_text(*, with_headers: bool = False) -> str:
    rows = []
    values = [[0.10 for _ in range(12)] for _ in range(8)]
    values[0][0] = 0.10
    values[0][1] = 0.10
    values[0][2] = 0.30
    values[0][3] = 0.30
    values[0][4] = 0.50
    values[0][5] = 0.50
    values[0][6] = 0.40
    values[0][7] = 0.40
    if with_headers:
        rows.append("\t" + "\t".join(str(index) for index in range(1, 13)))
    for row_index, row_name in enumerate("ABCDEFGH"):
        cells = "\t".join(f"{value:.3f}" for value in values[row_index])
        rows.append(f"{row_name}\t{cells}" if with_headers else cells)
    return "\n".join(rows)


def _linear_plate_and_annotations():
    plate = parse_bca_od_matrix(_matrix_text())
    annotations: dict[str, BcaWellAnnotation] = {}
    annotations = annotate_well_range(annotations, "A1", "A2", "Standard", name="BSA", standard_concentration=0)
    annotations = annotate_well_range(annotations, "A3", "A4", "Standard", name="BSA", standard_concentration=100)
    annotations = annotate_well_range(annotations, "A5", "A6", "Standard", name="BSA", standard_concentration=200)
    annotations = annotate_well_range(annotations, "A7", "A8", "Sample", name="Sample 1", dilution_factor=2, note="用户备注")
    return plate, annotations


def test_parse_plain_8_by_12_od_matrix() -> None:
    plate = parse_bca_od_matrix(_matrix_text())

    assert len(plate.values) == 96
    assert plate.value("A1") == pytest.approx(0.1)
    assert plate.value("H12") == pytest.approx(0.1)


def test_parse_matrix_with_row_and_column_headers() -> None:
    plate = parse_bca_od_matrix(_matrix_text(with_headers=True))

    assert plate.value("A3") == pytest.approx(0.3)
    assert plate.value("H12") == pytest.approx(0.1)


def test_annotation_and_batch_range_annotation_are_available() -> None:
    annotations: dict[str, BcaWellAnnotation] = {}
    annotations = annotate_well(annotations, "A1", "Blank")
    annotations = annotate_well_range(annotations, "B1", "B3", "Sample", name="S", dilution_factor=5)

    assert annotations["A1"].well_type == "Blank"
    assert {annotations[well].well_type for well in ("B1", "B2", "B3")} == {"Sample"}
    assert annotations["B3"].dilution_factor == 5


def test_standard_and_sample_replicate_statistics_and_linear_fit_are_correct() -> None:
    plate, annotations = _linear_plate_and_annotations()
    result = analyze_bca_assay(plate, annotations)

    assert result.standard_curve[1].mean_od == pytest.approx(0.3)
    assert result.standard_curve[1].sd == pytest.approx(0)
    assert result.standard_curve[1].cv_percent == pytest.approx(0)
    assert result.fit.slope == pytest.approx(0.002)
    assert result.fit.intercept == pytest.approx(0.1)
    assert result.fit.r_squared == pytest.approx(1.0)
    sample = result.sample_results[0]
    assert sample.mean_od == pytest.approx(0.4)
    assert sample.measured_concentration == pytest.approx(150)
    assert sample.original_sample_concentration == pytest.approx(300)
    assert sample.note == "用户备注"


def test_blank_subtraction_is_optional_and_negative_corrected_od_warns() -> None:
    text = _matrix_text().replace("0.100", "0.050", 2)
    lines = text.splitlines()
    row_b = lines[1].split("\t")
    row_b[0] = "0.020"
    lines[1] = "\t".join(row_b)
    text = "\n".join(lines)
    plate = parse_bca_od_matrix(text)
    annotations: dict[str, BcaWellAnnotation] = {}
    annotations = annotate_well_range(annotations, "A1", "A2", "Blank")
    annotations = annotate_well_range(annotations, "A3", "A4", "Standard", name="BSA", standard_concentration=0)
    annotations = annotate_well_range(annotations, "A5", "A6", "Standard", name="BSA", standard_concentration=100)
    annotations = annotate_well_range(annotations, "A7", "A8", "Standard", name="BSA", standard_concentration=200)
    annotations = annotate_well(annotations, "B1", "Sample", name="Low", dilution_factor=1)

    no_blank = analyze_bca_assay(plate, annotations, blank_subtraction_enabled=False)
    with_blank = analyze_bca_assay(plate, annotations, blank_subtraction_enabled=True)

    assert no_blank.blank_mean_od is None
    assert with_blank.blank_mean_od == pytest.approx(0.05)
    assert any("扣 blank 后 OD < 0" in warning for warning in with_blank.warnings)


def test_zero_standard_only_prompts_and_does_not_auto_blank_subtract() -> None:
    plate, annotations = _linear_plate_and_annotations()
    result = analyze_bca_assay(plate, annotations, blank_subtraction_enabled=False)

    assert result.blank_mean_od is None
    assert any("不会自动扣除" in warning for warning in result.warnings)


def test_low_r_squared_triggers_warning() -> None:
    plate = parse_bca_od_matrix(_matrix_text().replace("0.500", "0.900", 1))
    _, annotations = _linear_plate_and_annotations()
    result = analyze_bca_assay(plate, annotations)

    assert result.fit.r_squared is not None
    assert result.fit.r_squared < 0.98
    assert "标准曲线拟合质量需人工核对" in result.warnings


def test_high_cv_triggers_warnings_for_standard_and_sample() -> None:
    text = _matrix_text().replace("0.300", "0.800", 1).replace("0.400", "0.900", 1)
    plate = parse_bca_od_matrix(text)
    _, annotations = _linear_plate_and_annotations()
    result = analyze_bca_assay(plate, annotations)

    assert any("标准品重复孔差异较大" in warning for warning in result.warnings)
    assert any("样本重复孔差异较大" in warning for warning in result.warnings)


def test_sample_out_of_range_and_negative_concentration_warn() -> None:
    high_plate = parse_bca_od_matrix(_matrix_text().replace("0.400", "0.900", 2))
    _, annotations = _linear_plate_and_annotations()
    high = analyze_bca_assay(high_plate, annotations)
    assert any("样本 OD 超出标准曲线 OD 范围" in warning for warning in high.warnings)
    assert any("样本计算浓度超出标准浓度范围" in warning for warning in high.warnings)

    low_plate = parse_bca_od_matrix(_matrix_text().replace("0.400", "0.050", 2))
    low = analyze_bca_assay(low_plate, annotations)
    assert any("样本浓度计算为负数" in warning for warning in low.warnings)


def test_copy_text_contains_summary_and_review_notice() -> None:
    plate, annotations = _linear_plate_and_annotations()
    result = analyze_bca_assay(plate, annotations)
    text = result.copy_text()

    assert "标准曲线公式" in text
    assert "R²" in text
    assert "样本结果" in text
    assert "警告列表" in text
    assert BCA_REVIEW_NOTICE in text


def test_outlier_wells_are_not_automatically_removed() -> None:
    plate = parse_bca_od_matrix(_matrix_text().replace("0.400", "4.500", 1))
    _, annotations = _linear_plate_and_annotations()
    result = analyze_bca_assay(plate, annotations)

    sample = result.sample_results[0]
    assert sample.wells == ("A7", "A8")
    assert any("异常高 OD" in warning for warning in result.warnings)
