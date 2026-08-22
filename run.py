"""
Vision AI — process entrypoint (Railway / Docker / local).

Railway users sometimes set Start Command to `python run.py`.
This file starts the same FastAPI app as `main:app` via uvicorn.
Prefer Dockerfile CMD or: uvicorn main:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

import os
import sys


def main() -> None:
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    # Railway injects PORT; local default 5050
    port = int(os.getenv("PORT", "5050"))
    # Free/hobby: 1 worker is safer (memory + cold start)
    workers = int(os.getenv("WEB_WORKERS", "1"))
    reload = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

    # workers>1 is incompatible with reload
    if reload:
        workers = 1

    kwargs = {
        "app": "main:app",
        "host": host,
        "port": port,
        "proxy_headers": True,
        "forwarded_allow_ips": "*",
    }
    if workers > 1 and not reload:
        kwargs["workers"] = workers
    else:
        kwargs["reload"] = reload

    print(f"[Vision AI] starting uvicorn on {host}:{port} workers={kwargs.get('workers', 1)}", flush=True)
    uvicorn.run(**kwargs)


if __name__ == "__main__":
    main()
