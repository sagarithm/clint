import asyncio
import csv
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from commander import ColdMailerCLI
from core.cli_services import (
    ALLOWED_CONFIG_KEYS,
    SECRET_KEYS,
    mask,
    read_env,
    run_doctor_checks,
    write_env,
)
from core.database import get_db, init_db
from engine.director import OutreachDirector

console = Console()
app = typer.Typer(help="Clint CLI", add_completion=False, no_args_is_help=False)
config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_CONFIG = 3
EXIT_RUNTIME = 4
EXIT_NETWORK = 5
EXIT_INTERNAL = 10

def _require_tty_or_value(value: Optional[str], prompt_text: str, hide: bool = False) -> str:
    if value:
        return value
    if not sys.stdin.isatty():
        raise typer.Exit(code=EXIT_USAGE)
    return typer.prompt(prompt_text, hide_input=hide).strip()


async def _run_interactive() -> None:
    await init_db()
    cli = ColdMailerCLI()
    await cli.run()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        try:
            asyncio.run(_run_interactive())
        except KeyboardInterrupt:
            console.print("\nExiting Clint...")


@app.command("version")
def version_cmd(verbose: bool = typer.Option(False, "--verbose", help="Show runtime details")) -> None:
    try:
        cli_ver = version("clint-cli")
    except PackageNotFoundError:
        cli_ver = "0.0.0-dev"

    console.print(f"clint {cli_ver}")
    if verbose:
        console.print(f"python {sys.version.split()[0]}")
        console.print(f"platform {sys.platform}")


@app.command("init")
def init_cmd(
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Disable prompts"),
    openrouter_key: Optional[str] = typer.Option(None, "--openrouter-key"),
    smtp_user: Optional[str] = typer.Option(None, "--smtp-user"),
    smtp_pass: Optional[str] = typer.Option(None, "--smtp-pass"),
    sender_name: Optional[str] = typer.Option(None, "--sender-name"),
    sender_title: Optional[str] = typer.Option(None, "--sender-title"),
) -> None:
    current = read_env()

    if non_interactive:
        missing = [
            key
            for key, value in {
                "OPENROUTER_API_KEY": openrouter_key,
                "SMTP_USER_1": smtp_user,
                "SMTP_PASS_1": smtp_pass,
            }.items()
            if not value and not current.get(key)
        ]
        if missing:
            console.print(f"Missing required options in non-interactive mode: {', '.join(missing)}")
            raise typer.Exit(code=EXIT_USAGE)

    try:
        values = {
            "OPENROUTER_API_KEY": _require_tty_or_value(openrouter_key, "OpenRouter API key") if not non_interactive or openrouter_key else current.get("OPENROUTER_API_KEY", ""),
            "SMTP_USER_1": _require_tty_or_value(smtp_user, "SMTP user (gmail)") if not non_interactive or smtp_user else current.get("SMTP_USER_1", ""),
            "SMTP_PASS_1": _require_tty_or_value(smtp_pass, "SMTP app password", hide=True) if not non_interactive or smtp_pass else current.get("SMTP_PASS_1", ""),
            "SENDER_NAME": sender_name or current.get("SENDER_NAME") or (typer.prompt("Sender name") if not non_interactive and sys.stdin.isatty() else ""),
            "SENDER_TITLE": sender_title or current.get("SENDER_TITLE") or (typer.prompt("Sender title") if not non_interactive and sys.stdin.isatty() else ""),
        }
    except typer.Exit:
        console.print("Missing required input. Re-run with required flags or enable interactive mode.")
        raise

    current.update({k: v for k, v in values.items() if v})
    write_env(current)

    console.print("Saved configuration to .env")
    console.print(f"OPENROUTER_API_KEY={mask(current.get('OPENROUTER_API_KEY', ''))}")
    console.print(f"SMTP_USER_1={current.get('SMTP_USER_1', '')}")
    console.print(f"SMTP_PASS_1={mask(current.get('SMTP_PASS_1', ''))}")


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    if key not in ALLOWED_CONFIG_KEYS:
        console.print(f"Unknown config key: {key}")
        raise typer.Exit(code=EXIT_USAGE)

    values = read_env()
    values[key] = value.strip()
    write_env(values)

    out_value = mask(value) if key in SECRET_KEYS else value
    console.print(f"Set {key}={out_value}")


@config_app.command("show")
def config_show(
    as_json: bool = typer.Option(False, "--json", help="Output JSON"),
    show_secrets: bool = typer.Option(False, "--show-secrets", help="Show secrets in plain text"),
) -> None:
    values = read_env()
    rendered = {}
    for key, value in values.items():
        if key in SECRET_KEYS and not show_secrets:
            rendered[key] = mask(value)
        else:
            rendered[key] = value

    if as_json:
        import json

        console.print(json.dumps(rendered, indent=2))
        return

    table = Table(title="Clint Config")
    table.add_column("Key")
    table.add_column("Value")
    for key in sorted(rendered.keys()):
        table.add_row(key, rendered[key])
    console.print(table)


