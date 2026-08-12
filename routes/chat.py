import os
"""
Vision AI v2.0 - Chat Router
============================
Real-Time Agentic RAG with auto web search, document processing, and diagrams.
Production-ready with JWT authentication, detailed request logging, and caching.
"""

import time
import hashlib
from pathlib import Path
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
MAX_CHAT_MESSAGE = int(os.getenv("MAX_CHAT_MESSAGE", "20000"))

from services.llm import ask_ai
from services.multimodal import process_uploaded_file
from services.search import search_web, is_search_needed, auto_search_context, get_current_info
from services.self_optimizer import optimizer
from services.image_gen import generate_all_diagrams
from routes.login import get_current_active_user

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# ==========================================================
# RAG CACHE (disk-backed — shared across workers)
# ==========================================================
from services.rag_cache import RAGCache, rag_cache, session_user_key as _session_user_key

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
    message: str = Form(..., min_length=1, max_length=20000),
    files: List[UploadFile] = File(default=[]),
    model: str = Form("auto"),
    generate_images: bool = Form(True),
    preferred_language: str = Form("auto"),
    history_hint: str = Form(""),
    current_user: dict = Depends(get_current_active_user),
):
    if message and len(message) > MAX_CHAT_MESSAGE:
        raise HTTPException(status_code=400, detail=f"Message too long (max {MAX_CHAT_MESSAGE} characters)")
    start_time = time.time()
    user_name = current_user.get("full_name", "User")
    request_id = str(uuid.uuid4())

    # --- Production plan limits ---
    try:
        from routes.upgrade import PlanConfig
        from routes.login import user_db
        plan_id = (current_user.get("plan") or "free").lower()
        plan = PlanConfig.get_plan(plan_id) or PlanConfig.get_plan("free")
        limit = (plan or {}).get("limits", {}).get("messages_per_month", 60)
        # Guests share a stricter default so public use stays stable
        if current_user.get("is_guest"):
            limit = min(int(limit) if limit and int(limit) > 0 else 60,
                        int(__import__("os").getenv("GUEST_MESSAGES_PER_MONTH", "30")))
        if limit is not None and int(limit) >= 0:
            fresh = user_db.get_user(current_user.get("username", "")) or current_user
            month = __import__("datetime").datetime.utcnow().strftime("%Y-%m")
            used = int(fresh.get("messages_this_month") or 0)
            if fresh.get("usage_month") != month:
                used = 0
            # In-memory guest usage keyed by username
            if current_user.get("is_guest"):
                used = int(current_user.get("messages_this_month") or used)
            if used >= int(limit):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Free limit reached ({limit} messages). Create a free account or upgrade at /upgrade.html",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.debug(f"Plan limit check skipped: {e}")

    logger.info(f"\n{'='*70}")
    logger.info(f"🤖 [VISION AI] New Request from {user_name}")
    logger.info(f"🆔 Request ID: {request_id}")
    logger.info(f"📝 Message: {message[:100]}...")
    if preferred_language and str(preferred_language).strip().lower() not in ("", "auto"):
        message = f"[Please reply in language/locale: {preferred_language}]\n" + message
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

                    _uk = _session_user_key(request, current_user)
                    cache_key = rag_cache.get_key(file.filename, content, user_key=_uk)
                    rag_cache.set(
                        cache_key,
                        {
                            "filename": file.filename,
                            "content": content,
                            "timestamp": time.time(),
                            "user_key": _uk,
                        },
                    )
                    # Classify common exam document types from filename
                    fn_lower = (file.filename or "").lower()
                    if (
                        "_ms_" in fn_lower
                        or fn_lower.endswith("_ms.pdf")
                        or "mark_scheme" in fn_lower
                        or "markscheme" in fn_lower
                        or "-rms-" in fn_lower
                        or "_rms_" in fn_lower
                    ):
                        tag = "MARK SCHEME / ANSWER KEY"
                        hint = (
                            "This is an official mark scheme (answer key), NOT a question paper. "
                            "If the user asks to 'solve', interpret as: explain the answers, "
                            "show the physics reasoning behind each mark, and teach the concepts. "
                            "Do NOT invent different answers."
                        )
                    elif (
                        "_qp_" in fn_lower
                        or "-qp-" in fn_lower
                        or "question" in fn_lower
                        or "-que-" in fn_lower
                        or "_que_" in fn_lower
                        or "que-" in fn_lower
                    ):
                        tag = "QUESTION PAPER"
                        hint = (
                            "This is a QUESTION PAPER for student study / tutoring. "
                            "The user asked to solve it. Work through ALL questions systematically "
                            "with clear step-by-step reasoning, formulas, units, and final answers. "
                            "Educational homework help is allowed and required. "
                            "Never refuse as 'unauthorized advice' or 'unsafe'. "
                            "Never claim you cannot see the PDF when the text is in context."
                        )
                    elif "_er_" in fn_lower or "examiner" in fn_lower:
                        tag = "EXAMINER REPORT"
                        hint = "This is an examiner report. Summarize common mistakes and teaching points."
                    else:
                        tag = "UPLOADED DOCUMENT"
                        hint = (
                            "Use this document as the primary source. "
                            "If it looks like an exam paper and the user says solve/explain, "
                            "provide full educational solutions."
                        )
                    file_texts.append(
                        f"[{tag}: {file.filename}]\n"
                        f"[DOCUMENT GUIDANCE: {hint}]\n"
                        f"{content}"
                    )
                    logger.info(f"   ✅ Cached: {file.filename} as {tag} ({len(content)} chars)")
                except Exception as e:
                    logger.error(f"   ❌ Failed: {file.filename} - {e}")
                    file_texts.append(
                        f"[File: {file.filename}] Processing returned no usable text. "
                        "If this is a scan, ensure tesseract is installed; for images set GOOGLE_API_KEY."
                    )

            if file_texts:
                extra_context = "\n\n".join(file_texts)
                # Cap context so providers don't time out on 20MB PDFs
                MAX_CONTEXT_CHARS = 180_000
                if len(extra_context) > MAX_CONTEXT_CHARS:
                    extra_context = (
                        extra_context[:MAX_CONTEXT_CHARS]
                        + "\n\n[... document truncated for length; ask about a specific page/section ...]"
                    )
                    logger.info(f"Truncated file context to {MAX_CONTEXT_CHARS} chars")
                logger.info(f"📄 Document context injected. Continuing to chat...")

        # Re-inject previous file context if no new files uploaded.
        # Include solve/exam intents: "solve this pdf" must reuse the last paper.
        msg_l = (message or "").lower()
        _uk = _session_user_key(request, current_user)
        wants_prev = any(
            w in msg_l
            for w in (
                "previous document",
                "previous file",
                "the document",
                "the pdf",
                "this pdf",
                "this paper",
                "this document",
                "this file",
                "same paper",
                "same document",
                "us document",
                "yeh document",
                "that file",
                "that pdf",
                "that paper",
                "continue with the paper",
                "solve this",
                "solve the",
                "solve pdf",
                "solve it",
                "answer all",
                "answer every",
                "complete solution",
                "work through",
                "mark this",
                "question paper",
                "past paper",
            )
        )
        # Short follow-ups after an upload (common student flow)
        if not wants_prev and msg_l.strip() in {
            "solve",
            "solve?",
            "answers",
            "answer",
            "solutions",
            "solution",
            "mark scheme",
            "explain",
            "help",
            "continue",
            "next",
        }:
            wants_prev = True
        if not files and wants_prev:
            latest_file = rag_cache.get_latest(user_key=_uk)
            if latest_file:
                fn = latest_file.get("filename", "document")
                fn_lower = (fn or "").lower()
                if any(
                    x in fn_lower
                    for x in ("_ms_", "-ms-", "mark_scheme", "markscheme", "-rms-", "_rms_")
                ):
                    tag = "MARK SCHEME / ANSWER KEY"
                elif any(
                    x in fn_lower
                    for x in ("_qp_", "-qp-", "question", "-que-", "_que_", "que-")
                ):
                    tag = "QUESTION PAPER"
                else:
                    tag = "UPLOADED DOCUMENT"
                file_texts.append(
                    f"[{tag}: {fn}]\n"
                    f"[DOCUMENT GUIDANCE: Reused from previous upload in this session. "
                    f"If the user asked to solve, work through every question present.]\n"
                    f"{latest_file['content']}"
                )
                file_names.append(fn)
                extra_context = "\n\n".join(file_texts)
                MAX_CONTEXT_CHARS = 180_000
                if len(extra_context) > MAX_CONTEXT_CHARS:
                    extra_context = (
                        extra_context[:MAX_CONTEXT_CHARS]
                        + "\n\n[... document truncated for length; ask about a specific page/section ...]"
                    )
                    logger.info(f"Truncated file context to {MAX_CONTEXT_CHARS} chars")
                logger.info(f"Reusing previous upload for {_uk}: {fn} as {tag}")
            else:
                logger.info(f"No cached upload for user {_uk} to reuse")
        elif not files and rag_cache.get_latest(user_key=_uk):
            logger.info("Skipping RAG cache reuse (user did not reference previous document)")


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
                r"\b(download|downloaad|downlod|downlaod|save|grab|fetch|dl)\b",
                msg_l,
            )) or bool(re.search(
                r"\b(mp3|mp4|m4a|mkv|webm|flac|wav|1080p?|720p?|480p?|360p?|4k)\b|\.mp4|\.mp3",
                msg_l,
            ))


            if wants_download:
                # DEFAULT: server-side download → link on OUR domain (works in browser).
                # Direct googlevideo.com URLs almost always 403 in browsers (IP/cookie bound).
                # User can still ask: "direct links only" for advanced/IDM experiments.
                want_direct_only = any(
                    p in msg_l
                    for p in (
                        "direct link", "direct links", "cdn only", "direct only",
                        "googlevideo", "no server", "without server",
                    )
                )
                height = 720
                hm = re.search(r"\b(360|480|540|720|1080|1440|2160)p?\b", msg_l)
                if hm:
                    height = int(hm.group(1))
                elif "best" in msg_l or "highest" in msg_l or "4k" in msg_l:
                    height = 1080
                audio_only = any(
                    k in msg_l
                    for k in (
                        "mp3", "m4a", "aac", "wav", "flac", "ogg",
                        "audio only", "download audio", "audio track",
                        "music", "song", "yt music", "youtube music",
                        "only audio", "extract audio",
                    )
                )

                answer = None

                if want_direct_only:
                    try:
                        from services.youtube import list_direct_download_options
                        opts = await list_direct_download_options(youtube_url)
                    except Exception as e:
                        logger.warning(f"list_direct failed: {e}")
                        opts = {"status": "error", "error": str(e)}
                    if opts.get("status") == "success":
                        title = opts.get("title") or "Video"
                        videos = opts.get("videos") or []
                        audios = opts.get("audios") or []
                        lines = [
                            f"⬇️ **{title}** — direct CDN links (often **403 in browser**)",
                            "",
                            "_Google binds these to the server IP. Prefer normal download for a working link._",
                            "",
                        ]
                        def _row(label, size_mb, url, kind):
                            size = f" · ~{size_mb} MB" if size_mb else ""
                            return f"1. [{label}{size}]({url})"
                        if videos:
                            lines.append("**Video**")
                            for i, v in enumerate(videos, 1):
                                lines.append(f"{i}. [{v['label']}" + (f" · ~{v.get('size_mb')} MB" if v.get('size_mb') else "") + f"]({v['url']})")
                            lines.append("")
                        if audios:
                            lines.append("**Audio**")
                            for i, a in enumerate(audios, 1):
                                lines.append(f"{i}. [{a['label']}" + (f" · ~{a.get('size_mb')} MB" if a.get('size_mb') else "") + f"]({a['url']})")
                        lines.extend([
                            "",
                            "For a link that opens: `download 720p <url>` (server file on this site).",
                        ])
                        answer = "\n".join(lines)
                    else:
                        answer = (
                            "❌ Could not list direct links. "
                            "Use normal download instead: `download 720p <url>`"
                        )

                if answer is None:
                    # Primary path: download on server, serve from /upload/downloads/
                    try:
                        from services.youtube import download_video
                        result = await download_video(
                            youtube_url,
                            height=height or 720,
                            audio_only=audio_only,
                            quality=f"{height or 720}p",
                        )
                        if result.get("status") == "success":
                            base = str(request.base_url).rstrip("/")
                            link = f"{base}/upload/downloads/{result['filename']}"
                            note = result.get("note") or ""
                            kind = "Audio (MP3)" if audio_only else f"Video (~{height}p)"
                            answer = (
                                f"✅ **Download ready** — {kind}\n\n"
                                f"- **File:** `{result['filename']}`\n"
                                f"- **Size:** {result.get('file_size_mb', '?')} MB\n"
                                + (f"- **Note:** {note}\n" if note else "")
                                + f"\n"
                                f"**[⬇️ Click to download]({link})**\n\n"
                                f"This file is on **this site** (not googlevideo). "
                                f"Opens in browser and IDM/FDM.\n\n"
                                f"_Temporary file — older downloads are cleaned periodically._"
                            )
                        else:
                            err = result.get("error") or "unknown"
                            answer = (
                                f"❌ Download failed: {err}\n\n"
                                f"**Tips:** public video only; on Railway ensure Dockerfile build "
                                f"(ffmpeg + yt-dlp). Optional: mount `cookies.txt` if YouTube bot-checks."
                            )
                    except Exception as e:
                        logger.exception("server download failed")
                        answer = (
                            f"❌ Download error: {e}\n\n"
                            f"Need yt-dlp + ffmpeg on the server (Docker image includes them)."
                        )

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
        if (history_hint or '').strip():
            extra_context = (
                "[THIS CHAT THREAD - recent turns]\n"
                + (history_hint or '').strip()[:2000]
                + "\n\n"
                + extra_context
            )
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
        from services.image_gen import user_wants_creative_image, user_wants_diagram


        # v2.7.0 / v3.1.0: re-rank long docs, but NEVER collapse full exam papers on "solve"
        try:
            if extra_context and len(extra_context) > 2500 and (message or "").strip():
                from services.rag import enhance_file_context
                before = len(extra_context)
                extra_context = enhance_file_context(message, extra_context)
                logger.info(
                    f"RAG context: {before} → {len(extra_context)} chars "
                    f"(full-doc path keeps paper intact for solve)"
                )
        except Exception as _rag_e:
            logger.debug(f"RAG re-rank skip: {_rag_e}")

        pure_image_request = user_wants_creative_image(message) and (
            len(message.strip()) > 40
            or message.lower().strip().startswith(
                ("create ", "generate ", "draw ", "make ", "photorealistic", "show me")
            )
        )

        try:
            reasoning = optimizer.get_reasoning_recommendation(message)
        except Exception as e:
            logger.warning(f"⚠️ Optimizer error: {e}")
            reasoning = {"style": "default"}

        # Pure image prompts: skip long LLM essays — generate visual first
        if pure_image_request and generate_images:
            logger.info("🖼️ Pure image request — skipping essay LLM, generating image")
            answer = "Here is the image for your request."
            images = []
            try:
                from services.llm import detect_subject
                subject = detect_subject(message, extra_context)
                images = await generate_all_diagrams("", subject, user_message=message)
                if images:
                    logger.info(f"🖼️ Generated {len(images)} image(s)")
                    answer = "Here is the image for your request."
                else:
                    answer = (
                        "Image generation did not return a picture.\n\n"
                        "**Fix checklist:**\n"
                        "1. Colab Boost tab open + `/worker/health` shows `warmed: true`\n"
                        "2. Railway `WORKER_SECRET` matches Colab\n"
                        "3. Wait 1–2 min after model download, then retry\n"
                        "4. Chat API keys are never used for images — only Colab downloaded models"
                    )
            except Exception as e:
                logger.warning(f"⚠️ Image generation failed: {e}")
                answer = f"Image generation failed: {e}"
            response_time = time.time() - start_time
        else:
            # Force full-paper solve behavior when user asks to solve an uploaded paper
            msg_l2 = (message or "").lower()
            if file_texts and any(w in msg_l2 for w in ("solve", "answer all", "complete solution", "mark this")):
                extra_context = (
                    "[SOLVE MODE ACTIVATED]\n"
                    "Work through EVERY numbered question in the document below in order.\n"
                    "Do not stop after the cover page or equation list.\n"
                    "If some pages are missing from the extract, solve all questions that ARE present.\n"
                    "Never claim you cannot see the paper when [QUESTION PAPER] or [PDF Content] is below.\n""Use only questions present in the context — quote their numbers/stems. Do not invent questions.\n\n"
                ) + (extra_context or "")
            logger.info(f"🤖 Calling AI model: {model}...")
            logger.info(f"   Total Context Size: {len(extra_context)} chars")
            try:
                _heavy = bool(files or file_texts) or len(message or "") > 400 or len(extra_context or "") > 8000
                # Exam PDFs need a longer budget (large context + full solutions)
                _doc = bool(file_texts) or "[QUESTION PAPER" in (extra_context or "") or "[PDF Content" in (extra_context or "")
                _budget = 180.0 if _doc else (90.0 if _heavy else 45.0)
                # Optional per-request keys (Settings → Custom API Keys with override)
                _keys = {}
                try:
                    h = request.headers
                    if (h.get("x-vision-key-override") or "").lower() in ("1", "true", "yes"):
                        for hk, nk in (
                            ("x-vision-key-google", "GOOGLE_API_KEY"),
                            ("x-vision-key-groq", "GROQ_API_KEY"),
                            ("x-vision-key-deepseek", "DEEPSEEK_API_KEY"),
                            ("x-vision-key-openrouter", "OPENROUTER_API_KEY"),
                            ("x-vision-key-compat-base", "OPENAI_COMPAT_BASE"),
                            ("x-vision-key-compat-key", "OPENAI_COMPAT_KEY"),
                            ("x-vision-key-compat-model", "OPENAI_COMPAT_MODEL"),
                        ):
                            val = (h.get(hk) or "").strip()
                            if val:
                                _keys[nk] = val
                except Exception:
                    _keys = {}
                answer = await asyncio.wait_for(
                    asyncio.to_thread(ask_ai, message, extra_context, model, _keys or None),
                    timeout=_budget,
                )
            except asyncio.TimeoutError:
                logger.error("❌ AI error: provider chain exceeded time budget")
                answer = (
                    "The AI took too long on this turn (network, free-tier load, or a long exam paper).\n\n"
                    "**Try:** select **Gemini** or **Groq** in the model menu, ask for **Q1–Q5 first** "
                    "then the rest, or send again in a few seconds."
                )
            except Exception as e:
                logger.exception("AI request failed")
                answer = (
                    "I couldn't complete that request right now. "
                    "Please try again in a moment."
                )

            response_time = time.time() - start_time

            # ========================================================
            # GENERATE IMAGES / DIAGRAMS (use USER message as prompt source)
            # ========================================================
            images = []
            if generate_images:
                try:
                    from services.llm import detect_subject
                    subject = detect_subject(message, extra_context)
                    images = await generate_all_diagrams(answer, subject, user_message=message)
                    if images:
                        logger.info(f"🖼️ Generated {len(images)} diagram(s)")
                    if images and user_wants_creative_image(message):
                        answer = "Here is the image for your request."
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

        # Analytics dashboard counters (data/usage.json)
        try:
            from services.usage_tracker import record_message, record_image
            uid = (current_user or {}).get("username") or (current_user or {}).get("id") or "anon"
            record_message(user_id=str(uid), provider=str(model or "auto"))
            if images:
                for img in images:
                    record_image(user_id=str(uid), provider=str((img or {}).get("provider") or "image"))
        except Exception as e:
            logger.debug(f"usage_tracker failed: {e}")

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
            rag_files_loaded=max(len(file_names), len(file_texts), len(files or [])),
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



@router.post("/chat/clear-cache")
async def clear_chat_caches(current_user: dict = Depends(get_current_active_user)):
    """Clear in-memory RAG upload cache + web search cache."""
    try:
        rag_cache.clear()
    except Exception as e:
        logger.warning(f"RAG clear: {e}")
    try:
        from services.search import clear_search_cache
        clear_search_cache()
    except Exception as e:
        logger.warning(f"Search clear: {e}")
    return {"status": "ok", "message": "RAG and search caches cleared"}


logger.info("👁️ Vision AI Chat Router v2.0 - Ready")