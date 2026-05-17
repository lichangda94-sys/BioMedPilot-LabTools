from __future__ import annotations

import pytest

from labtools.calculators.calculator_models import CalculationError
from labtools.calculators.unit_conversion import (
    canonical_unit,
    mass_concentration_to_g_per_l,
    mass_to_g,
    molarity_to_m,
    parse_number,
    volume_to_l,
)


def test_supported_unit_aliases_are_canonicalized() -> None:
    assert canonical_unit("ug") == "µg"
    assert canonical_unit("uL") == "µL"
    assert canonical_unit("uM") == "µM"
    assert canonical_unit("ng/uL") == "ng/µL"
    assert canonical_unit("ug/mL") == "µg/mL"
    assert canonical_unit("ug/uL") == "µg/µL"
    assert canonical_unit("cells/uL") == "cells/µL"


def test_mass_volume_and_concentration_convert_to_base_units() -> None:
    assert mass_to_g(2, "mg") == pytest.approx(0.002)
    assert volume_to_l(500, "µL") == pytest.approx(0.0005)
    assert molarity_to_m(250, "µM") == pytest.approx(0.00025)
    assert mass_concentration_to_g_per_l(1, "mg/mL") == pytest.approx(1.0)
    assert mass_concentration_to_g_per_l(1, "µg/µL") == pytest.approx(1.0)
    assert mass_concentration_to_g_per_l(1, "ng/mL") == pytest.approx(1e-6)
    assert mass_concentration_to_g_per_l(1, "ng/µL") == pytest.approx(0.001)


def test_parse_number_reports_friendly_errors() -> None:
    with pytest.raises(CalculationError, match="请填写质量"):
        parse_number("", "质量")
    with pytest.raises(CalculationError, match="不能为负数"):
        parse_number("-1", "体积")
    with pytest.raises(CalculationError, match="必须大于 0"):
        parse_number("0", "目标体积", allow_zero=False)


def test_unknown_unit_reports_friendly_error() -> None:
    with pytest.raises(CalculationError, match="暂不支持单位"):
        canonical_unit("ppm")
