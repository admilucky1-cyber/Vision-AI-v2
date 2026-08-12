## 3.2.5 — 2026-08-12

- KaTeX: pre-render $$ math before markdown (fixes raw LaTeX in chat)
- yt-dlp: --no-config so Railway never hits Chrome cookie DB errors
- Admin-only Cache/Pay chips; desktop tool chips hidden on mobile
- Message bubbles: no nested vertical scrollbar

## 3.2.4 — 2026-08-12

- Mobile composer: cleaner bottom bar; free-tier strip hidden on small screens
- Sidebar width capped (~240–280px); response max-width 850px + RTL support
- Prompt Studio expanded (Study, Image, more exam/code/writing prompts)
- English forced for mostly-Latin STEM questions (e.g. quantum tunneling…)
- Simple Urdu vocabulary guidance (طریقہ not پدھتی); no foreign scripts

## 3.2.3 — 2026-08-12

- **Mobile YouTube download fix**: no longer loads 70MB into JS memory; uses direct attachment download
- Multi-key support: `GROQ_API_KEY_1`, `_2`, … or comma-separated keys with round-robin rotation
- Stronger anti-hallucination / no false wording; no mixed foreign scripts in Urdu answers
- Mobile shell polish (header, composer, touch targets, safe-area)

## 3.2.2 — 2026-08-12

