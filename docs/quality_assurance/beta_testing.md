# Beta Testing Guidelines

Beta Testing involves providing operational usage to a closed loop of human reviewers—primarily founders or lead growth operators utilizing the `clint dashboard` to verify lead quality before scaling autonomously.

## Deployment Environment
* Ran live with genuine `SMTP_USER_1` configurations and genuine proxies.
* Outgoing restrictions enabled to extremely low delays (e.g., `< 5 per day`).

## Metric Validation
During Beta, user acceptance determines success. Does the operator find value from the autonomous outreach?
1. **Pipeline Verification:** Utilizing `http://localhost:8000/api/leads`, operators manually categorize "Generated Proposal Quality". Is it human-like? Is it capturing business pain points?
2. **Experiment Tracking:** Start an A/B test campaign utilizing `core/experiments.py`.
3. **Observation:** Operators document Deliverability (spam drops) and Reply Rates natively transitioning from `sent` -> `replied_positive`.

## Feedback Cycles
Issues recorded in Beta usually map back to the `proposer.py`'s context injections (i.e. "The AI sounded too robotic"). Fixes involve updating legacy prompts or `prompt_compiler.py` and looping back to Alpha testing.
