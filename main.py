"""
Vision AI v2.8.3 - Production-Grade Multi-Modal AI Assistant
============================================================
Enterprise-ready FastAPI application with:
- Multi-provider AI routing (Gemini, DeepSeek, Groq, OpenRouter)
- Real-time Agentic RAG with document processing
- Diagram & image generation
- Self-learning optimizer
- YouTube tools
- JWT + OAuth2 authentication
- Rate limiting & security middleware

Version: 2.8.3
Author: Vision AI Team
License: MIT
"""

import os
import sys
import io
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field

# ==========================================================
# PATH RESOLUTION (Works from any directory)
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent
APP_VERSION = (BASE_DIR / "VERSION").read_text(encoding="utf-8").strip() if (BASE_DIR / "VERSION").exists() else "2.6.1"

# ==========================================================
# WINDOWS CONSOLE ENCODING FIX
# ==========================================================
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ==========================================================
# ENVIRONMENT VARIABLES
# ==========================================================
load_dotenv(BASE_DIR / ".env")

# ==========================================================
# LOGGING CONFIGURATION
# ==========================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"

# Create logs directory BEFORE configuring logging
(BASE_DIR / "logs").mkdir(exist_ok=True)

handlers = [
    logging.FileHandler(str(BASE_DIR / "logs" / "app.log"), encoding="utf-8"),
    logging.StreamHandler(sys.stdout),
]

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    handlers=handlers
)
logger = logging.getLogger("vision-ai")

def _worker_health_summary() -> dict:
    """Best-effort Colab/Kaggle worker status for /health."""
    try:
        from services.colab_worker import health as wh, is_enabled
        h = wh() if callable(wh) else {}
        return {
            "enabled": bool(is_enabled()) if callable(is_enabled) else False,
            "detail": h if isinstance(h, dict) else {"raw": str(h)[:200]},
        }
    except Exception as e:
        return {"enabled": False, "error": str(e)[:120]}


# Ensure all handlers use UTF-8
for handler in logging.root.handlers:
    if isinstance(handler, logging.FileHandler) and not handler.encoding:
        handler.encoding = "utf-8"
    if isinstance(handler, logging.StreamHandler):
        handler.encoding = "utf-8"

# ==========================================================
# CONFIGURATION MODELS
# ==========================================================
class AppConfig:
    """Centralized application configuration."""
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5050"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALLOWED_HOSTS: List[str] = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "*").split(",")]

    # Session
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", os.getenv("SECRET_KEY", "change-me"))

    # AI Providers
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")

    # Search
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")

    # Image Generation
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")

    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5050/auth/google/callback")

    # Rate Limiting
    RATE_LIMIT_SEARCH: str = os.getenv("RATE_LIMIT_SEARCH", "20/minute")
    RATE_LIMIT_DOWNLOAD: str = os.getenv("RATE_LIMIT_DOWNLOAD", "10/minute")
    RATE_LIMIT_CHAT: str = os.getenv("RATE_LIMIT_CHAT", "60/minute")

    # Paths
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    CACHE_DIR: Path = BASE_DIR / "cache"
    LOG_DIR: Path = BASE_DIR / "logs"
    DOWNLOAD_DIR: Path = BASE_DIR / "downloads"
    FRONTEND_DIR: Path = BASE_DIR / "frontend"

    @classmethod
    def validate(cls) -> List[str]:
        """Validate critical configuration. Raises in production on fatal misconfig."""
        warnings: List[str] = []
        errors: List[str] = []
        weak_secrets = {
            "change-me-in-production",
            "your-secret-key-here",
            "change-me",
            "secret",
            "changeme",
            "",
        }
        if cls.SECRET_KEY in weak_secrets or len(cls.SECRET_KEY) < 32:
            msg = "SECRET_KEY is missing, weak, or default. Set a long random SECRET_KEY."
            if not cls.DEBUG:
                errors.append(msg)
            else:
                warnings.append("WARNING: " + msg)
        if not any([cls.GOOGLE_API_KEY, cls.GROQ_API_KEY, cls.DEEPSEEK_API_KEY, cls.OPENROUTER_API_KEY]):
            warnings.append("WARNING: No AI provider API keys configured. Chat will not work.")
        if not cls.DEBUG and cls.ALLOWED_HOSTS == ["*"]:
            warnings.append("WARNING: ALLOWED_HOSTS=* in production. Pin to your domain.")
        if errors:
            for e in errors:
                logger.error(e)
            raise RuntimeError("Fatal configuration error: " + "; ".join(errors))
        return warnings