@config_app.command("doctor")
def config_doctor() -> None:
    checks = run_doctor_checks(read_env())

    table = Table(title="Clint Doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Details")

    failures = 0
    for name, (status, detail) in checks:
        if status == "FAIL":
            failures += 1
        table.add_row(name, status, detail)

    console.print(table)
    if failures:
        raise typer.Exit(code=EXIT_RUNTIME)


@app.command("run")
def run_cmd(
    query: Optional[str] = typer.Option(None, "--query"),
    target: int = typer.Option(50, "--target"),
    send_limit: int = typer.Option(20, "--send-limit"),
    dry_run: bool = typer.Option(True, "--dry-run/--live"),
) -> None:
    query_val = query or typer.prompt("Target niche query")

    console.print("Recommendation: keep outreach around 200 emails/day and 200 WhatsApp/day for better deliverability.")
    if dry_run:
        console.print(f"Dry run preview: query='{query_val}', target={target}, send_limit={send_limit}")
        return

    async def _run_live() -> None:
        await init_db()
        director = OutreachDirector()
        await director.execute_autonomous_batch(query_val, target_count=target, send_limit=send_limit)

    try:
        asyncio.run(_run_live())
    except Exception as exc:
        console.print(f"Run failed: {exc}")
        raise typer.Exit(code=EXIT_INTERNAL)


@app.command("scrape")
def scrape_cmd(
    query: Optional[str] = typer.Option(None, "--query"),
    target: int = typer.Option(10, "--target"),
    outreach: bool = typer.Option(False, "--outreach"),
) -> None:
    query_val = query or typer.prompt("Search query")

    async def _scrape() -> None:
        await init_db()
        cli = ColdMailerCLI()
        await cli.director.maps_scraper.scrape(query_val, max_results=target)
        if outreach:
            await cli._display_and_outreach(f"Discovery: {query_val}")
        else:
            async with get_db() as db:
                async with db.execute("SELECT COUNT(*) FROM leads WHERE status='new'") as cursor:
                    count = (await cursor.fetchone())[0]
            console.print(f"Discovery complete. Pending leads in queue: {count}")

    try:
        asyncio.run(_scrape())
    except Exception as exc:
        console.print(f"Scrape failed: {exc}")
        raise typer.Exit(code=EXIT_INTERNAL)


@app.command("followup")
def followup_cmd(
    days_since_last: int = typer.Option(3, "--days-since-last"),
    channel: Optional[str] = typer.Option(None, "--channel", help="email or whatsapp"),
) -> None:
    channel_value = channel.lower() if channel else None
    if channel_value and channel_value not in {"email", "whatsapp"}:
        console.print("Invalid --channel. Use email or whatsapp.")
        raise typer.Exit(code=EXIT_USAGE)

    async def _followup() -> None:
        await init_db()
        cli = ColdMailerCLI()
        async with get_db() as db:
            await db.execute(
                """
                UPDATE leads SET status='follow_up_ready'
                WHERE status='sent' AND last_outreach < datetime('now', ?)
                """,
                (f"-{days_since_last} days",),
            )
            await db.commit()

        if not channel_value:
            await cli._display_and_outreach("Follow-up Queue", status_filter="follow_up_ready")
            return

        async with get_db() as db:
            async with db.execute("SELECT * FROM leads WHERE status='follow_up_ready' ORDER BY score DESC") as cursor:
                leads = [dict(row) for row in await cursor.fetchall()]

        if not leads:
            console.print("No records found in follow-up queue.")
            return

        await cli._bulk_delivery(leads, channel_value)

    try:
        asyncio.run(_followup())
    except Exception as exc:
        console.print(f"Follow-up failed: {exc}")
        raise typer.Exit(code=EXIT_INTERNAL)


@app.command("export")
def export_cmd(
    table: str = typer.Option("all", "--table", help="leads|outreach_history|all"),
    out_dir: str = typer.Option("data/exports", "--out-dir"),
) -> None:
    table_value = table.lower()
    if table_value not in {"leads", "outreach_history", "all"}:
        console.print("Invalid --table. Use leads, outreach_history, or all.")
        raise typer.Exit(code=EXIT_USAGE)

    async def _export() -> None:
        await init_db()
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        tables = ["leads", "outreach_history"] if table_value == "all" else [table_value]

        async with get_db() as db:
            for table_name in tables:
                async with db.execute(f"SELECT * FROM {table_name}") as cursor:
                    rows = [dict(r) for r in await cursor.fetchall()]
                if not rows:
                    console.print(f"No rows in {table_name}; skipping.")
                    continue
                file_path = out_path / f"{table_name}.csv"
                with file_path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
                console.print(f"Exported {table_name} to {file_path}")

    try:
        asyncio.run(_export())
    except Exception as exc:
        console.print(f"Export failed: {exc}")
        raise typer.Exit(code=EXIT_INTERNAL)


@app.command("dashboard")
def dashboard_cmd(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    try:
        import uvicorn

        uvicorn.run("server:app", host=host, port=port, reload=reload)
    except Exception as exc:
        console.print(f"Dashboard failed: {exc}")
        raise typer.Exit(code=EXIT_INTERNAL)


def run() -> None:
    app()


if __name__ == "__main__":
    run()
