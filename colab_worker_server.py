"""
Vision AI Colab GPU Worker  v2.5.2
==================================
Run inside Google Colab (Runtime → GPU / T4).

Exposes:
  GET  /worker/health
  POST /worker/chat
  POST /worker/chat/stream   (SSE streaming)
  POST /worker/image
  POST /worker/warmup

Features:
  - Startup model preload + CUDA warm-up inference (kills first-request 30s latency)
  - Serverless-first image path (Hugging Face Inference API + Pollinations) → local GPU fallback
  - Optional streaming chat
  - Auto-register + heartbeat to main app

Env (Colab Secrets recommended):
  WORKER_SECRET          shared secret
  MAIN_APP_URL           your Railway / Render URL
  HF_TOKEN               Hugging Face token (free)
  GROQ_API_KEY / GOOGLE_API_KEY / OPENROUTER_API_KEY
  IMAGE_MODEL_PATH       optional local /content path
"""

from __future__ import annotations

import base64
import io
import os
import time
import threading
import json
from typing import Any, Dict, Optional, Generator

# Load secrets written by one-click boost (Colab often blocks userdata.get)
for _env_path in ("/content/.vision_boost.env", ".env"):
    if os.path.isfile(_env_path):
        try:
            from dotenv import load_dotenv
            load_dotenv(_env_path, override=False)
        except Exception:
            try:
                with open(_env_path) as _f:
                    for _line in _f:
                        _line = _line.strip()
                        if not _line or _line.startswith("#") or "=" not in _line:
                            continue
                        _k, _, _v = _line.partition("=")
                        if _k and _v and not os.environ.get(_k):
                            os.environ[_k] = _v
            except Exception:
                pass
        break

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

WORKER_SECRET = (os.getenv("WORKER_SECRET") or "").strip()
app = FastAPI(title="Vision AI Colab Worker", version="2.5.2")

# ---------------------------------------------------------------------------
# Global model state
# ---------------------------------------------------------------------------
_pipe = None
_pipe_name: Optional[str] = None
_warmed = False
_warmup_error: Optional[str] = None
_warmup_lock = threading.Lock()


def _check_secret(x_worker_secret: Optional[str] = None):
    if WORKER_SECRET and (x_worker_secret or "") != WORKER_SECRET:
        raise HTTPException(status_code=401, detail="Invalid worker secret")


class ChatIn(BaseModel):
    question: str = Field(..., min_length=1)
    context: str = ""
    model: str = "auto"
    temperature: float = 0.5
    max_tokens: int = 2048


class ImageIn(BaseModel):
    prompt: str = Field(..., min_length=1)
    steps: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


# ---------------------------------------------------------------------------
# GPU / VRAM helpers
# ---------------------------------------------------------------------------
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
        return "cpu"
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Image model load + WARMUP
# ---------------------------------------------------------------------------
def _cuda_memory_setup():
    """CUDA allocator + fragmentation tuning for free T4 / low-VRAM GPUs."""
    import os as _os
    _os.environ.setdefault(
        "PYTORCH_CUDA_ALLOC_CONF",
        "expandable_segments:True,max_split_size_mb:128",
    )
    try:
        import torch
        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True
            try:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
            except Exception:
                pass
    except Exception:
        pass


def _cuda_cleanup():
    """Release cached CUDA blocks after inference to avoid OOM on next request."""
    try:
        import gc
        gc.collect()
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            try:
                torch.cuda.ipc_collect()
            except Exception:
                pass
    except Exception:
        pass


