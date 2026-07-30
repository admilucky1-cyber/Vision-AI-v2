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
import re
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Form, UploadFile, File, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

import logging
logger = logging.getLogger("vision-ai.chat")

from services.llm import ask_ai
from services.multimodal import process_uploaded_file
from services.search import search_web, is_search_needed, auto_search_context, get_current_info
from services.self_optimizer import optimizer
from services.image_gen import generate_all_diagrams
from routes.login import get_current_active_user

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# ==========================================================
# RAG CACHE
# ==========================================================
class RAGCache:
    def __init__(self, max_size: int = 5):
        self._cache = {}
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

    def get_latest(self) -> Optional[dict]:
        if not self._cache:
            return None
        latest_key = max(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
        return self._cache.get(latest_key)

rag_cache = RAGCache(max_size=5)

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

@router.post("/chat/send", response_model=ChatResponse)
@limiter.limit("30/minute")
async def chat_send(
    request: Request,
    message: str = Form(..., min_length=1, max_length=10000),
    files: List[UploadFile] = File(default=[]),
    model: str = Form("auto"),
    generate_images: bool = Form(True),
    current_user: dict = Depends(get_current_active_user),
):
    start_time = time.time()
    user_name = current_user.get("full_name", "User")
    request_id = str(uuid.uuid4())

    # --- Production plan limits ---
    try:
        from routes.upgrade import PlanConfig
        from routes.login import user_db
        plan_id = (current_user.get("plan") or "free").lower()
        plan = PlanConfig.get_plan(plan_id) or PlanConfig.get_plan("free")
        limit = (plan or {}).get("limits", {}).get("messages_per_month", 1000)
        if limit is not None and int(limit) >= 0:
            # refresh usage from persisted user
            fresh = user_db.get_user(current_user.get("username", "")) or current_user
            month = __import__("datetime").datetime.utcnow().strftime("%Y-%m")
            used = int(fresh.get("messages_this_month") or 0)
            if fresh.get("usage_month") != month:
                used = 0
            if used >= int(limit):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Monthly message limit reached ({limit}). Upgrade your plan at /upgrade.html",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.debug(f"Plan limit check skipped: {e}")

    logger.info(f"\n{'='*70}")
    logger.info(f"🤖 [VISION AI] New Request from {user_name}")
    logger.info(f"🆔 Request ID: {request_id}")
    logger.info(f"📝 Message: {message[:100]}...")
    logger.info(f"{'='*70}")

    try:
        extra_context = ""
        file_names = []
        file_texts = []
        
        # 🚀 =================================================================
        # ROUTER PRIORITY 1: FILES / DOCUMENT PROCESSING
        # =================================================================
        if files:
            logger.info(f"📄 Processing {len(files)} file(s) for RAG...")
            for file in files:
                try:
                    # UploadFile.size is not always available before reading; bound later if needed
                    file_names.append(file.filename)
                    content = await asyncio.to_thread(process_uploaded_file, file)
                    if len(content) > 50 * 1024 * 1024:
                        raise HTTPException(status_code=413, detail=f"File {file.filename} exceeds 50MB limit")

                    cache_key = rag_cache.get_key(file.filename, content)
                    rag_cache.set(cache_key, {"filename": file.filename, "content": content, "timestamp": time.time()})
                    # Classify common exam document types from filename
                    fn_lower = (file.filename or "").lower()
                    if "_ms_" in fn_lower or fn_lower.endswith("_ms.pdf") or "mark_scheme" in fn_lower or "markscheme" in fn_lower:
                        tag = "MARK SCHEME / ANSWER KEY"
                        hint = (
                            "This is an official mark scheme (answer key), NOT a question paper. "
                            "If the user asks to 'solve', interpret as: explain the answers, "
                            "show the physics reasoning behind each mark, and teach the concepts. "
                            "Do NOT invent different answers."
                        )
                    elif "_qp_" in fn_lower or "question" in fn_lower:
                        tag = "QUESTION PAPER"
                        hint = (
                            "This is a question paper. Solve each question the user asks about "
                            "with clear reasoning, then state the final answer. "
                            "If they ask to solve the whole paper, work through all questions systematically."
                        )
                    elif "_er_" in fn_lower or "examiner" in fn_lower:
                        tag = "EXAMINER REPORT"
                        hint = "This is an examiner report. Summarize common mistakes and teaching points."
                    else:
                        tag = "UPLOADED DOCUMENT"
                        hint = "Use this document as the primary source for answering the user."
                    file_texts.append(
                        f"[{tag}: {file.filename}]\n"
                        f"[DOCUMENT GUIDANCE: {hint}]\n"
                        f"{content}"
                    )
                    logger.info(f"   ✅ Cached: {file.filename} as {tag} ({len(content)} chars)")
                except Exception as e:
                    logger.error(f"   ❌ Failed: {file.filename} - {e}")
                    file_texts.append(f"[File: {file.filename}] Could not process.")

            if file_texts:
                extra_context = "\n\n".join(file_texts)
                logger.info(f"📄 Document context injected. Continuing to chat...")

        # Re-inject previous file context if no new files uploaded
        if not files and len(rag_cache._cache) > 0:
            latest_file = rag_cache.get_latest()
            if latest_file and latest_file.get("content"):
                fn = latest_file.get("filename") or "document"
                fn_lower = fn.lower()
                if "_ms_" in fn_lower or "mark_scheme" in fn_lower or "markscheme" in fn_lower:
                    tag = "MARK SCHEME / ANSWER KEY"
                elif "_qp_" in fn_lower or "question" in fn_lower:
                    tag = "QUESTION PAPER"
                elif "_er_" in fn_lower or "examiner" in fn_lower:
                    tag = "EXAMINER REPORT"
                else:
                    tag = "UPLOADED DOCUMENT"
                file_texts.append(f"[{tag}: {fn}]\n{latest_file['content']}")
                logger.info(f"♻️ Re-injecting previous file context: {fn} as {tag}")
                extra_context = "\n\n".join(file_texts)

        # 🚀 =================================================================
        # ROUTER PRIORITY 2: YOUTUBE URL DETECTION
        # =================================================================
        youtube_pattern = (
            r'(https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?[^\s]*?v=|embed/|shorts/|live/)|youtu\.be/)'
            r'([a-zA-Z0-9_-]{11})[^\s]*)'
        )
        match = re.search(youtube_pattern, message or "")
        youtube_context_loaded = False
        youtube_url = None
        if match:
            youtube_url = match.group(0).rstrip(').,]}"\'')
            logger.info(f"🎬 YouTube URL detected: {youtube_url}")
            msg_l = (message or "").lower()

            # Download intent: download/save/grab/dl OR media quality keywords with URL
            wants_download = bool(re.search(
                r"\b(download|save|grab|fetch|dl)\b",
                msg_l,
            )) or bool(re.search(
                r"\b(mp3|mp4|m4a|mkv|webm|flac|wav|1080p?|720p?|480p?|360p?|4k)\b|\.mp4|\.mp3",
                msg_l,
            ))

            if wants_download:
                try:
                    from services.youtube import download_video, get_direct_media_urls
                except ImportError:
                    from services.youtube import download_video
                    get_direct_media_urls = None

                height = 720
                quality = "medium"
                hm = re.search(r"\b(360|480|540|720|1080|1440|2160)p?\b", msg_l)
                if hm:
                    height = int(hm.group(1))
                    quality = f"{height}p"
                elif "best" in msg_l or "highest" in msg_l or "4k" in msg_l:
                    height = 2160
                    quality = "best"
                elif "low" in msg_l:
                    height = 360
                    quality = "low"

                audio_only = any(
                    k in msg_l
                    for k in (
                        "mp3", "m4a", "aac", "wav", "flac", "ogg",
                        "audio only", "download audio", "audio track",
                        "music", "song", "yt music", "youtube music",
                        "only audio", "extract audio",
                    )
                )
                audio_format = "mp3"
                for af in ("flac", "wav", "ogg", "aac", "m4a", "mp3"):
                    if af in msg_l:
                        audio_format = af
                        break
                video_format = "mp4"
                for vf in ("mkv", "webm", "avi", "mp4"):
                    if re.search(rf"\b{vf}\b", msg_l):
                        video_format = vf
                        break
                audio_bitrate = None
                bm = re.search(r"\b(64|96|128|160|192|256|320)\s*k(?:bps)?\b", msg_l)
                if bm:
                    audio_bitrate = int(bm.group(1))

                logger.info(
                    f"⬇️ Download intent: height={height} quality={quality} "
                    f"audio_only={audio_only} vfmt={video_format} afmt={audio_format} abr={audio_bitrate}"
                )

                force_server = any(
                    p in msg_l
                    for p in ("server download", "save on server", "permanent link", "host file")
                )
                # MP3 needs ffmpeg convert on server
                if audio_only and audio_format == "mp3" and "direct" not in msg_l:
                    force_server = True
                # High-res video: server merge is more reliable than progressive CDN links
                if (not audio_only) and height and int(height) >= 1080 and "direct" not in msg_l:
                    force_server = True
                answer = None
                result = {"status": "error", "error": "unknown"}

                try:
                    if not force_server and get_direct_media_urls is not None:
                        direct = await get_direct_media_urls(
                            youtube_url,
                            height=height or 1080,
                            audio_only=audio_only,
                            quality=quality or "best",
                            audio_bitrate=audio_bitrate,
                        )
                        if direct.get("status") == "success" and direct.get("primary_url"):
                            size_line = (
                                f"- **Est. size:** ~{direct['size_mb']} MB\n"
                                if direct.get("size_mb") else ""
                            )
                            title_line = (
                                f"- **Title:** {direct['title']}\n"
                                if direct.get("title") else ""
                            )
                            if audio_only:
                                btn = f"[⬇️ Start download audio]({direct['primary_url']})"
                                kind = f"audio ({direct.get('ext', 'm4a').upper()}"
                                if audio_bitrate:
                                    kind += f", ≤{audio_bitrate}k"
                                kind += ")"
                            else:
                                kind = (
                                    f"video (requested ≤{height}p, got "
                                    f"{direct.get('resolution') or 'n/a'}, "
                                    f"{direct.get('ext', 'mp4').upper()})"
                                )
                                if direct.get("audio_url"):
                                    btn = (
                                        f"- [⬇️ Start download video]({direct['primary_url']})\n"
                                        f"- [⬇️ Start download audio track]({direct['audio_url']})"
                                    )
                                else:
                                    btn = f"[⬇️ Start download video]({direct['primary_url']})"
                            # Quality gate: if user asked ≥720p but stream is much lower, use server merge
                            got_h = direct.get("height")
                            if not audio_only and height and got_h and int(got_h) < int(height) * 0.7:
                                logger.warning(
                                    f"Direct stream {got_h}p << requested {height}p — falling back to server download"
                                )
                                answer = None  # trigger server path below
                            else:
                                answer = (
                                    f"✅ **Direct link ready** — {kind}\n\n"
                                    f"{title_line}{size_line}"
                                    f"{btn}\n\n"
                                    f"⚡ Browser / IDM / FDM fetches from the CDN.\n"
                                    f"⚠️ Links usually expire within a few hours.\n\n"
                                    f"_Server copy: `server download mp4 {height}p <url>`_"
                                )
                                result = {"status": "success", "mode": "direct"}

                    if answer is None:
                        result = await download_video(
                            youtube_url,
                            height=height,
                            audio_only=audio_only,
                            quality=quality,
                            video_format=video_format,
                            audio_format=audio_format,
                        )
                        if result.get("status") == "success":
                            base = str(request.base_url).rstrip("/")
                            link = f"{base}/upload/downloads/{result['filename']}"
                            kind = (
                                f"audio ({audio_format.upper()})"
                                if audio_only
                                else f"video (≤{height}p, {video_format.upper()})"
                            )
                            note = result.get("note") or ""
                            note_line = f"\n\nℹ️ {note}" if note else ""
                            answer = (
                                f"✅ **Download ready** — {kind}\n\n"
                                f"- **File:** `{result['filename']}`\n"
                                f"- **Size:** {result['file_size_mb']} MB\n"
                                f"- **Link:** [⬇️ Download {result['filename']}]({link})\n\n"
                                f"Stored under `/downloads`. Older files are cleaned periodically."
                                f"{note_line}"
                            )
                        else:
                            answer = (
                                f"❌ **Download failed**\n\n"
                                f"{result.get('error') or 'Unknown error'}\n\n"
                                f"**Tips:** `pip install -U yt-dlp`, set `FFMPEG_LOCATION`, "
                                f"or place `cookies.txt` for restricted videos."
                            )
                except Exception as dl_err:
                    logger.exception("YouTube download pipeline error")
                    answer = f"❌ **Download failed**\n\n{dl_err}"

                return ChatResponse(
                    answer=answer,
                    model_used="youtube-download",
                    context_length=0,
                    response_time=round(time.time() - start_time, 2),
                    reasoning_style="download",
                    rag_files_loaded=0,
                    search_performed=False,
                    images_generated=0,
                    images=[],
                    current_time=datetime.utcnow().isoformat() + "Z",
                )

            # Non-download: inject transcript for Q&A
            try:
                from services.youtube import get_video_context
                yt = await get_video_context(youtube_url, max_transcript_chars=25000)
                if yt.get("context_block"):
                    extra_context += "\n\n" + yt["context_block"]
                    youtube_context_loaded = True
                    logger.info(
                        f"✅ YouTube data injected "
                        f"(transcript={'yes' if yt.get('has_transcript') else 'no'}, "
                        f"{len(yt.get('transcript') or '')} chars)"
                    )
            except Exception as e:
                logger.warning(f"⚠️ YouTube processing failed: {e}")

        # ROUTER PRIORITY 3: PURE GREETING (exact match only, before search)
        # =================================================================
        from services.llm import is_greeting as _is_pure_greeting

        if _is_pure_greeting(message) and not files and not match:
            logger.info("👋 Pure greeting detected (no files/urls). Returning greeting.")
            return ChatResponse(
                answer="Hello! I am VISION AI. How can I assist you today?",
                model_used="system",
                context_length=0,
                response_time=round(time.time() - start_time, 2),
                reasoning_style="greeting",
                rag_files_loaded=0,
                search_performed=False,
                images_generated=0,
                images=[],
                current_time=datetime.utcnow().isoformat() + "Z",
            )

        # 🚀 =================================================================
        # ROUTER PRIORITY 4: WEB SEARCH (skip when documents are the focus)
        # =================================================================
        current_time_context = f"[CURRENT DATE & TIME: {get_current_info()}]"
        extra_context = current_time_context + "\n" + extra_context

        search_performed = False
        has_document_context = bool(file_texts) or any(
            m in extra_context
            for m in ("[MARK SCHEME", "[QUESTION PAPER", "[UPLOADED DOCUMENT", "[EXAMINER REPORT")
        )
        has_youtube_context = youtube_context_loaded or "[YOUTUBE VIDEO]" in extra_context or "[VIDEO TRANSCRIPT" in extra_context

        force_search = is_search_needed(message)
        if (has_document_context or has_youtube_context) and not force_search:
            logger.info("📄/🎬 Document or YouTube-focused request — skipping web search")
        else:
            real_time_results = await asyncio.to_thread(auto_search_context, message, "")
            if real_time_results and not real_time_results.startswith("[Web search unavailable"):
                extra_context += f"\n\n[REAL-TIME LIVE DATA FROM WEB]\n{real_time_results}"
                search_performed = True
                logger.info(f"🌐 Auto real-time data injected")

            if force_search:
                logger.info(f"🔍 Explicit web search triggered...")
                try:
                    web_results = await asyncio.to_thread(search_web, message, 5, True)
                    if web_results and not web_results.startswith("[No search"):
                        extra_context += f"\n\n[DEDICATED WEB SEARCH RESULTS]\n{web_results}"
                        search_performed = True
                        logger.info(f"   ✅ Search results added")
                except Exception as e:
                    logger.error(f"   ❌ Search error: {e}")

        # 🚀 =================================================================
        # ROUTER PRIORITY 5: FALLBACK TO NORMAL AI CHAT
        # =================================================================
        logger.info(f"🤖 Calling AI model: {model}...")
        logger.info(f"   Total Context Size: {len(extra_context)} chars")

        try:
            reasoning = optimizer.get_reasoning_recommendation(message)
        except Exception as e:
            logger.warning(f"⚠️ Optimizer error: {e}")
            reasoning = {"style": "default"}

        try:
            answer = await asyncio.wait_for(
                asyncio.to_thread(ask_ai, message, extra_context, model),
                timeout=50.0,
            )
        except asyncio.TimeoutError:
            logger.error("❌ AI error: provider chain exceeded 50s budget")
            answer = (
                "I apologize, but the AI providers took too long to respond. "
                "This can happen when a provider is degraded — please try again, "
                "or pick a specific model instead of 'auto' to skip the slower fallbacks."
            )
        except Exception as e:
            logger.error(f"❌ AI error: {e}")
            answer = f"I apologize, but I encountered an error while processing your request: {str(e)}. Please try again."

        response_time = time.time() - start_time

        # ========================================================
        # GENERATE DIAGRAMS
        # ========================================================
        images = []
        if generate_images:
            try:
                from services.llm import detect_subject
                subject = detect_subject(message, extra_context)
                images = await generate_all_diagrams(answer, subject, user_message=message)
                if images:
                    logger.info(f"🖼️ Generated {len(images)} diagram(s)")
            except Exception as e:
                logger.warning(f"⚠️ Image generation failed: {e}")

        try:
            from services.llm import detect_subject
            subject = detect_subject(message, extra_context)
            if optimizer:
                optimizer.learn_from_interaction(
                    question=message,
                    answer=answer[:500],
                    subject=subject,
                    provider=model,
                    success=not answer.startswith("[Error"),
                    response_time=response_time,
                    image_count=len(images),
                )
        except Exception as e:
            logger.warning(f"⚠️ Optimizer learning failed: {e}")

        try:
            from routes.login import user_db
            user_db.increment_message_count(current_user.get("username", ""))
        except Exception as e:
            logger.debug(f"usage increment failed: {e}")

        logger.info("=" * 70)
        logger.info(f"✅ FINAL RESPONSE DELIVERED ({len(answer)} chars, {response_time:.1f}s)")

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
            search_performed=search_performed,
            images_generated=len(images),
            images=response_images,
            current_time=datetime.utcnow().isoformat() + "Z",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ FATAL CHAT ERROR:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

logger.info("👁️ Vision AI Chat Router v2.0 - Ready")