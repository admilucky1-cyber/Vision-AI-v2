"""
Vision AI v2.0 - Chat Router
============================
Real-Time Agentic RAG with auto web search, document processing, and diagrams.
Production-ready with JWT authentication, detailed request logging, and caching.
"""

import time
import hashlib
import traceback
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Form, UploadFile, File, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address

# ==========================================================
# 🔥 DEBUG BLOCK: Force imports to fail loudly if missing
# ==========================================================
print("\n🔍 DEBUG: Loading chat.py dependencies...")
try:
    from services.llm import ask_ai
    print("✅ services.llm loaded successfully")
except ImportError as e:
    print(f"❌ CRITICAL ERROR: services.llm failed to load: {e}")
    raise e

try:
    from services.multimodal import process_uploaded_file
    print("✅ services.multimodal loaded successfully")
except ImportError as e:
    print(f"❌ CRITICAL ERROR: services.multimodal failed to load: {e}")
    raise e

try:
    from services.search import search_web, is_search_needed, auto_search_context, get_current_info
    print("✅ services.search loaded successfully")
except ImportError as e:
    print(f"❌ CRITICAL ERROR: services.search failed to load: {e}")
    raise e

try:
    from services.self_optimizer import optimizer
    print("✅ services.self_optimizer loaded successfully")
except ImportError as e:
    print(f"❌ CRITICAL ERROR: services.self_optimizer failed to load: {e}")
    raise e

try:
    from services.image_gen import generate_all_diagrams
    print("✅ services.image_gen loaded successfully")
except ImportError as e:
    print(f"❌ CRITICAL ERROR: services.image_gen failed to load: {e}")
    raise e

try:
    from routes.login import get_current_active_user
    print("✅ routes.login loaded successfully")
except ImportError as e:
    print(f"❌ CRITICAL ERROR: routes.login failed to load: {e}")
    raise e

print("🔍 DEBUG: All dependencies loaded successfully!\n")
# ==========================================================

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# ==========================================================
# RAG CACHE
# ==========================================================
class RAGCache:
    """Thread-safe RAG cache with LRU eviction."""

    def __init__(self, max_size: int = 5):
        self._cache: dict = {}
        self._max_size = max_size

    def get_key(self, filename: str, content: str) -> str:
        return hashlib.md5(f"{filename}:{content[:500]}".encode()).hexdigest()

    def get(self, key: str) -> Optional[dict]:
        return self._cache.get(key)

    def set(self, key: str, data: dict):
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest]
        self._cache[key] = data

    def clear(self):
        self._cache.clear()

rag_cache = RAGCache(max_size=5)

# ==========================================================
# RESPONSE MODEL
# ==========================================================
class ChatResponse(BaseModel):
    answer: str
    model_used: str
    context_length: int
    response_time: float
    reasoning_style: str
    rag_files_loaded: int
    search_performed: bool
    images_generated: int = 0
    images: List[dict] = Field(default_factory=list)
    current_time: str

