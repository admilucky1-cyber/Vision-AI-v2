from fastapi import APIRouter
from .chat import router as chat_router
from .login import router as login_router
from .upgrade import router as upgrade_router
from .upload import router as upload_router

router = APIRouter()

# Optional: root health endpoint for the API
@router.get("/")
async def api_root():
    return {"message": "Vision AI API v2.0", "status": "healthy"}

router.include_router(chat_router)
router.include_router(login_router)
router.include_router(upgrade_router)
router.include_router(upload_router)