import os
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import get_db
from app.downloader import process_channel

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_processing_lock = asyncio.Lock()


async def check_all_channels():
    """Check all enabled channels for new videos."""
    if _processing_lock.locked():
        logger.info("Previous scan still running, skipping this cycle")
        return

    async with _processing_lock:
        logger.info("Starting scheduled scan of all channels...")
        db = await get_db()
        try:
            cursor = await db.execute("SELECT id, name FROM channels WHERE enabled = 1")
            channels = await cursor.fetchall()
            for channel in channels:
                try:
                    logger.info(f"Processing channel: {channel['name']}")
                    await process_channel(channel["id"])
                except Exception as e:
                    logger.error(f"Error processing channel {channel['name']}: {e}")
            logger.info("Scheduled scan complete.")
        finally:
            await db.close()


def start_scheduler():
    """Start the background scheduler."""
    interval = int(os.environ.get("CHECK_INTERVAL_MINUTES", "30"))
    scheduler.add_job(
        check_all_channels,
        "interval",
        minutes=interval,
        id="check_channels",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — checking every {interval} minutes")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
