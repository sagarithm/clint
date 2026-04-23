# Unit Testing Protocol

Our Unit testing matrix leverages `pytest` exclusively to map isolated functional health. Native unit tests **must not** rely on network APIs passing (use mocker fixtures), guaranteeing that tests run deterministically offline in CI actions.

## 1. Environment & Tools
* **Library:** `pytest`
* **Async Library:** `pytest-asyncio` strictly handling asynchronous SQLite commands (`aiosqlite`). 
* **Location:** `tests/` relative to project root.

## 2. Core Fixtures
* Tests utilize short-lived database memories. If overriding `DB_PATH`, it must point to an arbitrary `:memory:` instance or `data/test.db` which spins up and drops fixtures per test class to avoid state leaking.

## 3. Structural Domains Covered
### Connectors
* Examples: `test_fiverr_connector.py`, `test_linkedin_connector.py`.
* Protocol: Supply fixed local mock JSON blobs corresponding to HTML drops and assert the Python normalization mapping succeeds (creating objects with valid formats).

### Quality Gates
* Protocol: Feed static strings to local functions. It functions as a calculator. Inputs must correctly validate `True / False` depending on parameter length and token arrays.

### Typer CLI (Isolated)
* Protocol: Mocks network or Database dependency exceptions explicitly using `@patch('core.database.get_db')`, forcing failure blocks and asserting valid CLI exit signals.
