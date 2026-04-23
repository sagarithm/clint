# Code Inspection Guidelines

Clint V2 strictly mandates objective code inspections driven by automated static analysis prior to production release candidates. Code inspection differs from Code Review by focusing on semantic defects, complexity metrics, and hardcoded variables.

## 1. Security Inspections
* **SQL Injection Verification:** Due to using `aiosqlite`, all dynamic parameters *must* be passed safely using tuple substitution `(?, ?)`. F-strings inside queries are highly scrutinized and rejected if untrusted data exists.
* **Secrets Segregation:** Code strings cannot hardcode LLM endpoints or email tokens. They must map through `core/config.py`.
* **LLM Prompts:** Ensure user-generated variables (lead names, strings) are properly sanitized when passed through `compile_outreach_prompt()` to mitigate Prompt Injection.

## 2. Resource Management
* **Orphaned Sessions:** Every instance of `Playwright` browsers, `httpx.AsyncClient` invocations, and `aiosmtplib` connections must be evaluated for `.close()` commands or `async with` blocks to prevent zombie processes on Linux servers.
* **Memory Leaks:** Validate that massive datasets (i.e. `clint export --table all`) return scalable row chunks (pagination in future) or write immediately to `csv` generators rather than consuming RAM lists entirely.

## 3. Deprecation Traces
* When utilizing `/docs/v2/15-release-versioning-policy.md`, inspectors must search to ensure older endpoints correctly deploy the `warn_deprecated("feature_name", ...)` hook from `core.utils` to respect SDK users.

## 4. Linting Rules
* We respect `flake8` standards.
* Max cyclomatic complexity target: `C901` < 15. The `worker_orchestrator.py` should be the only deeply nested class.
