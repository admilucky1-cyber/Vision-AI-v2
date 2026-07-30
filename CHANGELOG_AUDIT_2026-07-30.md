# Vision AI v2.0 — End-to-End Audit Changelog

**Date:** 2026-07-30  
**Scope:** Full project audit + production enhancements (YouTube, downloads, Prompt Studio, reliability)

---

## Summary

Production-ready pass over Vision AI v2.0 focusing on:

1. Robust YouTube transcription with multi-method fallback
2. Complete media download system (video + audio formats, quality, history)
3. Modern Prompt Studio redesign (search, tags, favorites, recent, mobile)
4. Path-safe file serving and clearer download UX in chat
5. Syntax verification of Python and frontend JS

No known critical regressions introduced; existing auth, chat, upgrade, and RAG flows preserved.

---

## 1. YouTube transcription (`services/youtube.py`)

### Fixes & enhancements
- **Multi-method transcript pipeline** with automatic fallback:
  1. `youtube-transcript-api` (manual captions → auto-generated; multi-language preference list)
  2. `yt-dlp` subtitle download (VTT/SRT parse)
- Compatible with both legacy class API and newer instance API of `youtube-transcript-api`
- **Multilingual preference order:** en, en-US, en-GB, ur, hi, ar, es, fr, de, …
- Optional **timestamps** in transcript text (`[HH:MM:SS] line`)
- `get_video_transcript_detailed()` returns language, generated flag, method, char count
- Graceful handling when captions are disabled / region-restricted / unavailable
- Long transcripts truncated safely for LLM context (`max_transcript_chars`)
- SRT and WebVTT parsers with HTML tag stripping and deduplication

### Context injection
- `get_video_context()` now includes transcript language/type/method metadata for the model

---

## 2. Media download system (`services/youtube.py` + `routes/upload.py`)

### Video formats
- MP4, MKV, WEBM, AVI (via yt-dlp merge-output-format)

### Audio formats
- MP3, M4A, AAC, WAV, FLAC, OGG

### Quality / resolution
- Presets: `best`, `high`, `medium`, `low`, `360p`, `480p`, `720p`, `1080p`
- Explicit height still supported

### Features
- Audio bitrate selection (e.g. `128K`, `192K`, `320K`)
- Optional direct `format_id` from `/upload/formats`
- File size **estimation** endpoint: `GET /upload/estimate`
- **Download history** persisted in `downloads/download_history.json` (`GET /upload/history`)
- Cookie auto-discovery (browser → static `cookies.txt` → env `YTDLP_COOKIES`)
- Retries, concurrent fragments, android+web player clients for resilience
- Path-traversal-safe file serving under `/upload/downloads/{filename}`
- Chat intent understands more phrases: mkv/webm/avi, flac/wav/ogg, “best/highest/low quality”

### API surface
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/upload/formats` | List formats + supported presets |
| GET/POST | `/upload/download` | Download with quality/format options |
| GET | `/upload/estimate` | Size estimate |
| GET | `/upload/info` | Metadata + transcript |
| GET | `/upload/transcript` | Dedicated transcript (lang + timestamps) |
| GET | `/upload/history` | Recent downloads |
| GET | `/upload/downloads/{file}` | Secure serve |
| DELETE | `/upload/cleanup` | Age-based cleanup |
| GET | `/upload/health` | yt-dlp + dir health |

---

## 3. Prompt Studio redesign (`frontend/static/js/index.js`)

### UX
- Clean card grid with category icons and tag chips
- Advanced **search** across text, tags, and categories
- **Tag filter** chips (`#transcript`, `#download`, `#python`, …)
- **Favorites** and **Recently used** (localStorage)
- One-click **copy** and **send to chat**
- Mobile-responsive layout; Esc / backdrop close; Ctrl+K open (existing)
- Keyboard-friendly focus on search when opened
- Clipboard fallback when `navigator.clipboard` is unavailable

### Structure
- Prompts are objects `{ t, tags }` with category metadata
- Categories: YouTube, Writing, Coding, Diagrams, Search, Documents, Study

---

## 4. Chat YouTube download intent (`routes/chat.py`)

- Parses height, quality keywords, audio vs video, container, and audio codec from natural language
- Passes `video_format` / `audio_format` / `quality` into the enhanced downloader
- Clearer success/failure messages including cookie guidance for bot checks

---

## 5. Verification

- `python3 -m py_compile` on core modules: **pass**
- `node --check` on `frontend/static/js/index.js`: **pass**
- Existing production fixes from `PRODUCTION_READINESS_FIXES.md` left intact (async LLM offload, payment gating, admin auth, etc.)

---

## 6. Deployment notes

- Ensure system tools for full feature set: `yt-dlp`, optionally `ffmpeg` (audio extract/merge), `tesseract-ocr`, `poppler-utils`, `graphviz` (see Dockerfile)
- Optional: place `cookies.txt` in project root or set `YTDLP_COOKIES` for restricted YouTube downloads
- Persist `data/`, `downloads/`, `uploads/`, `logs/` in production

---

## Files modified

- `services/youtube.py` — rewritten/enhanced
- `routes/upload.py` — rewritten/enhanced API
- `routes/chat.py` — download intent expansion
- `frontend/static/js/index.js` — Prompt Studio redesign

## Unchanged (verified still valid)

- Auth / JWT / OAuth (`routes/login.py`)
- Upgrade / payments (`routes/upgrade.py`)
- LLM router, search, image gen, multimodal, self-optimizer
- Main app lifespan, security middleware, static mounts
- Dockerfile / render.yaml / PRODUCTION.md guidance

---

## Hotfix — 2026-07-30 (evening)

### Download: Chrome cookie database errors
**Symptom:** `ERROR: Could not copy Chrome cookie database` when downloading audio/video.
**Cause:** Auto-probing browser cookies via `--cookies-from-browser chrome` on headless/server hosts (no usable Chrome profile).
**Fix:**
- Downloads try **without cookies first** (android player client works for most public videos).
- Cookies used only on bot-check retry, and only from an explicit `cookies.txt` / `YTDLP_COOKIES` path.
- Browser cookie extraction is **opt-in** via `YTDLP_ALLOW_BROWSER_COOKIES=1` + `YTDLP_COOKIES_FROM_BROWSER`.
- Clearer error messages when a cookie DB error or bot block occurs.

### Chat: “download music / yt music” intent
- Phrases like `download yt music`, `music`, `song`, `youtube music` now correctly force **audio-only MP3** extraction instead of full video.

### Download: missing ffmpeg / ffprobe
**Symptom:** `Postprocessing: ffprobe and ffmpeg not found` when requesting MP3.
**Cause:** Audio format conversion (`-x --audio-format mp3`) requires the `ffmpeg` system binary. Present in Dockerfile but missing on bare-metal / some PaaS hosts.
**Fix:**
- Detect ffmpeg at runtime.
- If missing and MP3/WAV/FLAC requested → download **native bestaudio** (usually M4A) without conversion so the user still gets a playable file.
- Clear error if conversion is forced and ffmpeg is absent.
- `/upload/health` reports `ffmpeg_available`.
- Install: `sudo apt install -y ffmpeg` or use the project Docker image.
