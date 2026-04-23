# Integration Testing Strategy

Integration testing confirms the harmonious interaction between distinct modules (Database + OpenRouter LLM + Orchestrator) in the Clint architecture. These tests intentionally omit mocked internal logic to ensure that cross-dependency pathways function seamlessly.

## Key Integration Vectors
1. **Database & Migrations Interaction:** 
   Confirm initialization (`core/database.py`) and programmatic upgrades (`migrations.py`) work synchronously in staging conditions.
2. **Director & Pipeline Batching:**
   The `engine/director.py` must reliably handle lists of leads, parsing them consecutively into `proposer.py` and tracking concurrency limits natively.
3. **Deadletter Traversal:**
   A test simulating an intent-to-send block dropping an event to `core/deadletter.py`, reading the database state, executing replay routes, and verifying successful extraction from the Deadletter table.

## The Playbook Methodology
To prove stability under duress (outages, rogue hallucinations, structural blocks), developers construct simulated sequences mapped via `tests/test_incident_playbooks.py`.
* Example: "LLM goes down." Simulate standard operation against invalid API mappings—the resulting integration must yield a local `fallback_template` natively deployed in DB rather than throwing unhandled tracebacks.
