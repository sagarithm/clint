# Coding Standards

This document establishes the universal coding standards for the **Clint V2** project. Adhering to these guidelines ensures readability, stability, and ease of contribution.

## 1. Core Principles
* **Evidence Before Action:** Never write state changes implicitly. Always mutate through `core/state_machine.py`.
* **Fail Gracefully, Alert Loudly:** Components like `engine/proposer.py` must fallback deterministically and log errors locally. Avoid silent catches.
* **Strict Typing:** We enforce native `typing` modules and `Pydantic` usage across the stack.

## 2. Python Architecture
* **Python Version:** 3.10+
* **Environment Loader:** Use `core.config.settings` strictly. Never read raw `os.environ` randomly in services.
* **Formatting:** We utilize `black` (line-length 100) and `isort` for import sorting.
* **Typing Checks:** Run `mypy` natively. All new functions must have signature annotations:
  ```python
  async def run_pipeline(limit: int, live_send: bool) -> Dict[str, Any]:
  ```

## 3. Asynchronous Standards
* **DB Connections:** Only use `aiosqlite`. Any new database interactions must use the `asynccontextmanager` from `core.database.get_db()`.
* **Network Execution:** For external APIs, utilize asynchronous `httpx` and explicitly define `timeout=45.0` or smaller to avoid thread lockups.
* **CLI Interactivity:** `typer` commands must appropriately encapsulate `asyncio.run()` in the entry points (`clint_cli.py`), avoiding nested event loops.

## 4. Error Handling & Exit Codes
* Rely on native exit codes assigned in `clint_cli.py`:
  * `EXIT_OK = 0`
  * `EXIT_USAGE = 2`
  * `EXIT_CONFIG = 3`
  * `EXIT_RUNTIME = 4`
  * `EXIT_NETWORK = 5`
* Standardize standard output: When emitting JSON strings or responses to CLI users, always use `_emit_command_result()`.

## 5. Directory Mapping
* `agent/core/`: Foundations, state, gates, SLA tracking.
* `agent/engine/`: Orchestration and execution brain.
* `agent/outreach/`: Downstream delivery (SMTP, WA).
* `agent/scrapers/`: Upstream intake (Maps, LinkedIn).
