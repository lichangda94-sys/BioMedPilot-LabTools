"""Public LabTools package extracted from BioMedPilot."""

from labtools.calculators import (
    CALCULATION_REVIEW_NOTICE,
    CalculationError,
    CalculationRecord,
    CalculationResult,
    CellSeedingInput,
    CellSeedingResult,
    DilutionInput,
    DilutionResult,
    MassMolarityInput,
    MassMolarityResult,
    QpcrMixInput,
    QpcrMixResult,
    WesternBlotLoadingInput,
    WesternBlotLoadingResult,
    calculate_cell_seeding,
    calculate_cell_seeding_v1,
    calculate_dilution,
    calculate_dilution_v1,
    calculate_mass_for_molar_solution,
    calculate_mass_molarity_v1,
    calculate_molar_concentration,
    calculate_qpcr_mix,
    calculate_qpcr_mix_v1,
    calculate_solution_preparation,
    calculate_western_blot_loading_v1,
    convert_concentration,
    format_cell_seeding_copy_text,
    format_dilution_copy_text,
    format_mass_molarity_copy_text,
)
from labtools.shared.version import APP_VERSION as __version__


def smoke_test() -> dict[str, object]:
    """Import key public surfaces and return a small status payload."""

    from labtools import cell_culture, elisa, pcr_qpcr, reagent_templates, western_blot

    return {
        "version": __version__,
        "modules": (
            "labtools.calculators",
            reagent_templates.__name__,
            western_blot.__name__,
            pcr_qpcr.__name__,
            cell_culture.__name__,
            elisa.__name__,
        ),
    }


__all__ = [
    "__version__",
    "CALCULATION_REVIEW_NOTICE",
    "CalculationError",
    "CalculationRecord",
    "CalculationResult",
    "CellSeedingInput",
    "CellSeedingResult",
    "DilutionInput",
    "DilutionResult",
    "MassMolarityInput",
    "MassMolarityResult",
    "QpcrMixInput",
    "QpcrMixResult",
    "WesternBlotLoadingInput",
    "WesternBlotLoadingResult",
    "calculate_cell_seeding",
    "calculate_cell_seeding_v1",
    "calculate_dilution",
    "calculate_dilution_v1",
    "calculate_mass_for_molar_solution",
    "calculate_mass_molarity_v1",
    "calculate_molar_concentration",
    "calculate_qpcr_mix",
    "calculate_qpcr_mix_v1",
    "calculate_solution_preparation",
    "calculate_western_blot_loading_v1",
    "convert_concentration",
    "format_cell_seeding_copy_text",
    "format_dilution_copy_text",
    "format_mass_molarity_copy_text",
    "smoke_test",
]
