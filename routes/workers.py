"""Colab/Kaggle GPU worker registration and status API."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from services import colab_worker as cw

router = APIRouter(prefix="/api/workers", tags=["workers"])


class RegisterIn(BaseModel):
    url: str = Field(..., min_length=8, max_length=500)
    kind: str = Field(default="colab", max_length=32)
    secret: str = Field(default="", max_length=200)
    meta: Optional[Dict[str, Any]] = None


class HeartbeatIn(BaseModel):
    url: str = Field(..., min_length=8, max_length=500)
    secret: str = Field(default="", max_length=200)


@router.get("")
@router.get("/")
def list_workers():
    """Public status for Boost UI / header indicator."""
    data = cw.list_workers()
    # Enrich with live probe summary (best-effort, short timeout)
    live = {"workers": [], "any_live": False}
    try:
        if hasattr(cw, "health"):
            h = cw.health()
            if isinstance(h, dict):
                live = h
    except Exception:
        pass
    return {
        **data,
        "live": live,
        "enabled": cw.is_enabled(),
        "live_ok": cw.is_live() if hasattr(cw, "is_live") else False,
    }


@router.post("/register")
def register(body: RegisterIn):
    try:
        return cw.register_worker(
            body.url, kind=body.kind, secret=body.secret, meta=body.meta
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/heartbeat")
def heartbeat(body: HeartbeatIn):
    try:
        return cw.heartbeat_worker(body.url, secret=body.secret)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.delete("")
def unregister(
    url: str,
    x_worker_secret: Optional[str] = Header(default=None, alias="X-Worker-Secret"),
):
    try:
        return cw.unregister_worker(url, secret=x_worker_secret or "")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
