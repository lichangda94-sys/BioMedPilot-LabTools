from __future__ import annotations

from labtools.calculators.calculation_record import CalculationRecord
from labtools.calculators.concentration_calculator import calculate_mass_for_molar_solution


def test_calculation_record_exports_json_compatible_dict() -> None:
    record = CalculationRecord.create(
        calculator_type="测试计算器",
        inputs={"value": 1, "items": ("a", "b")},
        outputs={"nested": {"answer": 2.5}},
        formula=("A = B",),
        warnings=("需要复核",),
    )

    payload = record.to_dict()

    assert payload["record_id"] == record.record_id
    assert payload["calculator_type"] == "测试计算器"
    assert payload["inputs"]["items"] == ["a", "b"]
    assert payload["outputs"]["nested"]["answer"] == 2.5
    assert payload["formula"] == ["A = B"]
    assert payload["warnings"] == ["需要复核"]
    assert "请人工复核计算结果后再用于实验" in payload["review_notice"]


def test_calculation_result_can_generate_record() -> None:
    result = calculate_mass_for_molar_solution(1, "mM", 1, "mL", 1000, output_unit="mg")
    record = result.to_record("称量质量")

    payload = record.to_dict()

    assert payload["calculator_type"] == "称量质量"
    assert payload["outputs"]["output_1"] == "所需质量：1 mg"
    assert payload["review_notice"] == "请人工复核计算结果后再用于实验。"