# ==========================================================
# CHAT ENDPOINT
# ==========================================================
@router.post("/chat/send", response_model=ChatResponse)
@limiter.limit("30/minute")
async def chat_send(
    request: Request,
    message: str = Form(..., min_length=1, max_length=10000, description="User message"),
    files: List[UploadFile] = File(default=[], description="Optional files for RAG"),
    model: str = Form("auto", description="AI model to use: auto, gemini, groq, deepseek, openrouter"),
    generate_images: bool = Form(True, description="Auto-generate diagrams if detected"),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Send a chat message with optional file uploads.
    """
    start_time = time.time()
    user_name = current_user.get("full_name", "User")
    request_id = str(uuid.uuid4()) 

    print("\n" + "=" * 70)
    print(f"🤖 [VISION AI] New Request from {user_name}")
    print(f"🆔 Request ID: {request_id}")
    print("=" * 70)

    try:
        extra_context = ""
        file_names = []
        file_texts = []

        # ========================================================
        # 1. RAG: Process Uploaded Files
        # ========================================================
        if files:
            print(f"📄 Processing {len(files)} file(s) for RAG...")
            for file in files:
                try:
                    if file.size > 50 * 1024 * 1024:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File {file.filename} exceeds 50MB limit"
                        )

                    file_names.append(file.filename)
                    content = await process_uploaded_file(file)

                    cache_key = rag_cache.get_key(file.filename, content)
                    rag_cache.set(cache_key, {
                        "filename": file.filename,
                        "content": content,
                        "timestamp": time.time(),
                    })

                    file_texts.append(f"[Uploaded File: {file.filename}]\n{content}")
                    print(f"   ✅ Cached: {file.filename} ({len(content)} chars)")
                except HTTPException:
                    raise
                except Exception as e:
                    print(f"   ❌ Failed: {file.filename} - {e}")
                    file_texts.append(f"[File: {file.filename}] Could not process.")

            if file_texts:
                extra_context = "\n\n".join(file_texts)

        # 🔥 CRITICAL FIX: Re-inject the last uploaded file for follow-up questions
        # If the user asks a follow-up without uploading a new file, we retrieve
        # the most recent file from the RAG cache and re-inject it.
        if not files and len(rag_cache._cache) > 0:
            # Get the most recent file from the cache
            latest_key = max(rag_cache._cache.keys(), key=lambda k: rag_cache._cache[k]["timestamp"])
            latest_file = rag_cache.get(latest_key)
            if latest_file and latest_file.get("content"):
                file_texts.append(f"[Uploaded File: {latest_file['filename']}]\n{latest_file['content']}")
                print(f"♻️ Re-injecting previous file context: {latest_file['filename']}")
                extra_context = "\n\n".join(file_texts)

        # ========================================================
        # 2. AUTO REAL-TIME WEB SEARCH
        # ========================================================
        current_time_context = f"[CURRENT DATE & TIME: {get_current_info()}]"
        extra_context = current_time_context + "\n" + extra_context

        # Auto-detect if search is needed
        real_time_results = auto_search_context(message, extra_context)
        if real_time_results and not real_time_results.startswith("[Web search unavailable"):
            extra_context += f"\n\n[REAL-TIME LIVE DATA FROM WEB]\n{real_time_results}"
            print(f"🌐 Auto real-time data injected ({len(real_time_results)} chars)")

        if is_search_needed(message):
            print(f"🔍 Explicit web search triggered for: '{message[:80]}...'")
            try:
                web_results = search_web(message, max_results=5, use_cache=False)
                if web_results and not web_results.startswith("[No search"):
                    extra_context += f"\n\n[DEDICATED WEB SEARCH RESULTS]\n{web_results}"
                    print(f"   ✅ Search results added ({len(web_results)} chars)")
                else:
                    print(f"   ⚠️ Search returned no results.")
            except Exception as e:
                print(f"   ❌ Search error: {e}")

        # ========================================================
        # 3. GET AI RESPONSE
        # ========================================================
        print(f"🤖 Calling AI model: {model}...")
        print(f"   Total Context Size: {len(extra_context)} chars")

        reasoning = optimizer.get_reasoning_recommendation(message)
        answer = ask_ai(question=message, context=extra_context, backend=model)
        response_time = time.time() - start_time

        # ========================================================
        # 4. GENERATE DIAGRAMS
        # ========================================================
        images = []
        if generate_images:
            try:
                from services.llm import detect_subject
                subject = detect_subject(message, extra_context)
                images = await generate_all_diagrams(answer, subject)
                if images:
                    print(f"🖼️ Generated {len(images)} diagram(s)")
            except Exception:
                pass 

        # ========================================================
        # 5. RECORD TO OPTIMIZER
        # ========================================================
        try:
            from services.llm import detect_subject
            subject = detect_subject(message, extra_context)
            optimizer.learn_from_interaction(
                question=message,
                answer=answer[:500],
                subject=subject,
                provider=model,
                success=not answer.startswith("[Error"),
                response_time=response_time,
                image_count=len(images),
            )
        except Exception:
            pass

        print("=" * 70)
        print(f"✅ FINAL RESPONSE DELIVERED")
        print(f"   Text: {len(answer)} chars")
        print(f"   Time: {response_time:.1f}s")
        print(f"   Request ID: {request_id}")
        print("=" * 70)

        # Normalize image dicts for the frontend, which expects a `data`
        # field on each image (frontend/static/js/index.js: img.data).
        # The generators return `image_data` internally, so map it here
        # rather than changing every generator function.
        response_images = [
            {**img, "data": img.get("image_data", "")}
            for img in images
            if img.get("image_data")
        ]

        return ChatResponse(
            answer=answer,
            model_used=model,
            context_length=len(extra_context),
            response_time=round(response_time, 2),
            reasoning_style=reasoning["style"],
            rag_files_loaded=len(files),
            search_performed=bool(real_time_results or is_search_needed(message)),
            images_generated=len(images),
            images=response_images,
            current_time=datetime.utcnow().isoformat() + "Z",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ FATAL CHAT ERROR:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )

@router.get("/chat/health")
async def chat_health():
    return {
        "status": "healthy",
        "rag_cache_size": len(rag_cache._cache),
        "optimizer_available": optimizer is not None,
    }

@router.post("/chat/clear-cache")
async def clear_rag_cache(current_user: dict = Depends(get_current_active_user)):
    rag_cache.clear()
    return {"message": "RAG cache cleared"}