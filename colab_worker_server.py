"""
Vision AI Colab GPU Worker
==========================
Run this file INSIDE Google Colab (or any machine with GPU).

It starts a tiny FastAPI server and exposes it with ngrok so your
main Vision AI web app can call:
  COLAB_WORKER_URL=https://xxxx.ngrok-free.app

Endpoints:
  GET  /worker/health
  POST /worker/chat   {question, context, model}
  POST /worker/image  {prompt}

Env (optional inside Colab):
  WORKER_SECRET=shared-secret   (must match server COLAB_WORKER_SECRET)
  GROQ_API_KEY / GOOGLE_API_KEY / OPENROUTER_API_KEY / HF_TOKEN
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
import uvicorn

WORKER_SECRET = (os.getenv("WORKER_SECRET") or "").strip()
app = FastAPI(title="Vision AI Colab Worker", version="1.0")

# Lazy model handles
_pipe = None
_pipe_name = None


def _check_secret(x_worker_secret: Optional[str] = None):
    if WORKER_SECRET and (x_worker_secret or "") != WORKER_SECRET:
        raise HTTPException(status_code=401, detail="Invalid worker secret")


class ChatIn(BaseModel):
    question: str = Field(..., min_length=1)
    context: str = ""
    model: str = "auto"


class ImageIn(BaseModel):
    prompt: str = Field(..., min_length=1)


@app.get("/worker/health")
def health(x_worker_secret: Optional[str] = Header(None)):
    _check_secret(x_worker_secret)
    vram = _vram_stats()
    return {
        "status": "ok",
        "gpu": _gpu_name(),
        "image_model": _pipe_name or "not-loaded",
        "vram_used_mb": vram.get("used_mb"),
        "vram_total_mb": vram.get("total_mb"),
        "vram_free_mb": vram.get("free_mb"),
        "chat_keys": {
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "google": bool(os.getenv("GOOGLE_API_KEY")),
            "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
        },
        "ts": time.time(),
    }


def _vram_stats() -> dict:
    try:
        import torch
        if not torch.cuda.is_available():
            return {}
        free, total = torch.cuda.mem_get_info()
        used = total - free
        return {
            "used_mb": int(used / (1024 * 1024)),
            "total_mb": int(total / (1024 * 1024)),
            "free_mb": int(free / (1024 * 1024)),
        }
    except Exception:
        return {}


def _gpu_name() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
    except Exception:
        pass
    return "cpu"


@app.post("/worker/chat")
def worker_chat(body: ChatIn, x_worker_secret: Optional[str] = Header(None)):
    _check_secret(x_worker_secret)
    q = body.question.strip()
    ctx = (body.context or "")[:12000]
    system = (
        "You are VISION AI running on a Colab GPU worker. "
        "Be accurate, direct, and helpful. Match the user's language. "
        "Do not output large ASCII art for image requests."
    )
    prompt = f"{system}\n\nContext:\n{ctx}\n\nUser: {q}\nAssistant:"

    # 1) Groq
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            for mid in ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"):
                try:
                    r = client.chat.completions.create(
                        model=mid,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": f"{ctx}\n\n{q}" if ctx else q},
                        ],
                        temperature=0.5,
                        max_tokens=2048,
                    )
                    ans = (r.choices[0].message.content or "").strip()
                    if len(ans) > 10:
                        return {"answer": ans, "model": f"groq/{mid}"}
                except Exception:
                    continue
        except Exception as e:
            pass

    # 2) OpenRouter free
    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
            r = client.chat.completions.create(
                model="openrouter/auto",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"{ctx}\n\n{q}" if ctx else q},
                ],
                max_tokens=2048,
            )
            ans = (r.choices[0].message.content or "").strip()
            if len(ans) > 10:
                return {"answer": ans, "model": "openrouter/auto"}
        except Exception:
            pass

    # 3) Gemini
    gkey = os.getenv("GOOGLE_API_KEY")
    if gkey:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gkey)
            model = genai.GenerativeModel("gemini-1.5-flash")
            r = model.generate_content(prompt)
            ans = (r.text or "").strip()
            if len(ans) > 10:
                return {"answer": ans, "model": "gemini-1.5-flash"}
        except Exception:
            pass

    raise HTTPException(status_code=503, detail="No chat provider available on worker")


def _load_image_pipe():
    global _pipe, _pipe_name
    if _pipe is not None:
        return _pipe
    import torch
    from diffusers import AutoPipelineForText2Image

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    # FLUX schnell is fast; SDXL turbo as fallback
    candidates = [
        ("black-forest-labs/FLUX.1-schnell", {"torch_dtype": dtype}),
        ("stabilityai/sdxl-turbo", {"torch_dtype": dtype, "variant": "fp16"}),
    ]
    last_err = None
    for name, kwargs in candidates:
        try:
            pipe = AutoPipelineForText2Image.from_pretrained(name, **kwargs)
            pipe = pipe.to(device)
            _pipe = pipe
            _pipe_name = name
            return pipe
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Could not load image model: {last_err}")


@app.post("/worker/image")
def worker_image(body: ImageIn, x_worker_secret: Optional[str] = Header(None)):
    _check_secret(x_worker_secret)
    prompt = body.prompt.strip()

    # 1) Fast path: Hugging Face Inference API (no 7GB download)
    hf = (os.getenv("HF_TOKEN") or "").strip()
    api_models = [
        "black-forest-labs/FLUX.1-schnell",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "runwayml/stable-diffusion-v1-5",
    ]
    import requests as req
    for model in api_models:
        try:
            headers = {"Authorization": f"Bearer {hf}"} if hf else {}
            r = req.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json={"inputs": prompt, "options": {"wait_for_model": True}},
                timeout=100,
            )
            ctype = r.headers.get("Content-Type", "")
            if r.status_code == 200 and "image" in ctype:
                return {
                    "success": True,
                    "image_data": base64.b64encode(r.content).decode("utf-8"),
                    "provider": f"HF-API/{model}",
                }
            # model loading
            if r.status_code == 503:
                time.sleep(8)
                r2 = req.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers=headers,
                    json={"inputs": prompt, "options": {"wait_for_model": True}},
                    timeout=120,
                )
                if r2.status_code == 200 and "image" in r2.headers.get("Content-Type", ""):
                    return {
                        "success": True,
                        "image_data": base64.b64encode(r2.content).decode("utf-8"),
                        "provider": f"HF-API/{model}",
                    }
        except Exception:
            continue

    # 2) Local GPU only (skip huge download on CPU)
    try:
        import torch
        if not torch.cuda.is_available():
            raise HTTPException(
                status_code=503,
                detail="No HF image yet and no GPU. Set HF_TOKEN in Colab Secrets and/or Runtime→GPU.",
            )
        pipe = _load_image_pipe()
        kwargs = {
            "prompt": prompt,
            "num_inference_steps": 4 if "turbo" in (_pipe_name or "") or "schnell" in (_pipe_name or "") else 20,
        }
        if "turbo" in (_pipe_name or ""):
            kwargs["guidance_scale"] = 0.0
        out = pipe(**kwargs)
        img = out.images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return {
            "success": True,
            "image_data": base64.b64encode(buf.getvalue()).decode("utf-8"),
            "provider": f"Colab/{_pipe_name}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image gen failed: {e}")



def register_with_main_app(public_url: str, kind: str = "colab") -> None:
    """Tell the Vision AI website about this worker (auto-integrate)."""
    main = (os.getenv("MAIN_APP_URL") or "").strip().rstrip("/")
    if not main:
        print("MAIN_APP_URL not set — skip auto-register (set it to your Railway/Render URL)")
        return
    secret = (os.getenv("WORKER_SECRET") or os.getenv("COLAB_WORKER_SECRET") or "").strip()
    payload = {
        "url": public_url.rstrip("/"),
        "kind": kind,
        "secret": secret,
        "meta": {"gpu": _gpu_name(), "host": kind},
    }
    try:
        import requests as req
        r = req.post(f"{main}/api/workers/register", json=payload, timeout=20)
        print("Register →", main, r.status_code, r.text[:200])
    except Exception as e:
        print("Register failed:", e)


def heartbeat_loop(public_url: str, interval: int = 120) -> None:
    import threading
    import time as _t
    main = (os.getenv("MAIN_APP_URL") or "").strip().rstrip("/")
    if not main:
        return
    secret = (os.getenv("WORKER_SECRET") or os.getenv("COLAB_WORKER_SECRET") or "").strip()

    def _run():
        import requests as req
        while True:
            try:
                req.post(
                    f"{main}/api/workers/heartbeat",
                    json={"url": public_url.rstrip("/"), "secret": secret},
                    timeout=15,
                )
            except Exception:
                pass
            _t.sleep(interval)

    threading.Thread(target=_run, daemon=True).start()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port)
