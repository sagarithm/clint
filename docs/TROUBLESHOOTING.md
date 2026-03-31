# Clint Troubleshooting

## 1. clint config doctor returns FAIL for OpenRouter

Symptoms:
- OpenRouter check FAIL
- Errors mentioning invalid credentials or unauthorized

Fix:
1. Run `clint init` and re-enter `OPENROUTER_API_KEY`.
2. Verify key is active on OpenRouter.
3. Retry `clint config doctor`.

## 2. SMTP auth failed

Symptoms:
- `SMTP auth failed` in doctor output or send logs

Fix:
1. Ensure Gmail 2FA is enabled.
2. Use Gmail App Password, not account password.
3. Re-run `clint init` with `SMTP_USER_1` and `SMTP_PASS_1`.
4. Retry `clint config doctor`.

## 3. Playwright unavailable or chromium not found

Symptoms:
- Doctor reports Playwright/Chromium missing

Fix:
1. Run `playwright install chromium`.
2. Re-run `clint config doctor`.

## 4. Database or logs path not writable

Symptoms:
- Doctor reports path write check failed

Fix:
1. Ensure current folder is writable.
2. Verify `DB_PATH` parent folder exists or can be created.
3. On Windows, run terminal as a user with write permissions.

## 5. clint run --live exits with config error

Symptoms:
- Message about missing credentials for live mode

Fix:
1. Run `clint init`.
2. Confirm required keys exist using `clint config show`.

## 6. Follow-up queue is empty

Symptoms:
- No records found in follow-up queue

Fix:
1. Ensure leads were previously sent.
2. Increase window: `clint followup --days-since-last 1`.
3. Confirm lead statuses in exports: `clint export --table leads`.

## 7. Common Exit Codes

- `2`: usage/validation problem
- `3`: missing/invalid local config
- `4`: runtime readiness/path/dependency problem
- `5`: network/auth transport failure
- `10`: unexpected internal error
