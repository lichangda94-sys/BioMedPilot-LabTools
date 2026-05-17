# Contributing to BioMedPilot-LabTools

Thank you for your interest in contributing to BioMedPilot-LabTools.

BioMedPilot-LabTools is the open-source laboratory tools module of **BioMedPilot / 医研智析**. The project welcomes contributions from biomedical researchers, PhD students, clinicians, laboratory users, Python developers, PyQt developers, UI/UX contributors, documentation contributors, and open-source maintainers.

This repository is intended for biomedical research assistance, laboratory workflow support, education, and software development preview. It is not intended for clinical diagnosis, treatment decisions, patient management, regulated medical use, or automated experimental execution without human review.

## Ways to Contribute

You can contribute by:

- Reporting bugs
- Improving documentation
- Adding tests
- Reviewing formulas
- Adding reagent templates
- Adding example calculations
- Improving Chinese or English wording
- Suggesting laboratory workflow improvements
- Improving validation and warning messages
- Adding or improving laboratory calculators
- Testing the package with non-confidential example values

You do not need to be a professional software engineer to contribute. Non-code contributions are welcome.

## Current Contribution Areas

Useful contribution areas include:

- General calculators
- Concentration calculation
- Dilution calculation
- Solution preparation
- Reagent template models and examples
- Western Blot loading calculator
- Western Blot protein loading helpers
- BCA assay helper
- SDS-PAGE gel template helper
- qPCR mix calculator
- Cell seeding calculator
- Unit conversion utilities
- Formula documentation
- User guide and developer guide
- Tests and examples

## Development Setup

Clone the repository:

```bash
git clone https://github.com/lichangda94-sys/BioMedPilot-LabTools.git
cd BioMedPilot-LabTools
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run the package smoke test:

```bash
python -m labtools --smoke-test
```

## Pull Request Guidelines

Before submitting a pull request:

- Keep changes focused and scoped.
- Explain what changed and why.
- Add or update tests when possible.
- Include example calculations when changing formulas.
- Avoid mixing unrelated changes in one pull request.
- Do not include private data, patient data, credentials, or local machine paths.
- Do not make clinical diagnosis, treatment, or regulated medical-use claims.
- Keep formulas, units, assumptions, validation rules, and warnings reviewable.

## Calculator Contribution Guidelines

When adding or modifying a calculator, include:

- Clear purpose
- Input fields
- Output fields
- Formula or calculation logic
- Unit handling
- Validation rules
- Warning rules
- Example calculation
- Tests where possible
- Documentation where possible

Calculation logic should be independent from UI code.

Good structure:

```text
UI or command entry point
  -> calls calculation service
  -> returns structured result
```

Avoid putting core formula logic directly inside UI components.

## Formula Review

Formulas should be transparent and reviewable.

When adding a formula, document:

- Formula
- Variable meanings
- Units
- Assumptions
- Example calculation
- Known limitations
- Warning or invalid-input conditions

All formulas should be reviewed before laboratory use.

## Privacy and Safety Rules

Do not submit:

- Patient data
- Private laboratory records
- API keys
- Access tokens
- Passwords
- Local credentials
- Confidential protocols
- Commercial secrets
- Unpublished proprietary protocols
- Third-party copyrighted content without permission
- Private BioMedPilot commercial modules
- AI/payment/membership/license-server/private prompt code

Use only non-confidential example values.

## Contribution Terms

Contributions are voluntary.

By submitting an issue, pull request, code, documentation, design, test case, formula, template, example, or other contribution, you agree that your contribution will be licensed under the same license as this repository.

Submitting a contribution does not create an employment, contractor, partnership, compensation, equity, ownership, or revenue-sharing relationship with the project owner.

The project maintainer may use, modify, distribute, sublicense, and integrate accepted contributions into BioMedPilot and related editions, including free, commercial, AI-assisted, cloud-based, premium, or future versions.

## Non-Clinical Scope

BioMedPilot-LabTools is intended for:

- Biomedical research assistance
- Laboratory workflow support
- Education
- Software development preview

It is not intended for:

- Clinical diagnosis
- Treatment decisions
- Patient management
- Regulated medical use
- Automated experimental execution without human review
- Replacement of laboratory SOPs
- Replacement of institutional protocols
- Replacement of researcher judgment

Users are responsible for reviewing all formulas, units, results, warnings, and experimental conditions before use.
