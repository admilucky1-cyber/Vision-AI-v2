"""
Vision AI Studio engine — image/video generation via existing workers + fallbacks.
Train-once / reuse LoRA is the long-term path; this module queues jobs and routes GPU work.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from services import model_registry as reg

logger = logging.getLogger("vision-ai.studio")


async def generate_image(
    *,
    prompt: str,
    model_id: str = "sdxl-turbo",
    lora_id: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    steps: int = 4,
    user: Optional[dict] = None,
) -> Dict[str, Any]:
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "error": "Prompt is required"}

    model = reg.get_model(model_id) or reg.get_model("pollinations-fallback")
    job = reg.create_job({
        "type": "image_generate",
        "prompt": prompt[:2000],
        "model_id": model_id,
        "lora_id": lora_id,
        "user": (user or {}).get("username"),
        "status": "running",
    })

    images: List[dict] = []
    provider = "none"
    error = None

    # 1) Colab / registered GPU worker
    try:
        from services import colab_worker as cw
        if hasattr(cw, "is_live") and cw.is_live():
            result = cw.generate_image(prompt, width=width, height=height)
            if result and result.get("image"):
                images.append({"provider": "colab", "data": result.get("image"), "mime": result.get("mime", "image/png")})
                provider = "colab"
    except Exception as e:
        logger.info("colab image skip: %s", e)

    # 2) Existing multi-engine image_gen / flux
    if not images:
        try:
            from services.image_gen import generate_all_diagrams
            imgs = await generate_all_diagrams("", "creative", user_message=prompt)
            if imgs:
                images = imgs if isinstance(imgs, list) else [imgs]
                provider = "image_gen"
        except Exception as e:
            logger.info("image_gen skip: %s", e)
            error = str(e)[:200]

    if not images:
        try:
            from services.flux_image import generate_image_with_fallback
            result = await generate_image_with_fallback(prompt, width=width, height=height)
            if result and (result.get("image") or result.get("url")):
                images.append(result)
                provider = result.get("provider") or "flux_fallback"
        except Exception as e:
            logger.info("flux fallback skip: %s", e)
            error = str(e)[:200]

    ok = bool(images)
    reg.update_job(
        job["id"],
        status="done" if ok else "failed",
        provider=provider,
        error=None if ok else (error or "No image provider available"),
        result_count=len(images),
    )
    return {
        "ok": ok,
        "job_id": job["id"],
        "model": model,
        "lora_id": lora_id,
        "provider": provider,
        "images": images,
        "error": None if ok else (error or "Generation failed — start Colab Boost or configure HF token"),
    }


def queue_lora_train(
    *,
    dataset_id: str,
    base_model: str,
    rank: int = 16,
    epochs: int = 10,
    resolution: int = 1024,
    user: Optional[dict] = None,
) -> Dict[str, Any]:
    """Queue LoRA training on Colab/Kaggle (does not run training inside Railway)."""
    job = reg.create_job({
        "type": "lora_train",
        "dataset_id": dataset_id,
        "base_model": base_model,
        "rank": rank,
        "epochs": epochs,
        "resolution": resolution,
        "user": (user or {}).get("username"),
        "status": "queued",
        "message": "Queued for GPU worker. Colab should pull this job, train, save LoRA to Drive, then register_lora.",
    })
    return {"ok": True, "job": job}


def queue_video(
    *,
    prompt: str,
    mode: str = "t2v",
    model_id: str = "svd-xt",
    user: Optional[dict] = None,
) -> Dict[str, Any]:
    job = reg.create_job({
        "type": "video_generate",
        "prompt": (prompt or "")[:2000],
        "mode": mode,
        "model_id": model_id,
        "user": (user or {}).get("username"),
        "status": "queued",
        "message": "Video jobs require a live Colab/Kaggle worker with SVD or similar loaded.",
    })
    return {
        "ok": True,
        "job": job,
        "note": "Short clips only on free T4 — not 60s HD. Worker must claim this job.",
    }
