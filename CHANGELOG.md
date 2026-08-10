## 2.8.6 — 2026-08-10

- Unified UI system (`unified-v286.css`) on all pages
- Fix AI/user text contrast (no dark-on-dark)
- Larger composer attach/mic/send/stop targets
- Prompt Studio full-height drawer; hide cramped icon strip
- Boost/upgrade/settings share same theme tokens

## 2.8.5 — 2026-08-10

- UI: Humanly Teal glass theme (reference-inspired green/teal)
- Choosable themes: Humanly, Default, Nord, Sunset, High Contrast, Soft Sepia
- Theme picker control in chat header
- Keeps v2.8.4 chat/button/download hotfix

## 2.8.4 — 2026-08-10

- HOTFIX: index.js SyntaxError broke ALL buttons/chat (image toolbar quotes)
- Restore Download chat in sidebar footer (was wiped by profile render)
- Remove broken `toggleProfileDropdown = undefined` overwrite
- Robust browser download for chat transcript + image links

## 2.8.3 — 2026-08-09

- OpenAPI: ENABLE_DOCS=1 enables /docs and /redoc in production
- Chat: MAX_CHAT_MESSAGE validation (default 20000)
- Mobile polish CSS (safe-area, iOS font-size, chips scroll)
- TROUBLESHOOTING.md + scripts/smoke_test.py
- tests/test_schemas.py

## 2.8.2 — 2026-08-09

- Recommended release after Git **v2.7.8**
- Image toolbar helper for PNG + SVG download
- Version banners aligned; chat message limit 20k
- `UPGRADE_FROM_2.7.8.md` push checklist

## 2.8.1 — 2026-08-09

- Tests: pytest for graph detection, I-V render, theme CSS, boost `__future__`
- CI: GitHub Actions workflow (`pytest` + bandit)
- Graphs: optional SVG export alongside PNG for I-V
- Themes: presets nord / sunset / high-contrast / soft-sepia
- schemas.py Pydantic ChatIn; SECURITY.md baseline

## 2.8.0 — 2026-08-09

- Graphs: matplotlib **I–V (current–voltage)** diagrams on request
- Frontend: graph/plot/chart use longer timeout; fewer false timeouts
- Eye-care theme: softer dark/light for reduced glare
- Docs: DRIVE_MOUNT.md

## 2.7.9 — 2026-08-09

- Chat UI: readable text colors for AI/user bubbles (dark + light)
- `chat-ui.css` linked on index; composer/status colors fixed
- Boost page: clearer Colab commands; body class fix
- colab_one_click_boost.py: valid `__future__` header retained

## 2.7.8-hotfix — 2026-08-09
- Fix: colab_one_click_boost.py __future__ import must be first (Colab SyntaxError)

## 2.7.8 — 2026-08-09

- Colab: sequential CPU offload preferred, memory guard, load_status for UI
- Optional torch.compile via ENABLE_TENSORRT=1 (TensorRT note in COLAB_GPU.md)
- Health: loading, load_status, offload_mode

## 2.7.7 — 2026-08-09

- UI: `vision-awesome.css` elevated dark/light visual system
- Docs: `VIDEO_MODELS.md` (Drive download for short video models)
- Docs: `LOGIC_CHECK.md` core flow verification
- Keeps v2.7.6 mobile/hamburger/footer fixes

## 2.7.6 — 2026-08-09

- Mobile responsive: chips scroll, no over-width, sidebar drawer
- Hamburger fixed (resize no longer kills open state)
- Sidebar footer themed (Download chat / user panel not white)
- Light theme closer to v2.7.2/3; dark mode localStorage
- Prompt Studio drawer + composer clear

## 2.7.5 — 2026-08-08

- UI polish across chat, plans, settings, boost (`polish-v275.css`)
- Plans always show **Rs** (never $) for PK amounts
- Prompt Studio: stronger master prompts (exams, Urdu, career, PDF/image)
- Payment block linked under plans (less “alone”)

## 2.7.4 — 2026-08-08

- Plans: **PKR prices** (Rs …) — no wrong $ on Pro/Student/Team/Enterprise
- Images: **Download / Full / Zoom** controls + lightbox
- Header chips stable on resize (icons stay visible)
- Banner dismissible; honest message when image gen returns no file

## 2.7.3 — 2026-08-08

- **UI:** stuck dim overlay fixed; sidebar visible by default; high-contrast New Chat / Clear Cache / Plan
- **Public:** guest chat without login (`ALLOW_GUEST=1`); no permission wall
- **Security:** guest quotas, robots tag configurable, SECURITY.md
- **Unique value banner** on chat page

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


