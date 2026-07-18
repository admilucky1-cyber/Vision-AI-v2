"""
AI Intelligence Hub - Main Application
Multi-modal AI assistant with document processing, diagram generation, and YouTube tools.
Version 7.0.0 - AGI-Level Self-Learning & Intelligent Auto-Updates
"""
import os
import sys
import io
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# All paths below are resolved relative to this file's own location,
# not the terminal's current directory — so `python main.py` works
# the same whether you launch it from this folder, a parent folder,
# or an IDE run button with a different working directory.
BASE_DIR = Path(__file__).resolve().parent

# ==========================================================
# FIX WINDOWS CONSOLE ENCODING FOR EMOJIS (MUST BE FIRST)
# ==========================================================
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

# ==========================================================
# LOGGING CONFIGURATION (FIXED: UTF-8 EVERYWHERE)
# ==========================================================
# Explicitly configure handlers to avoid Windows cp1252 issues
handlers = [
    logging.FileHandler(str(BASE_DIR / 'app.log'), encoding='utf-8'),
    logging.StreamHandler(sys.stdout)  # Use UTF-8 wrapped stdout
]
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
# Extra safety: ensure all existing root handlers use UTF-8
for handler in logging.root.handlers:
    if isinstance(handler, logging.FileHandler) and not handler.encoding:
        handler.encoding = 'utf-8'
    if isinstance(handler, logging.StreamHandler):
        # Force UTF-8 for stream handlers too (already wrapped above, but ensures safety)
        handler.encoding = 'utf-8'

# ==========================================================
# LIFESPAN MANAGEMENT
# ==========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Create required directories
    Path(BASE_DIR / 'uploads').mkdir(exist_ok=True)
    Path(BASE_DIR / 'cache').mkdir(exist_ok=True)
    Path(BASE_DIR / 'logs').mkdir(exist_ok=True)
    
    # Define start_time here so it can be used in the summary below
    global_start_time = time.time()

    # Initialize self-learning optimizer
    try:
        from services.self_optimizer import optimizer
        app.state.optimizer = optimizer

        print("=" * 70)
        print("AI Intelligence Hub Starting...")
        print("=" * 70)
        print(f" Version: 7.0.0 (AGI-Level Self-Learning)")
        print(f" Uploads: {(BASE_DIR / 'uploads').absolute()}")
        print(f" Cache: {(BASE_DIR / 'cache').absolute()}")
        print(f" Logs: {(BASE_DIR / 'logs').absolute()}")
        print(f" GROQ_API_KEY: {'Set' if os.getenv('GROQ_API_KEY') else 'Missing'}")
        print(f" HF_TOKEN: {'Set' if os.getenv('HF_TOKEN') else 'Missing'}")
        print(f" TAVILY_API_KEY: {'Set' if os.getenv('TAVILY_API_KEY') else 'Optional'}")
        print(f" OPENROUTER_API_KEY: {'Set' if os.getenv('OPENROUTER_API_KEY') else 'Optional'}")
        print(f" GOOGLE_API_KEY: {'Set' if os.getenv('GOOGLE_API_KEY') else 'Optional'}")
        from services.llm import GEMINI_AVAILABLE, GROQ_AVAILABLE
        print(f" Gemini AI: {'Active (Primary)' if GEMINI_AVAILABLE else 'Not Configured'}")
        print(f" Groq AI: {'Active (Backup)' if GROQ_AVAILABLE else 'Not Configured'}")
        print(f" Security Headers: {'Enabled'}")
        print(f" Rate Limiting: {'Enabled (10 requests/min)'}")
        print(f" Request Logging: {'Enabled'}")

        # Learning system status
        try:
            health = app.state.optimizer.get_health_status()
            print(f" Self-Learning: {'Active' if health.get('learning_database') == 'active' else 'New session'}")
            print(f" Lifetime interactions: {health.get('total_interactions', 0)}")
            print(f" Lifetime diagrams: {health.get('total_diagrams_lifetime', 0)}")
            print(f" Overall success rate: {health.get('overall_success_rate', 'N/A')}")
            print(f" Evolution stage: {app.state.optimizer._get_evolution_stage()}")
            print(f" Knowledge graph: {health.get('knowledge_graph_size', 0)} concepts")
            print(f" Internet learnings: {health.get('internet_learnings', 0)}")
            print(f" Best provider: {health.get('best_provider', 'N/A')}")
        except Exception as e:
            logging.warning(f"Could not load health status: {e}")

        print("=" * 70)
        print(f" Startup completed in {time.time() - global_start_time:.2f}s")
        print("=" * 70)

    except ImportError as e:
        logging.warning(f"Self-learning system not available: {e}")
        print("Self-learning system not initialized")

    yield

    # Shutdown
    try:
        if hasattr(app.state, 'optimizer'):
            report = app.state.optimizer.get_session_report()
            print("\n" + "=" * 70)
            print("SESSION SUMMARY")
            print("=" * 70)
            print(f" Duration: {report.get('session_duration', 'N/A')}")
            print(f" Diagrams requested: {report.get('diagrams_requested', 0)}")
            print(f" Diagrams generated: {report.get('diagrams_generated', 0)}")
            print(f" Success rate: {report.get('success_rate', 'N/A')}")
            print(f" Providers used: {report.get('providers_used', 'None')}")
            print(f" Subjects covered: {', '.join(report.get('subjects_covered', [])) if report.get('subjects_covered') else 'None'}")
            print(f" Failed attempts: {report.get('failed_attempts', 0)}")
            print(f" Learning events: {report.get('learning_events', 0)}")

            # Print suggestions
            suggestions = report.get('suggestions', [])
            if suggestions:
                print("\nIMPROVEMENT SUGGESTIONS:")
                for s in suggestions[:5]:
                    print(f"  {s}")
            print("=" * 70)
    except Exception as e:
        logging.debug(f"Could not generate session report: {e}")

    print("\nAI Intelligence Hub Shutting Down...")

