from pathlib import Path
import sys

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import clint_cli
from clint_cli import app

runner = CliRunner()


def test_config_set_invalid_key_returns_usage_error():
    result = runner.invoke(app, ["config", "set", "BAD_KEY", "value"])
    assert result.exit_code == 2
    assert "Unknown config key" in result.stdout


def test_init_non_interactive_requires_required_flags():
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", "--non-interactive"])
        assert result.exit_code == 2
        assert "Missing required options" in result.stdout


def test_run_dry_run_preview_default():
    result = runner.invoke(app, ["run", "--query", "Dentists in California"])
    assert result.exit_code == 0
    assert "Dry run preview" in result.stdout


def test_export_invalid_table_returns_usage_error():
    result = runner.invoke(app, ["export", "--table", "bad_table"])
    assert result.exit_code == 2
    assert "Invalid --table" in result.stdout


def test_doctor_missing_credentials_maps_to_config_exit(monkeypatch):
    monkeypatch.setattr(
        clint_cli,
        "run_doctor_checks",
        lambda _values: [("OpenRouter", ("FAIL", "OPENROUTER_API_KEY missing"))],
    )
    monkeypatch.setattr(clint_cli, "read_env", lambda: {})
    result = runner.invoke(app, ["config", "doctor"])
    assert result.exit_code == 3


def test_doctor_auth_failure_maps_to_network_exit(monkeypatch):
    monkeypatch.setattr(
        clint_cli,
        "run_doctor_checks",
        lambda _values: [("SMTP", ("FAIL", "SMTP auth failed: invalid credentials"))],
    )
    monkeypatch.setattr(clint_cli, "read_env", lambda: {})
    result = runner.invoke(app, ["config", "doctor"])
    assert result.exit_code == 5


def test_run_live_without_credentials_is_config_error(monkeypatch):
    monkeypatch.setattr(clint_cli, "read_env", lambda: {})
    result = runner.invoke(app, ["run", "--query", "Dentists", "--live"])
    assert result.exit_code == 3


def test_run_live_network_exception_maps_to_network_exit(monkeypatch):
    monkeypatch.setattr(
        clint_cli,
        "read_env",
        lambda: {
            "OPENROUTER_API_KEY": "x",
            "SMTP_USER_1": "u",
            "SMTP_PASS_1": "p",
        },
    )

    async def _noop_init_db():
        return None

    async def _raise_request_error(*_args, **_kwargs):
        import httpx

        raise httpx.RequestError("network", request=httpx.Request("GET", "https://example.com"))

    monkeypatch.setattr(clint_cli, "init_db", _noop_init_db)
    monkeypatch.setattr(
        clint_cli.OutreachDirector,
        "execute_autonomous_batch",
        _raise_request_error,
    )
    result = runner.invoke(app, ["run", "--query", "Dentists", "--live"])
    assert result.exit_code == 5


def test_worker_reddit_dry_run_success(monkeypatch):
    async def _noop_init_db():
        return None

    async def _run_pipeline(self, **_kwargs):
        return {"result": {"discovered": 1, "sent": 0}}

    monkeypatch.setattr(clint_cli, "init_db", _noop_init_db)
    monkeypatch.setattr(clint_cli.QueueWorkerOrchestrator, "run_reddit_pipeline", _run_pipeline)

    result = runner.invoke(app, ["worker-reddit", "--query", "web design help"])
    assert result.exit_code == 0
    assert "Worker pipeline completed" in result.stdout


def test_experiments_decide_success(monkeypatch):
    async def _noop_init_db():
        return None

    class _DummyDb:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def commit(self):
            return None

    async def _fake_decide(*_args, **_kwargs):
        return {"decision": "no_winner", "winner": "none"}

    monkeypatch.setattr(clint_cli, "init_db", _noop_init_db)
    monkeypatch.setattr(clint_cli, "get_db", lambda: _DummyDb())
    monkeypatch.setattr(clint_cli, "decide_experiment", _fake_decide)

    result = runner.invoke(app, ["experiments-decide", "--experiment-id", "1"])
    assert result.exit_code == 0
    assert "no_winner" in result.stdout


def test_deadletter_list_success(monkeypatch):
    async def _noop_init_db():
        return None

    class _DummyDb:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    async def _fake_list(*_args, **_kwargs):
        return [
            {
                "id": 1,
                "topic": "events.deadletter",
                "replay_status": "pending",
                "replay_attempts": 0,
                "created_at_utc": "2026-01-01 00:00:00",
            }
        ]

    monkeypatch.setattr(clint_cli, "init_db", _noop_init_db)
    monkeypatch.setattr(clint_cli, "get_db", lambda: _DummyDb())
    monkeypatch.setattr(clint_cli, "list_deadletter_events", _fake_list)

    result = runner.invoke(app, ["deadletter-list"])
    assert result.exit_code == 0
    assert "Deadletter Events" in result.stdout


def test_deadletter_replay_success(monkeypatch):
    async def _noop_init_db():
        return None

    class _DummyDb:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def commit(self):
            return None

    async def _fake_replay(*_args, **_kwargs):
        return {"event_id": 1, "status": "replayed"}

    monkeypatch.setattr(clint_cli, "init_db", _noop_init_db)
    monkeypatch.setattr(clint_cli, "get_db", lambda: _DummyDb())
    monkeypatch.setattr(clint_cli, "replay_deadletter_event", _fake_replay)

    result = runner.invoke(app, ["deadletter-replay", "--event-id", "1"])
    assert result.exit_code == 0
    assert "replayed" in result.stdout
