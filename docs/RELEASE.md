# Clint Release Guide

This guide defines the release process for the production branch.

## Branch and Version Strategy

- Production branch: `main`
- Version format: `vX.Y.Z` (semantic version tags)
- Current release line: `v1.0.2`

## Prerequisites

1. Local `main` is up to date.
2. CI is green.
3. Tests pass locally.
4. PyPI credentials or Trusted Publisher are configured.

## Pre-Release Checklist

```bash
git checkout main
git pull origin main
pytest -q
clint config doctor
```

## Create a Stable Release

1. Update version in `pyproject.toml`.
2. Update any release notes in docs.
3. Commit release changes.
4. Tag the commit.
5. Push main and tags.

```bash
git checkout main
git pull origin main
git add .
git commit -m "release: vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

## Publish Package (if manual)

```bash
python -m build
python -m twine upload dist/*
```

## Post-Release Validation

1. Verify tag exists on GitHub.
2. Verify package appears on PyPI.
3. Install and smoke test:

```bash
pip install -U sagarithm-clint
clint --help
clint version
python -c "from clint import Engine; print('ok')"
```

## Rollback Guidance

1. Stop new deployment rollout.
2. Revert offending commit on `main`.
3. Cut a follow-up patch release (`vX.Y.Z+1`) with fix.
4. Do not delete published PyPI versions; publish corrected patch.
