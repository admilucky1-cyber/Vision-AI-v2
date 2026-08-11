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
    print("failures=", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
