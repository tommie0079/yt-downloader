FROM python:3.12-slim

# Install ffmpeg + nodejs (needed by yt-dlp for JS-based YouTube extraction)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg nodejs && \
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

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7842"]
