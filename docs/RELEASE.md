# Clint Release Guide

## Prerequisites

1. CI must be green on v1.
2. Trusted Publisher configured on TestPyPI and PyPI.
3. GitHub environments configured: testpypi and pypi.

## Prerelease

```bash
git checkout v1
git pull origin v1
git tag v1.0.0rcN
git push origin v1.0.0rcN
```

Expected workflow jobs:

1. build
2. publish-testpypi
3. github-release

## Stable Release

```bash
git checkout v1
git pull origin v1
git tag v1.0.0
git push origin v1.0.0
```

Expected workflow jobs:

1. build
2. publish-pypi
3. github-release

## Post-release Validation

1. Check package page on PyPI.
2. Install package from PyPI.
3. Run `clint --help` and `clint version`.

