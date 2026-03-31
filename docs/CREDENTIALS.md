# Credential Setup

Clint requires user-owned credentials.

## Required

1. OPENROUTER_API_KEY
2. SMTP_USER_1
3. SMTP_PASS_1 (Gmail App Password)

## Optional

1. SENDER_NAME
2. SENDER_TITLE
3. FROM_EMAIL

## Setup Command

```bash
clint init
```

## Validate

```bash
clint config doctor
```

## Security Guidance

1. Never commit .env.
2. Never share SMTP app passwords.
3. Rotate credentials after suspected leak.
