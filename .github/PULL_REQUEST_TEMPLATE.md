# Pull Request

## Summary

Describe what changed and why.

## Type of change

- [ ] Documentation
- [ ] Test
- [ ] Calculator logic
- [ ] Reagent template
- [ ] Formula review
- [ ] Packaging or project metadata
- [ ] Other

## Scope checklist

- [ ] This change is scoped to the public BioMedPilot-LabTools repository.
- [ ] This change does not include patient data, private laboratory records, credentials, API keys, tokens, secrets, or local machine paths.
- [ ] This change does not include private BioMedPilot commercial modules, payment, membership, license-server, private prompt, or cloud-service code.
- [ ] This change does not add build artifacts, local cache, `.venv/`, `__pycache__/`, `*.pyc`, `project_storage/`, `dist/`, or `build/`.
- [ ] This change does not make clinical diagnosis, treatment decision, patient management, or regulated medical-use claims.

## Calculator or formula changes

If this pull request changes calculator behavior, complete this section:

- Formula:
- Variables and units:
- Assumptions:
- Validation rules:
- Warning rules:
- Example calculation:
- Known limitations:

## Tests

Run the relevant checks and paste the result:

```bash
pytest
python -m labtools --smoke-test
```

## Human review and safety

- [ ] I understand that LabTools outputs require human review before laboratory use.
- [ ] I documented formulas, assumptions, or safety boundaries where relevant.

## Additional notes

Add context for reviewers, open questions, or follow-up tasks.
