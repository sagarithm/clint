import aiosqlite
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from core.config import settings
from core.logger import logger
from core.migrations import run_migrations


async def _column_exists(db: aiosqlite.Connection, table: str, column: str) -> bool:
    async with db.execute(f"PRAGMA table_info({table})") as cursor:
        columns = await cursor.fetchall()
    return any(col[1] == column for col in columns)

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
    Initializes SQLite for both v1 runtime compatibility and v2 backbone tables.
    Uses additive migrations so existing local databases continue to work.
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
                lifecycle_state TEXT DEFAULT 'new',
                state_updated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Additive upgrades for already-initialized databases.
        if not await _column_exists(db, "leads", "lifecycle_state"):
            await db.execute("ALTER TABLE leads ADD COLUMN lifecycle_state TEXT DEFAULT 'new'")
        if not await _column_exists(db, "leads", "state_updated_at"):
            await db.execute("ALTER TABLE leads ADD COLUMN state_updated_at TIMESTAMP")

        # Keep lifecycle_state in sync for old records that predate v2 fields.
        await db.execute(
            """
            UPDATE leads
            SET lifecycle_state = COALESCE(NULLIF(lifecycle_state, ''), status, 'new')
            WHERE lifecycle_state IS NULL OR lifecycle_state = ''
            """
        )
        
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
        await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_lifecycle_state ON leads (lifecycle_state)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_category ON leads (category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads (email)")

        # V2 Backbone: source and evidence provenance.
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                source_platform TEXT NOT NULL,
                source_record_id TEXT,
                source_url TEXT,
                discovered_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_payload_json TEXT,
                adapter_version TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                evidence_type TEXT NOT NULL,
                evidence_text TEXT,
                evidence_value TEXT,
                evidence_confidence REAL DEFAULT 0,
                captured_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_enrichment_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                snapshot_version TEXT DEFAULT 'v2',
                website_summary TEXT,
                rating REAL DEFAULT 0,
                reviews_count INTEGER DEFAULT 0,
                social_links_json TEXT,
                contact_confidence REAL DEFAULT 0,
                enriched_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                fit_score REAL DEFAULT 0,
                intent_score REAL DEFAULT 0,
                authority_score REAL DEFAULT 0,
                timing_score REAL DEFAULT 0,
                risk_score REAL DEFAULT 0,
                priority_score REAL DEFAULT 0,
                reason_codes_json TEXT,
                scored_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """
        )

        # V2 Backbone: messaging and event lineage.
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS message_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                channel TEXT NOT NULL,
                template_id TEXT,
                prompt_version TEXT,
                subject TEXT,
                body TEXT,
                quality_score REAL DEFAULT 0,
                rejection_reason TEXT,
                correlation_id TEXT,
                created_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS outreach_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                channel TEXT,
                event_type TEXT NOT NULL,
                event_payload_json TEXT,
                correlation_id TEXT,
                occurred_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reply_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                channel TEXT,
                thread_ref TEXT,
                reply_text TEXT,
                classifier_label TEXT,
                classifier_confidence REAL DEFAULT 0,
                requires_human_review INTEGER DEFAULT 0,
                occurred_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """
        )

        # V2 Backbone: policy and state governance.
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS suppression_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_key TEXT NOT NULL,
                suppression_type TEXT NOT NULL,
                reason TEXT,
                source TEXT,
                created_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS compliance_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                check_name TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason TEXT,
                checked_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_state_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                from_state TEXT,
                to_state TEXT NOT NULL,
                reason TEXT,
                actor TEXT,
                occurred_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS connector_rejections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_platform TEXT NOT NULL,
                reason_code TEXT NOT NULL,
                reason_detail TEXT,
                raw_payload_json TEXT,
                occurred_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hypothesis TEXT,
                segment TEXT,
                metric_key TEXT NOT NULL,
                status TEXT DEFAULT 'planned',
                variant_a TEXT,
                variant_b TEXT,
                start_at_utc TIMESTAMP,
                end_at_utc TIMESTAMP,
                winner_variant TEXT,
                decision_note TEXT,
                created_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS experiment_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                variant TEXT NOT NULL,
                sample_size INTEGER DEFAULT 0,
                metric_value REAL DEFAULT 0,
                quality_impact REAL DEFAULT 0,
                recorded_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS deadletter_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                channel TEXT,
                topic TEXT NOT NULL,
                error_message TEXT,
                payload_json TEXT,
                replay_attempts INTEGER DEFAULT 0,
                replay_status TEXT DEFAULT 'pending',
                replayed_at_utc TIMESTAMP,
                replay_note TEXT,
                created_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
            """
        )

        if not await _column_exists(db, "deadletter_events", "replay_attempts"):
            await db.execute("ALTER TABLE deadletter_events ADD COLUMN replay_attempts INTEGER DEFAULT 0")
        if not await _column_exists(db, "deadletter_events", "replay_status"):
            await db.execute("ALTER TABLE deadletter_events ADD COLUMN replay_status TEXT DEFAULT 'pending'")
        if not await _column_exists(db, "deadletter_events", "replayed_at_utc"):
            await db.execute("ALTER TABLE deadletter_events ADD COLUMN replayed_at_utc TIMESTAMP")
        if not await _column_exists(db, "deadletter_events", "replay_note"):
            await db.execute("ALTER TABLE deadletter_events ADD COLUMN replay_note TEXT")

        # Backbone indexes.
        await db.execute("CREATE INDEX IF NOT EXISTS idx_lead_sources_platform_time ON lead_sources (source_platform, discovered_at_utc)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_lead_scores_priority ON lead_scores (priority_score)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_outreach_events_type_time ON outreach_events (event_type, occurred_at_utc)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_reply_events_label_time ON reply_events (classifier_label, occurred_at_utc)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_suppression_contact_key ON suppression_entries (contact_key)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_lead_state_transitions_lead_time ON lead_state_transitions (lead_id, occurred_at_utc)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_connector_rejections_platform_time ON connector_rejections (source_platform, occurred_at_utc)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_experiments_status_time ON experiments (status, created_at_utc)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_experiment_observations_exp_time ON experiment_observations (experiment_id, recorded_at_utc)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_deadletter_events_topic_time ON deadletter_events (topic, created_at_utc)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_deadletter_events_replay_status ON deadletter_events (replay_status, created_at_utc)")

        await db.commit()
        
        # Run advanced deterministic migrations
        await run_migrations(db)
        
    logger.info("Database initialization successful.")

if __name__ == "__main__":
    asyncio.run(init_db())
