"""Normalized model catalog API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from routes.login import get_current_active_user
from services import model_catalog as catalog

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("")
@router.get("/")
async def list_models(request: Request, current_user: dict = Depends(get_current_active_user)):
    keys = {}
    # optional per-user keys from headers already handled elsewhere
    return catalog.snapshot(keys)


@router.get("/migrate")
async def migrate_hint(model_id: str = ""):
    mid = catalog.migrate_model_id(model_id)
    return {
        "ok": True,
        "requested": model_id,
        "resolved": mid,
        "shutdown": catalog.is_shutdown(model_id),
        "changed": mid != model_id,
    }
