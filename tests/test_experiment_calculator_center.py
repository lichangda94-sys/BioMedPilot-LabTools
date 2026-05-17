from __future__ import annotations

import pytest

from labtools.calculators.experiment_calculator_center import (
    CellSeedingInput,
    DilutionInput,
    MassMolarityInput,
    calculate_cell_seeding_v1,
    calculate_dilution_v1,
    calculate_mass_molarity_v1,
    format_cell_seeding_copy_text,
    format_dilution_copy_text,
    format_mass_molarity_copy_text,
)


def test_l5b_dilution_calculates_stock_and_solvent_volumes() -> None:
    result = calculate_dilution_v1(DilutionInput(10, "mM", 1, "mM", 1000, "uL"))

    assert result.valid is True
    assert result.stock_volume == pytest.approx(100)
    assert result.stock_volume_unit == "µL"
    assert result.solvent_volume == pytest.approx(900)
    assert result.dilution_factor == pytest.approx(10)
    assert "实验辅助草稿" in result.summary
    assert "人工复核" in result.as_text()


def test_l5b_dilution_converts_units_with_stable_output_unit() -> None:
    result = calculate_dilution_v1(DilutionInput(1, "M", 100, "mM", 10, "mL"))

    assert result.valid is True
    assert result.stock_volume == pytest.approx(1)
    assert result.stock_volume_unit == "mL"
    assert result.solvent_volume == pytest.approx(9)
    assert result.dilution_factor == pytest.approx(10)


def test_l5b_dilution_reports_validation_errors() -> None:
    higher_target = calculate_dilution_v1(DilutionInput(10, "µM", 100, "µM", 1, "mL"))
    negative_stock = calculate_dilution_v1(DilutionInput(-1, "mM", 100, "µM", 1, "mL"))
    unknown_unit = calculate_dilution_v1(DilutionInput(10, "ppm", 100, "µM", 1, "mL"))
    mixed_dimensions = calculate_dilution_v1(DilutionInput(1, "mg/mL", 100, "µM", 1, "mL"))

    assert higher_target.valid is False
    assert "目标浓度不能高于 stock 浓度" in higher_target.errors[0]
    assert negative_stock.valid is False
    assert "不能为负数" in negative_stock.errors[0]
    assert unknown_unit.valid is False
    assert "暂不支持单位" in unknown_unit.errors[0]
    assert mixed_dimensions.valid is False
    assert "单位维度不同" in mixed_dimensions.errors[0]


def test_l5b_mass_molarity_calculates_required_mass() -> None:
    result = calculate_mass_molarity_v1(MassMolarityInput(100, 1, "mM", 10, "mL", "mg"))

    assert result.valid is True
    assert result.moles == pytest.approx(0.00001)
    assert result.required_mass == pytest.approx(1)
    assert result.required_mass_unit == "mg"
    assert "试剂纯度" in result.summary
    assert "人工复核" in result.as_text()


def test_l5b_mass_molarity_supports_unit_aliases() -> None:
    microgram = calculate_mass_molarity_v1(MassMolarityInput(100, 10, "uM", 1, "mL", "ug"))
    canonical_microgram = calculate_mass_molarity_v1(MassMolarityInput(100, 10, "µM", 1, "mL", "µg"))

    assert microgram.valid is True
    assert microgram.required_mass_unit == "µg"
    assert canonical_microgram.required_mass == pytest.approx(microgram.required_mass)


def test_l5b_mass_molarity_reports_validation_errors() -> None:
    bad_mw = calculate_mass_molarity_v1(MassMolarityInput(0, 1, "mM", 10, "mL", "mg"))
    bad_concentration = calculate_mass_molarity_v1(MassMolarityInput(100, 0, "mM", 10, "mL", "mg"))
    bad_volume = calculate_mass_molarity_v1(MassMolarityInput(100, 1, "mM", 0, "mL", "mg"))
    bad_mass_unit = calculate_mass_molarity_v1(MassMolarityInput(100, 1, "mM", 10, "mL", "IU"))

    assert bad_mw.valid is False
    assert "分子量必须大于 0" in bad_mw.errors[0]
    assert bad_concentration.valid is False
    assert "目标摩尔浓度必须大于 0" in bad_concentration.errors[0]
    assert bad_volume.valid is False
    assert "终体积必须大于 0" in bad_volume.errors[0]
    assert bad_mass_unit.valid is False
    assert "暂不支持单位" in bad_mass_unit.errors[0]


