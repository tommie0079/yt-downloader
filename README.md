# YT Channel Downloader

Automatically download all videos from YouTube channels — with a clean web UI and Docker 


## Features

- **Add YouTube channels** by URL or handle (e.g. `@ChannelName`)
- **Auto-downloads all existing videos** when a channel is added
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
| `POST` | `/api/channels` | Add a channel (`{url, download_path?}`) |
| `PATCH` | `/api/channels/:id` | Update channel (`{download_path?, enabled?}`) |
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