# ==========================================================
# FASTAPI APPLICATION SETUP
# ==========================================================
start_time = time.time()
app = FastAPI(
    title="AI Intelligence Hub",
    description="Multi-modal AI assistant with document processing, diagram generation, and YouTube tools.",
    version="7.0.0",
    lifespan=lifespan
)

# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# ==========================================================
# CUSTOM MIDDLEWARES
# ==========================================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID for request tracking."""
    correlation_id = request.headers.get("X-Correlation-ID", f"req_{time.time()}_{os.urandom(4).hex()}")
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

@app.middleware("http")
async def validate_content_type(request: Request, call_next):
    """Validate content type for POST requests."""
    if request.method == "POST" and request.headers.get("content-type"):
        content_type = request.headers["content-type"]
        valid_types = ["application/json", "multipart/form-data", "application/x-www-form-urlencoded"]
        if not any(valid_type in content_type for valid_type in valid_types):
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid content type: {content_type}"}
            )
    return await call_next(request)

# ==========================================================
# FASTAPI BUILT-IN MIDDLEWARES
# ==========================================================
# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted Hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",")
)

# Rate Limiting Error Handler (Handles 429 errors globally)
app.add_exception_handler(429, _rate_limit_exceeded_handler)


# ==========================================================
# IMPORT AND INCLUDE ROUTERS - UPDATED WITH UPLOAD
# ==========================================================
# ✅ Option 1: Import from routes package (if you have routes/__init__.py)
from routes import router as main_router

# ✅ Option 2: Import individual routers directly (if you prefer)
# from routes.chat import router as chat_router
# from routes.login import router as login_router

# ==========================================================
# Routers: chat -> /chat/*, login -> /auth/*
# (each sub-router already declares its own prefix, so no extra
# prefix is added here)
# ==========================================================
app.include_router(main_router)

# If using Option 2 (uncomment and use this instead):
# app.include_router(chat_router, prefix="/chat", tags=["Chat"])
# app.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])

# ==========================================================
# HEALTH CHECK ENDPOINT
# ==========================================================
@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "7.0.0",
        "middlewares": [
            "CORS",
            "GZip Compression",
            "Trusted Hosts",
            "Rate Limiting",
            "Request Logging",
            "Error Handler",
            "Security Headers",
            "Correlation ID",
            "Content Type Validation",
            "YouTube Logging"
        ],
        "environment": {
            "debug": bool(os.getenv("DEBUG", False)),
            "python_version": sys.version.split()[0],
        }
    }

# ==========================================================
# STATIC FILES & FRONTEND ROUTING (DEFINITIVE FIX)
# ==========================================================
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# 1. ROOT REDIRECT (serves the chat app; index.html's own checkAuth()
#    already bounces unauthenticated users to /frontend/login.html)
@app.get("/")
async def root_redirect():
    return FileResponse(str(BASE_DIR / 'frontend' / 'index.html'))

# 2. Mount the 'frontend' folder 
app.mount("/frontend", StaticFiles(directory=str(BASE_DIR / "frontend")), name="frontend")

# 3. Mount the 'static' folder for CSS
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5050,
        reload=True,
        log_config=None  # Use our custom logging config
    )