# Clint V2 Documentation Hub

This folder defines the V2 system as a CLI and Python library first product.
The goal is to build a production-grade AI outreach operating system that is
safe, measurable, and extensible.

## Scope Boundary
- Current build scope: Python package + CLI + API runtime.
- Future scope: SaaS control plane after V2 stability gates are passed.
- Primary commercial offer: web solutions (web design, UX, CRO, automation).

## Document Map
- 00-master-implementation-plan.md: product mission, phases, and readiness gates
- 01-source-connectors-and-filters.md: source contracts, normalization, filters
- 02-developer-todo.md: sprint backlog and acceptance checks
- 03-operating-guidelines.md: day-to-day operating system and decision policies
- 04-system-architecture.md: engine modules, state machine, worker topology
- 05-database-schema-v2.md: canonical schema for explainable automation
- 06-campaign-playbooks.md: web-solution playbooks by signal type
- 07-deliverability-and-email-safety.md: reputation-first sending policy
- 08-ai-prompt-and-personalization-spec.md: prompt compiler and quality gates
- 09-kpi-dashboard-and-experiments.md: KPI model and experiment workflow
- 10-launch-checklists.md: launch, rollback, and sign-off criteria
- 11-cli-product-spec.md: command model, UX guarantees, and runtime behavior
- 12-library-api-spec.md: package interface contracts and versioned APIs
- 13-connector-sdk-spec.md: connector plugin contract and lifecycle hooks
- 14-testing-quality-gates.md: test matrix, release gates, and non-functional SLOs
- 15-release-versioning-policy.md: version policy and deprecation lifecycle

## Recommended Read Order
1. 00 + 03: lock strategy, constraints, and operating standards.
2. 04 + 05: implement architecture and schema backbone.
3. 11 + 12 + 13: formalize CLI/package contracts and extension model.
4. 01 + 06 + 08: implement acquisition and messaging intelligence.
5. 07 + 09 + 10 + 14 + 15: harden operations, quality, and release discipline.

## Ownership Model
- Product/Founder: ICP, offer positioning, proof assets, launch decisions.
- Engineering: architecture, reliability, SDK, release quality.
- Growth Ops: campaign operations, suppression hygiene, feedback loops.
- Analytics: KPI integrity, experiment validity, attribution confidence.
