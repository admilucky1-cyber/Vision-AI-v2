"""
Lightweight free-proxy helper for yt-dlp (inspired by Petrprogs/yt-dlp-proxy).
Fetches public proxy lists, quick-tests connectivity, caches a working proxy.
Enable with: YTDLP_AUTO_PROXY=1
Optional static: YTDLP_PROXY=http://host:port
"""
from __future__ import annotations

import logging
import os
import random
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("vision-ai.ytdlp_proxy")

_LOCK = threading.RLock()
_CACHE: Dict[str, Any] = {"proxy": None, "ts": 0.0}
_TTL = int(os.getenv("YTDLP_PROXY_TTL_SEC", "900") or 900)


def _static_proxy() -> Optional[str]:
    p = (os.getenv("YTDLP_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or "").strip()
    return p or None


def _fetch_github_proxies(limit: int = 40) -> List[str]:
    """proxifly free list (http/socks)."""
    out: List[str] = []
    try:
        import requests
        r = requests.get(
            "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.json",
            timeout=12,
        )
        if r.status_code != 200:
            return out
        data = r.json()
        if not isinstance(data, list):
            return out
        random.shuffle(data)
        for row in data:
            if not isinstance(row, dict):
                continue
            proto = (row.get("protocol") or "http").lower()
            if proto not in ("http", "https", "socks4", "socks5"):
                continue
            ip = row.get("ip")
            port = row.get("port")
            if not ip or not port:
                continue
            out.append(f"{proto}://{ip}:{port}")
            if len(out) >= limit:
                break
    except Exception as e:
        logger.info("proxy list fetch failed: %s", e)
    return out


def _quick_ok(proxy: str, timeout: float = 4.0) -> bool:
    try:
        import requests
        r = requests.get(
            "https://www.youtube.com/generate_204",
            proxies={"http": proxy, "https": proxy},
            timeout=timeout,
            allow_redirects=True,
        )
        # 204 or any response means TCP/TLS path works
        return r.status_code < 500
    except Exception:
        return False


def get_working_proxy(force: bool = False) -> Optional[str]:
    """
    Return a proxy URL for yt-dlp, or None.
    Priority: YTDLP_PROXY env → auto free proxy (if YTDLP_AUTO_PROXY=1).
    """
    static = _static_proxy()
    if static:
        return static

    auto = (os.getenv("YTDLP_AUTO_PROXY") or "").strip().lower() in ("1", "true", "yes", "on")
    if not auto:
        return None

    with _LOCK:
        if not force and _CACHE.get("proxy") and (time.time() - float(_CACHE.get("ts") or 0)) < _TTL:
            return _CACHE["proxy"]

    candidates = _fetch_github_proxies(50)
    # Prefer http first (yt-dlp handles well)
    candidates.sort(key=lambda u: (0 if u.startswith("http://") else 1))
    tested = 0
    for proxy in candidates[:25]:
        tested += 1
        if _quick_ok(proxy):
            with _LOCK:
                _CACHE["proxy"] = proxy
                _CACHE["ts"] = time.time()
            logger.info("yt-dlp auto-proxy selected after %s tests: %s", tested, proxy.split("@")[-1])
            return proxy
    logger.warning("yt-dlp auto-proxy: no working proxy found (%s tested)", tested)
    with _LOCK:
        _CACHE["proxy"] = None
        _CACHE["ts"] = time.time()
    return None


def invalidate_proxy() -> None:
    with _LOCK:
        _CACHE["proxy"] = None
        _CACHE["ts"] = 0.0
