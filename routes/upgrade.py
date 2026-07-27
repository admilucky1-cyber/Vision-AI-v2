"""
Vision AI v2.0 - Upgrade Router
===============================
User plan management with validation and audit logging.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from routes.login import get_current_active_user, user_db

router = APIRouter(prefix="/upgrade", tags=["Upgrade"])
logger = logging.getLogger("vision-ai")  # 🔥 Added logging

# ==========================================================
# PLAN CONFIGURATION
# ==========================================================
class PlanConfig:
    """Available subscription plans."""

    PLANS: Dict[str, dict] = {
        "free": {
            "id": "free",
            "name": "Free",
            "price": 0.0,
            "currency": "USD",
            "billing": "forever",
            "features": [
                "Groq & Gemini AI Access",
                "Basic Markdown & Code",
                "1,000 messages / month",
                "Standard support",
            ],
            "limits": {
                "messages_per_month": 1000,
                "file_upload_size_mb": 10,
                "concurrent_chats": 3,
            }
        },
        "pro": {
            "id": "pro",
            "name": "Pro",
            "price": 9.99,
            "currency": "USD",
            "billing": "month",
            "features": [
                "DeepSeek & OpenRouter Access",
                "Advanced Image & File Analysis",
                "Unlimited messages",
                "Priority support",
                "Custom prompts",
            ],
            "limits": {
                "messages_per_month": -1,  # unlimited
                "file_upload_size_mb": 50,
                "concurrent_chats": 10,
            }
        },
        "team": {
            "id": "team",
            "name": "Team",
            "price": 29.00,
            "currency": "USD",
            "billing": "month",
            "features": [
                "All Pro features",
                "5 Team Members",
                "Shared Knowledge Base",
                "Team Analytics Dashboard",
                "API access",
            ],
            "limits": {
                "messages_per_month": -1,
                "file_upload_size_mb": 100,
                "concurrent_chats": 25,
                "team_members": 5,
            }
        },
        "enterprise": {
            "id": "enterprise",
            "name": "Enterprise",
            "price": 49.00,
            "currency": "USD",
            "billing": "month",
            "features": [
                "All Team features",
                "Fine-tuning access",
                "Dedicated Cloud",
                "SLA guarantee",
                "Custom integrations",
                "Dedicated account manager",
            ],
            "limits": {
                "messages_per_month": -1,
                "file_upload_size_mb": 500,
                "concurrent_chats": -1,
                "team_members": -1,
            }
        }
    }

    @classmethod
    def get_plan(cls, plan_id: str) -> dict:
        return cls.PLANS.get(plan_id.lower())

    @classmethod
    def list_plans(cls) -> List[dict]:
        return [
            {"id": k, **v}
            for k, v in cls.PLANS.items()
        ]

# ==========================================================
# REQUEST/RESPONSE MODELS
# ==========================================================
class UpgradeRequest(BaseModel):
    plan: str = Field(..., pattern=r"^(free|pro|team|enterprise)$")

class PlanResponse(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    billing: str
    features: List[str]
    limits: dict

class UserPlanResponse(BaseModel):
    username: str
    current_plan: str
    plan_details: dict
    upgraded_at: Optional[str] = None

# ==========================================================
# ROUTES
# ==========================================================
@router.get("/plans", response_model=List[PlanResponse])
async def list_available_plans():
    """List all available subscription plans."""
    return PlanConfig.list_plans()

@router.get("/me", response_model=UserPlanResponse)
async def get_user_plan(current_user: dict = Depends(get_current_active_user)):
    """Get current user's subscription plan."""
    username = current_user["username"]
    user = user_db.get_user(username)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    plan_id = user.get("plan", "free")
    plan_details = PlanConfig.get_plan(plan_id) or PlanConfig.get_plan("free")

    return UserPlanResponse(
        username=username,
        current_plan=plan_id,
        plan_details=plan_details,
        upgraded_at=user.get("upgraded_at"),
    )

@router.post("/upgrade")
async def upgrade_user_plan(
    plan_data: UpgradeRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """
    Upgrade user to a specific plan.

    - **plan**: Plan ID (free, pro, team, enterprise)
    """
    plan = plan_data.plan.lower()
    plan_details = PlanConfig.get_plan(plan)

    if not plan_details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan '{plan}' is not available. Choose from: {list(PlanConfig.PLANS.keys())}"
        )

    username = current_user["username"]
    user = user_db.get_user(username)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # 🔥 Optional: prevent upgrading to same plan
    if user.get("plan") == plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User already on {plan} plan"
        )

    # Update user plan
    updates = {
        "plan": plan,
        "plan_price": plan_details["price"],
        "upgraded_at": datetime.now(timezone.utc).isoformat(),
    }
    user_db.update_user(username, updates)

    # 🔥 Added audit logging
    logger.info(f"User {username} upgraded to {plan} plan")

    return {
        "message": f"Successfully upgraded to {plan_details['name']} plan!",
        "plan": plan,
        "plan_details": plan_details,
        "upgraded_at": updates["upgraded_at"],
    }

@router.post("/downgrade")
async def downgrade_to_free(current_user: dict = Depends(get_current_active_user)):
    """Downgrade user to free plan."""
    username = current_user["username"]
    user = user_db.get_user(username)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    current_plan = user.get("plan", "free")
    if current_plan == "free":
        return {"message": "Already on free plan"}

    updates = {
        "plan": "free",
        "plan_price": 0.0,
        "downgraded_at": datetime.now(timezone.utc).isoformat(),
    }
    user_db.update_user(username, updates)

    # 🔥 Added audit logging
    logger.info(f"User {username} downgraded from {current_plan} to free plan")

    return {
        "message": "Successfully downgraded to Free plan",
        "previous_plan": current_plan,
        "downgraded_at": updates["downgraded_at"],
    }