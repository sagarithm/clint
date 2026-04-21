# V2 Implementation Mapping (Docs to Code)

## Purpose
Map V2 documentation requirements to current code modules and execution order.

## Core Runtime Modules
- CLI entry and command surface: clint_cli.py, commander.py
- Engine orchestration: engine/director.py
- AI reasoning and messaging: engine/auditor.py, engine/proposer.py, engine/engine.py
- Data and reliability: core/database.py, core/scorer.py, core/reliability.py
- Channel operators: outreach/email_operator.py, outreach/whatsapp_operator.py
- Source acquisition: scrapers/maps.py, scrapers/web_crawler.py
- API runtime: server.py

## Mapping Matrix

### docs/v2/04-system-architecture.md
- Current coverage: strong
- Existing modules: engine/director.py, engine/worker_orchestrator.py, core/state_machine.py, core/event_bus.py, server.py
- Remaining work:
  - external queue backend (current worker topology is in-process)
  - broader replay handlers for non-ingest deadletter payload types

### docs/v2/05-database-schema-v2.md
- Current coverage: strong
- Existing module: core/database.py
- Remaining work:
  - continue additive migrations for future connector-specific payload metadata

### docs/v2/01-source-connectors-and-filters.md
- Current coverage: partial
- Existing modules: scrapers/maps.py, scrapers/connectors/*.py, core/connectors.py
- Remaining work:
  - production fetch implementations for LinkedIn, X/Threads, and Fiverr connectors
  - broaden worker orchestration beyond Reddit-specific pipeline entrypoint

### docs/v2/08-ai-prompt-and-personalization-spec.md
- Current coverage: partial
- Existing modules: engine/proposer.py, engine/auditor.py
- Remaining work:
  - deeper prompt compiler layer separation
  - expanded quality evidence persistence and reviewer tooling

### docs/v2/07-deliverability-and-email-safety.md
- Current coverage: medium
- Existing modules: outreach/email_operator.py, core/reliability.py, core/policy.py
- Remaining work:
  - sender-level adaptive throttle/pause automation
  - deeper multi-channel policy harmonization

### docs/v2/11-cli-product-spec.md
- Current coverage: strong
- Existing modules: clint_cli.py, commander.py, core/deadletter.py
- Remaining work:
  - standardized machine-readable summary envelope across all command paths

### docs/v2/12-library-api-spec.md
- Current coverage: partial
- Existing module: engine/engine.py
- Remaining work:
  - richer typed result contracts
  - stable domain exception classes

## Recommended Build Order
1. Schema and state backbone.
2. Connector and scoring contracts.
3. Prompt quality-gate contracts.
4. Dispatch safety and suppression enforcement.
5. CLI and library API contract hardening.
6. Reliability and release governance hardening.
