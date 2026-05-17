# BioMedPilot-LabTools

`BioMedPilot-LabTools` is the open-source extraction of the reusable LabTools
calculation layer from the private BioMedPilot project.

Current public scope:

- general concentration, dilution, and solution-preparation calculators
- qPCR mix helpers
- cell seeding helpers
- reagent template models, validation, calculation, and local JSON store
- Western Blot loading, protein-loading, BCA, and SDS-PAGE gel-template logic

Excluded from this initial import:

- BioMedPilot application shell and desktop UI
- AI-assisted logic, cloud or membership features, payment or license services
- private prompts, user data, local cache, and build artifacts

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Test

```bash
pytest
python -m labtools --smoke-test
```

## Package Layout

```text
labtools/
  calculators/
  reagent_templates/
  western_blot/
  shared/
  pcr_qpcr/
  elisa/
  cell_culture/
```
