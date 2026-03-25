import aiosqlite
import asyncio
from core.config import settings

async def init_db():
    async with aiosqlite.connect(settings.DB_PATH) as db:
        # Leads Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                website TEXT,
                phone TEXT,
                address TEXT,
                rating REAL,
                reviews_count INTEGER,
                business_category TEXT,
                screenshot_path TEXT,
                about_us_info TEXT,
                source TEXT,
                category TEXT,
                email TEXT,
                social_links TEXT,
                audit_summary TEXT,
                score INTEGER,
                outreach_step INTEGER DEFAULT 0, -- 0: never contacted, 1: first outreach, 2: follow-up...
                last_outreach TIMESTAMP,
                status TEXT DEFAULT 'new', -- new, audit_pending, draft_ready, pending_review, approved, sent, failed
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Outreach History Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS outreach_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                channel TEXT, -- email, whatsapp
                content TEXT,
                status TEXT,
                error_message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        """)

        # Daily Limits Tracker
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                emails_sent INTEGER DEFAULT 0,
                whatsapp_sent INTEGER DEFAULT 0
            )
        """)

        await db.commit()

if __name__ == "__main__":
    asyncio.run(init_db())
