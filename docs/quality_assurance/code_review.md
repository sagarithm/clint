# Code Review Guidelines

The Clint V2 Code Review process is vital to ensuring that system robustness and safety requirements are met prior to merging into `dev` or `main`.

## Review Priorities

### 1. Safety and Outreach Protection
* **Dry-Run by Default:** Ensure any new `clint_cli.py` or `worker_orchestrator.py` script defaults to `dry_run = True`. Live execution must be explicit.
* **Quality Gates:** Verify that any new template generation correctly routes through `core.quality_gate.evaluate_message_quality()`.
* **State Verification:** Confirm that lead states are altered securely using `transition_lead_state()` instead of arbitrary raw `UPDATE` SQL clauses.

### 2. Architectural Adherence
* **Database Migrations:** If changes are made to `database.py` tables, ensure they are appended to the `MIGRATIONS` array inside `core/migrations.py` rather than altering existing active schema silently.
* **Config Overrides:** Any new setting requires appending to `core/config.py` using `Pydantic` `BaseSettings` types.

### 3. Asynchronous Efficiency 
* **Semaphore Controls:** Examine bounded batch limits (e.g. `asyncio.Semaphore(bounded)`) within API/CLI mass operations to prevent connection exhaustion.
* **Connection Pooling:** Reject code that opens bare DB connections without using the managed `get_db()` context manager.

## Review Process
1. **Automated Checks:** GitHub actions (Pytest & Linting) must turn green.
2. **Reviewer Check:** A peer engineer verifies the "Review Priorities."
3. **Approval:** Wait for at least one explicit approval.
4. **Merge Strategy:** Squash and merge feature branches into `dev` with standard Conventional Commits.
