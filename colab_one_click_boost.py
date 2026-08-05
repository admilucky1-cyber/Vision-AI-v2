"""
Vision AI — ONE-CLICK GPU Boost for Google Colab
Reads Colab Secrets more reliably (exact names + fallbacks).
"""
from __future__ import annotations

import os
import sys
import time
import threading
import asyncio
import traceback

DEFAULT_APP = "https://vision-ai-v2-production.up.railway.app"
DEFAULT_SECRET = "vision-colab-secret"
REPO = "https://github.com/admilucky1-cyber/Vision-AI-v2.git"
ROOT = "/content/Vision-AI"


def _userdata_get(name: str) -> str:
    """Read one Colab secret; return '' if missing/denied."""
    try:
        from google.colab import userdata
    except Exception:
        return ""
    try:
        got = userdata.get(name)
        if got is None:
            return ""
        return str(got).strip()
    except Exception as e:
        # NotebookAccessError / SecretNotFoundError
        return ""


def _secret(name: str, default: str = "", aliases: list | None = None) -> str:
    """Try env, then Colab userdata name, then aliases."""
    names = [name] + list(aliases or [])
    # env first
    for n in names:
        v = (os.environ.get(n) or "").strip()
        if v:
            return v
    # Colab secrets
    for n in names:
        v = _userdata_get(n)
        if v:
            os.environ[n] = v  # cache for child processes
            return v
    return (default or "").strip()


def debug_secrets():
    """Print which secrets are visible (not values)."""
    candidates = [
        "NGROK_TOKEN", "HF_TOKEN", "GROQ_API_KEY", "GOOGLE_API_KEY",
        "OPENROUTER_API_KEY", "WORKER_SECRET", "COLAB_WORKER_SECRET",
        "MAIN_APP_URL", "TELEGRAM_BOT_TOKEN",
    ]
    print("--- Secret check (names only) ---")
    found = 0
    for n in candidates:
        v = _userdata_get(n)
        ok = bool(v)
        if ok:
            found += 1
        print(f"  {'OK' if ok else '--'}  {n}")
    if found == 0:
        print("No secrets readable. Check:")
        print("  1) Name is EXACT (e.g. NGROK_TOKEN not NGROK)")
        print("  2) Notebook access toggle is ON (blue)")
        print("  3) Runtime → Restart runtime after adding secrets")
    print("---------------------------------")
    return found


def ensure_project():
    import subprocess
    if not os.path.isdir(ROOT):
        subprocess.check_call(["git", "clone", "--depth", "1", REPO, ROOT])
    else:
        try:
            subprocess.check_call(
                ["git", "-C", ROOT, "pull", "--ff-only"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    os.chdir(ROOT)
    if not os.path.isfile("colab_worker_server.py"):
        raise SystemExit("colab_worker_server.py missing — git pull/push the repo")


def pip_install():
    import subprocess
    pkgs = [
        "fastapi",
        "uvicorn[standard]",
        "pyngrok",
        "requests==2.32.4",
        "openai",
        "google-generativeai",
        "pillow",
        "pydantic",
    ]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *pkgs])


def run_uvicorn():
    try:
        import uvicorn
        config = uvicorn.Config(
            "colab_worker_server:app",
            host="0.0.0.0",
            port=7860,
            log_level="info",
            loop="asyncio",
        )
        server = uvicorn.Server(config)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.serve())
    except Exception:
        print("WORKER THREAD CRASH:")
        traceback.print_exc()


def main():
    print("=== Vision AI One-Click Boost ===")
    debug_secrets()

    ensure_project()
    pip_install()

    main_url = _secret("MAIN_APP_URL", DEFAULT_APP).rstrip("/")
    secret = (
        _secret("WORKER_SECRET", "", aliases=["COLAB_WORKER_SECRET"])
        or DEFAULT_SECRET
    )
    ngrok_token = _secret("NGROK_TOKEN", "", aliases=["NGROK_AUTHTOKEN", "NGROK"])
    hf = _secret("HF_TOKEN", "")
    groq = _secret("GROQ_API_KEY", "", aliases=["GROQ_KEY"])
    google = _secret("GOOGLE_API_KEY", "", aliases=["GOOGLE_KEY", "GEMINI_API_KEY"])

    if hf:
        os.environ["HF_TOKEN"] = hf
    if groq:
        os.environ["GROQ_API_KEY"] = groq
    if google:
        os.environ["GOOGLE_API_KEY"] = google

    if not ngrok_token:
        print("NGROK_TOKEN not readable from Secrets.")
        print("Exact name must be: NGROK_TOKEN")
        print("https://dashboard.ngrok.com/get-started/your-authtoken")
        try:
            ngrok_token = input("Or paste ngrok token now: ").strip()
        except EOFError:
            ngrok_token = ""
    if not ngrok_token:
        raise SystemExit("NGROK_TOKEN required")

    os.environ["MAIN_APP_URL"] = main_url
    os.environ["WORKER_SECRET"] = secret
    os.environ["COLAB_WORKER_SECRET"] = secret

    os.makedirs("/content", exist_ok=True)
    with open("/content/.vision_boost.env", "w") as f:
        f.write(f"MAIN_APP_URL={main_url}\nWORKER_SECRET={secret}\n")

    from pyngrok import ngrok, conf
    conf.get_default().auth_token = ngrok_token

    threading.Thread(target=run_uvicorn, daemon=True).start()
    print("Worker starting on :7860 …")

    import requests as req
    headers = {"X-Worker-Secret": secret}

    ready = False
    last_err = ""
    for _ in range(40):
        try:
            h = req.get("http://127.0.0.1:7860/worker/health", headers=headers, timeout=2)
            if h.status_code == 200:
                ready = True
                print("Local worker OK:", h.text[:120])
                break
            last_err = f"HTTP {h.status_code} {h.text[:80]}"
        except Exception as e:
            last_err = str(e)
        time.sleep(0.5)

    if not ready:
        print("WARNING: local worker not ready:", last_err)

    public = ngrok.connect(7860, bind_tls=True).public_url
    print("Public:", public)

    r = req.post(
        f"{main_url}/api/workers/register",
        json={"url": public, "kind": "colab", "secret": secret, "meta": {"one_click": True}},
        timeout=25,
    )
    print("Register:", r.status_code, r.text[:240])

    def hb():
        while True:
            try:
                req.post(
                    f"{main_url}/api/workers/heartbeat",
                    json={"url": public, "secret": secret},
                    timeout=15,
                )
            except Exception:
                pass
            time.sleep(90)

    threading.Thread(target=hb, daemon=True).start()

    try:
        ph = req.get(f"{public}/worker/health", headers=headers, timeout=20)
        print("Public health:", ph.status_code, ph.text[:160])
    except Exception as e:
        print("Public health check failed:", e)

    print("=" * 50)
    print("DONE — leave this tab open")
    print("HF_TOKEN:", "yes" if hf else "NO — add for fast images")
    print("GROQ:", "yes" if groq else "no")
    print("Check:", f"{main_url}/boost")
    print("=" * 50)

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("Stopped")


if __name__ == "__main__":
    main()
