## 2.7.2 — 2026-08-08

- Production ready: PKR Free/Student/Pro plans with hard free limits (60 msgs default)
- Monetization env vars + MONETIZE.md + READY.md
- Keeps v2.7.1 llm.py `__future__` Railway fix

## 2.7.1 — 2026-08-08

- **Hotfix:**  —  must be first (Railway SyntaxError)

## 2.7.0 — 2026-08-08

### Practical free-tier muscle
- **RAG re-ranker** (`services/rag.py`): all-MiniLM-L6-v2 ranks document chunks before the LLM
- **Complex chat**: optional Colab local Qwen (default **3B** on T4; 7B via `LOCAL_LLM_ID` when image pipe unloaded)
- **Auto keep-alive**: `/worker/ping` + 5‑minute background loop (reduces idle death; Colab can still disconnect)

### Notes
- Local 7B and SDXL should not stay loaded together on free T4 VRAM
- Normal chat still uses Groq/Gemini/OpenRouter cascade

## 2.6.3 — 2026-08-08
- Phase 1: Google Drive model cache + copy-to-/content for faster Colab image loads
- SDXL-turbo preferred on free T4; FLUX optional via PREFER_FLUX=1
- Docs: COLAB_DRIVE_CACHE.md

## 2.6.2 — 2026-08-08
- Mobile UI: no stuck dark overlay; responsive chips/buttons
- Chat UI refresh: modern bubbles, glass composer, free-tier bar
- Text no longer overflows buttons on small screens

## 2.6.2 — 2026-08-07
- Version set to **2.6.2** across package (VERSION, README, main, worker, routes, versions.json)
- CRITICAL: Permissions-Policy now `microphone=(self)` (was `microphone=()` which blocked mic)
- Chat speed: Colab live-cache fast-fail, shorter provider timeouts, greeting fast-path
- Exam PDF solve + settings layout + image routing fixes retained
- Full deployable tree; index.js cache-bust `?v=254`

## 2.5.4 — mic root cause
- CRITICAL: Permissions-Policy was microphone=() which BLOCKED mic site-wide even when Edge Allow was on
- Fixed to microphone=(self), camera=(self)
- index.js cache-bust ?v=254

## 2.5.4 — 2026-08-06 (speed + reliability)
- Chat latency: shorter provider timeouts (Groq/OpenRouter 18s, DeepSeek 22s)
- Colab boost: 3s health probe + 45s live cache; dead ngrok no longer blocks 90s
- Colab chat only when worker is LIVE; image still uses GPU worker
- Greeting fast-path (hi/hello) without provider round-trip
- Server budget 32s light / 90s heavy; frontend 45s light + 1 auto-retry on Failed to fetch
- Exam PDF solve + settings/mic/image fixes retained

- Settings grid layout tightened (2-col stretch, session full-width)
- Mic: re-check permission each click (no permanent false deny)
- Exam PDFs: detect -que-/-rms- filenames; educational solve required
- Skip LLM safety-refusal responses and try next provider
- Image gen routing retained from 2.5.3 (photography ≠ chart)
- Full package zip policy: every release ships complete tree

## 2.5.2 — 2026-08-06
- Version set to 2.5.2 across package (VERSION, README, worker, registry)
- Continues 2.5.1 UI, Colab secrets, image display/quality line

## 2.5.1 — 2026-08-06
## 2.6.2 — OAuth hardening
- Dynamic Google redirect URI (APP_BASE_URL / request)
- Robust userinfo fetch + session-friendly errors
- OAUTH_GOOGLE.md setup guide

