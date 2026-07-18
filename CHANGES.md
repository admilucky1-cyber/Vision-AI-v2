# What was fixed

## Critical bugs
1. **Double `/auth` prefix (main.py)** — `login.py` already declares
   `prefix="/auth"`. main.py was adding a *second* `/auth` on top of
   the whole router bundle, so `/chat/send` became `/auth/chat/send`,
   `/upload/*` became `/auth/upload/*`, and `/auth/login` became
   `/auth/auth/login`. None of these matched what index.html/login.html
   actually called. Fixed: `app.include_router(main_router)` — no
   extra prefix, since each sub-router sets its own.

2. **Root route always served login.html (main.py)** — even after a
   successful login, `/` returned `frontend/login.html` again, so
   users could never actually reach the chat UI. `index.html` already
   has its own `checkAuth()` that redirects unauthenticated users to
   `/frontend/login.html`, so root now serves `frontend/index.html`
   and lets that logic do its job.

3. **Dead YouTube logging middleware (main.py)** — was checking
   `request.url.path.startswith("/youtube")`, but the yt-dlp
   download/format endpoints actually live under `/upload/*`. It never
   logged anything. Repointed at `/upload` instead of deleting it.

## Removed (confirmed unused/orphaned — nothing imported them)
- `vector_store.py` — chromadb/sentence-transformers RAG store, never
  called; chat.py uses its own in-memory dict cache instead.
- `flux_image.py` — duplicate of the `generate_with_flux()` already
  inside image_gen.py, never called.
- `style.css` — never linked; index.html has its own inline `<style>`.
- `image_gen.py` — diagram generation feature, built but never wired
  into chat.py. Removed per your call — re-add later if you want
  diagrams in chat answers.

## Restructured
Files were flattened in the upload; main.py's imports
(`from routes import ...`, `from services.llm import ...`, etc.)
expect a package layout, so:
- `chat.py`, `login.py`, `upload.py`, `__init__.py` → `routes/`
- `llm.py`, `multimodal.py`, `search.py`, `self_optimizer.py` → `services/`
- `index.html`, `login.html` → `frontend/`
Also stripped a stray UTF-8 BOM character from `routes/__init__.py`
that would have caused a SyntaxError on import.

## Still worth doing (not changed — your call)
- `login.py` stores/compares the password in **plain text** with a
  single hardcoded user. Fine for solo testing, not for anything
  public. Swap in `passlib`/`bcrypt` hashing when ready.
- `login.html` pre-fills the password field with `password123` in
  plain view — remove before showing this to anyone else.
- `SECRET_KEY` is read from `.env` with no fallback/validation — if
  it's missing, token creation fails silently. Add a startup check.
- No `requirements.txt` was included, so dependency versions weren't
  verified (chromadb/sentence-transformers can now be dropped from it
  since vector_store.py is gone).

## Removed by you (this round)
- `routes/upload.py` (the yt-dlp video downloader) — deleted per your
  request. Cleaned up everything that referenced it so nothing's left
  dangling:
  - `routes/__init__.py` no longer imports/includes `upload_router`
  - `main.py`: dropped the `downloads/` directory creation, the
    `/downloads` static mount (was mounted twice), and the media
    logging middleware (had nothing left to log without `/upload/*`)
  - `slowapi` is still imported/configured in `main.py` (rate-limit
    exception handler) but nothing currently uses `@limiter.limit(...)`
    since that only lived in the removed file — harmless to leave in
    place if you want rate limiting on future routes, or remove the
    slowapi setup entirely if you don't.
  - Since `upload.py` is gone, `yt-dlp` is no longer a dependency —
    drop it from your requirements if you'd already added it.

## Fixed: 404 on /frontend/login.html (and any other static asset)
`main.py` was resolving `frontend/`, `static/`, `uploads/`, `cache/`,
`logs/`, and `app.log` as paths **relative to your terminal's current
directory** when you run `python main.py` — not relative to where
`main.py` itself lives. If you launch the server from a different
folder than the project root (a common IDE/PowerShell gotcha), FastAPI
can't find `frontend/login.html` and returns a 404, even though the
file is right there on disk.

Fixed by anchoring every one of those paths to `BASE_DIR = Path(__file__).resolve().parent`
— the server now finds its own files correctly no matter which
directory you launch it from.
