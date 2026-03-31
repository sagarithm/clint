import asyncio
import os
from pathlib import Path
from typing import Dict, Optional

import httpx
from dotenv import dotenv_values

ENV_FILE = Path(".env")
SECRET_KEYS = {"OPENROUTER_API_KEY", "SMTP_PASS_1"}
ALLOWED_CONFIG_KEYS = {
    "OPENROUTER_API_KEY",
    "SMTP_USER_1",
    "SMTP_PASS_1",
    "SMTP_HOST_1",
    "SMTP_PORT_1",
    "SENDER_NAME",
    "SENDER_TITLE",
    "FROM_EMAIL",
    "AI_MODEL",
    "DB_PATH",
    "MIN_DELAY_SECONDS",
    "MAX_DELAY_SECONDS",
}


def mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def read_env() -> Dict[str, str]:
    values = dotenv_values(ENV_FILE)
    return {k: str(v) for k, v in values.items() if v is not None}


def write_env(values: Dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in sorted(values.items())]
    temp_path = ENV_FILE.with_suffix(".env.tmp")
    temp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temp_path.replace(ENV_FILE)


async def doctor_openrouter(key: str) -> tuple[str, str]:
    if not key:
        return "FAIL", "OPENROUTER_API_KEY missing"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {key}"},
            )
        if resp.status_code == 200:
            return "PASS", "OpenRouter credentials valid"
        if resp.status_code in (401, 403):
            return "FAIL", "OpenRouter credentials invalid"
        return "WARN", f"OpenRouter check returned HTTP {resp.status_code}"
    except Exception as exc:
        return "WARN", f"OpenRouter check failed: {exc}"


async def doctor_smtp(user: str, password: str, host: str, port: int) -> tuple[str, str]:
    if not user or not password:
        return "FAIL", "SMTP_USER_1/SMTP_PASS_1 missing"
    try:
        import aiosmtplib

        async with aiosmtplib.SMTP(hostname=host, port=port, use_tls=False, start_tls=True, timeout=15) as smtp:
            await smtp.login(user, password)
        return "PASS", "SMTP authentication successful"
    except Exception as exc:
        return "FAIL", f"SMTP auth failed: {exc}"


def doctor_playwright() -> tuple[str, str]:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            path = pw.chromium.executable_path
        if path and os.path.exists(path):
            return "PASS", "Playwright chromium available"
        return "FAIL", "Playwright installed but chromium not found"
    except Exception as exc:
        return "FAIL", f"Playwright unavailable: {exc}"


def doctor_paths(db_path: str) -> tuple[str, str]:
    try:
        data_dir = Path("data")
        logs_dir = Path("logs")
        db_parent = Path(db_path).parent if Path(db_path).parent != Path("") else Path(".")
        for p in [data_dir, logs_dir, db_parent]:
            p.mkdir(parents=True, exist_ok=True)
        test_file = logs_dir / ".clint_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return "PASS", "Data/log paths writable"
    except Exception as exc:
        return "FAIL", f"Path write check failed: {exc}"


def run_doctor_checks(values: Dict[str, str]) -> list[tuple[str, tuple[str, str]]]:
    host = values.get("SMTP_HOST_1", "smtp.gmail.com")
    port = int(values.get("SMTP_PORT_1", "587"))
    db_path = values.get("DB_PATH", "data/clint.db")

    return [
        ("OpenRouter", asyncio.run(doctor_openrouter(values.get("OPENROUTER_API_KEY", "")))),
        (
            "SMTP",
            asyncio.run(
                doctor_smtp(
                    values.get("SMTP_USER_1", ""),
                    values.get("SMTP_PASS_1", ""),
                    host,
                    port,
                )
            ),
        ),
        ("Playwright", doctor_playwright()),
        ("Paths", doctor_paths(db_path)),
    ]
