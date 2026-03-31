# Clint Privacy and Data Handling

Clint is a local-first CLI. By default, your campaign data is stored in local project files.

## What Clint Stores Locally

1. Database:
- Default path: `data/clint.db`
- Contains leads, outreach history, and stats

2. Logs:
- Path: `logs/outreach.log`
- Contains operational logs with secret redaction safeguards

3. Session data:
- WhatsApp session profile under `data/whatsapp_session`

4. Exports:
- CSV exports under `data/exports`

## Credentials

- Credentials are user-supplied and stored locally in `.env`.
- Secrets should never be committed to Git.
- `clint config show` masks secrets by default.

## Data Retention Recommendations

1. Periodically archive or purge old campaign data from `data/clint.db`.
2. Remove stale CSV exports and screenshots when no longer needed.
3. Rotate credentials if you suspect accidental exposure.

## Sharing Logs and Reports

Before sharing logs externally:
1. Review content for sensitive business information.
2. Keep recipient data minimized.
3. Avoid sharing raw database files unless necessary.

## Responsibility

Operators are responsible for lawful data handling, recipient consent, and compliance with local regulations and platform policies.
