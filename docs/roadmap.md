# BioMedPilot-LabTools Roadmap

This roadmap describes the planned development direction of BioMedPilot-LabTools.

BioMedPilot-LabTools is currently in Developer Preview. The roadmap may change as the package matures and as contributors provide feedback.

## Current Package Status

The repository has been converted into a standalone public Python package rooted at `labtools`.

Current validation:

```bash
pytest
python -m labtools --smoke-test
```

Current public package areas include:

- General calculators
- Concentration calculation
- Dilution calculation
- Solution preparation
- Calculation records
- Reagent template models / calculator / store
- Western Blot loading calculator
- Western Blot protein loading helpers
- BCA assay helper
- SDS-PAGE gel template helper
- qPCR mix calculator
- Cell seeding calculator
- Unit conversion helpers
- Package smoke test

## Project Goals

BioMedPilot-LabTools aims to provide open, local-first, testable laboratory tools for biomedical research workflows.

The project focuses on:

- Laboratory calculators
- Reagent template management
- Reagent preparation workflows
- Western Blot calculation helpers
- PCR / qPCR calculation tools
- ELISA / absorbance tools
- Cell experiment utilities
- Formula documentation
- Human-review-based scientific assistance

The project is not intended for clinical diagnosis, treatment decisions, regulated medical use, or automated experimental execution without human review.

## Phase 1: Public Package Stabilization

Status: In progress

Goals:

- Keep the public package clean and independently testable
- Keep private BioMedPilot shell code out of this repository
- Maintain package smoke test
- Maintain test suite
- Improve README and documentation
- Add contribution and security documentation
- Add issue and pull request templates

Validation target:

```bash
pytest
python -m labtools --smoke-test
```

## Phase 2: Documentation Recovery and Improvement

Status: In progress

Goals:

- Restore Chinese README
- Restore contribution guide
- Restore security policy
- Add roadmap
- Add good-first-issues guide
- Add developer guide
- Add calculator specification
- Add formula reference
- Add user guide

Planned documents:

- `README_zh.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `docs/roadmap.md`
- `docs/good_first_issues.md`
- `docs/developer_guide.md`
- `docs/calculator_spec.md`
- `docs/formula_reference.md`
- `docs/user_guide.md`

## Phase 3: Reagent Templates

Status: Planned

Goals:

- Improve reagent template examples
- Add common buffer templates
- Add scaling examples
- Add pH record examples
- Add solvent/top-up examples
- Add addition order and preparation-stage examples

Candidate templates:

- PBS
- TBS
- TBST
- RIPA lysis buffer
- SDS-PAGE running buffer
- Transfer buffer
- Blocking buffer
- BCA working reagent

## Phase 4: Western Blot Tools

Status: Partially implemented

Goals:

- Improve Western Blot loading calculator documentation
- Add example workflows
- Add more tests if needed
- Improve protein loading helper documentation
- Improve BCA assay helper documentation
- Improve SDS-PAGE gel template helper documentation

Target contribution areas:

- User guide
- Formula explanation
- Example calculations
- Validation and warning rules
- Non-confidential example data

## Phase 5: PCR / qPCR Tools

Status: Partially implemented

Goals:

- Improve qPCR mix calculator
- Add primer dilution examples
- Add master mix examples
- Add tests and documentation
- Add reaction-count and extra-volume examples

Potential future features:

- Primer dilution calculator
- qPCR reaction setup helper
- Master mix calculator
- Plate setup helper
- Standard curve helper

## Phase 6: ELISA / Absorbance Tools

Status: Planned / early package structure available

Goals:

- Add ELISA standard curve helper
- Add absorbance interpolation logic
- Add dilution factor correction
- Add out-of-range warnings
- Add tests and examples

Initial approach:

- Start with transparent linear standard curve logic
- Discuss 4PL fitting separately
- Keep curve assumptions visible and documented

## Phase 7: Cell Experiment Tools

Status: Partially implemented

Goals:

- Improve cell seeding calculator
- Add plate format examples
- Add drug dilution helper
- Add transfection helper
- Add tests and documentation

Target contribution areas:

- Example workflows
- Plate format presets
- Validation warnings
- Unit tests

## Phase 8: Public API and Integration

Status: Planned

Goals:

- Clarify public import paths
- Improve package-level API documentation
- Keep calculation logic independent from UI
- Support integration into BioMedPilot
- Support standalone package use

Design principles:

- Calculation logic should be testable without UI
- UI should call calculation services
- UI should not contain core formula logic
- BioMedPilot integration should remain modular

## Contribution Priorities

Good first contributions:

- Add reagent template examples
- Add example calculations
- Add documentation
- Improve Chinese or English wording
- Add formula explanations
- Add tests for edge cases
- Add validation and warning examples

Help wanted:

- qPCR primer dilution calculator
- ELISA standard curve calculator
- Cell seeding examples
- SDS-PAGE gel preparation documentation
- BCA protein assay documentation
- PyQt UI examples if kept optional and separate
- User workflow feedback

## Non-Goals

The following are not goals of this public repository:

- Clinical diagnosis
- Treatment recommendations
- Patient management
- Regulated medical decision-making
- Automatic experimental execution without human review
- Automatic ROI recognition
- Automatic Western Blot band detection
- Automatic cell counting
- Production-grade image analysis algorithms
- Membership system
- Payment system
- License server
- Cloud AI service
- Private prompt libraries
- Private BioMedPilot commercial modules

## Relationship with BioMedPilot

BioMedPilot-LabTools is maintained as an open-source laboratory tools module related to BioMedPilot / 医研智析.

Accepted contributions may be integrated into BioMedPilot and related editions, including free, commercial, AI-assisted, premium, or future versions.

The open-source module is intended to remain useful as a standalone laboratory research toolkit while also supporting integration into the broader BioMedPilot ecosystem.

## Suggested Issue Labels

- `good first issue`
- `help wanted`
- `documentation`
- `calculator`
- `reagent-template`
- `western-blot`
- `pcr-qpcr`
- `elisa`
- `cell-culture`
- `ui-ux`
- `testing`
- `research-feedback`

## Notes

This roadmap is a planning document. It does not guarantee that all listed features will be implemented.

All calculations, formulas, and experimental workflows should be reviewed by users before laboratory use.
