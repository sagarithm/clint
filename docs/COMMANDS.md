# Clint Commands Reference

This guide covers every command available in the Clint CLI, including the new scoring overrides and common workflow scenarios.

## 🚀 Quick Start (Common Workflows)

### Situation A: "I want Clint to handle everything (Autonomous)"
Finds leads, audits their websites, generates AI pitches, and sends them one by one.
```bash
clint run --query "Dentists in California" --target 20 --live
```

### Situation B: "I want to send to low-score leads too"
By default, Clint skips leads with a score below 5. Use `--min-score` to lower the bar.
```bash
clint run --query "Roofers in Austin" --min-score 1 --live
```

### Situation C: "I want to find leads now, but send later"
Scrapes leads and saves them to the database without starting outreach.
```bash
clint scrape --query "HVAC in Miami" --target 50
```

### Situation D: "I want to follow up with people from 3 days ago"
Finds leads who haven't replied and were contacted at least 3 days ago.
```bash
clint followup --days-since-last 3 --channel email
```

---

## 🛠️ Complete Command List

### `clint version`
Show installed version and runtime environment.
```bash
clint version
clint version --verbose
```

### `clint init`
Interactive setup for API keys and SMTP credentials.
```bash
clint init
# Non-interactive (CI/CD)
clint init --non-interactive --openrouter-key <KEY> --smtp-user <EMAIL> --smtp-pass <PASS>
```

### `clint config`
Manage individual configuration settings.
```bash
clint config show             # Show current settings (masked)
clint config show --secrets   # Show plain-text secrets
clint config set <KEY> <VAL>  # Set a specific key (e.g. SENDER_NAME)
clint config doctor           # Run health checks (SMTP, AI, Browser)
```

### `clint run`
The primary autonomous outreach engine.
- `--query`: Search niche (e.g. "Dentists in Dallas").
- `--target`: Number of leads to find (default 50).
- `--send-limit`: Max emails to send in this batch (default 20).
- `--min-score`: Minimum lead score (1-10) to trigger outreach (default 5).
- `--live`: Switch from dry-run to actual delivery.
```bash
clint run --query "Lawyers in NY" --target 10 --min-score 3 --live
```

### `clint scrape`
Manual lead discovery.
- `--target`: Number of leads to collect.
- `--outreach`: If passed, immediately enters interactive outreach review for the found leads.
```bash
clint scrape --query "Gyms in LA" --target 25 --outreach
```

### `clint followup`
Sequence management for passive leads.
- `--days-since-last`: Minimum days since last contact (default 3).
- `--channel`: Filter by `email` or `whatsapp`.
```bash
clint followup --days-since-last 5
```

### `clint export`
Export your database to CSV for CRM import.
- `--table`: Choose `leads`, `outreach_history`, or `all`.
- `--out-dir`: Where to save the files (default `data/exports`).
```bash
clint export --table leads --out-dir ./backups
```

### `clint upgrade`
Update Clint CLI to the latest version automatically from PyPI.
```bash
clint upgrade
```

### `clint dashboard`
Launch the high-end web interface.
```bash
clint dashboard --host 127.0.0.1 --port 8000 --reload
```

### `clint worker-reddit`
Run the staged Reddit worker pipeline with safe dry-run defaults.
- `--query`: Intent keyword for source discovery.
- `--limit`: Max records to process in this run (default 20).
- `--dry-run/--live`: Dry-run by default; use `--live` for real sends.
```bash
clint worker-reddit --query "dentist website redesign" --limit 20
clint worker-reddit --query "roofing leads" --limit 10 --live
```

### `clint experiments-decide`
Apply auto-decision policy to an experiment.
- `--experiment-id`: Required experiment identifier.
- `--min-sample`: Minimum sample size per variant (default 30).
- `--min-uplift-pct`: Minimum uplift required to promote (default 5.0).
- `--max-negative-quality-impact`: Maximum allowed quality degradation (default -5.0).
```bash
clint experiments-decide --experiment-id 3
clint experiments-decide --experiment-id 3 --min-sample 50 --min-uplift-pct 8
```

### `clint deadletter-list`
List deadletter records for operational triage.
- `--status`: Optional replay status filter.
- `--limit`: Maximum rows to return (default 25).
```bash
clint deadletter-list
clint deadletter-list --status pending --limit 100
```

### `clint deadletter-replay`
Replay a deadletter record through the supported recovery path.
- `--event-id`: Required deadletter event ID.
```bash
clint deadletter-replay --event-id 42
```

---

## 🚦 Exit Codes
Use these to debug script failures:
- `0`: Success
- `2`: Usage Error (Missing flags/args)
- `3`: Config Error (Missing API keys/SMTP)
- `4`: Runtime Error (Database/Filesystem)
- `5`: Network Error (Timeout/Auth Fail)
- `10`: Internal Error (Crash)

## 💡 Pro Tips
1. **Always run a dry-run first**: The default behavior of `clint run` is dry-run. It shows you what *would* happen without sending anything.
2. **Interactive Review**: Simply typing `clint` (with no arguments) opens the **Command Center**, where you can manually review leads and edit AI proposals before they go out.
