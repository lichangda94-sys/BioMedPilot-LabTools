# Good First Issues

This page lists beginner-friendly contribution ideas for BioMedPilot-LabTools.

You do not need to be a professional software engineer to contribute. Biomedical researchers, PhD students, clinicians, laboratory users, documentation contributors, and developers are welcome.

Please do not submit patient data, private laboratory records, confidential protocols, API keys, credentials, or third-party copyrighted content that you do not have permission to share.

## How to Start

1. Choose one issue or task from the list below.
2. Read the current package code and tests if relevant.
3. Leave a comment if you want to work on a GitHub issue.
4. Fork the repository.
5. Make a focused change.
6. Add or update tests where possible.
7. Submit a pull request.

If you are not ready to submit code, you can still contribute by improving issue discussions, checking formulas, suggesting examples, or improving documentation.

## Beginner-Friendly Contribution Areas

## 1. Improve Documentation

Good tasks:

- Improve README wording
- Improve README_zh wording
- Add missing examples
- Add formula explanations
- Add screenshots or diagrams when UI becomes available
- Improve user-facing warnings and disclaimers

Expected contribution type:

- Documentation
- Wording review
- Example workflow
- Non-code contribution

## 2. Add Reagent Template Examples

Goal:

Add clear reagent template examples to demonstrate structure, scaling, pH records, solvent/top-up handling, and preparation-stage logic.

Candidate templates:

- PBS
- TBS
- TBST
- RIPA lysis buffer
- Transfer buffer
- Blocking buffer
- BCA working reagent

Expected contribution types:

- Example template
- Documentation
- Unit test
- Formula explanation
- Safety and review notes

Important note:

Recipes can vary between laboratories. Examples should be presented as reviewable templates, not universal SOPs.

## 3. qPCR Primer Dilution Calculator

Goal:

Add or improve a calculator for preparing primer working solutions from concentrated primer stocks.

Expected contribution types:

- Calculation logic
- Unit tests
- Example calculation
- Documentation
- UI wording suggestion

Example formula:

```text
C1 x V1 = C2 x V2

Stock volume = target concentration x final volume / stock concentration
Diluent volume = final volume - stock volume
```

## 4. ELISA Standard Curve Calculator

Goal:

Add a calculator for estimating sample concentrations from ELISA standard curve absorbance values.

Expected contribution types:

- Linear standard curve logic
- Unit tests
- Example data
- Documentation
- Warning rules for out-of-range samples

Initial implementation can start with simple linear regression. More advanced 4PL fitting can be discussed later.

## 5. Cell Seeding Examples

Goal:

Improve cell seeding calculator examples and documentation.

Expected contribution types:

- Example calculations
- Plate format examples
- Unit tests
- Documentation
- Validation rules

Example logic:

```text
Total cells required = target cells per well x number of wells
Cell suspension volume = total cells required / current cell concentration
Medium volume = total preparation volume - cell suspension volume
```

## 6. SDS-PAGE Gel Preparation Documentation

Goal:

Improve documentation and examples for SDS-PAGE resolving gel and stacking gel preparation helpers.

Expected contribution types:

- Recipe preset documentation
- Calculation explanation
- Unit tests
- Safety warning text
- Example workflows

Important note:

Acrylamide handling requires appropriate laboratory safety procedures. The tool should provide calculation assistance only and should not replace institutional SOPs.

## 7. BCA Protein Assay Documentation

Goal:

Improve BCA working reagent and protein assay documentation.

Expected contribution types:

- Example assay setup
- Formula explanation
- Test examples
- Documentation
- Warning messages

Example reagent logic:

```text
Reagent A : Reagent B = 50 : 1
Reagent A volume = total working reagent volume x 50 / 51
Reagent B volume = total working reagent volume x 1 / 51
```

## 8. Western Blot Loading Calculator User Guide

Goal:

Add or improve a user guide explaining how to use the Western Blot loading calculator.

Expected contribution types:

- Documentation
- Example calculation
- Field explanation
- Warning explanation
- Workflow review notes

Suggested sections:

- Purpose
- Required inputs
- Output interpretation
- 4X / 5X loading buffer logic
- Reducing agent options
- Lane layout
- Low-volume warnings
- Example calculation

## Non-Code Contributions

You can contribute without writing code.

Useful non-code contributions include:

- Checking formulas
- Suggesting laboratory workflow improvements
- Improving Chinese wording
- Improving English wording
- Adding examples
- Reviewing documentation
- Reporting confusing concepts
- Suggesting missing calculators
- Testing with non-confidential example values

## Privacy and Scope Reminder

Do not submit:

- Patient data
- Private laboratory records
- Confidential protocols
- API keys
- Access tokens
- Passwords
- Commercial secrets
- Third-party copyrighted content without permission

BioMedPilot-LabTools is for biomedical research assistance, laboratory workflow support, education, and software development preview. It is not for clinical diagnosis, treatment decisions, regulated medical use, or automated experimental execution without human review.

## Contribution Terms

Contributions are voluntary.

By submitting an issue, pull request, code, documentation, design, test case, formula, template, example, or other contribution, you agree that your contribution will be licensed under the same license as this repository.

Submitting a contribution does not create an employment, contractor, partnership, compensation, equity, ownership, or revenue-sharing relationship with the project owner.

Accepted contributions may be integrated into BioMedPilot and related editions, including free, commercial, AI-assisted, cloud-based, premium, or future versions.
