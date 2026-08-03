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
    return {
        "status": "ok",
        "gpu": _gpu_name(),
        "image_model": _pipe_name or "not-loaded",
        "chat_keys": {
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "google": bool(os.getenv("GOOGLE_API_KEY")),
            "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
        },
        "ts": time.time(),
    }


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
    try:
        pipe = _load_image_pipe()
        import torch
        kwargs = {"prompt": prompt, "num_inference_steps": 4 if "turbo" in (_pipe_name or "") or "schnell" in (_pipe_name or "") else 20}
        if "turbo" in (_pipe_name or ""):
            kwargs["guidance_scale"] = 0.0
        out = pipe(**kwargs)
        img = out.images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return {
            "success": True,
            "image_data": b64,
            "provider": f"Colab/{_pipe_name}",
        }
    except Exception as e:
        # HF inference API fallback from worker
        hf = os.getenv("HF_TOKEN")
        if hf:
            try:
                import requests
                r = requests.post(
                    "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
                    headers={"Authorization": f"Bearer {hf}"},
                    json={"inputs": prompt},
                    timeout=90,
                )
                if r.status_code == 200 and "application/json" not in r.headers.get("Content-Type", ""):
                    return {
                        "success": True,
                        "image_data": base64.b64encode(r.content).decode("utf-8"),
                        "provider": "Colab/HF-API-FLUX-schnell",
                    }
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Image gen failed: {e}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port)
