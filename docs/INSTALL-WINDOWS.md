# Install on Windows

## Prerequisites

1. Python 3.10+
2. Git (optional, for source installs)

## Recommended Install

```powershell
python -m pip install --upgrade pip
python -m pip install sagarithm-clint
playwright install chromium
```

## Verify

```powershell
clint --help
clint version
```

## If clint is not recognized

Use module invocation:

```powershell
python -m clint_cli --help
```

Or add Python Scripts path to PATH, usually:

- C:\Users\<username>\AppData\Roaming\Python\Python3xx\Scripts
