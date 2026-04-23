# Architecture & Code Walkthrough

A structured walkthrough is performed for onboarding engineers aiming to comprehend the data flow and orchestration sequence of the Clint engine.

## Step 1: Ingestion & Discovery
* **Files:** `scrapers/maps.py`, `scrapers/web_crawler.py`
* **Trigger:** Calling `clint scrape` or via `PipelineRequest` to the API.
* **Logic Flow:** Scrapers target platforms securely via Playwright, extract fields (`phone`, `website`, `rating`), and pass raw dictionaries into `normalize_connector_record`.
* **Persistence:** Data is locked in the SQL `leads` and provenance is stored securely in `lead_sources`.

## Step 2: Evaluation & Proposing
* **Files:** `engine/proposer.py`, `core/quality_gate.py`
* **Trigger:** Calling `clint run` or the `WorkerOrchestrator` queues.
* **Logic Flow:**
  1. The DB compiles an outreach backlog depending on the score. 
  2. The LLM (`proposer.py`) compiles a highly targeted message via `compile_outreach_prompt()`.
  3. The Proposal **MUST** pass `evaluate_message_quality()`. Too many tokens? Too short? It drops safely without exception and logs.

## Step 3: Execution & Deadletter
* **Files:** `outreach/email_operator.py`, `outreach/whatsapp_operator.py`, `core/deadletter.py`
* **Trigger:** Dispatcher scripts iterating through validated drafts.
* **Logic Flow:** Operations rotate API proxies/SMTP creds via asynchronous execution. If an operator fails due to transient delays, it wraps into a deadletter event queue tracking for automated future replay routing via CLI tools.

## Step 4: Observer Loop & SLAs
* **Files:** `server.py`, `core/sla_monitor.py`, `core/reply_intelligence.py`
* **Logic Flow:** A background thread tracks inbound replies. It scores user "intention" via intelligence markers, transitioning leads to SLA-monitored queues (`replied_positive`). If humans fail to respond in `SLA_BREACH_HOURS`, the background manager sends system alerts.
