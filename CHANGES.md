# Changes — this pass

Note: the CHANGES.md shipped in this zip described fixes (double `/auth`
prefix, files removed, upload.py deleted, etc.) that didn't match what
was actually in the code — e.g. it said `vector_store.py`, `flux_image.py`,
`image_gen.py`, `style.css`, and `routes/upload.py` were all removed, but
every one of them was still present and wired in. Treat that file as
stale; this one reflects what was actually verified and changed just now.

## Critical: login was breaking because of a Python import-order gotcha
`main.py` already had router-isolation logic (each of login/chat/upload/
upgrade is imported independently, in its own try/except, so one broken
router can't take the others down). But `routes/__init__.py` did this
at the top of the file, unconditionally:

```python
from .chat import router as chat_router
from .login import router as login_router
...
```

Importing *any* submodule, e.g. `routes.login`, always executes the
parent package's `__init__.py` first — that's just how Python import
works. So the moment `chat.py`'s import chain hit a problem (see next
item), `routes/__init__.py` itself raised, which broke importing
`routes.login` too, even though login doesn't depend on chat at all.
This silently defeated the isolation main.py was built for and is the
real reason login kept failing. **Fixed**: stripped `routes/__init__.py`
down to a docstring — nothing actually imports the aggregated router it
used to build, so this is safe.

## Fragile diagram dependencies could take chat.py down
`services/image_gen.py` imported `matplotlib`, `plotly`, and `graphviz`
at module load time with no fallback. `routes/chat.py` imports this
module directly, so if any one of those three wasn't installed on the
deploy target (graphviz in particular also needs a system `dot` binary,
not just the Python package), the whole chat router failed to load —
and per the bug above, that used to cascade into login too. **Fixed**:
each engine now imports inside its own try/except and sets an
`_AVAILABLE` flag; the seven `draw_*()` functions check their flag and
return a normal `{"success": False, "error": "..."}` instead of raising.

## XSS in the chat UI (frontend/index.html)
AI answers were rendered with `marked.parse(text)` and inserted via
`innerHTML` with no sanitization. Since answers can reflect content
from uploaded documents or web search results — both effectively
untrusted input — a crafted document or a prompt-injection attempt
could get raw `<script>`/`onerror=` markup to execute in the user's
session, where the JWT access token lives in `localStorage`. **Fixed**:
added DOMPurify and sanitize marked's output before insertion. Also
rebuilt the AI-image grid using real DOM nodes instead of string
interpolation, and escaped `showToast()` messages (some come from
`data.detail`, i.e. server error text).

## No brute-force protection on login/register
`routes/login.py` already had `slowapi`'s `Limiter` instantiated but
never applied to `/auth/login` or `/auth/register`. **Fixed**: added
`@limiter.limit("10/minute")` to login and `@limiter.limit("5/minute")`
to register.

## requirements.txt
- Added `itsdangerous` — required by `starlette.middleware.sessions.SessionMiddleware`,
  which `main.py` adds unconditionally. Missing it can crash the app at
  startup.
- Removed `passlib[bcrypt]` — `routes/login.py` calls `bcrypt.hashpw`/
  `bcrypt.checkpw` directly, passlib was never actually used. Added a
  plain `bcrypt>=4.0.0` pin instead (this also sidesteps the known
  passlib+bcrypt>=4.1 `__about__` incompatibility, since passlib isn't
  in the path at all now).
- Removed `chromadb` / `sentence-transformers` — nothing imports them
  now that the two dead vector-store duplicates are gone (next item).

## Removed confirmed-dead duplicate files
Neither of these was imported anywhere in the codebase:
- `services/rag/vector_store.py`
- `services/hf/flux_image.py` (duplicate FLUX image-gen helper —
  `services/image_gen.py` already has its own `generate_with_flux()`)

## Still worth doing (not changed — flagging for you)
- `frontend/login.html` shows the default demo password
  (`aftab` / `password123`) directly on the page. Fine for local dev,
  remove that line before this is reachable by anyone else.
- `SECRET_KEY`/`SESSION_SECRET` fall back to `"change-me-in-production"`
  with only a startup log warning, not a hard failure. Worth making
  `AppConfig.validate()` refuse to start in production without a real
  secret.
- `frontend/static/css/style.css` isn't linked from any HTML file —
  `index.html`, `login.html`, and `upgrade.html` all use their own
  inline `<style>` blocks. It's dead weight right now; let me know if
  you want it merged in as a shared stylesheet or removed.
- CORS/TrustedHost both default to `allow_origins=["*"]` /
  `allowed_hosts=["*"]` unless `ALLOWED_HOSTS` is set in `.env` — fine
  for local dev, set `ALLOWED_HOSTS` explicitly before this is public.
