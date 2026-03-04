import os
import logging
import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from app.database import init_db, get_db
from app.downloader import fetch_channel_info, process_channel, COOKIES_FILE, register_ws, unregister_ws
from app.scheduler import start_scheduler, stop_scheduler, check_all_channels

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "/downloads")
APP_VERSION = "1.0.0"
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="YT Channel Downloader", lifespan=lifespan)


# ── Models ──────────────────────────────────────────────

class AddChannelRequest(BaseModel):
    url: str
    download_path: str | None = None
    date_filter: str | None = None


class UpdateChannelRequest(BaseModel):
    download_path: str | None = None
    enabled: bool | None = None
    date_filter: str | None = None


# ── API Routes ──────────────────────────────────────────

@app.get("/api/channels")
async def list_channels():
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT c.*, "
            "COALESCE(v.total_videos, 0) AS total_videos, "
            "COALESCE(v.downloaded_videos, 0) AS downloaded_videos, "
            "COALESCE(v.downloading_videos, 0) AS downloading_videos, "
            "COALESCE(v.pending_videos, 0) AS pending_videos, "
            "COALESCE(v.failed_videos, 0) AS failed_videos "
            "FROM channels c "
            "LEFT JOIN ("
            "  SELECT channel_id, "
            "    COUNT(*) AS total_videos, "
            "    SUM(CASE WHEN status = 'downloaded' THEN 1 ELSE 0 END) AS downloaded_videos, "
            "    SUM(CASE WHEN status = 'downloading' THEN 1 ELSE 0 END) AS downloading_videos, "
            "    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_videos, "
            "    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_videos "
            "  FROM videos GROUP BY channel_id"
            ") v ON v.channel_id = c.id "
            "ORDER BY c.added_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.exception("Error listing channels")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await db.close()


@app.post("/api/channels")
async def add_channel(req: AddChannelRequest):
    # Normalize channel URL
    url = req.url.strip()
    if not url.startswith("http"):
        url = f"https://www.youtube.com/@{url}"

    # Fetch channel info
    info = await fetch_channel_info(url)
    if not info:
        raise HTTPException(status_code=400, detail="Could not find a YouTube channel at that URL.")

    download_path = req.download_path or os.path.join(DEFAULT_DOWNLOAD_DIR, info["name"])

    db = await get_db()
    try:
        # Check duplicate
        cursor = await db.execute("SELECT id FROM channels WHERE url = ?", (info["url"],))
        if await cursor.fetchone():
            raise HTTPException(status_code=409, detail="Channel already added.")

        date_filter = req.date_filter or ""
        cursor = await db.execute(
            "INSERT INTO channels (name, url, download_path, date_filter) VALUES (?, ?, ?, ?)",
            (info["name"], info["url"], download_path, date_filter),
        )
        await db.commit()
        channel_id = cursor.lastrowid
    finally:
        await db.close()

    # Kick off initial download in background
    asyncio.create_task(process_channel(channel_id))

    return {"id": channel_id, "name": info["name"], "url": info["url"], "download_path": download_path, "date_filter": date_filter}


@app.patch("/api/channels/{channel_id}")
async def update_channel(channel_id: int, req: UpdateChannelRequest):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM channels WHERE id = ?", (channel_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Channel not found")

        if req.download_path is not None:
            await db.execute("UPDATE channels SET download_path = ? WHERE id = ?", (req.download_path, channel_id))
        if req.enabled is not None:
            await db.execute("UPDATE channels SET enabled = ? WHERE id = ?", (int(req.enabled), channel_id))
        if req.date_filter is not None:
            await db.execute("UPDATE channels SET date_filter = ? WHERE id = ?", (req.date_filter, channel_id))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@app.delete("/api/channels/{channel_id}")
async def delete_channel(channel_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM channels WHERE id = ?", (channel_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Channel not found")
        await db.execute("DELETE FROM videos WHERE channel_id = ?", (channel_id,))
        await db.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@app.get("/api/channels/{channel_id}/videos")
