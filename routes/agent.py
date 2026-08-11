"""Agent status and skill suggestion API."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List

from services.agent_orchestrator import agent_orchestrator

router = APIRouter(prefix="/agent", tags=["agent"])


class SuggestIn(BaseModel):
    query: str = Field(default="", max_length=4000)


@router.get("/status")
def agent_status():
    return agent_orchestrator.get_status()


@router.post("/suggest")
def agent_suggest(body: SuggestIn):
    skills = agent_orchestrator.suggest_skill(body.query or "")
    return {"skills": skills}


@router.post("/warmup")
def agent_warmup():
    return agent_orchestrator.warmup_colab()
