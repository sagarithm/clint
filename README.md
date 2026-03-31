# Clint: AI-Driven Enterprise Outreach v1 🚀

Clint is a production-ready, asynchronous automation suite designed for high-conversion lead generation. It combines advanced stealth scraping, AI-powered audits, and multi-step outreach sequences into a powerful pipeline.

Full documentation is available in `docs/README.md`.

## 🌟 Premium Features

### 🛡️ Stealth & Safety (Human Mimicry)
- **Dynamic Fingerprinting**: Random User-Agents and Viewports for every session.
- **Human-Movements**: Randomized mouse hovering, scrolling, and typing patterns to evade bot detection.
- **Persistent Sessions**: Secure WhatsApp session handling to avoid repeated QR scans.

### 🤖 AI-Powered Intelligence
- **Founder Mode (Autonomous)**: Single-command lead generation, enrichment, and outreach (Scrape → Audit → Send).
- **Multi-Step Sequences**: Automated follow-up logic (Step 1: Pitch → Step 2: Reminder → Step 3: Final Call).
- **Lead Scoring**: Visual ranking (0-10) based on digital presence and social proof.
- **Deep Audit**: AI-driven analysis of Branding, UI/UX, and Tech frameworks.

### 📈 Clint Command Center
- **Visual Intelligence**: Monitor lead quality and sequence progress in a premium Tailwind v4 interface.
- **Dry Run Mode**: Safe simulation mode to verify outreach logic without actual delivery.
- **Rich Logging**: Every action is mirrored to `logs/outreach.log` for full auditability.

---

## 🛠 Setup

### 1. Installation
```bash
pip install -r requirements.txt
playwright install chromium
```

Or install as a CLI package:

```bash
pip install .
```

Or install as an isolated global CLI (recommended):

```bash
pipx install .
```

### 2. Configuration
Update your `.env` with:
- `OPENROUTER_API_KEY`: For AI Audits/Proposals.
- `SMTP_USER_1`/`SMTP_PASS_1`: Your email credentials.
- `SENDER_NAME`/`SENDER_TITLE`: Personalized signature info.

---

## 🚀 Execution

### First 5 Commands (Recommended Path)

```bash
clint version
clint init
clint config doctor
clint run --query "Dentists in California"
clint run --query "Dentists in California" --live
```

| Flow | Command |
| :--- | :--- |
| **Interactive CLI (menu mode)** | `clint` |
| **Autonomous Run (dry-run default)** | `clint run --query "Dentists in California"` |
| **Discovery-only scrape** | `clint scrape --query "Hotels in London" --target 20` |
| **Follow-up queue** | `clint followup --days-since-last 3` |
| **Dashboard server** | `clint dashboard --host 127.0.0.1 --port 8000` |
| **Config doctor** | `clint config doctor` |

---

## 🛡 Safety & Limits
- **Recommended Volume**: For better deliverability and reduced bot-detection risk, keep outreach around **200 emails/day** and **200 WhatsApp messages/day**.
- **Delays**: Randomized 5-15s intervals between every outreach attempt.
- **Logs**: Detailed execution history at `logs/outreach.log`.

---

*Clint v1.0.0 | Launch Ready*
