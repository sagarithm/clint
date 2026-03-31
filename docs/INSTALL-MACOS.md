# Install on macOS

## Prerequisites

1. Python 3.10+
2. pip

## Install

```bash
python3 -m pip install --upgrade pip
python3 -m pip install sagarithm-clint
playwright install chromium
```

## Verify

```bash
clint --help
clint version
```

## Optional (isolated global install)

```bash
python3 -m pip install pipx
python3 -m pipx ensurepath
pipx install sagarithm-clint
```
