"""
Vision AI — Model / LoRA registry (Drive-aware architecture).

Storage principle:
  Google Drive = archive   |   Colab/Kaggle = compute only
  Registry JSON lives on the app (Railway data/) and points at Drive paths.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("vision-ai.model_registry")

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
REGISTRY_PATH = DATA / "model_registry.json"
_LOCK = threading.RLock()

DEFAULT_REGISTRY: Dict[str, Any] = {
    "version": 1,
    "updated": 0,
    "storage": {
        "accounts": {
            "A_images": {
                "label": "IMAGE_MODELS",
                "drive_folder": os.getenv("DRIVE_IMAGE_MODELS", "VISION-AI-STORAGE/IMAGE_MODELS"),
            },
            "B_videos": {
                "label": "VIDEO_MODELS",
                "drive_folder": os.getenv("DRIVE_VIDEO_MODELS", "VISION-AI-STORAGE/VIDEO_MODELS"),
            },
            "C_datasets": {
                "label": "DATASETS",
                "drive_folder": os.getenv("DRIVE_DATASETS", "VISION-AI-STORAGE/DATASETS"),
            },
        }
    },
    "models": [
        {
            "id": "sdxl-turbo",
            "name": "SDXL Turbo",
            "type": "image",
            "family": "sdxl",
            "source": "huggingface",
            "hf_id": "stabilityai/sdxl-turbo",
            "license": "openrail++",
            "vram_gb": 6,
            "workflows": ["t2i", "batch"],
            "loras": [],
            "drive_path": "VISION-AI-STORAGE/IMAGE_MODELS/sdxl-turbo",
            "enabled": True,
        },
        {
            "id": "flux-schnell",
            "name": "FLUX.1 Schnell",
            "type": "image",
            "family": "flux",
            "source": "huggingface",
            "hf_id": "black-forest-labs/FLUX.1-schnell",
            "license": "apache-2.0",
            "vram_gb": 12,
            "workflows": ["t2i", "i2i"],
            "loras": [],
            "drive_path": "VISION-AI-STORAGE/IMAGE_MODELS/flux-schnell",
            "enabled": True,
        },
        {
            "id": "pollinations-fallback",
            "name": "Pollinations (free fallback)",
            "type": "image",
            "family": "api",
            "source": "pollinations",
            "vram_gb": 0,
            "workflows": ["t2i"],
            "loras": [],
            "enabled": True,
        },
        {
            "id": "svd-xt",
            "name": "Stable Video Diffusion XT",
            "type": "video",
            "family": "svd",
            "source": "huggingface",
            "hf_id": "stabilityai/stable-video-diffusion-img2vid-xt",
            "vram_gb": 16,
            "workflows": ["i2v"],
            "loras": [],
            "drive_path": "VISION-AI-STORAGE/VIDEO_MODELS/svd-xt",
            "enabled": True,
            "notes": "Short clips only on free T4; not 60s HD",
        },
    ],
    "loras": [],
    "datasets": [],
    "jobs": [],
}


def _load() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        data = json.loads(json.dumps(DEFAULT_REGISTRY))
        data["updated"] = time.time()
        _save(data)
        return data
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return json.loads(json.dumps(DEFAULT_REGISTRY))
        # merge defaults for missing keys
        for k, v in DEFAULT_REGISTRY.items():
            data.setdefault(k, v)
        return data
    except Exception as e:
        logger.warning("registry load failed: %s", e)
        return json.loads(json.dumps(DEFAULT_REGISTRY))


def _save(data: Dict[str, Any]) -> None:
    data["updated"] = time.time()
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(REGISTRY_PATH)


def list_models(kind: Optional[str] = None) -> List[Dict[str, Any]]:
    with _LOCK:
        data = _load()
        models = data.get("models") or []
        if kind:
            models = [m for m in models if m.get("type") == kind]
        return [m for m in models if m.get("enabled", True)]


def get_model(model_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        data = _load()
        for m in data.get("models") or []:
            if m.get("id") == model_id:
                return m
        return None


def list_loras(model_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with _LOCK:
        data = _load()
        loras = data.get("loras") or []
        if model_id:
            loras = [l for l in loras if model_id in (l.get("base_models") or []) or l.get("base_model") == model_id]
        return loras


def register_lora(entry: Dict[str, Any]) -> Dict[str, Any]:
    with _LOCK:
        data = _load()
        entry = dict(entry)
        entry.setdefault("id", f"lora_{uuid.uuid4().hex[:10]}")
        entry.setdefault("created", time.time())
        data.setdefault("loras", []).append(entry)
        _save(data)
        return entry


def register_dataset(entry: Dict[str, Any]) -> Dict[str, Any]:
    with _LOCK:
        data = _load()
        entry = dict(entry)
        entry.setdefault("id", f"ds_{uuid.uuid4().hex[:10]}")
        entry.setdefault("created", time.time())
        data.setdefault("datasets", []).append(entry)
        _save(data)
        return entry


def create_job(job: Dict[str, Any]) -> Dict[str, Any]:
    with _LOCK:
        data = _load()
        job = dict(job)
        job.setdefault("id", f"job_{uuid.uuid4().hex[:12]}")
        job.setdefault("status", "queued")
        job.setdefault("created", time.time())
        job.setdefault("updated", time.time())
        data.setdefault("jobs", []).insert(0, job)
        data["jobs"] = data["jobs"][:200]
        _save(data)
        return job


def update_job(job_id: str, **fields) -> Optional[Dict[str, Any]]:
    with _LOCK:
        data = _load()
        for j in data.get("jobs") or []:
            if j.get("id") == job_id:
                j.update(fields)
                j["updated"] = time.time()
                _save(data)
                return j
        return None


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        data = _load()
        for j in data.get("jobs") or []:
            if j.get("id") == job_id:
                return j
        return None


def list_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    with _LOCK:
        data = _load()
        return (data.get("jobs") or [])[:limit]


def storage_map() -> Dict[str, Any]:
    with _LOCK:
        return (_load().get("storage") or {})


def snapshot() -> Dict[str, Any]:
    with _LOCK:
        data = _load()
        return {
            "version": data.get("version"),
            "updated": data.get("updated"),
            "models": len(data.get("models") or []),
            "loras": len(data.get("loras") or []),
            "datasets": len(data.get("datasets") or []),
            "jobs": len(data.get("jobs") or []),
            "storage": data.get("storage"),
        }