- **Language default English** — no more random Urdu on English STEM questions
- Stricter Urdu detection (explicit request or clear Roman-Urdu phrases only)
- **Mobile YouTube download** — `?dl=1` + blob/octet-stream force save
- Math fences ````math` normalized to `$$` for KaTeX
- Professional chat typography (headings, lists, tables, KaTeX spacing)
- Mobile responsive polish for bubbles, actions, safe-area

## 3.2.1 — 2026-08-12

- Production hardening (workers=1, CORS_ORIGINS, ALLOWED_HOSTS fatal in prod)
- Password min length 10; refresh rate limit; payment plan/amount hardening
- KaTeX math rendering in chat
- **Prompt Studio fix**: panel no longer stays off-screen / blurred empty page
- Version alignment across VERSION, main.py, pyproject, frontend, tests
- Safer API-key form (DOM assignment, not HTML interpolation)
- YouTube URL domain restriction; simplified public /health

## 3.2.0 — 2026-08-12 (production hardening patch)

- **Complete exam-solve release** (consolidates 3.1.0–3.1.6)
- `services/rag_cache.py`: shared disk cache module (clean imports, multi-worker)
- Expanded smoke tests: full-doc intent, disk cache, session key, doc timeouts
- `COMPLETE.md` deploy checklist
- Env: `DOC_PROVIDER_TIMEOUT`, `DOC_MAX_TOKENS`, `PDF_OCR_MAX_PAGES`
- **Production fixes applied** (see `PRODUCTION_FIXES_v3.2.0.md`):
  - WEB_WORKERS default 1; CORS_ORIGINS; ALLOWED_HOSTS=* fatal in prod
  - Password min 10; refresh rate limit; payment plan/amount hardening
  - KaTeX math rendering; safer API-key form; YouTube domain checks
  - Public /health simplified; version test fixed for 3.x

### Included reliability stack
- Full ordered paper context (no invent)
- Follow-up solve reuses upload
- Multi-worker disk cache + stable client id
- Guest IP / refresh fixes
- Long client & provider timeouts
- Document-used toast + larger completions

## 3.1.6 — 2026-08-12

- **Best-of-bests exam reliability polish**
  - `rag_files_loaded` counts **reused cache papers** (was always 0 on follow-up solve)
  - Larger completion size on document context (`DOC_MAX_TOKENS`, default 8192)
  - Toast shows **document context used** when paper is in the request
  - Solve inject: never invent questions; quote real Q numbers from context
- Builds on 3.1.0–3.1.5: full context, follow-up reuse, disk multi-worker cache, stable client id, long timeouts

## 3.1.5 — 2026-08-12

- **Client timeout:** follow-up `solve this pdf` / exam phrases use 5‑minute browser timeout (was 90s without files)
- **Provider timeouts:** document context uses up to 120s per model (was 24–28s — too short for full papers)
- Server document budget 180s; clearer timeout guidance (solve by question range if needed)
- Prior: stable client id (3.1.4), disk multi-worker cache (3.1.3)

## 3.1.4 — 2026-08-12

- **Stable exam session:** browser `X-Vision-Client-Id` (localStorage UUID) keys the RAG cache so upload → solve works even when guest JWT/IP varies
- Guest IP uses `X-Forwarded-For` / `X-Real-IP` behind Railway
- Guest token **refresh** no longer fails (guests are not in user_db)
- Prior: disk multi-worker cache (3.1.3), follow-up solve phrases (3.1.2), full-doc RAG skip (3.1.0)

## 3.1.3 — 2026-08-12

- **Multi-worker exam fix:** RAG upload cache is **disk-backed** (`data/rag_cache/`) so Railway/uvicorn with 2+ workers still reuses the paper on follow-up “solve this pdf”
- Per-user isolation + 1h TTL preserved
- Prior: follow-up solve intents (3.1.2), full-document RAG skip (3.1.0)

## 3.1.2 — 2026-08-12

- **Best-fit exam flow:** follow-up messages (`solve this pdf`, `solve`, `answer all`, `this paper`…) **reuse the last uploaded document** for that user
- **Per-user RAG cache** (TTL 1h) so multi-tenant deploys do not mix papers
- Reused files keep QUESTION PAPER / MARK SCHEME tags from filename
- Bare `except` cleaned in upgrade plan expiry
- Prior 3.1.1 polish + 3.1.0 full-document RAG skip (no invented questions)

## 3.1.1 — 2026-08-12

- **Package polish:** README + TROUBLESHOOTING for exam PDF; clean `.env.example` (no duplicate OAuth keys; PDF/RAG notes)
- Smoke test covers full-document RAG skip intent
- Dockerfile label v3.1.1; frontend version strings aligned
- Prior 3.1.0: skip top-k RAG on “solve this pdf” so real questions are used

## 3.1.0 — 2026-08-11

- **CRITICAL fix — exam PDF hallucination:** "solve this pdf" no longer runs top-k RAG that collapsed ~50k-char papers to ~12k random chunks (model then invented generic questions).
- Full-document intent (`solve`, `answer all`, question-paper tags) keeps the ordered extract intact (up to ~100k chars) with smart question-body preference.
- System prompt: must quote real question numbers/stems from context; forbid inventing unrelated physics problems.
- Prior: guest JWT (3.0.9), exam extract quality (3.0.8), Colab-only images (3.0.7)

## 3.0.9 — 2026-08-11

- **CRITICAL:** Guest JWT no longer fails with "Could not validate credentials" (guests are not in user_db)
- **Chat reliability:** if Groq/OpenRouter/DeepSeek alone fails, soft-fallback to other free keys
- **Groq:** prefer `llama-3.1-8b-instant` first; better empty/HTTP logging
- Prior: exam PDF full context (3.0.8), Colab-only images (3.0.7), Prompt Studio unfreeze (3.0.6)

## 3.0.8 — 2026-08-11

- **Exam PDF solve:** context no longer truncated to cover page (~16k chars)
- **Smart truncate:** prioritizes pages with Q1/Q2… over front-matter
- **PDF extract:** PyMuPDF + best-of methods; quality gate triggers OCR when extract is cover-only
- **Auto route:** long question papers use Gemini first (1M context)
- **Solve mode:** explicit instruction to work through every question present

## 3.0.7 — 2026-08-11

- **Chat speed:** auto cascade is light/free first (Groq → OpenRouter free → DeepSeek → Gemini Flash); optional **Light / fast** menu item
- **Image gen:** Colab **downloaded models only** by default — never uses Gemini/Groq/OpenRouter chat keys for images; `IMAGE_ALLOW_CLOUD=1` to re-enable HF/Pollinations
- **Latency:** fewer free-model tries, tighter chat timeout (45s light / 90s heavy), skip Colab local LLM on auto chat
- **Roman Urdu:** electrical slang (e.g. current bund) interpreted correctly; blank model replies handled better

## 3.0.6 — 2026-08-11

- **Prompt Studio:** close always clears overlay, body overflow, and drawer classes (fixes frozen/dimmed chat)
- **No more CDN highlight.js:** self-hosted `hljs-lite.js` + `hljs-atom-one-dark.css` (fixes Tracking Prevention block)
- **prompt_studio.js:** no longer overwrites `closePromptStudio`; Escape + backdrop close reliably
- **CSS safety:** closed drawers have pointer-events:none so they cannot trap clicks

## 3.0.5 — 2026-08-11

- **Custom API keys:** Settings keys with override are sent on every chat (`X-Vision-Key-*`); server applies them for that request only (never logged)
- **Local LLM:** Ollama, LM Studio, and generic OpenAI-compatible base URL + model (env + Settings)
- **Model menu:** Auto / Groq / Gemini / OpenRouter / DeepSeek / Ollama / LM Studio / OpenAI-compat / Colab
- **Version headers:** every response includes `X-Vision-AI-Version` and `X-App-Version`
