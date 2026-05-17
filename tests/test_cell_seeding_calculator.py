from __future__ import annotations

import pytest

from labtools.calculators.calculator_models import CalculationError
from labtools.calculators.cell_seeding_calculator import calculate_cell_seeding


def test_cell_seeding_calculates_required_volume_with_loss() -> None:
    result = calculate_cell_seeding(1_000_000, "cells/mL", 10_000, 24, loss_percent=10)

    assert result.result_value == pytest.approx(264.0)
    assert result.result_unit == "µL"
    assert result.record_outputs["total_cells"] == pytest.approx(264000)
    assert result.record_outputs["per_well_volume_uL"] == pytest.approx(11.0)
    text = result.as_text()
    assert "总细胞数 = 目标每孔细胞数 x 孔数" in text
    assert "请人工复核计算结果后再用于实验" in text


def test_cell_seeding_allows_zero_loss() -> None:
    result = calculate_cell_seeding(1_000_000, "cells/mL", 10_000, 10, loss_percent=0)

    assert result.record_outputs["total_cells"] == pytest.approx(100000)
    assert result.result_value == pytest.approx(100.0)


def test_cell_seeding_rejects_zero_or_negative_density() -> None:
    with pytest.raises(CalculationError, match="当前细胞悬液浓度必须大于 0"):
        calculate_cell_seeding(0, "cells/mL", 10_000, 24)
    with pytest.raises(CalculationError, match="不能为负数"):
        calculate_cell_seeding(-1, "cells/mL", 10_000, 24)


def test_cell_seeding_rejects_negative_loss() -> None:
    with pytest.raises(CalculationError, match="额外损耗比例不能为负数"):
        calculate_cell_seeding(1_000_000, "cells/mL", 10_000, 24, loss_percent=-1)
