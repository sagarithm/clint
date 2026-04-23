# Final Operational Testing (The 100/100 Protocol)

This is the absolute final verification pipeline. It assesses Clint V2 natively from the perspective of an end-user / operator executing campaigns in the real world. Every aspect—from CLI font rendering to SMTP deliverability—is scrutinized here. 

This test MUST be executed successfully before initiating automated volume outreach.

---

## Phase 1: Environment & CLI Lifecycle Validation
Before data ingestion occurs, the user experience and configuration guardrails must be absolute.

- [ ] **1.1 Version Verification**: Open terminal from outside the virtual environment root. Run `clint --version`. Ensure standard output renders identical to target release `v1.0.3` without throwing native Python pathing errors.
- [ ] **1.2 Doctor Health Check**: Run `clint config doctor`. 
  - *Criteria*: The Typer `rich` output must display all required environment variables (`OPENROUTER_API_KEY`, `SMTP_USER_1`, `DB_PATH`) in green checks.
- [x] **1.3 Database Zero-State**: Check `/data/clint.db`. If populated from previous developer interactions, securely wipe leads (using `clint export --flush` or direct drop) to guarantee a sterile testing environment.

---

## Phase 2: True Muti-Channel Data Intake (Scrapers)
Run targeted, ultra-specific pipelines instead of generic inputs to verify the integrity of Playwright and RSS parsers.

- [x] **2.1 Maps Mimicry**: Execute `clint run maps --query "Digital Agencies in Austin, TX" --limit 3`. 
  - *Criteria*: Ensure `playwright` correctly bypasses headless detection to extract real entity `phone` numbers and `website` addresses.
- [x] **2.2 Upwork Pipeline**: Trigger Upwork feed extraction parsing.
  - *Criteria*: Validate `<title>` and `<description>` elements do not leak HTML elements into the SQLite structures.
- [x] **2.3 Data Saturation Verification**: Utilize `clint export` or DB browser to confirm records contain provenance traces (`source_name=maps`, `scraped_at_utc`).

---

## Phase 3: The "Brain" Audit (Generative Accuracy)
This phase tests whether the `proposer.py` and `prompt_compiler.py` honor your settings in `config.py`.

- [x] **3.1 Identity Check**: Read the raw generated output for a specific lead inside the SQLite `message_drafts` table.
  - *Criteria*: Does the signature explicitly state "**Sagar Kewat | Founder | Pixartual**"? Does it include the correct taglines?
- [x] **3.2 Context Hallucination Check**: 
  - *Criteria*: Ensure the AI uses facts pulled directly from the scraper record (e.g., "I saw you are an agency based in Austin") rather than inventing details natively.
- [x] **3.3 Deterministic Fallback Trigger Test**: Sever the wifi connection or rename the `OPENROUTER_API_KEY` explicitly. Rerun generation.
  - *Criteria*: Pipeline must seamlessly revert to the static logic block bypassing API errors. No traceback exceptions in terminal. 

---

## Phase 4: Delivery & Network Reputation
Verify system dispatch stability against SMTP spam filters. 

- [x] **4.1 Mail-Tester Validation**: Initiate a singular live targeted dispatch toward a dynamic testing address at `mail-tester.com`.
  - *Criteria*: Output must score **10/10**. Validating SPF, DKIM, and DMARC rendering. Any score dropping below 8 indicates SMTP rot.
- [x] **4.2 Delay Bounding**: Dispatch to two leads consecutively.
  - *Criteria*: The terminal natively records a programmatic sleep reflecting `MIN_DELAY_SECONDS` up to `MAX_DELAY_SECONDS` bounds to prevent Google/Microsoft IP reputation penalties.
- [x] **4.3 Dry-Run Safety Harness**: Expose the generator logic in `clint run --limit 10`. Do not apply `--live-send`.
  - *Criteria*: The CLI must clearly warn `DRY RUN EXECUTED` and zero actual dispatches hit target systems.

---

## Phase 5: Dashboard GUI Realism 
A backend is only as reliable as its frontend display. 

- [x] **5.1 Server Uptime**: Initiate `uvicorn server:app` or `python server.py`. 
- [x] **5.2 Reactivity**: Open `http://localhost:8000/`.
  - *Criteria*: Fast load times. Chart metrics accurately represent the "3 Scraped Leads" and "1 Mail-Tester Dispatch" generated in previous phases.
- [x] **5.3 Deadletter Visualization**: Using the API manually, push an intent-to-send block. 
  - *Criteria*: Verify the system accurately pushes to `core/deadletter.py` and visualizing on the UI without reloading.

---

## Phase 6: Post-Dispatch Reply Intelligence & SLAs
Test the longest-running automated threads dictating conversion workflows.

- [x] **6.1 Intelligence Interception**: From the receiving test email, reply with: *"This is interesting, what are your rates?"*
- [x] **6.2 State Reclassification Validation**: 
  - *Criteria*: `reply_intelligence.py` assigns an Intent Label mapping closer to `replied_positive` (> 0.82 confidence). `leads` lifecycle transitions out of `sent` into `replied`.
- [x] **6.3 Background Operator SLA Alerting**: Using developer tools or clock shifts, forcefully wind time past the `SLA_BREACH_HOURS` variable in configuration. 
  - *Criteria*: The asynchronous loop residing in `server.py` natively tracks the breach, drops an alert payload targeting `hello@pixartual.studio`, successfully hitting your inbound inbox automatically as a notification to rescue the lead!

---
> [!IMPORTANT]
> A failure within **Phase 3** or **Phase 4** necessitates hard development halts. Reputation damage via rogue generation or SMTP burning cascades negatively onto the entire brand infrastructure. Do not bypass these checks.
