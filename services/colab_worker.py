"""
Vision AI — multi free-worker client (Colab + Kaggle + any ngrok/localtunnel).

Env:
  COLAB_WORKER_URL=https://a.ngrok-free.app
  KAGGLE_WORKER_URL=https://b.ngrok-free.app
  WORKER_URLS=https://a...,https://b...   # optional comma list (extra)
  COLAB_WORKER_SECRET=shared-secret
  COLAB_CHAT_TIMEOUT=90
  COLAB_IMAGE_TIMEOUT=120

Website tries workers in order; first healthy one wins. API keys remain fallback.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("vision-ai.colab_worker")

COLAB_WORKER_SECRET = (os.getenv("COLAB_WORKER_SECRET") or os.getenv("WORKER_SECRET") or "").strip()
TIMEOUT_CHAT = float(os.getenv("COLAB_CHAT_TIMEOUT", "90"))
TIMEOUT_IMAGE = float(os.getenv("COLAB_IMAGE_TIMEOUT", "120"))


def _worker_urls() -> List[str]:
    urls: List[str] = []
    for key in ("COLAB_WORKER_URL", "KAGGLE_WORKER_URL"):
        v = (os.getenv(key) or "").strip().rstrip("/")
        if v and v not in urls:
            urls.append(v)
    extra = (os.getenv("WORKER_URLS") or "").strip()
    if extra:
        for part in extra.split(","):
            u = part.strip().rstrip("/")
            if u and u not in urls:
                urls.append(u)
    return urls


def is_enabled() -> bool:
    return bool(_worker_urls())


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if COLAB_WORKER_SECRET:
        h["X-Worker-Secret"] = COLAB_WORKER_SECRET
    return h


def health(url: Optional[str] = None) -> Dict[str, Any]:
    targets = [url] if url else _worker_urls()
    if not targets:
        return {"ok": False, "reason": "no worker URLs configured"}
    results = []
    any_ok = False
    for u in targets:
        try:
            r = requests.get(f"{u}/worker/health", timeout=8, headers=_headers())
            if r.status_code == 200:
                data = r.json() if r.content else {}
                data["ok"] = True
                data["url"] = u
                results.append(data)
                any_ok = True
            else:
                results.append({"ok": False, "url": u, "status": r.status_code})
        except Exception as e:
            results.append({"ok": False, "url": u, "error": str(e)})
    return {"ok": any_ok, "workers": results, "count": len(targets)}


def _first_live_url() -> Optional[str]:
    for u in _worker_urls():
        try:
            r = requests.get(f"{u}/worker/health", timeout=6, headers=_headers())
            if r.status_code == 200:
                return u
        except Exception:
            continue
    return None


def chat(question: str, context: str = "", model: str = "auto") -> Optional[str]:
    if not _worker_urls():
        return None
    # Prefer last-known live; else try all
    order = _worker_urls()
    live = _first_live_url()
    if live:
        order = [live] + [u for u in order if u != live]
    for u in order:
        try:
            r = requests.post(
                f"{u}/worker/chat",
                json={"question": question, "context": context or "", "model": model},
                headers=_headers(),
                timeout=TIMEOUT_CHAT,
            )
            if r.status_code != 200:
                logger.warning(f"worker chat {u} status={r.status_code}")
                continue
            data = r.json()
            answer = (data.get("answer") or "").strip()
            if len(answer) > 10:
                logger.info(f"Worker chat OK via {u} ({data.get('model', '?')})")
                return answer
        except Exception as e:
            logger.warning(f"worker chat {u} failed: {e}")
    return None


def generate_image(prompt: str) -> Optional[Dict[str, Any]]:
    if not _worker_urls():
        return None
    order = _worker_urls()
    live = _first_live_url()
    if live:
        order = [live] + [u for u in order if u != live]
    for u in order:
        try:
            r = requests.post(
                f"{u}/worker/image",
                json={"prompt": prompt},
                headers=_headers(),
                timeout=TIMEOUT_IMAGE,
            )
            if r.status_code != 200:
                logger.warning(f"worker image {u} status={r.status_code}")
                continue
            data = r.json()
            if data.get("success") and data.get("image_data"):
                logger.info(f"Worker image OK via {u}")
                return data
        except Exception as e:
            logger.warning(f"worker image {u} failed: {e}")
    return None


def keep_alive_ping() -> Dict[str, Any]:
    """Ping all workers + return summary (for cron / GitHub Actions)."""
    return health()