def _load_image_pipe():
    """Load FLUX.1-schnell / SDXL-Turbo / SD-1.5 with aggressive low-VRAM opts for T4."""
    global _pipe, _pipe_name
    if _pipe is not None:
        return _pipe

    _cuda_memory_setup()
    import torch
    from diffusers import AutoPipelineForText2Image

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    low_vram = (os.getenv("LOW_VRAM", "1") or "1").strip() not in ("0", "false", "False")

    hf_token = (
        os.getenv("HF_TOKEN")
        or os.getenv("HUGGING_FACE_HUB_TOKEN")
        or os.getenv("HUGGINGFACE_TOKEN")
        or ""
    ).strip()

    candidates = [
        ("black-forest-labs/FLUX.1-schnell", {"torch_dtype": dtype}),
        ("stabilityai/sdxl-turbo", {"torch_dtype": dtype, "variant": "fp16"}),
        ("runwayml/stable-diffusion-v1-5", {"torch_dtype": dtype}),
    ]

    last_err = None
    for name, kwargs in candidates:
        try:
            print(f"[warmup] Loading image model: {name} (low_vram={low_vram}, hf_token={'yes' if hf_token else 'no'}) ...")
            if hf_token:
                kwargs = {**kwargs, "token": hf_token}
            pipe = AutoPipelineForText2Image.from_pretrained(name, **kwargs)

            if device == "cuda" and low_vram:
                try:
                    pipe.enable_model_cpu_offload()
                except Exception:
                    try:
                        pipe.enable_sequential_cpu_offload()
                    except Exception:
                        pipe = pipe.to(device)
            else:
                pipe = pipe.to(device)

            for enabler in ("enable_attention_slicing", "enable_vae_slicing", "enable_vae_tiling"):
                try:
                    getattr(pipe, enabler)()
                except Exception:
                    pass
            try:
                pipe.enable_xformers_memory_efficient_attention()
            except Exception:
                try:
                    pipe.enable_attention_slicing("max")
                except Exception:
                    pass

            _pipe = pipe
            _pipe_name = name
            print(f"[warmup] Loaded {_pipe_name}")
            return pipe
        except Exception as e:
            last_err = e
            print(f"[warmup] Failed {name}: {e}")
            _cuda_cleanup()
            continue
    raise RuntimeError(f"Could not load any image model: {last_err}")


def _run_warmup_inference():
    """
    Single short inference so CUDA kernels, weights and allocator are hot.
    Prevents the classic 20-40 s first-user latency on Colab.
    """
    global _warmed, _warmup_error
    with _warmup_lock:
        if _warmed:
            return
        try:
            t0 = time.time()
            pipe = _load_image_pipe()
            steps = 1 if "schnell" in (_pipe_name or "") or "turbo" in (_pipe_name or "") else 2
            kwargs = {
                "prompt": "warmup test, simple red circle on white background",
                "num_inference_steps": steps,
            }
            if "turbo" in (_pipe_name or ""):
                kwargs["guidance_scale"] = 0.0
            _ = pipe(**kwargs)
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
            except Exception:
                pass
            _warmed = True
            _warmup_error = None
            print(f"[warmup] Inference warm-up OK in {time.time() - t0:.1f}s  model={_pipe_name}")
        except Exception as e:
            _warmup_error = str(e)[:300]
            print(f"[warmup] FAILED: {e}")


def _background_warmup():
    """Non-blocking startup warm-up."""
    def _job():
        try:
            _run_warmup_inference()
        except Exception as e:
            print(f"[warmup] background error: {e}")
    threading.Thread(target=_job, daemon=True, name="vision-warmup").start()


@app.on_event("startup")
def on_startup():
    print("[worker] Startup — scheduling model warm-up")
    _background_warmup()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/worker/health")
