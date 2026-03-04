<div align="center">

# 📺 YT Channel Downloader

**Automatically download all videos from YouTube channels — with a clean web UI and Docker support.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)](Dockerfile)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776ab?logo=python&logoColor=white)](requirements.txt)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red?logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)

<img width="1180" height="839" alt="youtube" src="https://github.com/user-attachments/assets/4d1726fd-0be9-4cd5-b047-cd481215e9e5" />


*Self-hosted YouTube channel archiver with Plex/Jellyfin/Emby integration*

</div>

---

## ✨ Features

- **Add YouTube channels** by URL, handle, or playlist
- **Auto-downloads all existing videos** when a channel is added
- **Playlist support** — download entire YouTube playlists, not just channels
- **Date range filter** — download only videos from the last 1, 2, 3, or 5 years, or set a custom cutoff date
- **Checks for new videos** on a configurable schedule (default: every 30 min)
- **Custom download paths** per channel
- **Pause/resume** channels
- **Manual scan** per channel or all at once
- **Video status tracking** — downloaded, downloading, pending, failed
- **Live download progress** via WebSocket — see real-time download status in the UI
- **Discord & Telegram notifications** — get notified when new videos are downloaded
- **Plex-ready** — embeds upload date metadata and date-prefixed filenames for proper sorting
- **Health check endpoint** for monitoring and orchestration
- Dark/light mode responsive web UI
- **Multi-arch Docker images** — runs on x86_64, ARM64 (Raspberry Pi, Synology NAS)

## Prerequisites — Installing Docker

### Windows