# ==========================================================
# LIFESPAN MANAGEMENT
# ==========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    global_start_time = time.time()
    app.state.start_time = global_start_time

    # Create directories
    for dir_path in [
        AppConfig.UPLOAD_DIR, 
        AppConfig.CACHE_DIR, 
        AppConfig.LOG_DIR, 
        AppConfig.DOWNLOAD_DIR
    ]:
        dir_path.mkdir(exist_ok=True, parents=True)

    # Validate config
    warnings = AppConfig.validate()
    for warning in warnings:
        logger.warning(warning)

    # Initialize optimizer
    try:
        from services.self_optimizer import optimizer
        app.state.optimizer = optimizer
        health = optimizer.get_health_status()

        logger.info("=" * 70)
        logger.info(f"Vision AI v{APP_VERSION} Starting...")
        logger.info("=" * 70)
        logger.info(f"Version: {APP_VERSION} (Production Ready)")
        logger.info(f"Debug Mode: {AppConfig.DEBUG}")
        logger.info(f"Uploads: {AppConfig.UPLOAD_DIR.absolute()}")
        logger.info(f"Cache: {AppConfig.CACHE_DIR.absolute()}")
        logger.info(f"Logs: {AppConfig.LOG_DIR.absolute()}")
        logger.info(f"Downloads: {AppConfig.DOWNLOAD_DIR.absolute()}")
        logger.info("-" * 70)
        logger.info("AI Providers:")
        logger.info(f"  Gemini:    {'Active (Primary)' if AppConfig.GOOGLE_API_KEY else 'Not Configured'}")
        logger.info(f"  DeepSeek:  {'Active' if AppConfig.DEEPSEEK_API_KEY else 'Not Configured'}")
        logger.info(f"  Groq:      {'Active (Backup)' if AppConfig.GROQ_API_KEY else 'Not Configured'}")
        logger.info(f"  OpenRouter: {'Active (Fallback)' if AppConfig.OPENROUTER_API_KEY else 'Not Configured'}")
        logger.info("-" * 70)
        logger.info("Services:")
        logger.info(f"  Tavily Search: {'Active' if AppConfig.TAVILY_API_KEY else 'Not Configured'}")
        logger.info(f"  HF Image Gen:  {'Active' if AppConfig.HF_TOKEN else 'Not Configured'}")
        logger.info(f"  Google OAuth:  {'Active' if (AppConfig.GOOGLE_CLIENT_ID and AppConfig.GOOGLE_CLIENT_SECRET) else 'Not Configured'}")
        logger.info("-" * 70)
        logger.info("Self-Learning System:")
        logger.info(f"  Status: {'Active' if health.get('learning_database') == 'active' else 'New Session'}")
        logger.info(f"  Total Interactions: {health.get('total_interactions', 0)}")
        logger.info(f"  Knowledge Graph: {health.get('knowledge_graph_size', 0)} concepts")
        if hasattr(optimizer, '_get_evolution_stage'):
            logger.info(f"  Evolution Stage: {optimizer._get_evolution_stage()}")
        logger.info("-" * 70)
        logger.info(f"Startup completed in {time.time() - global_start_time:.2f}s")
        logger.info("=" * 70)

    except ImportError as e:
        logger.warning(f"Self-learning system not available: {e}")
        app.state.optimizer = None

    yield

    # ==========================================================
    # ✅ SHUTDOWN SAFETY
    # ==========================================================
    try:
        if hasattr(app.state, "optimizer") and app.state.optimizer is not None:
            report = app.state.optimizer.get_session_report()
            logger.info("=" * 70)
            logger.info("SESSION SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Duration: {report.get('session_duration', 'N/A')}")
            logger.info(f"Diagrams Requested: {report.get('diagrams_requested', 0)}")
            logger.info(f"Diagrams Generated: {report.get('diagrams_generated', 0)}")
            logger.info(f"Success Rate: {report.get('success_rate', 'N/A')}")
            logger.info(f"Providers Used: {report.get('providers_used', 'None')}")
            logger.info(f"Subjects Covered: {', '.join(report.get('subjects_covered', [])) or 'None'}")
            logger.info(f"Failed Attempts: {report.get('failed_attempts', 0)}")
            logger.info(f"Learning Events: {report.get('learning_events', 0)}")
            suggestions = report.get('suggestions', [])
            if suggestions:
                logger.info("Improvement Suggestions:")
                for s in suggestions[:5]:
                    logger.info(f"  - {s}")
            logger.info("=" * 70)
        else:
            logger.info("Optimizer not available — skipping session report.")
    except Exception as e:
        logger.debug(f"Could not generate session report: {e}")

    logger.info("Vision AI Shutting Down...")

