# Vision AI v3.2.2

> Production-ready multi-modal AI assistant: exam PDF solve, chat cascade, YouTube tools, Colab GPU images, local LLM, and PKR plan upgrades.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![Version](https://img.shields.io/badge/version-3.2.2-brightgreen)](VERSION)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

**Live App:** https://vision-ai-v2-production.up.railway.app  
**GitHub:** https://github.com/admilucky1-cyber/Vision-AI-v2

---

## What is Vision AI?

Vision AI is a browser-based assistant for students and professionals (Pakistan-focused, usable worldwide). It combines:

- **Chat** with free multi-provider cascade (Groq → OpenRouter free → DeepSeek → Gemini)
- **PDF / exam paper solve** with full-document context (no cover-only / no invented questions)
- **YouTube** transcript, summary, quiz, and server-side download
- **Image generation** via Google Colab downloaded models only (by default)
- **Local LLM** (Ollama, LM Studio, OpenAI-compatible)
- **Custom API keys** from the browser (per-request override headers)
- **Prompt Studio**, themes, voice STT/TTS, and Easypaisa / bank plan upgrades

Guests can use the app without a waitlist.

---

## What’s new in v3.2.2 (CRITICAL)

### Exam PDF “solve this pdf” no longer invents questions

**Root cause:** On full-paper commands (`solve`, `solve this pdf`, `answer all`…), RAG top‑k re-ranking collapsed a ~50k-character question paper into ~12k of random chunks. Models then invented generic physics questions.

**Fix:**

| Component | Change |
|-----------|--------|
| `services/rag.py` | Detects full-document intent + `[QUESTION PAPER]` / `[MARK SCHEME]` tags → **skips top‑k RAG** and keeps ordered extract (up to ~100k chars) |
| `services/llm.py` | System prompt: quote real Q numbers/stems from context; **forbid inventing** unrelated problems |
| `routes/chat.py` | Solve-mode injection + clearer context-size logging |
| Prior (3.0.8) | PyMuPDF + quality gate + OCR fallback; smart truncate prefers Q1/Q2… over cover sheet; Gemini-first for long papers |

**Expected behaviour after deploy:** Upload `4ph1-1p-que-20240523.pdf` (or any Edexcel/AQA paper) → say **“solve this pdf”** → answers follow the **real** paper questions in order.

Check Railway logs for: `RAG skip (full-document intent) → keeping N chars` (N should be tens of thousands, not ~12 000).

---

## Recent release highlights

| Version | Summary |
|---------|---------|
| **3.2.2** | **Complete** exam-solve release (cache module + full smoke + checklist) |
| **3.1.6** | Exam polish: cache reuse counted, larger completions, document-used toast |
| **3.1.5** | Long exam timeouts (client 5 min, providers 120s on documents) |
| **3.1.4** | Stable browser session id for exam cache; guest refresh/IP |
| **3.1.3** | Disk-backed RAG cache (multi-worker Railway) so follow-up solve keeps the paper |
| **3.1.2** | Follow-up **solve this pdf** reuses last upload (per-user cache) |
| **3.1.1** | Package polish: TROUBLESHOOTING, clean `.env.example`, smoke test for exam path |
| **3.1.0** | Skip top‑k RAG on full-document solve; anti-invent prompt; full paper context |
| **3.0.9** | Guest JWT no longer fails; soft free-model fallback; Groq `llama-3.1-8b-instant` first |
| **3.0.8** | Exam extract: PyMuPDF + quality gate + OCR; smart page preference; Gemini-first; solve mode |
| **3.0.7** | Light/fast cascade; **images = Colab downloaded models only** (`IMAGE_ALLOW_CLOUD=0` default) |
| **3.0.6** | Prompt Studio close/unfreeze; self-hosted highlight.js (Tracking Prevention fix) |
| **3.0.5** | Custom API key headers; Ollama / LM Studio / OpenAI-compat; Student plan; global themes; hamburger/focus fix |
| **3.0.0–3.0.4** | Glass UI, plans grid, composer/chat chrome, mobile download |

Full history: `CHANGELOG.md` and `versions.json`.

---

## Features

| Area | Capability |
|------|------------|
| **Chat** | Auto cascade: Groq → OpenRouter free → DeepSeek → Gemini Flash; optional Light / provider / local menu |
| **Exam PDF** | Full ordered context on “solve”; PyMuPDF + pdfplumber + OCR quality gate; step-by-step tutoring |
| **Documents** | PDF, images, text; RAG for targeted Q&A; skip RAG when solving entire paper |
| **Images** | Colab GPU (downloaded models only by default); optional HF/Pollinations if `IMAGE_ALLOW_CLOUD=1` |
| **Vision Q&A** | Attach image in composer |
| **YouTube** | Transcript, summary, quiz; downloads via server `/upload/downloads/` (avoids browser 403) |
| **Local LLM** | Ollama, LM Studio, any OpenAI-compatible base URL + model (env + Settings) |
| **Custom keys** | Settings → override → `X-Vision-Key-*` headers per request (never logged) |
| **Voice** | Mic STT (HTTPS/localhost) + Speak TTS |
| **Prompt Studio** | Category master prompts; reliable close (Escape + backdrop) |
| **Plans** | Free / Student / Pro / Team / Enterprise — PKR manual pay (Easypaisa / bank) |
| **UI** | Themes site-wide, user messages on right, hamburger/focus unfreeze, version in title + About |
| **Boost** | `colab_one_click_boost.py` + worker auto-register |

---

## Quick start (local)

```bash
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
cp .env.example .env
# Edit .env: SECRET_KEY + at least one of GOOGLE_API_KEY / GROQ_API_KEY / OPENROUTER_API_KEY / DEEPSEEK_API_KEY

python main.py
# → http://localhost:5050
```

Optional checks:

```bash
pytest tests/ -q
python scripts/smoke_test.py
```

---

## Environment (important)

Copy `.env.example` → `.env`. Never commit `.env` or `cookies.txt`.

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | JWT / session secret (required in production) |
| `GOOGLE_API_KEY` | Gemini (preferred for long exam papers) |
| `GROQ_API_KEY` | Fast free chat |
| `OPENROUTER_API_KEY` | Free OpenRouter models |
| `DEEPSEEK_API_KEY` | DeepSeek chat |
| `OPENAI_COMPAT_BASE` / `OPENAI_COMPAT_KEY` | Ollama / LM Studio / local OpenAI-compatible |
| `WORKER_SECRET` | Must match Colab Boost worker |
| `MAIN_APP_URL` | Public app URL for worker callback |
| `IMAGE_ALLOW_CLOUD` | `0` = Colab-only images (default); `1` = allow HF/Pollinations |
| `PDF_OCR_MAX_PAGES` | OCR page limit (default 40) |
| `RERANK_ENABLED` | `1` default; full-document solve still skips top‑k |

Browser **Settings → Custom API Keys** can override server keys for a single request when override is enabled.

---

## Deploy (Railway + GitHub)

1. Push this tree to **GitHub** `main` on `admilucky1-cyber/Vision-AI-v2`  
   - **Never** commit `.env` or `cookies.txt`
2. Railway uses **Dockerfile** and deploys when `main` updates  
   - Live: https://vision-ai-v2-production.up.railway.app
3. Set the same env vars in Railway (Secrets)
4. Colab Boost (optional GPU images): run `colab_one_click_boost.py` with Secrets  
   `NGROK_TOKEN`, `HF_TOKEN`, `WORKER_SECRET`, `MAIN_APP_URL`, optional LLM keys

Docs:

| File | Topic |
|------|--------|
| `DEPLOY.md` | General deploy |
| `RAILWAY_DEPLOY.md` | Railway specifics |
| `QUICKSTART.md` | Fast local path |
| `COLAB_GPU.md` / `COLAB_DRIVE_CACHE.md` | GPU worker + Drive cache |
| `SECURITY.md` | Keys, guests, headers |
| `TROUBLESHOOTING.md` | Common failures |
| `MONETIZE.md` | Plans / payments |
| `PRODUCTION.md` | Production checklist |

Optional: `ENABLE_DOCS=1` for OpenAPI at `/docs`.

---

## Exam solve reliability stack (v3.1.0 → v3.2.2)

1. Full ordered paper context (no top‑k collapse / no invented questions)
2. Follow-up `solve this pdf` reuses last upload
3. Disk cache shared across Railway workers
4. Stable browser `X-Vision-Client-Id` session
5. Long timeouts (client 5 min, providers ~120s, server ~180s)
6. UI shows document context used; larger completion tokens for full solutions

## Exam PDF solve — how to use

1. Upload the question paper PDF (filenames with `-que-`, `_qp_`, `question` are tagged **QUESTION PAPER**).
2. Message: **`solve this pdf`** or **`solve`** / **`answer all`**.
   - Same request with the file attached **or** a follow-up after upload both work (cache, 1 hour, per user).
3. Model should work through **every question present** in order with formulas, units, and reasoning.
4. Mark schemes (`-ms-`, `_ms_`) are treated as answer keys to **explain**, not invent.

If answers look invented:

- Confirm deployed version is **3.1.0+** (`/api/version` or Settings → About).
- Check logs for `RAG skip (full-document intent)`.
- Ensure PyMuPDF / OCR deps are in the image (`requirements.txt` + Dockerfile system packages).

---

## Image generation tips

1. Keep Colab Boost tab open until health shows `"warmed": true`.
2. Match `WORKER_SECRET` on Railway and Colab.
3. Chat API keys are **not** used for images by default (Colab downloaded models only).
4. First image after a cold start can take 1–2 minutes.

---

## Project layout

```
main.py                 # FastAPI entry
routes/                 # chat, upload, login, upgrade, usage, …
services/               # llm, multimodal, rag, youtube, image_gen, …
frontend/               # HTML + static CSS/JS
scripts/                # smoke_test, keep_alive
colab_*.py              # GPU worker helpers
Dockerfile, railway.toml, render.yaml, docker-compose.yml
.env.example, VERSION, CHANGELOG.md, versions.json
```

---

## Themes

Humanly Teal (default), Vision Default, Nord, Sunset, High Contrast, Soft Sepia, and more.  
Theme is applied site-wide and stored in `localStorage`.

---

## Version headers

Every response includes `X-Vision-AI-Version` and `X-App-Version`.  
UI shows version in title, About, and Settings.

---

## License

MIT — see `LICENSE`.

---

## Support / next steps after download

1. Unzip **VISION-AI-v3.2.2-FINAL.zip**
2. Copy `.env.example` → `.env` and add keys
3. Local: `pip install -r requirements.txt && python main.py`
4. Production: push to GitHub `main` so Railway redeploys
5. Test: upload a real past paper → **solve this pdf**
