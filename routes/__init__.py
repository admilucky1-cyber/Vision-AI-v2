from fastapi import APIRouter
from .chat import router as chat_router
from .login import router as login_router

router = APIRouter()
router.include_router(chat_router)
router.include_router(login_router)
