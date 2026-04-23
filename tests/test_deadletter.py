from pathlib import Path
import sys
import asyncio

import aiosqlite

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.deadletter import replay_deadletter_event


class _ReplayHandler:
    def __init__(self):
        self.calls = []

    async def replay_reddit_raw_record(self, raw_record):
        self.calls.append(("reddit_raw", raw_record))
        return {"route": "reddit_raw"}

    async def replay_upwork_raw_record(self, raw_record):
        self.calls.append(("upwork_raw", raw_record))
        return {"route": "upwork_raw"}

    async def replay_fiverr_raw_record(self, raw_record):
        self.calls.append(("fiverr_raw", raw_record))
        return {"route": "fiverr_raw"}

    async def replay_linkedin_raw_record(self, raw_record):
        self.calls.append(("linkedin_raw", raw_record))
        return {"route": "linkedin_raw"}

    async def replay_x_threads_raw_record(self, raw_record):
        self.calls.append(("x_threads_raw", raw_record))
        return {"route": "x_threads_raw"}

    async def replay_enrich_stage(self, *, lead_id, source):
        self.calls.append(("enrich", lead_id, source))
        return {"route": "enrich", "lead_id": lead_id}

    async def replay_draft_stage(self, *, lead_id, source):
        self.calls.append(("draft", lead_id, source))
        return {"route": "draft", "lead_id": lead_id}

    async def replay_dispatch_stage(self, *, lead_id, source, live_send):
        self.calls.append(("dispatch", lead_id, source, live_send))
        return {"route": "dispatch", "lead_id": lead_id, "live_send": live_send}


async def _setup_db(db):
    await db.execute(
        """
        CREATE TABLE deadletter_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            channel TEXT,
            lead_id INTEGER,
            payload_json TEXT,
            replay_attempts INTEGER DEFAULT 0,
            replay_status TEXT DEFAULT 'pending',
            replay_note TEXT,
            replayed_at_utc TEXT,
            created_at_utc TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    await db.commit()


def test_replay_routes_upwork_raw_payload():
    async def _run():
        handler = _ReplayHandler()
        async with aiosqlite.connect(":memory:") as db:
            db.row_factory = aiosqlite.Row
            await _setup_db(db)
            await db.execute(
                "INSERT INTO deadletter_events(topic, payload_json) VALUES(?, ?)",
                ("events.deadletter", '{"source_platform":"upwork","source_record_id":"u-1"}'),
            )
            await db.commit()

            result = await replay_deadletter_event(db, event_id=1, replay_handler=handler)
            await db.commit()

        assert result["status"] == "replayed"
        assert result["replay_result"]["route"] == "upwork_raw"
        assert handler.calls[0][0] == "upwork_raw"

    asyncio.run(_run())


def test_replay_routes_fiverr_raw_payload():
    async def _run():
        handler = _ReplayHandler()
        async with aiosqlite.connect(":memory:") as db:
            db.row_factory = aiosqlite.Row
            await _setup_db(db)
            await db.execute(
                "INSERT INTO deadletter_events(topic, payload_json) VALUES(?, ?)",
                ("events.deadletter", '{"source_platform":"fiverr","source_record_id":"f-1"}'),
            )
            await db.commit()

            result = await replay_deadletter_event(db, event_id=1, replay_handler=handler)
            await db.commit()

        assert result["status"] == "replayed"
        assert result["replay_result"]["route"] == "fiverr_raw"
        assert handler.calls[0][0] == "fiverr_raw"

    asyncio.run(_run())


def test_replay_routes_linkedin_raw_payload():
    async def _run():
        handler = _ReplayHandler()
        async with aiosqlite.connect(":memory:") as db:
            db.row_factory = aiosqlite.Row
            await _setup_db(db)
            await db.execute(
                "INSERT INTO deadletter_events(topic, payload_json) VALUES(?, ?)",
                ("events.deadletter", '{"source_platform":"linkedin","source_record_id":"li-1"}'),
            )
            await db.commit()

            result = await replay_deadletter_event(db, event_id=1, replay_handler=handler)
            await db.commit()

        assert result["status"] == "replayed"
        assert result["replay_result"]["route"] == "linkedin_raw"
        assert handler.calls[0][0] == "linkedin_raw"

    asyncio.run(_run())


def test_replay_routes_x_threads_raw_payload():
    async def _run():
        handler = _ReplayHandler()
        async with aiosqlite.connect(":memory:") as db:
            db.row_factory = aiosqlite.Row
            await _setup_db(db)
            await db.execute(
                "INSERT INTO deadletter_events(topic, payload_json) VALUES(?, ?)",
                ("events.deadletter", '{"source_platform":"x_threads","source_record_id":"x-1"}'),
            )
            await db.commit()

            result = await replay_deadletter_event(db, event_id=1, replay_handler=handler)
            await db.commit()

        assert result["status"] == "replayed"
        assert result["replay_result"]["route"] == "x_threads_raw"
        assert handler.calls[0][0] == "x_threads_raw"

    asyncio.run(_run())


def test_replay_routes_stage_dispatch_as_dry_run():
    async def _run():
        handler = _ReplayHandler()
        async with aiosqlite.connect(":memory:") as db:
            db.row_factory = aiosqlite.Row
            await _setup_db(db)
            await db.execute(
                "INSERT INTO deadletter_events(topic, channel, lead_id, payload_json) VALUES(?, ?, ?, ?)",
                (
                    "events.deadletter",
                    "email",
                    44,
                    '{"stage":"dispatch","source":"upwork_pipeline"}',
                ),
            )
            await db.commit()

            result = await replay_deadletter_event(db, event_id=1, replay_handler=handler)
            await db.commit()

        assert result["status"] == "replayed"
        assert result["replay_result"]["route"] == "dispatch"
        assert handler.calls[0] == ("dispatch", 44, "upwork_pipeline", False)

    asyncio.run(_run())


def test_replay_without_payload_marked_unsupported():
    async def _run():
        handler = _ReplayHandler()
        async with aiosqlite.connect(":memory:") as db:
            db.row_factory = aiosqlite.Row
            await _setup_db(db)
            await db.execute(
                "INSERT INTO deadletter_events(topic, payload_json) VALUES(?, ?)",
                ("events.deadletter", None),
            )
            await db.commit()

            result = await replay_deadletter_event(db, event_id=1, replay_handler=handler)
            await db.commit()

            async with db.execute("SELECT replay_status FROM deadletter_events WHERE id = 1") as cursor:
                row = await cursor.fetchone()

        assert result["status"] == "unsupported"
        assert row["replay_status"] == "unsupported"

    asyncio.run(_run())
