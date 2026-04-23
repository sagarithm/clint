# Black Box Testing

Within Clint V2, Black Box testing primarily targets the two interface boundaries available to the end operator: the Typer CLI and the FastAPI Control Plane. Engineers must ensure functionality operates cleanly without caring about the database routing inside.

## Typer CLI Testing Strategy
* **Tool:** `typer.testing.CliRunner`
* **Test Vectors:**
  1. Input `clint config doctor`. Check exit codes (`0`, `3`, `5`) and message outputs without looking manually at the `.env` verification internals.
  2. Test `clint run` with and without credentials, with dry-run flags. Does the output structurally match expectations?
  3. Validate `clint run --limit "NAN"` mapping back the native Usage Error `EXIT_USAGE`.
* **Execution Script Example:** See `test_cli_contract.py` which mocks nothing except environment variables to prove the overarching Typer framework is stable.

## FastAPI Endpoints Testing
* **Tool:** `fastapi.testclient.TestClient`
* **Test Vectors:**
  1. **Payload Inject:** Submitting an invalid `PipelineRequest` missing required attributes. Does it return 422?
  2. **Stat Requests:** Verify `/api/stats` responds properly based on the `test` data state.
  3. **Event Trigger:** Hitting the `/api/deadletter/replay` JSON hook.

## Acceptance Criteria
To pass Black Box constraints, all CLI subcommands and API paths must map responses cleanly that match the documented `v2` payload specs without internal stack trace leakage.
