# Quality Assurance Master Checklist

This exhaustive checklist dictates the specific unit, integration, and operational verifications required prior to clearing any Clint V2 release candidate into production. It addresses all aspects—from fundamental database schema persistence to overarching systemic fallback structures.

---

## 1. Infrastructure & Code Quality (Static / Pre-commit)
* [x] **PEP-8 Protocol**: Syntax completely passes `flake8` checks without masking critical rules.
* [x] **Type Annotations**: `mypy` scan yields `0` errors; native typing is applied across `core`, `engine`, and `scrapers`.
* [x] **Settings Object**: API keys and environment variables strictly traverse through `core.config.settings` utilizing `pydantic-settings`; no loose `os.environ` fetching.
* [x] **Resource Cleanup**: Static analysis confirms all `aiosmtplib`, `httpx.AsyncClient`, and `playwright` connections possess proper `.close()` bindings or `async with` blocks.
* [x] **Database Isolation**: `init_db()` is secured and local testing utilizes isolated memory datasets (i.e. strictly bypassing production `./data/clint.db`).

---

## 2. Platform Scrapers & Connectors (Unit/White Box Testing)
* [x] **Fiverr RSS Intake**: Pipeline flawlessly transforms structured feed dictionaries into standardized SQL Lead objects. 
* [x] **Upwork Syntax Normalization**: Pipeline accurately catches and sanitizes XML character limits for Upwork profiles.
* [x] **LinkedIn Parsing**: Handles variable missing profile items (like absent website links) without `KeyError` failures.
* [x] **X/Threads Connector Processing**: Ingests URL parameters correctly into metadata.
* [x] **Google Maps Crawler Resilience**: Playwright mimicry routines correctly spoof browser configurations to overcome strict rate limits gracefully.

---

## 3. Core Engine & State Verification (Unit Testing)
* [x] **Additive Migrations**: Validate that `core/migrations.py` functions smoothly on fresh deployments (`v2_001_initial_backbone`).
* [x] **Rollback Triggers**: Confirm `migrations.rollback_migration()` removes target columns safely and leaves schema intact.
* [x] **State Machine Validation**: Executing `transition_lead_state()` on an existing ID safely alters lifecycle status, appends reason, and timestamps event natively.
* [x] **Pre-Send Policy Filters**: `enforce_pre_send_policy()` absolutely prevents messaging any lead matching the local internal domain structures or `BLACKLIST`.

---

## 4. Automation Quality Gates (Unit Testing)
* [x] **Token Sweeping**: `evaluate_message_quality()` guarantees that texts involving brackets (e.g., `[Insert name here]`) violently trip the -50 integer scale reduction, failing validation outright.
* [x] **Length Limitations**: Assert the quality gate correctly penalizes severely truncated bodies (under standard token sizes) as "insufficiently personalized."
* [x] **Prompt Assembly Integrity**: Verify `compile_outreach_prompt()` embeds context objects smoothly without creating syntactic LLM confusion.

---

## 5. Intelligence, Proposal & Dispatch (Integration Testing)
* [x] **API Connectivity**: Proposer natively calls out to LLM architecture models without TLS/SSL cert routing failures.
* [x] **Dispatch Safety Verification**: Running outbound modules like the `EmailOperator` respects `MAX_DELAY_SECONDS` bounds to prevent immediate IP burning.
* [x] **SLA Thread Accuracy**: Background loops evaluating database states successfully flag dormant `replied_positive` leads over `SLA_BREACH_HOURS` config lengths.
* [x] **Reply Classification Confidence**: Neutral, affirmative, and negative inbound test-texts accurately return >`0.80` prediction targets from `reply_intelligence.py`. 

---

## 6. Typer Command Line Interface (Black Box Testing)
* [x] **Doctor Validation**: Submitting `clint config doctor` returns native visual markers and standard configuration validations (`EXIT_OK` `0`) when environment passes.
* [x] **Missing Credentials Guard**: Deploying execution commands identically throws a clean `EXIT_CONFIG` `3` when `OPENROUTER_API_KEY` is ripped from the `.env`.
* [x] **Live/Dry Command Overrides**: Default `clint run` triggers strictly inside `--dry-run`; `live` mutations require explicit affirmative flags and visual confirmations.
* [x] **Data Export Execution**: Issuing `clint export --table <X>` triggers local output processing (.csv mapping) without memory timeouts.

---

## 7. FastAPI Control Plane (Local API Testing)
* [x] **Payload Strictness Guard**: Malformed REST packets directed into `/api/outreach/generate` invoke accurate `422 Unprocessable` responses inherently via FastAPI Pydantic maps.
* [x] **Experiment Loop Hooks**: Endpoints successfully trace `/api/experiments/create` straight through to `decide` via HTTP logic alone.
* [x] **Server Startup Bindings**: Calling `uvicorn server:app` organically fires SLA background watchers as part of the internal server `lifespan`.
* [x] **Dashboard Render Fallbacks**: When visiting `/` (Root), the endpoint effectively locates and serves the nested local `dashboard.html` asset or fails securely.

---

## 8. Incident Playbooks & Deadletter Pipeline (Chaos Integrity)
* [x] **Local Fallback Switch**: `Engine Provider Outage` simulation verifies that `Engine` intelligently routes blank responses into hardcoded, personalized strings instead of locking pipelines.
* [x] **Event Persistence**: Deliberate network disconnects during pipeline actions write full traces to `deadletter_events` instead of purging data into memory voids.
* [x] **Event Replay Execution**: Hitting the deadletter replay framework forces the item back through the specific broken schema pipeline accurately. 

---

## 9. Operation Finalization (Alpha/Beta Operator Tracking)
* [x] **Deliverability Check**: 100 test emails hit an internal inbox effectively verifying SPF/DKIM structural formatting mapping within SMTP. 
* [x] **Deprecation Flow Validations**: Any obsolete framework commands reliably issue `DeprecationWarning` console notifications, logging the behavior actively for analytics tracking.
* [x] **Data Wipe Success**: Final operator clears the internal test leads leveraging raw administrative control configurations prior to main launch.

---
**Review Completed By:** _________________________  
**Target Release Tag:** _________________________  
**Date:** _________________________  
