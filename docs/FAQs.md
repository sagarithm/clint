# FAQs

## Which command should users run to install?

Use:

```bash
pip install sagarithm-clint
```

Then run:

```bash
clint --help
```

## What if clint command is not found?

Run:

```bash
python -m clint_cli --help
```

Then add Python Scripts folder to PATH.

## Is there a hosted backend for credentials?

No. Users provide and manage their own credentials.

## Does Clint enforce hard daily send caps?

No hard caps are enforced by default. It provides safety-oriented recommendations.

## Why is my PyPI package page 404?

Usually because only TestPyPI release exists. Publish stable tag and verify publish-pypi job success.
