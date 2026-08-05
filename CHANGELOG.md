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

## [2.0.0] — 2026-07-28

- Initial production-oriented release: multi-provider LLM routing, Agentic RAG, diagram generation, JWT + Google OAuth, rate limiting, self-learning optimizer, YouTube tools.

## [2.0.2] — 2026-07-29

### Fixed
- Complete `services/llm.py`: all providers defined; no UnboundLocalError on search helpers
- Exact greeting detection (no substring false positives)
- Narrow ambiguity filter so short factual questions reach the model
- Greeting short-circuit runs before web search; conversational greetings go to LLM
- Search ownership clarified (chat primary; llm last-resort only)
- Web-result synthesis instructions in system prompt

## [2.0.3] — 2026-07-29

### Fixed
- Web search no longer false-triggers on exam PDF body text
- Cambridge-style `_ms_` / `_qp_` / `_er_` documents labeled and handled correctly
- Document-focused solve/explain requests skip web search
- Stronger exam tutoring prompts; no external "PDF solver" product spam

## [2.0.4] — 2026-07-29

### Fixed
- Search dashboard JSON vs HTML route collision
- Mobile sidebar reserving black empty space
- YouTube transcript fetch (no longer depends on OAuth caption download)
- YouTube summarize no longer falls through to generic web advice

## [2.0.5] — 2026-07-30

### Fixed
- YouTube **download** requests from chat now use server-side yt-dlp (not external tool advice)
- Download link path corrected to `/upload/downloads/{file}` (+ `/downloads` static mount)
- Height parsing for 360p/480p/720p/1080p and audio/MP3 intents

## [2.1.0] — 2026-07-30 — Production ready

### Added
- Persistent user store (`data/users.json`) with thread-safe saves
- Admin bootstrap via `ADMIN_USERNAME` / `ADMIN_PASSWORD`
- Monthly message limits enforced per plan
- Dockerfile + docker-compose.yml + render.yaml
- PRODUCTION.md deployment guide
- Hard fail on weak SECRET_KEY when DEBUG=false

### Security
- No hardcoded default users/passwords
- Production uvicorn workers + proxy headers

## [2.1.1] — 2026-07-30

### Added (required production extras)
- Stripe Checkout + webhook (`/upgrade/checkout`, `/upgrade/webhook/stripe`)
- Real usage stats from persisted message counts
- Procfile, Caddyfile (HTTPS reverse proxy)
- robots.txt
- Request body size limit (55 MB default)
- Admin role check (not only username == admin)

## [2.1.2] — 2026-07-30

### Merged from legacy services (3-week-old)
- Gemini auto chain prioritizes **2.5 Flash → 2.5 Pro → DeepSeek → 2.0 Flash → Groq**
- Default `ask_gemini` model: `gemini-2.5-flash`
- STEM subject teaching mode (physics/chemistry/math/…) when no exam/YouTube document context
- Expanded physics keyword detection
- Google Image Search uses `safe=active` (removed `safe=off`)
- `GOOGLE_ENGINE_ID` documented in `.env.example`

## [2.1.3] — 2026-07-30

### Fixed (runtime feedback)
- Search: expand `pk`/`pak` → Pakistan, `pm` → Prime Minister, fix typos (primminsiter, offical)
- Search triggers for current officials / PM queries
- YouTube download: support `YTDLP_COOKIES` file or `YTDLP_COOKIES_FROM_BROWSER` for bot checks

## [2.2.0] — 2026-07-31 — Voice + UI v3

### Added
- **Voice input** (browser Web Speech API): mic button in composer
- **Voice output**: Speak / Stop on AI messages (`speechSynthesis`)
- Quick hint chips: Image Q&A, Solve PDF, YouTube, Voice
- `v3-ui.css` — glass composer, gradients, mic pulse, refined actions
- Image attach toast guidance
- `capture=environment` for mobile camera on file input

### Notes
- Voice needs Chrome/Edge (or Safari); HTTPS or localhost for mic permission
- Server Whisper / paid TTS can be added later as Pro upgrades
