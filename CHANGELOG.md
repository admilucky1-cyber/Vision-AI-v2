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
- Larger chat image display; medical anatomy prompt framing
- Colab secrets: Notebook-access diagnostics, interactive paste, .vision_boost.env handoff
- CUDA low-VRAM + higher GPU image steps (turbo 8 / 1024²)
- RunPod serverless client; /usage analytics dashboard
- Upgrade payment layout (QR rows, 2-col form); Settings grid spacing
- README + VERSION aligned to 2.5.1

## 2.4.6 — 2026-08-05
- Free-first provider cascade (Groq, Gemini Flash, OpenRouter :free)
- FREE_STACK.md forever-free guide
- localStorage history no longer stores base64 images
- Payment QR codes; multi-language chat preference
- Colab one-click boost + educational diagram AI path

## 2.4.2 — 2026-08-05
- One-click Colab boost fixes (uvicorn loop, health secret headers)
- Image gen: HF Inference API first; skip 7GB CPU FLUX download
- Creative image routing for phrases like draw an eagle
- Boost UI heartbeat yellow/red timeouts
- Signal handlers only on main thread

# Changelog — Vision AI

## [2.1.0] — 2026-08-03

### Added
- Regenerative / nature green theme (light + dark)
- Payment flow: pending confirmation (no fake success)
- Owner notify: Telegram bot, ntfy.sh, optional CallMeBot WhatsApp
- \`versions.json\` registry + versions page (host any release)
- Multi-language TTS detection (Urdu, Hindi, CJK, etc.)
- \`.env.example\` with payment + Telegram vars

### Fixed
- Missing \`_notify_admin_new_payment\` implementation
- Upgrade UI message now shows wait-for-confirmation

### Changed
- CSS primary colors → forest green
- VERSION file → 2.1.0

---

## [2.0.1] — 2026-07-29

### Fixed
- Pydantic v2 compatibility: all `@validator` → `@field_validator` + `@classmethod`
- CORS: removed illegal `allow_origins=["*"]` + `allow_credentials=True` combination
- SentenceTransformer embedding load (duplicate init + invalid `model_kwargs`)
- `UploadFile.size` AttributeError risk on chat file uploads
- Relative path breakage for `search_cache.json`, learning DB, knowledge graph, ChromaDB
- Missing `logger` in authentication module
- Production log noise from debug `print` statements
- Committed `logs/app.log` containing JWTs removed from distribution

### Added
- `.env.example` with every documented environment variable
- `data/` directory for persistent JSON state
- `FIX_REPORT.md` documenting every issue and remediation
- `.gitkeep` placeholders for empty runtime directories

### Changed
- State files relocated under `data/`
- `.gitignore` updated for `data/` and `chroma_db/`

### Security
- Default SECRET_KEY warning now uses structured logging
- CORS origins tightened for non-debug deployments