def health(x_worker_secret: Optional[str] = Header(None)):
    _check_secret(x_worker_secret)
    vram = _vram_stats()
    return {
        "status": "ok",
        "version": "2.5.2",
        "gpu": _gpu_name(),
        "image_model": _pipe_name or "not-loaded",
        "warmed": _warmed,
        "warmup_error": _warmup_error,
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


@app.post("/worker/warmup")
def force_warmup(x_worker_secret: Optional[str] = Header(None)):
    """Manual trigger (useful after Colab reconnect)."""
    _check_secret(x_worker_secret)
    _run_warmup_inference()
    return {
        "warmed": _warmed,
        "model": _pipe_name,
        "error": _warmup_error,
        "vram": _vram_stats(),
    }


# ---------------------------------------------------------------------------
# Chat (non-streaming) – free API cascade
# Note: Qwen2.5-32B does NOT fit free Colab T4 (16 GB). Use API cascade.
# ---------------------------------------------------------------------------
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
                        temperature=body.temperature,
                        max_tokens=body.max_tokens,
                    )
                    ans = (r.choices[0].message.content or "").strip()
                    if len(ans) > 10:
                        return {"answer": ans, "model": f"groq/{mid}", "warmed": _warmed}
                except Exception:
                    continue
        except Exception:
            pass

    # 2) OpenRouter free (DeepSeek-V3 preferred when available)
    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
            for mid in (
                "deepseek/deepseek-chat-v3-0324:free",
                "deepseek/deepseek-chat:free",
                "meta-llama/llama-3.3-70b-instruct:free",
                "openrouter/auto",
            ):
                try:
                    r = client.chat.completions.create(
                        model=mid,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": f"{ctx}\n\n{q}" if ctx else q},
                        ],
                        max_tokens=body.max_tokens,
                        temperature=body.temperature,
                    )
                    ans = (r.choices[0].message.content or "").strip()
                    if len(ans) > 10:
                        return {"answer": ans, "model": f"openrouter/{mid}", "warmed": _warmed}
                except Exception:
                    continue
        except Exception:
            pass

    # 3) Gemini
    gkey = os.getenv("GOOGLE_API_KEY")
    if gkey:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gkey)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"{system}\n\nContext:\n{ctx}\n\nUser: {q}\nAssistant:"
            r = model.generate_content(prompt)
            ans = (r.text or "").strip()
            if len(ans) > 10:
                return {"answer": ans, "model": "gemini-1.5-flash", "warmed": _warmed}
        except Exception:
            pass

    raise HTTPException(status_code=503, detail="No chat provider available on worker")


# ---------------------------------------------------------------------------
# Streaming chat (SSE)
# ---------------------------------------------------------------------------
@app.post("/worker/chat/stream")
def worker_chat_stream(body: ChatIn, x_worker_secret: Optional[str] = Header(None)):
    _check_secret(x_worker_secret)
    q = body.question.strip()
    ctx = (body.context or "")[:12000]
    system = (
        "You are VISION AI on Colab. Be accurate and concise. Match user language."
    )

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    def event_generator() -> Generator[str, None, None]:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
                stream = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"{ctx}\n\n{q}" if ctx else q},
                    ],
                    temperature=body.temperature,
                    max_tokens=body.max_tokens,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        yield _sse({"token": delta})
                yield _sse({"done": True, "model": "groq/llama-3.3-70b-versatile"})
                return
            except Exception as e:
                yield _sse({"error": f"groq stream failed: {e}"})

        # Fallback: non-stream then chunked emit
        try:
            from openai import OpenAI
            or_key = os.getenv("OPENROUTER_API_KEY")
            if or_key:
                client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
                r = client.chat.completions.create(
                    model="meta-llama/llama-3.3-70b-instruct:free",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"{ctx}\n\n{q}" if ctx else q},
                    ],
                    max_tokens=body.max_tokens,
                )
                ans = (r.choices[0].message.content or "").strip()
                step = max(20, len(ans) // 12)
                for i in range(0, len(ans), step):
                    yield _sse({"token": ans[i : i + step]})
                yield _sse({"done": True, "model": "openrouter/llama-3.3"})
                return
        except Exception as e:
            yield _sse({"error": str(e)})
        yield _sse({"done": True, "error": "no streaming provider"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Image generation — SERVERLESS FIRST, then local GPU
# ---------------------------------------------------------------------------
def _serverless_hf_image(prompt: str, hf_token: str) -> Optional[Dict[str, Any]]:
    """
    Pure serverless path via Hugging Face Inference API.
    No GPU required on the worker. Free-tier rate limits apply.
    """
    import requests as req

    api_models = [
        "black-forest-labs/FLUX.1-schnell",
        "stabilityai/sdxl-turbo",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "runwayml/stable-diffusion-v1-5",
    ]
    headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}
    for model in api_models:
        try:
            r = req.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json={
                    "inputs": prompt,
                    "options": {"wait_for_model": True},
                },
                timeout=100,
            )
            ctype = r.headers.get("Content-Type", "")
            if r.status_code == 200 and "image" in ctype:
                return {
                    "success": True,
                    "image_data": base64.b64encode(r.content).decode("utf-8"),
                    "provider": f"HF-Serverless/{model}",
                }
            if r.status_code == 503:
                time.sleep(6)
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
                        "provider": f"HF-Serverless/{model}",
                    }
        except Exception:
            continue
    return None


