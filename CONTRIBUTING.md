# Contributing to Clint

Thanks for contributing to Clint.

## Development Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
pip install -e .
playwright install chromium
```

## Local Validation

Run before opening a PR:

```bash
python -m build
python clint_cli.py --help
python clint_cli.py config doctor
```

If you add tests, run:

```bash
pytest
```

## Coding Guidelines

1. Keep changes small and focused.
2. Preserve existing command behavior unless intentionally changing contract.
3. Avoid logging secrets.
4. Add or update docs when changing CLI flags or workflows.

## Pull Request Checklist

1. Explain what changed and why.
2. Link related issue.
3. Include manual test steps and outcomes.
4. Confirm no secrets are committed.
5. Confirm docs are updated for user-visible changes.

## Commit Message Style

Use clear, scoped commit messages, for example:

- `feat(cli): add config doctor checks`
- `fix(outreach): prevent duplicate sends`
- `docs(readme): update quickstart commands`
