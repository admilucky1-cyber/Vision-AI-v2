#!/usr/bin/env python3
"""Production entrypoint — reads PORT from env."""
from __future__ import annotations
import os
import sys

def main() -> int:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5050") or "5050")
    print(f"[Vision AI] starting uvicorn on {host}:{port} workers=1", flush=True)
    import uvicorn
    uvicorn.run("main:app", host=host, port=port, workers=1, log_level="info")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
