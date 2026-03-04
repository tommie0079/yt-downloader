# YT Channel Downloader

Automatically download all videos from YouTube channels — with a clean web UI and Docker support.


<img width="1180" height="839" alt="youtube" src="https://github.com/user-attachments/assets/4d1726fd-0be9-4cd5-b047-cd481215e9e5" />




## Features

- **Add YouTube channels** by URL or handle (e.g. `@ChannelName`)
- **Auto-downloads all existing videos** when a channel is added
- **Date range filter** — download only videos from the last 1, 2, 3, or 5 years, or set a custom cutoff date
- **Checks for new videos** on a configurable schedule (default: every 30 min)
- **Custom download paths** per channel
- **Pause/resume** channels
- **Manual scan** per channel or all at once
- **Video status tracking** — downloaded, downloading, pending, failed
- **Plex-ready** — embeds upload date metadata and date-prefixed filenames for proper sorting
- Dark-themed responsive web UI

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

## Tech Stack

- **Backend:** Python / FastAPI
- **Downloader:** yt-dlp
- **Database:** SQLite (via aiosqlite)
- **Scheduler:** APScheduler
- **Container:** Docker

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
