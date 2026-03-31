# Clint Quickstart (10 Minutes)

## 1. Install

```bash
pip install sagarithm-clint
playwright install chromium
```

## 2. Configure

```bash
clint init
```

Provide:

- OPENROUTER_API_KEY
- SMTP_USER_1
- SMTP_PASS_1
- sender identity fields

## 3. Verify Setup

```bash
clint config doctor
```

## 4. First Safe Run (Dry Run)

```bash
clint run --query "Dentists in California"
```

## 5. Live Run

```bash
clint run --query "Dentists in California" --live
```

## 6. Dashboard (Optional)

```bash
clint dashboard --host 127.0.0.1 --port 8000
```