# ==========================================================
# FASTAPI APPLICATION
# ==========================================================
# OpenAPI: on in DEBUG, or when ENABLE_DOCS=1 (recommended for your own ops only)
_enable_docs = bool(getattr(AppConfig, "DEBUG", False)) or (
    (os.getenv("ENABLE_DOCS", "0") or "0").strip().lower() in ("1", "true", "yes")
)
app = FastAPI(
    title="Vision AI",
    description="Production-grade multi-modal AI assistant with document processing, diagram generation, and multi-model support.",
    version=APP_VERSION,
    docs_url="/docs" if _enable_docs else None,
    redoc_url="/redoc" if _enable_docs else None,
    lifespan=lifespan,
)

# ==========================================================
# RATE LIMITER
# ==========================================================
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# ==========================================================
# SECURITY MIDDLEWARE
# ==========================================================

# Max request body (55 MB) — protects upload endpoints
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", str(55 * 1024 * 1024)))

@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > MAX_BODY_BYTES:
        return JSONResponse(
            status_code=413,
            content={"error": "Payload too large", "max_bytes": MAX_BODY_BYTES},
        )
    return await call_next(request)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=(self)"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID for request tracking and logging."""
    correlation_id = request.headers.get("X-Correlation-ID", f"req_{int(time.time())}_{os.urandom(4).hex()}")
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

@app.middleware("http")
async def validate_content_type(request: Request, call_next):
    """Validate content type for POST requests."""
    if request.method == "POST" and request.headers.get("content-type"):
        content_type = request.headers["content-type"].lower()
        valid_types = ["application/json", "multipart/form-data", "application/x-www-form-urlencoded"]
        if not any(vt in content_type for vt in valid_types):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid content type",
                    "detail": f"Received: {content_type}",
                    "allowed": valid_types
                }
            )
    return await call_next(request)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        f"{request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Duration: {duration:.3f}s | "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    return response

# ==========================================================
# BUILT-IN MIDDLEWARE
# ==========================================================
app.add_middleware(
    SessionMiddleware,
    secret_key=AppConfig.SESSION_SECRET,
    max_age=86400,  # 24h — OAuth state must survive Google redirect
    same_site="lax",  # required for top-level OAuth return
    https_only=not AppConfig.DEBUG,  # True on Railway (HTTPS)
)

# When allow_credentials=True, origins cannot be "*". Use explicit origins in production.
# Colab may call register/heartbeat from browser tools; Python requests ignore CORS.
_cors_origins = ["*"] if AppConfig.DEBUG else [h for h in AppConfig.ALLOWED_HOSTS if h != "*"]
if not _cors_origins:
    _cors_origins = ["http://localhost:5050", "http://127.0.0.1:5050"]