1. Download [Docker Desktop](https://www.docker.com/products/docker-desktop/) and run the installer.
2. During setup, enable **WSL 2** when prompted.
3. Restart your computer.
4. Open Docker Desktop and wait for it to finish starting.
5. Verify in a terminal:
   ```bash
   docker --version
   docker-compose --version
   ```

### Synology NAS (DSM 7)

1. Open **Package Center** in DSM.
2. Search for **Container Manager** (or **Docker** on older DSM versions) and install it.
3. SSH into the NAS:
   ```bash
   ssh your-user@your-nas-ip
   ```
4. Verify Docker is available:
   ```bash
   sudo docker --version
   sudo docker-compose --version
   ```
   If `docker-compose` is not found, install it:
   ```bash
   sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
     -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

### Linux (Debian / Ubuntu)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add your user to the docker group (no sudo needed for docker commands)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose-plugin

# Verify
docker --version
docker compose version
```

Log out and back in for the group change to take effect.

## Quick Start

```bash
docker-compose up -d --build
```

Then open **http://localhost:7842** in your browser.

### Synology NAS Setup

Before deploying on a Synology NAS, SSH into the NAS and create the required directories:

```bash
sudo mkdir -p /volume1/docker/yt-downloader/data
sudo mkdir -p /volume1/hdd/youtube
```

Then uncomment the Synology volume paths in `docker-compose.yml` and comment out the Windows paths.

## Configuration

Environment variables (set in `docker-compose.yml`):

| Variable | Default | Description |
|---|---|---|
| `DOWNLOAD_DIR` | `/downloads` | Default base directory for downloads |
| `CHECK_INTERVAL_MINUTES` | `30` | How often to check channels for new videos |
| `COOKIES_FILE` | `/app/data/cookies.txt` | Path to Netscape-format cookies file for YouTube authentication |
| `DISCORD_WEBHOOK_URL` | *(empty)* | Discord webhook URL for download notifications |
| `TELEGRAM_BOT_TOKEN` | *(empty)* | Telegram bot token for notifications |
| `TELEGRAM_CHAT_ID` | *(empty)* | Telegram chat ID to send notifications to |

## YouTube Cookies (Bot Detection Fix)

If you see the error **"Sign in to confirm you're not a bot"**, you need to provide YouTube cookies:

1. Install a browser extension to export cookies in **Netscape format**:
   - Chrome: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. Log in to YouTube in your browser.
3. Use the extension to export cookies for `youtube.com` — save the file as `cookies.txt`.
4. Upload the file via the **web UI** — click the **"Upload cookies.txt"** button at the top of the page.

The app will automatically detect and use the cookies file. If the file is missing, it runs without cookies.

> **Note:** YouTube cookies expire periodically. If downloads start failing again, re-export and re-upload fresh cookies via the web UI.

## Date Range Filter

By default, all videos from a channel are downloaded. You can limit this per channel:

| Filter | Effect |
|---|---|
| **All time** | Download every video (default) |
| **Last 1 year** | Videos uploaded in the past 12 months |
| **Last 2 years** | Videos uploaded in the past 2 years |
| **Last 3 years** | Videos uploaded in the past 3 years |
| **Last 5 years** | Videos uploaded in the past 5 years |
| **Custom** | Enter a specific `YYYY-MM-DD` cutoff date |

- Set the filter when adding a channel, or change it anytime from the channel card dropdown.
- The filter applies during scanning — videos older than the cutoff are skipped entirely.
- Changing the filter does **not** remove already-downloaded videos.

## Volumes

| Host Path | Container Path | Purpose |
|---|---|---|
| `./downloads` | `/downloads` | Downloaded videos |
| `./data` | `/app/data` | SQLite database (persisted) |

You can change the host-side paths in `docker-compose.yml` to save videos wherever you want on your system.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/channels` | List all channels with stats |
| `POST` | `/api/channels` | Add a channel (`{url, download_path?, date_filter?}`) |
| `PATCH` | `/api/channels/:id` | Update channel (`{download_path?, enabled?, date_filter?}`) |
| `DELETE` | `/api/channels/:id` | Remove a channel |
| `GET` | `/api/channels/:id/videos` | List videos (`?status=` filter) |
| `POST` | `/api/channels/:id/scan` | Manually scan a channel |
| `POST` | `/api/scan-all` | Scan all channels |
| `GET` | `/api/settings` | Get current settings |
| `GET` | `/api/health` | Health check (status, uptime, version) |
| `GET` | `/api/cookies/status` | Check if cookies file exists |
| `POST` | `/api/cookies/upload` | Upload a cookies.txt file |
| `DELETE` | `/api/cookies` | Remove the cookies file |
| `WS` | `/ws/progress` | WebSocket for live download progress |

## Notifications

Get notified when new videos are downloaded.

### Discord

1. In your Discord server, go to **Server Settings → Integrations → Webhooks**.
2. Click **New Webhook**, choose a channel, and copy the webhook URL.
3. Set the `DISCORD_WEBHOOK_URL` environment variable in `docker-compose.yml`.

### Telegram

1. Message [@BotFather](https://t.me/BotFather) on Telegram and create a new bot.
2. Copy the bot token.
3. Send a message to your bot, then get your chat ID from `https://api.telegram.org/bot<TOKEN>/getUpdates`.
4. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `docker-compose.yml`.

## Health Check

The `/api/health` endpoint returns the application status:

```json
{
  "status": "healthy",
  "uptime": "2d 5h 30m",
  "version": "1.0.0",
  "channels": 5,
  "total_videos": 342,
  "downloaded_videos": 338
}
```

Use this with Docker health checks, Uptime Kuma, or any monitoring system.

## Tech Stack

- **Backend:** Python / FastAPI
- **Downloader:** yt-dlp
- **Database:** SQLite (via aiosqlite)
- **Scheduler:** APScheduler
- **Container:** Docker (multi-arch: amd64, arm64)
- **Real-time:** WebSocket for live progress

## Comparison with Alternatives

| Feature | YT Channel Downloader | TubeSync | YoutubeDL-Material |
|---|---|---|---|
| One-command setup | ✅ | ✅ | ✅ |
| Single Docker container | ✅ | ❌ (needs Redis) | ❌ (needs Mongo) |
| Date range filter | ✅ | ❌ | ❌ |
| Plex metadata embedding | ✅ | ✅ | ❌ |
| Playlist support | ✅ | ❌ | ✅ |
| Discord/Telegram notifications | ✅ | ❌ | ❌ |
| Live download progress | ✅ | ❌ | ✅ |
| Cookie management UI | ✅ | ❌ | ❌ |
| ARM64 / Raspberry Pi | ✅ | ✅ | ✅ |
| Resource usage | ~50 MB RAM | ~300 MB | ~400 MB |

## Plex Integration

Videos are downloaded with embedded metadata and date-prefixed filenames (e.g. `2025-03-15 - Video Title [id].mp4`), making them easy to sort by date in Plex.

### Setup

1. In Plex, go to **Settings → Manage → Libraries** and click **Add Library**.
2. Select **Other Videos** as the library type.
3. Point the library folder to your download directory (e.g. `/volume1/hdd/youtube` or the relevant subfolder per channel).
4. Under **Advanced**, set the agent to **Personal Media** or **Personal Media Shows**.
5. Once the library is created, click the channel folder → **Sort by** → **Date** (or **Originally Available**) to sort videos chronologically by their YouTube upload date.

### How It Works

- The `FFmpegMetadata` postprocessor embeds the YouTube upload date into each MP4 file's metadata. Plex reads this as the **Originally Available** date.
- Filenames are prefixed with the upload date (`YYYY-MM-DD`), so videos also sort correctly in any file browser.

> **Note:** Only newly downloaded videos include the embedded metadata and date prefix. To re-process existing videos, delete them and their entries from the download archive (`.yt-dlp-archive.txt` inside each channel folder), then trigger a re-scan.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**If you find this useful, please ⭐ star the repo — it helps others discover it!**

</div>
