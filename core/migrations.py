import aiosqlite
from core.logger import logger
from typing import Callable, List, Tuple
from contextlib import asynccontextmanager

# Define migrations as tuples of (version, up_script, down_script)
MIGRATIONS = [
    (
        "v2_001_initial_backbone",
        """
        -- Add any missing columns generically 
        ALTER TABLE deadletter_events ADD COLUMN replay_route TEXT DEFAULT 'default';
        """,
        """
        -- Down script 
        ALTER TABLE deadletter_events DROP COLUMN replay_route;
        """
    )
]

async def _init_migration_table(db: aiosqlite.Connection) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    await db.commit()

async def get_applied_migrations(db: aiosqlite.Connection) -> set[str]:
    await _init_migration_table(db)
    async with db.execute("SELECT version FROM schema_migrations") as cursor:
        rows = await cursor.fetchall()
    return {row[0] for row in rows}

async def run_migrations(db: aiosqlite.Connection) -> None:
    """Run all pending schema migrations."""
    applied = await get_applied_migrations(db)
    
    for version, up_sql, _ in MIGRATIONS:
        if version not in applied:
            logger.info(f"Applying migration {version}...")
            try:
                await db.executescript(up_sql)
                await db.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
                await db.commit()
                logger.info(f"Successfully applied {version}.")
            except Exception as e:
                logger.error(f"Migration {version} failed: {e}")
                await db.rollback()
                raise

async def rollback_migration(db: aiosqlite.Connection, version_to_rollback: str) -> None:
    """Deterministically roll back a specific migration."""
    applied = await get_applied_migrations(db)
    if version_to_rollback not in applied:
        logger.warning(f"Migration {version_to_rollback} is not applied. Skipping rollback.")
        return

    for version, _, down_sql in reversed(MIGRATIONS):
        if version == version_to_rollback:
            logger.info(f"Rolling back migration {version}...")
            try:
                await db.executescript(down_sql)
                await db.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
                await db.commit()
                logger.info(f"Successfully rolled back {version}.")
                return
            except Exception as e:
                logger.error(f"Rollback {version} failed: {e}")
                await db.rollback()
                raise
    
    logger.error(f"Migration {version_to_rollback} not found in defined MIGRATIONS.")
