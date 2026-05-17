# Security Policy

BioMedPilot-LabTools is an open-source laboratory tools package for biomedical research workflow assistance.

This repository should not contain sensitive data, private user data, patient data, credentials, API keys, local cache files, build artifacts, private BioMedPilot modules, or commercial-only logic.

## Reporting Security Issues

Please do not report security vulnerabilities through public GitHub issues.

If you find a security problem, please contact the maintainer privately.

When reporting a security issue, please include:

- A brief description of the issue
- Affected files or functions
- Steps to reproduce if safe to share
- Potential impact
- Suggested fix if available

Do not include patient data, credentials, secrets, private laboratory records, or confidential protocols.

## Sensitive Data Policy

Do not submit:

- Patient data
- Personal health information
- Private laboratory records
- API keys
- Access tokens
- Passwords
- Local credentials
- SSH keys
- `.env` files
- Local database files
- Private project storage
- Commercial secrets
- Confidential protocols
- Unpublished proprietary protocols
- Private BioMedPilot commercial modules
- AI/payment/membership/license-server/private prompt code

## Files and Directories That Should Not Be Committed

The following should not be committed:

```text
.venv/
__pycache__/
*.pyc
.env
*.key
*.pem
*.sqlite
*.db
project_storage/
dist/
build/
.git.private-history-backup/
LabTools-private-history-backup/
```

The public repository should focus on reusable LabTools package code, tests, examples, and documentation.

## Non-Clinical Scope

BioMedPilot-LabTools is intended for biomedical research assistance, laboratory workflow support, education, and software development preview.

It is not intended for:

- Clinical diagnosis
- Treatment decisions
- Patient management
- Regulated medical use
- Automated experimental execution without human review
- Replacement of laboratory SOPs or institutional protocols

## Maintainer Checklist Before Release

Before publishing or tagging a release, check:

```bash
git status
find . -name ".env" -o -name "*.key" -o -name "*.pem" -o -name "*.sqlite" -o -name "*.db"
grep -R "OPENAI_API_KEY\\|api_key\\|password\\|token\\|secret\\|project_storage\\|membership\\|payment\\|license_server" . --exclude-dir=.git --exclude-dir=.venv
pytest
python -m labtools --smoke-test
```

Review any matches carefully before release.
