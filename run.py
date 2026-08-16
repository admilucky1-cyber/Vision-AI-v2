#!/usr/bin/env python3
"""Production entrypoint — reads PORT from env (no shell ${PORT} expansion needed)."""
from __future__ import annotations

import os
import sys


def _int_env(name: str, default: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def main() -> None:
    # Railway always injects PORT; local default 5050
    port = _int_env("PORT", 5050)
    workers = _int_env("WEB_WORKERS", 1)
    host = os.environ.get("HOST", "0.0.0.0").strip() or "0.0.0.0"
    print(f"Starting Vision AI via run.py on {host}:{port} workers={workers}", flush=True)

    # Prefer uvicorn.run so we never pass a broken CLI string
    import uvicorn

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=max(1, workers),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
