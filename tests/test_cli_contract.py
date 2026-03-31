from typer.testing import CliRunner

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
