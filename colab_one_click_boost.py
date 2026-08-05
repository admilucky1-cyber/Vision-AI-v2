"""
Vision AI — ONE-CLICK GPU Boost for Google Colab
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


def _secret(name: str, default: str = "") -> str:
    v = (os.environ.get(name) or default or "").strip()
    try:
        from google.colab import userdata
        try:
            got = userdata.get(name)
            if got:
                return str(got).strip()
        except Exception:
            pass
    except Exception:
        pass
    return v or default


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
    ensure_project()
    pip_install()

    main_url = _secret("MAIN_APP_URL", DEFAULT_APP).rstrip("/")
    secret = _secret("WORKER_SECRET", DEFAULT_SECRET) or DEFAULT_SECRET
    ngrok_token = _secret("NGROK_TOKEN", "")

    if not ngrok_token:
        print("Add Colab Secret NGROK_TOKEN (once), then re-run.")
        print("https://dashboard.ngrok.com/get-started/your-authtoken")
        ngrok_token = input("Or paste ngrok token now: ").strip()
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
        if ph.status_code == 401:
            print("HINT: WORKER_SECRET mismatch. Use vision-colab-secret on Colab AND Railway COLAB_WORKER_SECRET")
    except Exception as e:
        print("Public health check failed:", e)

    print("=" * 50)
    print("DONE — leave this tab open")
    print("Secret used:", secret)
    print("Check:", f"{main_url}/boost")
    print("=" * 50)

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("Stopped")


if __name__ == "__main__":
    main()
