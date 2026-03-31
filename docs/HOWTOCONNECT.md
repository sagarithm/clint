# How to Connect Clint

This guide explains how to connect Clint to your required services.

## 1. OpenRouter

1. Generate API key from OpenRouter.
2. Run `clint init` and paste key when prompted.

## 2. Gmail SMTP

1. Enable 2FA on Gmail.
2. Create Gmail App Password.
3. Run `clint init` and enter SMTP_USER_1 and SMTP_PASS_1.

## 3. Browser Automation

Install Chromium runtime for Playwright:

```bash
playwright install chromium
```

## 4. Verify Full Connectivity

```bash
clint config doctor
```