async def list_videos(channel_id: int, status: str | None = None):
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                "SELECT * FROM videos WHERE channel_id = ? AND status = ? ORDER BY created_at DESC",
                (channel_id, status),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM videos WHERE channel_id = ? ORDER BY created_at DESC",
                (channel_id,),
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


@app.post("/api/channels/{channel_id}/scan")
async def scan_channel(channel_id: int):
    """Manually trigger a scan + download for a channel."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM channels WHERE id = ?", (channel_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Channel not found")
    finally:
        await db.close()

    asyncio.create_task(process_channel(channel_id))
    return {"ok": True, "message": "Scan started in background"}


@app.post("/api/scan-all")
async def scan_all():
    """Manually trigger a scan of all channels."""
    asyncio.create_task(check_all_channels())
    return {"ok": True, "message": "Full scan started in background"}


@app.get("/api/settings")
async def get_settings():
    return {
        "default_download_dir": DEFAULT_DOWNLOAD_DIR,
        "check_interval_minutes": int(os.environ.get("CHECK_INTERVAL_MINUTES", "30")),
    }


# ── Health Check ───────────────────────────────────────

def _format_uptime(seconds: float) -> str:
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    uptime = time.time() - _start_time
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM channels")
        channels_count = (await cursor.fetchone())["cnt"]
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM videos")
        total_videos = (await cursor.fetchone())["cnt"]
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM videos WHERE status = 'downloaded'")
        downloaded_videos = (await cursor.fetchone())["cnt"]
    finally:
        await db.close()

    return {
        "status": "healthy",
        "uptime": _format_uptime(uptime),
        "version": APP_VERSION,
        "channels": channels_count,
        "total_videos": total_videos,
        "downloaded_videos": downloaded_videos,
    }


# ── WebSocket Progress ─────────────────────────────────

@app.websocket("/ws/progress")
async def websocket_progress(ws: WebSocket):
    """WebSocket endpoint for live download progress updates."""
    await ws.accept()
    register_ws(ws)
    try:
        while True:
            # Keep connection alive, wait for client messages (ping/pong)
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        unregister_ws(ws)


# ── Cookie Management ──────────────────────────────────

@app.get("/api/cookies/status")
async def cookies_status():
    """Check if a cookies file exists and return basic info."""
    cookie_path = Path(COOKIES_FILE)
    if cookie_path.is_file():
        stat = cookie_path.stat()
        return {
            "exists": True,
            "size": stat.st_size,
            "modified": stat.st_mtime,
        }
    return {"exists": False}


@app.post("/api/cookies/upload")
async def upload_cookies(file: UploadFile = File(...)):
    """Upload a Netscape-format cookies.txt file."""
    content = await file.read()

    # Basic validation: check it looks like a Netscape cookie file
    text = content.decode("utf-8", errors="replace")
    lines = text.strip().splitlines()
    if not lines:
        raise HTTPException(status_code=400, detail="Empty file")

    # Check for tab-separated cookie lines
    has_cookies = any(line.strip() and not line.startswith("#") and "\t" in line for line in lines)

    if not has_cookies:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Please export cookies in Netscape/cookies.txt format."
        )

    # Write the raw bytes to preserve tabs and encoding exactly
    cookie_path = Path(COOKIES_FILE)
    cookie_path.parent.mkdir(parents=True, exist_ok=True)
    cookie_path.write_bytes(content)

    return {"ok": True, "message": "Cookies uploaded successfully", "size": len(content)}


@app.delete("/api/cookies")
async def delete_cookies():
    """Remove the cookies file."""
    cookie_path = Path(COOKIES_FILE)
    if cookie_path.is_file():
        cookie_path.unlink()
        return {"ok": True, "message": "Cookies deleted"}
    raise HTTPException(status_code=404, detail="No cookies file found")


# ── Serve Frontend ─────────────────────────────────────

@app.get("/favicon.ico")
async def favicon():
    return Response(content=b"", media_type="image/x-icon", status_code=204)


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(os.path.dirname(__file__), "static", "index.html")) as f:
        return f.read()