for _extra in (
    "https://colab.research.google.com",
):
    if _extra not in _cors_origins and "*" not in _cors_origins:
        _cors_origins.append(_extra)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# TrustedHostMiddleware rejects requests if host not in list; "*" is valid for open deploy
_trusted = AppConfig.ALLOWED_HOSTS if AppConfig.ALLOWED_HOSTS != ["*"] else ["*"]
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=_trusted,
)

# ==========================================================
# ROUTER IMPORTS - ISOLATED LOADING (FIXES LOGIN 404)
# ==========================================================
from fastapi import APIRouter

# 🟢 FIX: Add middleware method to APIRouter for compatibility
def _router_middleware(self, *args, **kwargs):
    """Dummy middleware method for APIRouter compatibility."""
    def decorator(func):
        return func
    return decorator

# 🟢 FIX: Add exception_handler method to APIRouter for compatibility
def _router_exception_handler(self, *args, **kwargs):
    """Dummy exception_handler method for APIRouter compatibility."""
    def decorator(func):
        return func
    return decorator

# Patch APIRouter to have middleware and exception_handler methods
APIRouter.middleware = _router_middleware
APIRouter.exception_handler = _router_exception_handler

main_router = APIRouter()
_loaded = []
_failed = []

def _load_router(name: str, import_fn):
    try:
        r = import_fn()
        main_router.include_router(r)
        _loaded.append(name)
    except Exception as e:
        _failed.append((name, str(e)))
        logger.error(f"❌ Failed to load '{name}' router: {e}")

# Load each router independently. If chat fails, login still loads!
_load_router("login", lambda: __import__("routes.login", fromlist=["router"]).router)
_load_router("chat", lambda: __import__("routes.chat", fromlist=["router"]).router)
_load_router("upload", lambda: __import__("routes.upload", fromlist=["router"]).router)
_load_router("upgrade", lambda: __import__("routes.upgrade", fromlist=["router"]).router)

if _loaded:
    logger.info(f"✅ Routers loaded: {', '.join(_loaded)}")
if _failed:
    logger.error(f"⚠️ Routers NOT loaded: {', '.join(n for n, _ in _failed)} — check errors above")

app.include_router(main_router)

# Needed for the admin-only search-dashboard routes below. Matches the
# same top-level import already used in routes/chat.py and
# routes/upgrade.py. If routes.login failed to load above, essentially
# nothing in this app works anyway (chat and upgrade already import this
# the same way), so this doesn't introduce a new failure mode.
from routes.login import get_current_active_user

# Health check to debug router issues
@app.get("/health/routers", tags=["System"])
async def router_health():
    return {"loaded": _loaded, "failed": [{"router": n, "error": e} for n, e in _failed]}

# ==========================================================
# HEALTH CHECK
# ==========================================================
@app.get("/health", tags=["System"])
async def health_check():
    """Comprehensive system health check."""
    from services.llm import GEMINI_AVAILABLE, GROQ_AVAILABLE

    uptime_seconds = int(time.time() - getattr(app.state, "start_time", time.time()))
    uptime_human = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m"

    return {
        "status": "healthy",
        "uptime": uptime_human,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": APP_VERSION,
        "environment": {
            "debug": AppConfig.DEBUG,
            "python_version": sys.version.split()[0],
        },
        "services": {
            "gemini": bool(AppConfig.GOOGLE_API_KEY),
            "groq": bool(AppConfig.GROQ_API_KEY),
            "deepseek": bool(AppConfig.DEEPSEEK_API_KEY),
            "openrouter": bool(AppConfig.OPENROUTER_API_KEY),
            "tavily": bool(AppConfig.TAVILY_API_KEY),
            "huggingface": bool(AppConfig.HF_TOKEN),
            "google_oauth": bool(AppConfig.GOOGLE_CLIENT_ID and AppConfig.GOOGLE_CLIENT_SECRET),
        },
        "colab_workers": _worker_health_summary(),
        "middlewares": [
            "CORS", "GZip", "TrustedHosts", "RateLimiting", "SecurityHeaders",
            "CorrelationID", "ContentValidation", "RequestLogging", "SessionManagement"
        ],
    }