def _serverless_pollinations(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Extra free serverless endpoint (no API key required).
    Best-effort public service — not guaranteed SLA.
    """
    import requests as req
    try:
        from urllib.parse import quote
        url = (
            f"https://image.pollinations.ai/prompt/{quote(prompt[:300])}"
            f"?width=1024&height=1024&nologo=true"
        )
        r = req.get(url, timeout=90)
        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
            return {
                "success": True,
                "image_data": base64.b64encode(r.content).decode("utf-8"),
                "provider": "Pollinations-Serverless",
            }
    except Exception:
        pass
    return None


@app.post("/worker/image")
def worker_image(body: ImageIn, x_worker_secret: Optional[str] = Header(None)):
    _check_secret(x_worker_secret)
    prompt = (body.prompt or "").strip()
    if prompt and "matches the prompt exactly" not in prompt.lower():
        prompt = prompt + ", matches the prompt exactly, coherent scene, no unrelated people or objects"

    # 1) SERVERLESS FIRST (no local GPU load, free-tier friendly)
    hf = (os.getenv("HF_TOKEN") or "").strip()
    result = _serverless_hf_image(prompt, hf)
    if result:
        return result

    # 2) Secondary free serverless
    result = _serverless_pollinations(prompt)
    if result:
        return result

    # 3) Local GPU (Colab) – only if serverless failed
    try:
        import torch
        if not torch.cuda.is_available():
            raise HTTPException(
                status_code=503,
                detail=(
                    "Serverless image APIs failed and no GPU available. "
                    "Set HF_TOKEN in Colab Secrets and/or enable Runtime→GPU."
                ),
            )
        if not _warmed:
            _run_warmup_inference()
        pipe = _load_image_pipe()
        steps = body.steps
        if steps is None:
            # Higher defaults for clearer T4 output (turbo still fast at 8)
            if "turbo" in (_pipe_name or ""):
                steps = 8
            elif "schnell" in (_pipe_name or ""):
                steps = 6
            else:
                steps = 28
        kwargs = {
            "prompt": prompt,
            "num_inference_steps": steps,
        }
        if "turbo" in (_pipe_name or ""):
            kwargs["guidance_scale"] = 0.0
        kwargs["width"] = int(body.width or 1024)
        kwargs["height"] = int(body.height or 1024)
        out = pipe(**kwargs)
        img = out.images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        del out, img, buf
        _cuda_cleanup()
        return {
            "success": True,
            "image_data": b64,
            "provider": f"Colab-GPU/{_pipe_name}",
            "warmed": _warmed,
            "vram": _vram_stats(),
        }
    except HTTPException:
        raise
    except Exception as e:
        _cuda_cleanup()
        raise HTTPException(status_code=500, detail=f"Image gen failed: {e}")


# ---------------------------------------------------------------------------
# Registration / heartbeat helpers
# ---------------------------------------------------------------------------
def register_with_main_app(public_url: str, kind: str = "colab") -> None:
    main = (os.getenv("MAIN_APP_URL") or "").strip().rstrip("/")
    if not main:
        print("MAIN_APP_URL not set — skip auto-register")
        return
    secret = (os.getenv("WORKER_SECRET") or os.getenv("COLAB_WORKER_SECRET") or "").strip()
    payload = {
        "url": public_url.rstrip("/"),
        "kind": kind,
        "secret": secret,
        "meta": {"gpu": _gpu_name(), "host": kind, "warmed": _warmed},
    }
    try:
        import requests as req
        r = req.post(f"{main}/api/workers/register", json=payload, timeout=20)
        print("Register →", main, r.status_code, r.text[:200])
    except Exception as e:
        print("Register failed:", e)


def heartbeat_loop(public_url: str, interval: int = 120) -> None:
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
                    json={"url": public_url.rstrip("/"), "secret": secret, "warmed": _warmed},
                    timeout=15,
                )
            except Exception:
                pass
            _t.sleep(interval)

    threading.Thread(target=_run, daemon=True).start()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    print(f"[worker] Starting on 0.0.0.0:{port}  (warmup runs in background)")
    uvicorn.run(app, host="0.0.0.0", port=port)
