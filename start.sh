#!/bin/sh
# Railway/Docker entrypoint — expands PORT/WEB_WORKERS in a real shell
set -e
PORT="${PORT:-5050}"
WEB_WORKERS="${WEB_WORKERS:-1}"
# Ensure integer
case "$PORT" in
  ''|*[!0-9]*) PORT=5050 ;;
esac
case "$WEB_WORKERS" in
  ''|*[!0-9]*) WEB_WORKERS=1 ;;
esac
echo "Starting Vision AI on 0.0.0.0:${PORT} workers=${WEB_WORKERS}"
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --workers "$WEB_WORKERS" \
  --proxy-headers \
  --forwarded-allow-ips='*'
