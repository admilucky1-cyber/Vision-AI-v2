# Vision AI v5.6.2 — Production image
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=5050 \
    DEBUG=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl build-essential tesseract-ocr poppler-utils graphviz \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install -U yt-dlp

COPY . .

RUN mkdir -p uploads downloads logs cache data chroma_db \
    && useradd -m -u 10001 appuser \
    && chmod +x /app/start.sh 2>/dev/null || true \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 5050
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -fsS "http://127.0.0.1:${PORT:-5050}/health" || exit 1
CMD ["python", "run.py"]