def test_l5b_cell_seeding_calculates_suspension_and_medium_volumes() -> None:
    result = calculate_cell_seeding_v1(CellSeedingInput(1e6, "cells/mL", 10000, 24, 500, "uL", 10))

    assert result.valid is True
    assert result.total_cells_required == pytest.approx(264000)
    assert result.total_final_volume == pytest.approx(13200)
    assert result.required_cell_suspension_volume == pytest.approx(264)
    assert result.required_medium_volume == pytest.approx(12936)
    assert result.required_medium_volume_unit == "µL"
    assert result.overage_percentage == pytest.approx(10)
    assert "辅助计算草稿" in result.summary
    assert "人工复核" in result.as_text()


def test_l5b_cell_seeding_reports_validation_errors() -> None:
    bad_wells = calculate_cell_seeding_v1(CellSeedingInput(1e6, "cells/mL", 10000, 0, 500, "µL", 10))
    bad_concentration = calculate_cell_seeding_v1(CellSeedingInput(0, "cells/mL", 10000, 24, 500, "µL", 10))
    bad_target = calculate_cell_seeding_v1(CellSeedingInput(1e6, "cells/mL", 0, 24, 500, "µL", 10))
    insufficient_density = calculate_cell_seeding_v1(CellSeedingInput(100, "cells/mL", 10000, 24, 500, "µL", 10))

    assert bad_wells.valid is False
    assert "孔数必须大于 0" in bad_wells.errors[0]
    assert bad_concentration.valid is False
    assert "当前细胞悬液浓度必须大于 0" in bad_concentration.errors[0]
    assert bad_target.valid is False
    assert "目标每孔细胞数必须大于 0" in bad_target.errors[0]
    assert insufficient_density.valid is False
    assert "浓度不足" in insufficient_density.errors[0]


def test_l5b_cell_seeding_supports_cells_per_microliter_alias() -> None:
    result = calculate_cell_seeding_v1(CellSeedingInput(1000, "cells/uL", 10000, 1, 500, "µL", 0))

    assert result.valid is True
    assert result.required_cell_suspension_volume == pytest.approx(10)
    assert result.required_cell_suspension_volume_unit == "µL"


def test_l7a_dilution_copy_text_is_user_facing_and_reviewable() -> None:
    input_data = DilutionInput(10, "mM", 1, "mM", 1000, "uL")
    result = calculate_dilution_v1(input_data)

    text = format_dilution_copy_text(input_data, result)

    assert "溶液稀释 C1V1=C2V2" in text
    assert "stock volume" in text
    assert "100 µL" in text
    assert "solvent volume" in text
    assert "900 µL" in text
    assert "人工核对" in text
    assert "实验辅助计算草稿，不替代实验 SOP" in text
    assert "正式 SOP" not in text
    assert "临床诊断" not in text
    assert "production" not in text


def test_l7a_mass_molarity_copy_text_includes_inputs_and_required_mass() -> None:
    input_data = MassMolarityInput(100, 1, "mM", 10, "mL", "mg")
    result = calculate_mass_molarity_v1(input_data)

    text = format_mass_molarity_copy_text(input_data, result)

    assert "摩尔浓度 / 称量质量换算" in text
    assert "MW 100 g/mol" in text
    assert "concentration 1 mM" in text
    assert "volume 10 mL" in text
    assert "required mass" in text
    assert "1 mg" in text
    assert "人工核对" in text


def test_l7a_cell_seeding_copy_text_includes_cell_and_volume_outputs() -> None:
    input_data = CellSeedingInput(1e6, "cells/mL", 10000, 24, 500, "uL", 10)
    result = calculate_cell_seeding_v1(input_data)

    text = format_cell_seeding_copy_text(input_data, result)

    assert "细胞接种密度计算" in text
    assert "total cells" in text
    assert "264000 cells" in text
    assert "suspension volume" in text
    assert "264 µL" in text
    assert "medium volume" in text
    assert "12936 µL" in text
    assert "实验辅助计算草稿，不替代实验 SOP" in text


def test_l7a_invalid_results_do_not_generate_success_copy_text() -> None:
    invalid_dilution_input = DilutionInput(1, "mM", 10, "mM", 1, "mL")
    invalid_mass_input = MassMolarityInput(0, 1, "mM", 10, "mL", "mg")
    invalid_cell_input = CellSeedingInput(0, "cells/mL", 10000, 24, 500, "µL", 10)

    assert format_dilution_copy_text(invalid_dilution_input, calculate_dilution_v1(invalid_dilution_input)) == ""
    assert format_mass_molarity_copy_text(invalid_mass_input, calculate_mass_molarity_v1(invalid_mass_input)) == ""
    assert format_cell_seeding_copy_text(invalid_cell_input, calculate_cell_seeding_v1(invalid_cell_input)) == ""
