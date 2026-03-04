FROM python:3.12-slim

# Install ffmpeg + deno (needed by yt-dlp for JS-based YouTube extraction)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl unzip && \
    curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh && \
    apt-get purge -y curl unzip && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Default download directory
RUN mkdir -p /downloads

ENV DOWNLOAD_DIR=/downloads
ENV DATABASE_PATH=/app/data/channels.db
ENV CHECK_INTERVAL_MINUTES=30

EXPOSE 7842

HEALTHCHECK --interval=60s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7842/api/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7842"]
