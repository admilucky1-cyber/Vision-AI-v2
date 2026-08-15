#!/usr/bin/env python3
"""Local smoke checks — no live server required for unit parts."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    failures = 0
    # version
    v = (ROOT / "VERSION").read_text().strip()
    print(f"VERSION={v}")
    # detection
    from services.image_gen import user_wants_diagram, user_wants_creative_image
    assert user_wants_diagram("create graph between current and voltage")
    assert user_wants_creative_image("photorealistic image of a mosque")
    print("OK detection")
    # optional matplotlib
    try:
        from services.image_gen import MATPLOTLIB_AVAILABLE, draw_iv_graph
        if MATPLOTLIB_AVAILABLE:
            r = draw_iv_graph(True)
            assert r.get("success") and r.get("image_data")
            print("OK iv graph", "svg" if r.get("svg_data") else "png-only")
        else:
            print("SKIP iv graph (no matplotlib)")
    except Exception as e:
        print("FAIL iv", e)
        failures += 1
    # CSS
    for name in ("eye-care.css", "theme-presets.css"):
        p = ROOT / "frontend/static/css" / name
        if not p.is_file():
            print("FAIL missing", name)
            failures += 1
        else:
            print("OK", name)
    # full-document RAG skip (exam PDF "solve this pdf")
    try:
        from services.rag import _is_full_document_intent

        assert _is_full_document_intent("solve this pdf", "") is True
        assert _is_full_document_intent("what is force?", "plain chat") is False
        assert _is_full_document_intent("explain", "[QUESTION PAPER: x.pdf]") is True
        print("OK full-document intent")
    except Exception as e:
        print("FAIL full-document intent", e)
        failures += 1

    # VERSION file matches expected major line
    if not v.startswith("3."):
        print("WARN VERSION not 3.x:", v)

    # optional live health
    import os, urllib.request

    base = (os.getenv("SMOKE_BASE_URL") or "").rstrip("/")
    if base:
        try:
            with urllib.request.urlopen(base + "/health", timeout=10) as resp:
                print("OK health", resp.status)
        except Exception as e:
            print("FAIL health", e)
            failures += 1

    # disk RAG cache (multi-worker exam follow-up)
    try:
        import time
        from services.rag_cache import RAGCache, session_user_key
        class _H(dict):
            def get(self, k, default=None):
                return dict.get(self, k, default)
        class _R:
            headers = _H({"x-vision-client-id": "test-client-id-12345"})
        uk = session_user_key(_R(), {"username": "guest_x"})
        assert uk.startswith("c_"), uk
        c = RAGCache(max_size=3, ttl_sec=3600)
        c.clear()
        key = c.get_key("paper.pdf", "Q1 content here", user_key=uk)
        c.set(key, {"filename": "paper.pdf", "content": "Q1 real question", "user_key": uk, "timestamp": time.time()})
        got = c.get_latest(user_key=uk)
        assert got and "Q1 real" in got["content"], got
        assert c.get_latest(user_key="other") is None
        c2 = RAGCache(max_size=3, ttl_sec=3600)
        assert c2.get_latest(user_key=uk) and "Q1 real" in c2.get_latest(user_key=uk)["content"]
        c.clear(uk)
        print("OK disk RAG cache + session key")
    except Exception as e:
        print("FAIL disk RAG cache", e)
        failures += 1


    # provider timeout helper
    try:
        from services.llm import _provider_timeout, _out_tokens, _is_document_context
        assert _is_document_context("[QUESTION PAPER: x]\nQ1")
        assert _provider_timeout("[QUESTION PAPER]", 28) >= 28
        assert _out_tokens("[QUESTION PAPER]", 4096) >= 4096
        print("OK doc timeout/token helpers")
    except Exception as e:
        print("FAIL doc helpers", e)
        failures += 1

    print("failures=", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
