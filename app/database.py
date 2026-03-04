import os
import aiosqlite
from pathlib import Path

DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/channels.db")


async def get_db() -> aiosqlite.Connection:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DATABASE_PATH, timeout=30)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA busy_timeout=10000")
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                download_path TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                date_filter TEXT NOT NULL DEFAULT '',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                video_id TEXT NOT NULL UNIQUE,
                title TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                downloaded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE
            );
        """)
        await db.commit()

        # ── Migrations ──────────────────────────────────────────
        # Add date_filter column if missing (existing databases)
        cursor = await db.execute("PRAGMA table_info(channels)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "date_filter" not in columns:
            await db.execute("ALTER TABLE channels ADD COLUMN date_filter TEXT NOT NULL DEFAULT ''")
            await db.commit()
    finally:
        await db.close()
