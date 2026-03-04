# Contributing to YT Channel Downloader

Thanks for your interest in contributing! Here's how you can help.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/yt-downloader.git
   cd yt-downloader
   ```
3. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/my-feature
   ```

## Development Setup

### Running Locally (without Docker)

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn app.main:app --host 0.0.0.0 --port 7842 --reload
```

### Running with Docker

```bash
docker-compose up -d --build
```

The app will be available at `http://localhost:7842`.

## Project Structure

```
app/
├── main.py          # FastAPI routes, API endpoints, WebSocket
├── downloader.py    # yt-dlp download logic, notifications
├── database.py      # SQLite schema and migrations
├── scheduler.py     # APScheduler background jobs
└── static/
    └── index.html   # Single-page web UI
```

## Making Changes

- **Backend**: All Python code is in `app/`. The API uses FastAPI with async handlers.
- **Frontend**: The entire UI is a single `app/static/index.html` file — vanilla HTML/CSS/JS, no build step.
- **Database**: Schema changes go in `app/database.py`. Add migrations at the bottom of `init_db()` for backwards compatibility.

## Code Style

- Python: Follow PEP 8, use type hints where practical
- Keep it simple — this is a single-container app, no complex abstractions needed
- Test your changes with Docker before submitting

## Submitting Changes

1. **Commit** your changes with a clear message:
   ```bash
   git commit -m "Add feature: description of what it does"
   ```
2. **Push** to your fork:
   ```bash
   git push origin feature/my-feature
   ```
3. Open a **Pull Request** against the `main` branch

## Reporting Issues

- Use [GitHub Issues](https://github.com/tommie0079/yt-downloader/issues)
- Include your Docker version, OS, and any error logs
- For yt-dlp errors, include the full error message from the container logs

## Ideas for Contributions

- 🌍 Internationalization / translations
- 📊 Download statistics dashboard
- 🔔 Additional notification providers (Pushover, Gotify, etc.)
- 📱 Mobile-optimized UI improvements
- 🧪 Test coverage
- 📖 Documentation improvements

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
