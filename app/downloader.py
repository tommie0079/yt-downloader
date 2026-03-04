import os
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

import yt_dlp

from app.database import get_db

logger = logging.getLogger(__name__)

DEFAULT_DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "/downloads")
COOKIES_FILE = os.environ.get("COOKIES_FILE", "/app/data/cookies.txt")


def _get_yt_dlp_opts(download_path: str, archive_file: str) -> dict:
    """Return yt-dlp options for downloading."""
    return {
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "merge_output_format": "mp4",
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            },
            {
                "key": "FFmpegMetadata",      # Embeds upload_date → Plex "Originally Available"
            },
        ],
        "outtmpl": os.path.join(download_path, "%(upload_date>%Y-%m-%d)s - %(title)s [%(id)s].%(ext)s"),
        "download_archive": archive_file,
        "ignoreerrors": True,
        "no_overwrites": True,
        "writeinfojson": False,
        "writethumbnail": False,
        "quiet": False,
        "no_warnings": False,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
        **({"cookiefile": COOKIES_FILE} if os.path.isfile(COOKIES_FILE) else {}),
    }


async def fetch_channel_info(url: str) -> dict | None:
    """Fetch channel name and metadata without downloading."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlist_items": "0",
        **({"cookiefile": COOKIES_FILE} if os.path.isfile(COOKIES_FILE) else {}),
    }

    def _extract():
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if info:
                    return {
                        "name": info.get("channel") or info.get("uploader") or info.get("title", "Unknown"),
                        "url": info.get("channel_url") or info.get("webpage_url") or url,
                    }
            except Exception as e:
                logger.error(f"Error fetching channel info for {url}: {e}")
        return None

    return await asyncio.to_thread(_extract)


def _parse_date_filter(date_filter: str) -> str | None:
    """Convert a date_filter value to a YYYYMMDD cutoff date string.

    Supported formats:
      ''          -> None  (all videos)
      '1y'        -> 1 year ago
      '2y'        -> 2 years ago
      '3y'        -> 3 years ago
      '5y'        -> 5 years ago
      'YYYY-MM-DD' -> exact date
    """
    if not date_filter:
        return None
    date_filter = date_filter.strip()
    if date_filter.endswith("y"):
        try:
            years = int(date_filter[:-1])
            cutoff = datetime.utcnow() - timedelta(days=years * 365)
            return cutoff.strftime("%Y%m%d")
        except ValueError:
            return None
    # Try parsing as YYYY-MM-DD
    try:
        cutoff = datetime.strptime(date_filter, "%Y-%m-%d")
        return cutoff.strftime("%Y%m%d")
    except ValueError:
        return None


async def fetch_channel_videos(url: str, date_filter: str = "") -> list[dict]:
    """Fetch all video IDs from a channel, optionally filtered by date."""
    # Use /videos tab to get only actual uploads
    channel_videos_url = url.rstrip("/") + "/videos"
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        **({"cookiefile": COOKIES_FILE} if os.path.isfile(COOKIES_FILE) else {}),
    }

    cutoff = _parse_date_filter(date_filter)

    def _extract():
        videos = []
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(channel_videos_url, download=False)
                if info and "entries" in info:
                    for entry in info["entries"]:
                        if not entry:
                            continue
                        vid_id = entry.get("id", "")
                        # Filter out non-video entries (channel IDs, playlist IDs, etc.)
                        if not vid_id or len(vid_id) != 11:
                            continue
                        # Apply date filter if set
                        if cutoff:
                            upload_date = entry.get("upload_date") or ""
                            if upload_date and upload_date < cutoff:
                                continue
                        videos.append({
                            "video_id": vid_id,
                            "title": entry.get("title", "Unknown"),
                        })
            except Exception as e:
                logger.error(f"Error fetching videos for {url}: {e}")
        return videos

    return await asyncio.to_thread(_extract)


async def download_video(video_id: str, download_path: str, archive_file: str) -> tuple[bool, str]:
    """Download a single video. Returns (success, error_message)."""
    Path(download_path).mkdir(parents=True, exist_ok=True)
    opts = _get_yt_dlp_opts(download_path, archive_file)
    # For individual downloads, don't ignore errors so we can detect failures
    opts["ignoreerrors"] = False
    url = f"https://www.youtube.com/watch?v={video_id}"

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                ret = ydl.download([url])
                # ret == 0 means success, 1 means error
                if ret != 0:
                    return False, f"yt-dlp returned error code {ret}"
                return True, ""
            except Exception as e:
                return False, str(e)

    return await asyncio.to_thread(_download)


async def process_channel(channel_id: int):
    """Discover new videos for a channel and download them."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM channels WHERE id = ? AND enabled = 1", (channel_id,))
        channel = await cursor.fetchone()
        if not channel:
            return

        channel_url = channel["url"]
        download_path = channel["download_path"]
        archive_file = os.path.join(download_path, ".yt-dlp-archive.txt")

        logger.info(f"Scanning channel: {channel['name']} ({channel_url})")

        # Fetch all videos from the channel (applying date filter)
        date_filter = channel["date_filter"] if "date_filter" in channel.keys() else ""
        videos = await fetch_channel_videos(channel_url, date_filter)
        logger.info(f"Found {len(videos)} videos for {channel['name']}" + (f" (filter: {date_filter})" if date_filter else ""))

        for video in videos:
            # Check if we already know about this video
            cursor = await db.execute(
                "SELECT id, status FROM videos WHERE video_id = ?", (video["video_id"],)
            )
            existing = await cursor.fetchone()

            if existing:
                # Skip already downloaded or currently downloading
                if existing["status"] in ("downloaded", "downloading"):
                    continue
                # Retry failed videos
                video_db_id = existing["id"]
            else:
                # Insert new video record
                cursor = await db.execute(
                    "INSERT INTO videos (channel_id, video_id, title, status) VALUES (?, ?, ?, 'pending')",
                    (channel_id, video["video_id"], video["title"]),
                )
                await db.commit()
                video_db_id = cursor.lastrowid

            # Mark as downloading
            await db.execute("UPDATE videos SET status = 'downloading' WHERE id = ?", (video_db_id,))
            await db.commit()

            # Download
            success, error = await download_video(video["video_id"], download_path, archive_file)

            if success:
                await db.execute(
                    "UPDATE videos SET status = 'downloaded', downloaded_at = ?, error_message = NULL WHERE id = ?",
                    (datetime.utcnow().isoformat(), video_db_id),
                )
            else:
                await db.execute(
                    "UPDATE videos SET status = 'failed', error_message = ? WHERE id = ?",
                    (error, video_db_id),
                )
            await db.commit()

        logger.info(f"Finished processing channel: {channel['name']}")
    finally:
        await db.close()
