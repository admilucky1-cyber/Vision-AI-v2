"""Vision AI Model Studio API — models, generate, train queue, jobs."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from routes.login import get_current_active_user
from services import model_registry as reg
from services import studio_engine as engine
from services.quota import can_generate_images

router = APIRouter(prefix="/api/studio", tags=["Studio"])


class GenerateIn(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    model_id: str = Field(default="sdxl-turbo", max_length=64)
    lora_id: Optional[str] = Field(default=None, max_length=64)
    width: int = Field(default=1024, ge=256, le=1536)
    height: int = Field(default=1024, ge=256, le=1536)


class TrainIn(BaseModel):
    dataset_id: str = Field(..., min_length=1, max_length=64)
    base_model: str = Field(default="flux-schnell", max_length=64)
    rank: int = Field(default=16, ge=4, le=128)
    epochs: int = Field(default=10, ge=1, le=50)
    resolution: int = Field(default=1024, ge=512, le=1024)


class VideoIn(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    mode: str = Field(default="t2v", max_length=16)
    model_id: str = Field(default="svd-xt", max_length=64)


class DatasetIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    drive_path: str = Field(default="", max_length=500)
    image_count: int = Field(default=0, ge=0)


@router.get("/status")
async def studio_status():
    return {"ok": True, "registry": reg.snapshot()}


@router.get("/models")
async def studio_models(type: Optional[str] = None):
    return {"models": reg.list_models(type)}


@router.get("/loras")
async def studio_loras(model_id: Optional[str] = None):
    return {"loras": reg.list_loras(model_id)}


@router.get("/storage")
async def studio_storage():
    return reg.storage_map()


@router.get("/jobs")
async def studio_jobs(
    current_user: dict = Depends(get_current_active_user),
    limit: int = 30,
):
    jobs = reg.list_jobs(limit=min(limit, 100))
    # non-admin only sees own jobs
    if (current_user.get("role") or "") != "admin" and not current_user.get("is_admin"):
        uname = current_user.get("username")
        jobs = [j for j in jobs if j.get("user") == uname]
    return {"jobs": jobs}


@router.get("/jobs/{job_id}")
async def studio_job(job_id: str, current_user: dict = Depends(get_current_active_user)):
    job = reg.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/generate")
async def studio_generate(
    body: GenerateIn,
    current_user: dict = Depends(get_current_active_user),
):
    plan = (current_user.get("plan") or "free").lower()
    ok, msg = can_generate_images(is_guest=bool(current_user.get("is_guest")), plan=plan)
    if not ok:
        raise HTTPException(402, detail=msg)
    result = await engine.generate_image(
        prompt=body.prompt,
        model_id=body.model_id,
        lora_id=body.lora_id,
        width=body.width,
        height=body.height,
        user=current_user,
    )
    if not result.get("ok"):
        raise HTTPException(503, detail=result.get("error") or "Generation failed")
    return result


@router.post("/train")
async def studio_train(
    body: TrainIn,
    current_user: dict = Depends(get_current_active_user),
):
    plan = (current_user.get("plan") or "free").lower()
    if current_user.get("is_guest") or plan in ("free", "guest"):
        raise HTTPException(402, detail="LoRA training requires a paid plan and a live GPU worker")
    return engine.queue_lora_train(
        dataset_id=body.dataset_id,
        base_model=body.base_model,
        rank=body.rank,
        epochs=body.epochs,
        resolution=body.resolution,
        user=current_user,
    )


@router.post("/video")
async def studio_video(
    body: VideoIn,
    current_user: dict = Depends(get_current_active_user),
):
    plan = (current_user.get("plan") or "free").lower()
    if current_user.get("is_guest") or plan in ("free", "guest"):
        raise HTTPException(402, detail="Video generation requires a paid plan and GPU worker")
    return engine.queue_video(
        prompt=body.prompt,
        mode=body.mode,
        model_id=body.model_id,
        user=current_user,
    )


@router.post("/datasets")
async def studio_register_dataset(
    body: DatasetIn,
    current_user: dict = Depends(get_current_active_user),
):
    if current_user.get("is_guest"):
        raise HTTPException(401, detail="Sign in required")
    entry = reg.register_dataset({
        "name": body.name,
        "description": body.description,
        "drive_path": body.drive_path,
        "image_count": body.image_count,
        "owner": current_user.get("username"),
    })
    return {"ok": True, "dataset": entry}
