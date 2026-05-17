from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from labtools.calculators.calculator_models import REVIEW_TIP


def _json_compatible(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


@dataclass(frozen=True)
class CalculationRecord:
    record_id: str
    calculator_type: str
    created_at: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    formula: list[str]
    warnings: list[str] = field(default_factory=list)
    review_notice: str = REVIEW_TIP

    @classmethod
    def create(
        cls,
        *,
        calculator_type: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        formula: list[str] | tuple[str, ...],
        warnings: list[str] | tuple[str, ...] | None = None,
        review_notice: str = REVIEW_TIP,
    ) -> "CalculationRecord":
        return cls(
            record_id=uuid4().hex,
            calculator_type=calculator_type,
            created_at=datetime.now(timezone.utc).isoformat(),
            inputs=dict(inputs),
            outputs=dict(outputs),
            formula=list(formula),
            warnings=list(warnings or []),
            review_notice=review_notice,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "calculator_type": self.calculator_type,
            "created_at": self.created_at,
            "inputs": _json_compatible(self.inputs),
            "outputs": _json_compatible(self.outputs),
            "formula": _json_compatible(self.formula),
            "warnings": _json_compatible(self.warnings),
            "review_notice": self.review_notice,
        }

    def summary_lines(self) -> tuple[str, ...]:
        output_text = "；".join(f"{key}: {value}" for key, value in self.outputs.items())
        return (
            f"最近一次计算：{self.calculator_type}",
            f"记录编号：{self.record_id[:8]}",
            output_text or "暂无输出摘要",
            self.review_notice,
        )
