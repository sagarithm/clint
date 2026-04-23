# White Box Testing

White box testing targets the deepest intelligence and routing structures of Clint V2, ensuring logic flows, mathematical boundaries, and database states behave identically as written.

## State Machine Traversal
* **Component:** `core.state_machine.transition_lead_state`
* **Testing:** Directly supply `leads` IDs and examine `aiosqlite` records pre-and-post function execution. Verify if `reason` codes and `actor` fingerprints correctly commit to the ledger strings, rather than merely checking the UI.

## Quality Gate Mathematics
* **Component:** `core.quality_gate.evaluate_message_quality`
* **Testing:** The logic drops values by `-50` for placeholder brackets `[[]]`. We inject strings possessing exact structural failures and assert the integer scores drop properly.
* **Goal:** Prove deterministic blocking thresholds function predictably. 

## Prompt Compilation Assembly
* **Component:** `core.prompt_compiler.py` (and legacy generation in `proposer.py`).
* **Testing:** Bypassing HTTP operations, we feed exact dummy data strings (`lead_name`, `metrics`) to verify that the templating engine formats variables correctly without injecting syntactical HTML bugs.

## SLA Operations
* **Testing Iteration:** Modify timestamps manually of mock leads directly via `Cursor` in setup fixtures. Run `check_sla_breaches()`. Read `.log` stdout or local memory queues to assert exactly `int` length breaches triggered emails successfully.
