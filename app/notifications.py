"""Notification support for Discord and Telegram webhooks."""

import os
import logging
import asyncio

import httpx

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def _is_discord_enabled() -> bool:
    return bool(DISCORD_WEBHOOK_URL)


def _is_telegram_enabled() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


async def send_discord(title: str, message: str, color: int = 0x4CAF50):
    """Send a Discord webhook notification."""
    if not _is_discord_enabled():
        return
    payload = {
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color,
            }
        ]
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if resp.status_code not in (200, 204):
                logger.warning(f"Discord webhook returned {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to send Discord notification: {e}")


async def send_telegram(title: str, message: str):
    """Send a Telegram bot notification."""
    if not _is_telegram_enabled():
        return
    text = f"<b>{title}</b>\n{message}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"Telegram API returned {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")


async def notify_download(channel_name: str, video_title: str, video_id: str):
    """Send download notification to all configured services."""
    title = "📺 New Video Downloaded"
    message = (
        f"**Channel:** {channel_name}\n"
        f"**Video:** {video_title}\n"
        f"**Link:** https://www.youtube.com/watch?v={video_id}"
    )
    telegram_message = (
        f"Channel: {channel_name}\n"
        f"Video: {video_title}\n"
        f"Link: https://www.youtube.com/watch?v={video_id}"
    )

    tasks = []
    if _is_discord_enabled():
        tasks.append(send_discord(title, message))
    if _is_telegram_enabled():
        tasks.append(send_telegram(title, telegram_message))
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def notify_error(channel_name: str, video_title: str, error: str):
    """Send error notification to all configured services."""
    title = "❌ Download Failed"
    message = (
        f"**Channel:** {channel_name}\n"
        f"**Video:** {video_title}\n"
        f"**Error:** {error}"
    )
    telegram_message = (
        f"Channel: {channel_name}\n"
        f"Video: {video_title}\n"
        f"Error: {error}"
    )

    tasks = []
    if _is_discord_enabled():
        tasks.append(send_discord(title, message, color=0xFF4444))
    if _is_telegram_enabled():
        tasks.append(send_telegram(title, telegram_message))
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
