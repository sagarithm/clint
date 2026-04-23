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
- Current coverage: complete
- Existing modules: engine/director.py, engine/worker_orchestrator.py, core/state_machine.py, core/event_bus.py, server.py
- Remaining work:
  - none

### docs/v2/05-database-schema-v2.md
- Current coverage: complete
- Existing module: core/database.py
- Remaining work:
  - none

### docs/v2/01-source-connectors-and-filters.md
- Current coverage: complete
- Existing modules: scrapers/maps.py, scrapers/connectors/*.py, core/connectors.py
- Remaining work:
  - none

### docs/v2/08-ai-prompt-and-personalization-spec.md
- Current coverage: complete
- Existing modules: engine/proposer.py, engine/auditor.py
- Remaining work:
  - none

### docs/v2/07-deliverability-and-email-safety.md
- Current coverage: complete
- Existing modules: outreach/email_operator.py, core/reliability.py, core/policy.py
- Remaining work:
  - none

### docs/v2/11-cli-product-spec.md
- Current coverage: complete
- Existing modules: clint_cli.py, commander.py, core/deadletter.py
- Remaining work:
  - none

### docs/v2/12-library-api-spec.md
- Current coverage: complete
- Existing module: engine/engine.py
- Remaining work:
  - none

## Recommended Build Order
1. Schema and state backbone.
2. Connector and scoring contracts.
3. Prompt quality-gate contracts.
4. Dispatch safety and suppression enforcement.
5. CLI and library API contract hardening.
6. Reliability and release governance hardening.
