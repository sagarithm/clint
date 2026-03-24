# ColdMailer: High-Tech AI Outreach Agent 🚀

ColdMailer is a professional-grade, asynchronous automation suite designed for high-conversion lead generation and AI-driven outreach. It combines advanced web scraping, AI-powered website auditing, and multi-channel messaging (Email & WhatsApp) into a seamless, high-performance pipeline.

## 🌟 Key Features

### 🔍 Advanced Lead Discovery
- **Google Maps Scraper**: Specialized scraper with robust handling for modern DOM structures. 
- **Deep Knowledge Extraction**: Automatically collects **Ratings, Review Counts, and Business Categories** to provide deep context for outreach.
- **Asynchronous Processing**: Fast, scalable scraping that handles search results and detail panels concurrently.

### 🤖 AI-Powered Intelligence
- **Website Auditor**: Crawls lead websites to identify gaps in Branding, UI/UX, SaaS Design, SEO, and AI innovation.
- **Personalized Proposer**: Uses OpenRouter-powered LLMs to generate highly tailored pitches. 
- **Rapport Building**: Automatically mentions lead-specific "social proof" (like high ratings/reviews) to build instant trust.
- **Proposal Preview**: Review and approve AI-generated messages before they are sent.

### 📈 Outreach & Tracking
- **Multi-Channel Delivery**: Integrated Email (SMTP/Exchange) and WhatsApp automation.
- **Outreach History**: Complete database logging of every message sent, including channel, content, and status.
- **Auto-Export**: Automatically generates/updates `leads_export.csv` and `outreach_history_export.csv` after every successful search.
- **Live Dashboard**: A beautiful Rich-based CLI for monitoring pipeline progress and stats.

---

## 🛠 Getting Started

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/your-repo/ColdMailer.git
cd ColdMailer

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configuration
Create a `.env` file in the root directory:
```env
OPENROUTER_API_KEY=your_openrouter_api_key
AI_MODEL=openai/gpt-3.5-turbo  # or gpt-4o

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password

# Database Path
DB_PATH=data/coldmailer.db
```

### 3. Usage
Run the main entry point to access the interactive CLI:
```bash
python main.py
```
- **Option 1**: Start the search and audit pipeline.
- **Option 2**: Review leads and send personalized proposals.
- **Option 3**: (New) Data is auto-exported, but you can manually trigger CSV exports here.

---

## 🛡 Safety & Best Practices
- **Rate Limiting**: The system includes random delays and human-like scrolling to avoid detection.
- **Volume**: 
    - **Email**: Recommended 50-200/day per account.
    - **WhatsApp**: Recommended under 100/day to stay within safe automation limits.
- **Human-in-the-loop**: Use the **Proposal Preview** feature to ensure quality before sending.

---

## 🚀 Future Roadmap & Enhancements

1. **Multi-Source Scraping**: Integration with Yelp, LinkedIn, and Apollo.io APIs.
2. **CRM Sync**: Native connectors for HubSpot, Pipedrive, and Salesforce.
3. **Sentiment Analysis**: Automatic categorization of lead replies as "Interested", "Referred", or "Negative".
4. **Proxy Support**: Native support for rotating residential proxies for high-volume scraping.
5. **Campaign Sequences**: Multi-step follow-up cadences (e.g., Email -> WhatsApp -> LinkedIn).
6. **Web Dashboard**: A full-stack React/Next.js dashboard for visualizing conversion rates and ROI.

---

*Built with ❤️ for High-Tech Outreach Teams.*
