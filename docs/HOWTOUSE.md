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
    python run_outreach.py
    ```
2.  Select **Initial** mode.
3.  Enter a query like `"Hotels in London"` or `"Dentists in Satna"`.
4.  Specify the number of leads (e.g., `10`).
5.  **Dry Run**: Select `n` for real outreach or `y` to just test the logic.

---

## 3. Automated Follow-ups (Follow-up Mode)
The system automatically tracks who you've messaged.
1.  Run `python run_outreach.py` and select **Follow-up**.
2.  The system will scan for leads who were messaged more than **3 days ago** and haven't replied.
3.  AI will generate a context-aware "Step 2" reminder for them.

---

## 4. Using the Dashboard
1.  Start the backend server:
    ```powershell
    python server.py
    ```
2.  Visit `http://localhost:8000` in your browser.
3.  **Lead Scoring**: Look for the color-coded scores:
    - 🟢 **7-10**: High Priority (Good website/reviews)
    - 🟡 **4-6**: Medium Priority
    - 🔴 **0-3**: Low Priority
4.  **Action**: You can view screenshots and lead details directly in the table.

---

## 5. Stealth & Safety Tips
- **Limits**: Stick to 50-100 emails/day per account to remain under the radar.
- **WhatsApp**: Do not close the Chromium window manually while it's typing; it mimics human patterns to avoid bans.
- **Dry Run**: Always use Dry Run when testing new prompt changes in `engine/proposer.py`.

---

*Happy Hunting!*