@app.get("/health/detailed", tags=["System"])
async def health_check_detailed():
    """Detailed health check with optimizer stats."""
    health_data = await health_check()
    if hasattr(app.state, "optimizer") and app.state.optimizer:
        health_data["optimizer"] = app.state.optimizer.get_health_status()
    return health_data

# ==========================================================
# STATIC FILES & FRONTEND ROUTING
# ==========================================================

# 1. Mount the entire frontend folder so CSS/JS/Images load properly
app.mount("/frontend", StaticFiles(directory=str(AppConfig.FRONTEND_DIR)), name="frontend")
app.mount("/downloads", StaticFiles(directory=str(AppConfig.DOWNLOAD_DIR)), name="downloads")

# 2. Serve index.html
@app.get("/")
async def root_redirect():
    """Serve main chat application."""
    index_path = AppConfig.FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Frontend not found")

# 3. Serve upgrade.html
@app.get("/upgrade.html")
async def serve_upgrade_html():
    """Serve the pricing page correctly."""
    upgrade_path = AppConfig.FRONTEND_DIR / "upgrade.html"
    if upgrade_path.exists():
        return FileResponse(str(upgrade_path))
    raise HTTPException(status_code=404, detail="Upgrade page not found")

# 4. Serve settings.html
@app.get("/settings.html")
async def serve_settings_html():
    """Serve the settings page correctly."""
    settings_path = AppConfig.FRONTEND_DIR / "settings.html"
    if settings_path.exists():
        return FileResponse(str(settings_path))
    raise HTTPException(status_code=404, detail="Settings page not found")

# 4a. Usage analytics dashboard
@app.get("/usage")
@app.get("/usage.html")
async def serve_usage_html():
    path = AppConfig.FRONTEND_DIR / "usage.html"
    if path.exists():
        return FileResponse(str(path))
    raise HTTPException(status_code=404, detail="Usage dashboard not found")

# 4b. Versions registry (JSON + page) — host / switch any release


@app.get("/api/keep-alive")
@app.get("/ping")
async def keep_alive_ping():
    """Cheap endpoint for UptimeRobot / GitHub Actions to prevent free-host sleep."""
    from datetime import datetime, timezone
    workers = {"ok": False}
    try:
        from services.colab_worker import keep_alive_ping as wp
        workers = wp()
    except Exception as e:
        workers = {"ok": False, "error": str(e)}
    return {
        "ok": True,
        "service": "vision-ai",
        "ts": datetime.now(timezone.utc).isoformat(),
        "workers": workers,
    }


# ---- Free GPU workers (Colab / Kaggle) auto-registration ----
from pydantic import BaseModel, Field
from typing import Optional as _Opt

class WorkerRegisterBody(BaseModel):
    url: str = Field(..., min_length=8)
    kind: str = "colab"
    secret: str = ""
    meta: dict = {}

class WorkerHeartbeatBody(BaseModel):
    url: str = Field(..., min_length=8)
    secret: str = ""

@app.post("/api/workers/register")
async def api_worker_register(body: WorkerRegisterBody):
    """Colab/Kaggle call this after ngrok starts — app stores worker URL."""
    try:
        from services.colab_worker import register_worker
        return register_worker(body.url, body.kind, body.secret, body.meta)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workers/heartbeat")
async def api_worker_heartbeat(body: WorkerHeartbeatBody):
    try:
        from services.colab_worker import heartbeat_worker
        return heartbeat_worker(body.url, body.secret)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workers")
async def api_workers_list():
    from services.colab_worker import list_workers, health
    info = list_workers()
    info["live"] = health()
    return info


@app.get("/api/colab-status")
async def colab_worker_status():
    """Whether the optional Google Colab GPU worker is reachable."""
    try:
        from services.colab_worker import health
        return health()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/version")
