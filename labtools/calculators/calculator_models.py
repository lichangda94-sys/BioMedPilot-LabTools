from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


REVIEW_TIP = "请人工复核计算结果后再用于实验。"


class CalculationError(ValueError):
    """User-facing calculation validation error."""


@dataclass(frozen=True)
class CalculationResult:
    title: str
    input_summary: tuple[str, ...]
    formula: tuple[str, ...]
    result_lines: tuple[str, ...]
    review_tip: str = REVIEW_TIP
    result_value: float | None = None
    result_unit: str | None = None
    warnings: tuple[str, ...] = ()
    record_inputs: dict[str, Any] = field(default_factory=dict)
    record_outputs: dict[str, Any] = field(default_factory=dict)

    def as_text(self) -> str:
        sections = [
            "输入摘要",
            *self.input_summary,
            "",
            "计算公式",
            *self.formula,
            "",
            "结果",
            *self.result_lines,
            "",
        ]
        if self.warnings:
            sections.extend(["提示", *self.warnings, ""])
        sections.extend(["复核提示", self.review_tip])
        return "\n".join(sections)

    def to_record(self, calculator_type: str):
        from labtools.calculators.calculation_record import CalculationRecord

        inputs = self.record_inputs or {f"input_{index + 1}": value for index, value in enumerate(self.input_summary)}
        outputs = self.record_outputs or {f"output_{index + 1}": value for index, value in enumerate(self.result_lines)}
        return CalculationRecord.create(
            calculator_type=calculator_type,
            inputs=inputs,
            outputs=outputs,
            formula=list(self.formula),
            warnings=list(self.warnings),
            review_notice=self.review_tip,
        )
