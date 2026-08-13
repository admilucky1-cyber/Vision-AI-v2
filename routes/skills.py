"""Skill market API — list / run / install (server-side registry)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

from services.skill_router import skill_router

router = APIRouter(prefix="/api/skills", tags=["skills"])


class RunIn(BaseModel):
    skill_id: str
    prompt: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)


class InstallIn(BaseModel):
    name: str
    code: str
    description: str = ""


@router.get("")
def list_skills():
    return {"skills": skill_router.list_skills()}


@router.post("/run")
def run_skill(body: RunIn):
    return {"result": skill_router.run(body.skill_id, body.prompt, body.context)}


@router.post("/install")
def install_skill(body: InstallIn):
    out = skill_router.install_skill(body.name, body.code, body.description)
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=out.get("error") or "install failed")
    return out


@router.delete("/{skill_id}")
def remove_skill(skill_id: str):
    out = skill_router.remove_skill(skill_id)
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=out.get("error") or "remove failed")
    return out


@router.get("/suggest")
def suggest(q: str = ""):
    return {"suggestion": skill_router.suggest_skill(q)}
