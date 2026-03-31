import aiosqlite
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from core.config import settings
from core.logger import logger

@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    A context manager that provides a clean, asynchronous connection to the database.
    Ensures row_factory is set to Row for dictionary-like access.
    """
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

async def init_db() -> None:
    """
    Initializes the SQLite database with the required schema.
    Indexes are added to critical columns for high-performance lookups.
    """
    async with aiosqlite.connect(settings.DB_PATH) as db:
        logger.info(f"Initializing database at: {settings.DB_PATH}")
        
        # 1. Leads Table: Core storage for business prospects
        await db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                website TEXT,
                phone TEXT,
                address TEXT,
                rating REAL DEFAULT 0.0,
                reviews_count INTEGER DEFAULT 0,
                business_category TEXT,
                screenshot_path TEXT,
                about_us_info TEXT,
                source TEXT,
                category TEXT,
                email TEXT,
                social_links TEXT,
                score INTEGER DEFAULT 0,
                outreach_step INTEGER DEFAULT 0,
                last_outreach TIMESTAMP,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Outreach History: Tracks every message sent for auditability
        await db.execute("""
            CREATE TABLE IF NOT EXISTS outreach_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                channel TEXT,
                content TEXT,
                status TEXT,
                error_message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        """)

        # 3. Daily Stats: Enforces daily sending limits
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                emails_sent INTEGER DEFAULT 0,
                whatsapp_sent INTEGER DEFAULT 0
            )
        """)

        # Performance Architecture: Indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads (status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_category ON leads (category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads (email)")

        await db.commit()
    logger.info("Database initialization successful.")

if __name__ == "__main__":
    asyncio.run(init_db())