async def api_version():
    """App version + build info for Settings / About."""
    import json
    from datetime import datetime, timezone
    ver = APP_VERSION
    try:
        vpath = BASE_DIR / "VERSION"
        if vpath.exists():
            ver = vpath.read_text(encoding="utf-8").strip() or ver
    except Exception:
        pass
    current = ver
    try:
        jpath = BASE_DIR / "versions.json"
        if jpath.exists():
            data = json.loads(jpath.read_text(encoding="utf-8"))
            current = data.get("current") or ver
    except Exception:
        pass
    return {
        "version": ver,
        "current": current,
        "app": "Vision AI Regenerative",
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/versions.json")
async def serve_versions_json():
    path = BASE_DIR / "versions.json"
    if path.exists():
        return FileResponse(str(path), media_type="application/json")
    raise HTTPException(status_code=404, detail="versions.json not found")


@app.get("/boost")
@app.get("/boost.html")
async def serve_boost_page():
    """In-app GPU Boost page — connect Colab/Kaggle from the browser."""
    path = AppConfig.FRONTEND_DIR / "boost.html"
    if path.exists():
        return FileResponse(str(path), media_type="text/html")
    raise HTTPException(status_code=404, detail="Boost page not found")

@app.get("/versions")
@app.get("/versions.html")
async def serve_versions_page():
    path = AppConfig.FRONTEND_DIR / "versions.html"
    if path.exists():
        return FileResponse(str(path), media_type="text/html")
    raise HTTPException(status_code=404, detail="Versions page not found")

# 5. 🟢 CRITICAL FIX: Serve login.html with raw HTML, NOT JSON
@app.get("/login.html")
async def serve_login_html(request: Request):
    """Serve the login page correctly."""
    login_path = AppConfig.FRONTEND_DIR / "login.html"
    if login_path.exists() and login_path.is_file():
        # ✅ Force the browser to treat it as raw HTML, not JSON
        return FileResponse(str(login_path), media_type="text/html")
    raise HTTPException(status_code=404, detail="Login page not found")

# 6. Serve favicon.ico
@app.get("/robots.txt")
async def robots_txt():
    path = AppConfig.FRONTEND_DIR / "robots.txt"
    if path.exists():
        return FileResponse(str(path), media_type="text/plain")
    return JSONResponse({"detail": "not found"}, status_code=404)


@app.get("/favicon.ico")
async def serve_favicon():
    """Serve site favicon (ICO preferred, PNG fallback)."""
    fav_dir = AppConfig.FRONTEND_DIR / "static" / "favicon"
    for name, media in (
        ("favicon.ico", "image/x-icon"),
        ("favicon-32x32.png", "image/png"),
        ("favicon-16x16.png", "image/png"),
    ):
        path = fav_dir / name
        if path.exists() and path.is_file():
            return FileResponse(str(path), media_type=media)
    return JSONResponse(content={"detail": "Favicon not found"}, status_code=404)

# 7. Search Cache Dashboard (HTML) + JSON API
def _require_admin(current_user: dict) -> dict:
    """Same role check already used in routes/upgrade.py."""
    if current_user.get("role") != "admin" and current_user.get("username") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user

@app.get("/admin/search")
@app.get("/admin/search/")
async def serve_search_dashboard():
    """Serve the search cache dashboard HTML page.

    Auth is enforced client-side (Bearer token from localStorage) and on
    the JSON APIs below. Browser navigation cannot send Authorization
    headers, so this HTML route must stay public or the page never loads.
    """
    dashboard_path = AppConfig.FRONTEND_DIR / "admin" / "search-dashboard.html"
    if dashboard_path.exists() and dashboard_path.is_file():
        return FileResponse(str(dashboard_path), media_type="text/html")
    raise HTTPException(status_code=404, detail="Search dashboard not found")


@app.get("/admin/search/stats")
async def search_stats_api(current_user: dict = Depends(get_current_active_user)):
    """JSON stats for the search-cache dashboard. Previously had no auth at
    all -- reachable by anyone who knew the URL, no login required."""
    _require_admin(current_user)
    try:
        from services.search import get_search_stats
        return get_search_stats()
    except Exception as e:
        logger.error(f"Search stats error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e), "total_entries": 0, "max_cache_size": 0, "cache_duration_seconds": 0, "recent_queries": []},
        )


@app.post("/admin/search/clear")
async def search_clear_api(current_user: dict = Depends(get_current_active_user)):
    """Clear the search cache. Same admin gate as the other search routes."""
    _require_admin(current_user)
    try:
        from services.search import clear_search_cache
        clear_search_cache()
        return {"status": "ok", "message": "Search cache cleared"}
    except Exception as e:
        logger.error(f"Search clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 8. Admin payment verification dashboard (manual Easypaisa/bank reviews)
@app.get("/admin/payments")
@app.get("/admin/payments/")
async def serve_payments_dashboard():
    """Admin payment verification UI (HTML).

    Same pattern as /admin/search: page is public HTML; /upgrade/admin/*
    JSON APIs enforce admin JWT. Client redirects to login if no token.
    """
    path = AppConfig.FRONTEND_DIR / "admin" / "payments.html"
    if path.exists() and path.is_file():
        return FileResponse(str(path), media_type="text/html")
    raise HTTPException(status_code=404, detail="Payments dashboard not found")

# ==========================================================
# CATCH-ALL ROUTE FOR SPA (Keep this at the BOTTOM!)
# ==========================================================
@app.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all route for SPA frontends."""
    if path.startswith(("api/", "auth/", "upgrade/", "upload/", "admin/", "chat/", "health")):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    index_path = AppConfig.FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Page not found")

# ==========================================================
# GRACEFUL SHUTDOWN HANDLER (FIXED FOR POWERSHELL)
# ==========================================================
import signal
import sys

def shutdown_handler(signum, frame):
    """Handle Ctrl+C gracefully for Linux/Mac."""
    print("\n\n🛑 Shutting down gracefully...")
    try:
        if hasattr(app.state, "optimizer") and app.state.optimizer is not None:
            if hasattr(app.state.optimizer, 'save_and_shutdown'):
                result = app.state.optimizer.save_and_shutdown()
                print(f"✅ {result.get('message', 'Data saved')}")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"⚠️ Error during shutdown: {e}")
    sys.exit(0)

# Signals only work in the main thread (Colab/background threads must skip this)
import threading
if threading.current_thread() is threading.main_thread():
    try:
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
    except ValueError:
        pass  # e.g. non-main thread or restricted environment

# ==========================================================
# MAIN ENTRY POINT
# ==========================================================
if __name__ == "__main__":
    import uvicorn
    try:
        run_kwargs = dict(
            app="main:app",
            host=AppConfig.HOST,
            port=AppConfig.PORT,
            log_config=None,
            access_log=True,
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
        if AppConfig.DEBUG:
            run_kwargs["reload"] = True
            # Critical: do NOT reload when yt-dlp writes into downloads/ (kills active downloads)
            run_kwargs["reload_excludes"] = [
                "downloads/*",
                "downloads/**",
                "uploads/*",
                "uploads/**",
                "cache/*",
                "cache/**",
                "data/*",
                "data/**",
                "logs/*",
                "logs/**",
                "*/__pycache__/*",
                "*.pyc",
            ]
        else:
            run_kwargs["workers"] = int(os.getenv("WEB_WORKERS", "2"))
        uvicorn.run(**run_kwargs)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down gracefully...")
        try:
            if hasattr(app.state, "optimizer") and app.state.optimizer is not None:
                if hasattr(app.state.optimizer, 'save_and_shutdown'):
                    result = app.state.optimizer.save_and_shutdown()
                    print(f"✅ {result.get('message', 'Data saved')}")
            print("👋 Goodbye!")
        except Exception as e:
            print(f"⚠️ Error during shutdown: {e}")