"""
Vision AI v3.0 — API Vault
Secure provider registry, env-based keys, fallback routing, connection tests.
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("vision-ai.api_vault")


class ProviderVault:
    """Maps logical providers to environment variable names and supports fallbacks."""

    PROVIDERS: Dict[str, Dict[str, Any]] = {
        "openai": {
            "env": ["OPENAI_API_KEY"],
            "test_url": "https://api.openai.com/v1/models",
            "auth": "bearer",
        },
        "claude": {
            "env": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
            "test_url": "https://api.anthropic.com/v1/models",
            "auth": "x-api-key",
            "extra_headers": {"anthropic-version": "2023-06-01"},
        },
        "grok": {
            "env": ["XAI_API_KEY", "GROK_API_KEY"],
            "test_url": "https://api.x.ai/v1/models",
            "auth": "bearer",
        },
        "deepseek": {
            "env": ["DEEPSEEK_API_KEY"],
            "test_url": "https://api.deepseek.com/models",
            "auth": "bearer",
        },
        "gemini": {
            "env": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
            "test_url": None,  # tested via query param style
            "auth": "query",
        },
        "mistral": {
            "env": ["MISTRAL_API_KEY"],
            "test_url": "https://api.mistral.ai/v1/models",
            "auth": "bearer",
        },
        "huggingface": {
            "env": ["HF_TOKEN", "HUGGINGFACE_TOKEN"],
            "test_url": "https://huggingface.co/api/whoami-v2",
            "auth": "bearer",
        },
        "replicate": {
            "env": ["REPLICATE_API_TOKEN"],
            "test_url": "https://api.replicate.com/v1/account",
            "auth": "token",
        },
        "runpod": {
            "env": ["RUNPOD_API_KEY"],
            "test_url": "https://api.runpod.ai/v2",
            "auth": "bearer",
        },
        "groq": {
            "env": ["GROQ_API_KEY"],
            "test_url": "https://api.groq.com/openai/v1/models",
            "auth": "bearer",
        },
        "openrouter": {
            "env": ["OPENROUTER_API_KEY"],
            "test_url": "https://openrouter.ai/api/v1/models",
            "auth": "bearer",
        },
    }

    # Preferred chat cascade (aligns with existing llm.py spirit)
    CHAT_FALLBACK_ORDER: List[str] = [
        "groq", "gemini", "openrouter", "deepseek", "openai", "claude", "mistral", "grok",
    ]

    def __init__(self) -> None:
        self._cache: Dict[str, Optional[str]] = {}

    def get_key(self, provider: str) -> Optional[str]:
        provider = (provider or "").lower().strip()
        if provider in self._cache:
            return self._cache[provider]
        meta = self.PROVIDERS.get(provider)
        if not meta:
            self._cache[provider] = None
            return None
        for env_name in meta["env"]:
            val = (os.getenv(env_name) or "").strip()
            if val:
                self._cache[provider] = val
                return val
        self._cache[provider] = None
        return None

    def list_configured(self) -> List[str]:
        return [p for p in self.PROVIDERS if self.get_key(p)]

    def get_optimal_provider(
        self,
        preferred: Optional[str] = None,
        purpose: str = "chat",
    ) -> Tuple[Optional[str], Optional[str]]:
        """Return (provider_name, api_key) using preferred then fallback order."""
        order = list(self.CHAT_FALLBACK_ORDER)
        if purpose == "image":
            order = ["huggingface", "replicate", "runpod", "openai"]
        if preferred:
            preferred = preferred.lower().strip()
            if preferred in order:
                order.remove(preferred)
            order.insert(0, preferred)
        for name in order:
            key = self.get_key(name)
            if key:
                return name, key
        return None, None

    def test_connection(self, provider: str, key: Optional[str] = None) -> Dict[str, Any]:
        """Lightweight connectivity probe. Does not store the key."""
        import requests

        provider = (provider or "").lower().strip()
        meta = self.PROVIDERS.get(provider)
        if not meta:
            return {"ok": False, "provider": provider, "error": "unknown provider"}
        api_key = (key or self.get_key(provider) or "").strip()
        if not api_key:
            return {"ok": False, "provider": provider, "error": "no API key configured"}

        url = meta.get("test_url")
        if not url:
            if provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                try:
                    r = requests.get(url, timeout=12)
                    return {
                        "ok": r.status_code < 400,
                        "provider": provider,
                        "status": r.status_code,
                    }
                except Exception as e:
                    return {"ok": False, "provider": provider, "error": str(e)}
            return {"ok": True, "provider": provider, "note": "no probe URL; key present"}

        headers: Dict[str, str] = {}
        auth = meta.get("auth")
        if auth == "bearer":
            headers["Authorization"] = f"Bearer {api_key}"
        elif auth == "x-api-key":
            headers["x-api-key"] = api_key
        elif auth == "token":
            headers["Authorization"] = f"Token {api_key}"
        extra = meta.get("extra_headers") or {}
        headers.update(extra)

        try:
            r = requests.get(url, headers=headers, timeout=12)
            ok = r.status_code < 400
            return {
                "ok": ok,
                "provider": provider,
                "status": r.status_code,
                "error": None if ok else (r.text or "")[:200],
            }
        except Exception as e:
            logger.warning("vault test %s failed: %s", provider, e)
            return {"ok": False, "provider": provider, "error": str(e)}


# Module singleton
vault = ProviderVault()

__all__ = ["ProviderVault", "vault"]
