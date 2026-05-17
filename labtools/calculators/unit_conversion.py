from __future__ import annotations

import math

from labtools.calculators.calculator_models import CalculationError


MASS_UNITS: dict[str, float] = {
    "g": 1.0,
    "mg": 1e-3,
    "µg": 1e-6,
    "ng": 1e-9,
}

VOLUME_UNITS: dict[str, float] = {
    "L": 1.0,
    "mL": 1e-3,
    "µL": 1e-6,
}

MOLARITY_UNITS: dict[str, float] = {
    "M": 1.0,
    "mM": 1e-3,
    "µM": 1e-6,
    "nM": 1e-9,
}

MASS_CONCENTRATION_UNITS: dict[str, float] = {
    "mg/mL": 1.0,
    "µg/µL": 1.0,
    "µg/mL": 1e-3,
    "ng/mL": 1e-6,
    "ng/µL": 1e-3,
}

CELL_DENSITY_UNITS: dict[str, float] = {
    "cells/mL": 1.0,
    "cells/µL": 1000.0,
}

UNIT_ALIASES = {
    "ug": "µg",
    "μg": "µg",
    "uL": "µL",
    "ul": "µL",
    "μL": "µL",
    "uM": "µM",
    "um": "µM",
    "μM": "µM",
    "ug/mL": "µg/mL",
    "μg/mL": "µg/mL",
    "ug/uL": "µg/µL",
    "ug/μL": "µg/µL",
    "µg/uL": "µg/µL",
    "μg/uL": "µg/µL",
    "μg/μL": "µg/µL",
    "ng/uL": "ng/µL",
    "ng/μL": "ng/µL",
    "cells/uL": "cells/µL",
    "cells/μL": "cells/µL",
    "cell/mL": "cells/mL",
    "cells/ml": "cells/mL",
}


def canonical_unit(unit: str) -> str:
    text = str(unit or "").strip()
    if not text:
        raise CalculationError("请选择单位。")
    canonical = UNIT_ALIASES.get(text, text)
    if (
        canonical in MASS_UNITS
        or canonical in VOLUME_UNITS
        or canonical in MOLARITY_UNITS
        or canonical in MASS_CONCENTRATION_UNITS
        or canonical in CELL_DENSITY_UNITS
    ):
        return canonical
    raise CalculationError(f"暂不支持单位：{text}。")


def parse_number(value: object, field_name: str, *, allow_zero: bool = True) -> float:
    if value is None or str(value).strip() == "":
        raise CalculationError(f"请填写{field_name}。")
    try:
        number = float(str(value).strip())
    except ValueError as exc:
        raise CalculationError(f"{field_name}必须是有效数字。") from exc
    if not math.isfinite(number):
        raise CalculationError(f"{field_name}必须是有效数字。")
    if number < 0:
        raise CalculationError(f"{field_name}不能为负数。")
    if not allow_zero and number == 0:
        raise CalculationError(f"{field_name}必须大于 0。")
    return number


def format_number(value: float) -> str:
    if value == 0:
        return "0"
    absolute = abs(value)
    if 1e-3 <= absolute < 1e6:
        text = f"{value:.6f}".rstrip("0").rstrip(".")
        return text or "0"
    return f"{value:.6g}"


def unit_kind(unit: str) -> str:
    canonical = canonical_unit(unit)
    if canonical in MASS_UNITS:
        return "mass"
    if canonical in VOLUME_UNITS:
        return "volume"
    if canonical in MOLARITY_UNITS:
        return "molarity"
    if canonical in MASS_CONCENTRATION_UNITS:
        return "mass_concentration"
    if canonical in CELL_DENSITY_UNITS:
        return "cell_density"
    raise CalculationError(f"暂不支持单位：{unit}。")


def validate_molecular_weight(value: object) -> float:
    return parse_number(value, "分子量（g/mol）", allow_zero=False)


def mass_to_g(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MASS_UNITS:
        raise CalculationError(f"{canonical} 不是质量单位。")
    return value * MASS_UNITS[canonical]


def g_to_mass(value_g: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MASS_UNITS:
        raise CalculationError(f"{canonical} 不是质量单位。")
    return value_g / MASS_UNITS[canonical]


def volume_to_l(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in VOLUME_UNITS:
        raise CalculationError(f"{canonical} 不是体积单位。")
    return value * VOLUME_UNITS[canonical]


def l_to_volume(value_l: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in VOLUME_UNITS:
        raise CalculationError(f"{canonical} 不是体积单位。")
    return value_l / VOLUME_UNITS[canonical]


def molarity_to_m(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MOLARITY_UNITS:
        raise CalculationError(f"{canonical} 不是物质的量浓度单位。")
    return value * MOLARITY_UNITS[canonical]


def m_to_molarity(value_m: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MOLARITY_UNITS:
        raise CalculationError(f"{canonical} 不是物质的量浓度单位。")
    return value_m / MOLARITY_UNITS[canonical]


def mass_concentration_to_g_per_l(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MASS_CONCENTRATION_UNITS:
        raise CalculationError(f"{canonical} 不是质量浓度单位。")
    return value * MASS_CONCENTRATION_UNITS[canonical]


def g_per_l_to_mass_concentration(value_g_per_l: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MASS_CONCENTRATION_UNITS:
        raise CalculationError(f"{canonical} 不是质量浓度单位。")
    return value_g_per_l / MASS_CONCENTRATION_UNITS[canonical]


def supported_concentration_units() -> tuple[str, ...]:
    return tuple(MOLARITY_UNITS) + tuple(MASS_CONCENTRATION_UNITS)


def supported_mass_units() -> tuple[str, ...]:
    return tuple(MASS_UNITS)


def supported_volume_units() -> tuple[str, ...]:
    return tuple(VOLUME_UNITS)


def supported_cell_density_units() -> tuple[str, ...]:
    return tuple(CELL_DENSITY_UNITS)
