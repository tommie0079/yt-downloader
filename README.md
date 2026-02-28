# YT Channel Downloader

Automatically download all videos from YouTube channels — with a clean web UI and Docker support.

## Features

- **Add YouTube channels** by URL or handle (e.g. `@ChannelName`)
- **Auto-downloads all existing videos** when a channel is added
- **Checks for new videos** on a configurable schedule (default: every 30 min)
- **Custom download paths** per channel
- **Pause/resume** channels
- **Manual scan** per channel or all at once
- **Video status tracking** — downloaded, downloading, pending, failed
- Dark-themed responsive web UI

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
