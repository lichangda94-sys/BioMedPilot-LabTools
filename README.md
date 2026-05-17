# BioMedPilot-LabTools

BioMedPilot-LabTools is the open-source LabTools module for BioMedPilot / 医研智析. It provides reusable, test-covered Python helpers for common laboratory calculations, reagent template workflows, and Western Blot preparation utilities.

This repository is a standalone public package. It does not include the private BioMedPilot desktop shell or private application services.

## 中文简介

BioMedPilot-LabTools 是 BioMedPilot / 医研智析 的开源实验工具模块，当前聚焦于实验辅助计算、试剂模板、Western Blot 上样与相关配制工具。所有结果都应由实验人员结合实验室 SOP、试剂说明书和实际实验设计进行人工复核。

## Current Scope

The current package includes:

- General calculator models and shared calculation result handling
- Concentration calculation helpers
- Dilution calculation helpers
- Solution preparation helpers
- Calculation record serialization helpers
- qPCR mix calculator
- Cell seeding calculator
- Reagent template models, validation, preparation calculator, and local JSON store
- Western Blot loading calculator
- Western Blot protein loading helpers
- Western Blot loading record export helpers
- BCA assay helper for plate parsing, annotations, curve fitting, and review warnings
- SDS-PAGE gel template helper for user-defined gel templates and batch calculations
- Package-level smoke test via `python -m labtools --smoke-test`

The package is intended for reusable calculation and model logic first. UI code and private BioMedPilot application-shell integrations are intentionally outside the public package surface.

## Safety Boundaries

BioMedPilot-LabTools is an experimental laboratory helper library. It is not a medical device and must not be used as a substitute for professional review.

- Not for clinical diagnosis
- Not for treatment decisions
- Not for regulated medical use
- Not a replacement for laboratory SOPs, reagent manuals, safety policies, or human review
- All calculations and generated preparation records require human verification before use

## Installation

For local development:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Validation

Run the test suite and smoke test:

```bash
pytest
python -m labtools --smoke-test
```

Current known validation status for the initial public package:

```text
pytest: 124 passed
python -m labtools --smoke-test: passed
```

## Project Structure

```text
labtools/
  __init__.py
  __main__.py
  calculators/
    calculation_record.py
    calculator_models.py
    cell_seeding_calculator.py
    concentration_calculator.py
    dilution_calculator.py
    experiment_calculator_center.py
    qpcr_mix_calculator.py
    solution_preparation_calculator.py
    unit_conversion.py
  reagent_templates/
    calculator.py
    models.py
    store.py
  western_blot/
    bca_assay.py
    calculator.py
    exporter.py
    models.py
    protein_loading.py
    sds_page_gel_templates.py
    store.py
  shared/
    storage.py
    version.py
  pcr_qpcr/
  elisa/
  cell_culture/

tests/
  test_*.py
```

## Contribution Areas

Contributions are welcome when they improve the public package while preserving the safety boundaries above. Useful contribution areas include:

- Bug reports with reproducible inputs and expected behavior
- Documentation improvements and examples
- Additional tests for calculators, serialization, and edge cases
- Calculator improvements with clearly documented formulas
- Reagent template model and validation improvements
- Formula review by domain experts
- UI wording suggestions for future integrations, especially wording that improves safety, clarity, and human-review expectations

For formula or calculator changes, please include the source of the formula, unit assumptions, edge cases, and tests that show expected behavior.

## Commercial And Integration Boundary

This repository is the open-source LabTools module for BioMedPilot / 医研智析.

Accepted contributions may be integrated into BioMedPilot and related editions, including free, commercial, AI-assisted, cloud-based, premium, or future versions. Submitting a contribution does not create an employment, compensation, equity, ownership, or revenue-sharing relationship.

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
