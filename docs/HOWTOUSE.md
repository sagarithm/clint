# ColdMailer - User Guide

This guide will walk you through setting up and running your first high-conversion outreach campaign.

## 1. Setup & Requirements

### API Keys
1.  **OpenRouter**: Obtain an API key from [openrouter.ai](https://openrouter.ai/). This powers the AI Audit and Proposal generation.
2.  **Gmail**: If using Gmail, you MUST generate an **App Password**. Regular passwords will not work due to 2FA.

### Environment (.env)
Fill in your details in the `.env` file:
- `SENDER_NAME`: Your name (e.g., Sagar Kewat)
- `SENDER_TITLE`: Your professional title.
- `SMTP_USER_1`: Your full Gmail address.
- `SMTP_PASS_1`: Your 16-character App Password.

---

## 2. Finding New Leads (Initial Mode)
1.  Run the outreach script:
    ```powershell
    clint scrape --query "Hotels in London" --target 10
    ```
2.  This collects new leads into the pending queue.
3.  To launch autonomous outreach, use:
    ```powershell
    clint run --query "Hotels in London" --target 10 --send-limit 5 --live
    ```
4.  By default, `clint run` is dry-run unless `--live` is provided.

---

## 3. Resuming a Batch (Resume Mode)
If your internet cuts out or you manually stop the script (Ctrl+C), do not worry:
1.  Run `clint` and choose **REVIEW** from the command center menu.
2.  The system will skip Google Maps and immediately pick up all leads that were captured but not yet sent to.
3.  This ensures no duplicates and saves you time.

---

## 4. Automated Follow-ups (Follow-up Mode)
The system automatically tracks who you've messaged.
1.  Run:
    ```powershell
    clint followup --days-since-last 3
    ```
2.  The system will scan for leads who were messaged more than **3 days ago** and haven't replied.
3.  AI will generate a context-aware "Step 2" reminder for them.

---

## 4. Using the Dashboard
1.  Start the backend server:
    ```powershell
    clint dashboard --host 127.0.0.1 --port 8000
    ```
2.  Visit `http://localhost:8000` in your browser.
3.  **Lead Scoring**: Look for the color-coded scores:
    - 🟢 **7-10**: High Priority (Good website/reviews)
    - 🟡 **4-6**: Medium Priority
    - 🔴 **0-3**: Low Priority
4.  **Action**: You can view screenshots and lead details directly in the table.

---

## 5. Stealth & Safety Tips
- **Recommended Volume**: Keep outreach around 200 emails/day and 200 WhatsApp/day for better deliverability and lower bot-detection risk.
- **WhatsApp**: Do not close the Chromium window manually while it's typing; it mimics human patterns to avoid bans.
- **Dry Run**: Always use Dry Run when testing new prompt changes in `engine/proposer.py`.

---

*Happy Hunting!*
