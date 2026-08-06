"""
Vision AI v2.0 - Authentication Router
======================================
JWT-based authentication with Google OAuth2 support.
Production-ready with proper error handling and security.

Features:
- Username/password authentication with bcrypt hashing
- JWT token generation with configurable expiry
- Token blacklisting for logout
- Google OAuth2 integration
- User profile management
"""

import os
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Set, List  # ✅ FIX: Added missing Optional import
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, Field, EmailStr, field_validator
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address

import logging
logger = logging.getLogger("vision-ai.auth")

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

# ==========================================================
# CONFIGURATION
# ==========================================================
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Validate critical configuration
if SECRET_KEY == "change-me-in-production":
    logger.warning("Using default SECRET_KEY. Set a secure key in .env file!")

# ==========================================================
# OAUTH2 SETUP
# ==========================================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# ==========================================================
# DATA MODELS
# ==========================================================
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v

class UserResponse(BaseModel):
    username: str
    full_name: str
    email: str
    plan: str = "free"
    created_at: str
    disabled: bool = False
    expires_in: Optional[int] = None  # Added for token expiry info

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str

    @field_validator('token_type')
    @classmethod
    def validate_token_type(cls, v):
        if v != "bearer":
            raise ValueError('token_type must be "bearer"')
        return v

class TokenRefresh(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if v.strip() == "":
            raise ValueError('New password cannot be empty')
        return v

class UpdateProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)

# ==========================================================
# DATABASE (Production: Replace with PostgreSQL/MongoDB)
# ==========================================================
class UserDatabase:
    """
    File-backed user store (JSON under data/users.json).
    Suitable for single-instance production. For multi-instance, switch to Postgres.
    """

    def __init__(self, path: Optional[Path] = None):
        import json
        import threading

        self._json = json
        self._lock = threading.RLock()
        data_dir = Path(__file__).resolve().parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        self._path = path or (data_dir / "users.json")
        self._users: Dict[str, dict] = {}
        self._blacklisted_tokens: Set[str] = set()
        self._load()
        self._seed_admin_from_env()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = self._json.loads(self._path.read_text(encoding="utf-8"))
            self._users = {k.lower(): v for k, v in (raw.get("users") or {}).items()}
            self._blacklisted_tokens = set(raw.get("blacklist") or [])
            logger.info(f"Loaded {len(self._users)} users from {self._path}")
        except Exception as e:
            logger.error(f"Failed to load users.json: {e}")

    def _save(self) -> None:
        payload = {
            "users": self._users,
            "blacklist": list(self._blacklisted_tokens)[-5000:],  # cap growth
        }
        tmp = self._path.with_suffix(".tmp")
        try:
            tmp.write_text(self._json.dumps(payload, indent=2, default=str), encoding="utf-8")
            tmp.replace(self._path)
        except Exception as e:
            logger.error(f"Failed to persist users.json: {e}")

    def _hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _seed_admin_from_env(self) -> None:
        """Optional bootstrap admin via ADMIN_USERNAME / ADMIN_PASSWORD (once)."""
        admin_user = (os.getenv("ADMIN_USERNAME") or "").strip()
        admin_pass = (os.getenv("ADMIN_PASSWORD") or "").strip()
        admin_email = (os.getenv("ADMIN_EMAIL") or "admin@localhost").strip()
        if not admin_user or not admin_pass:
            return
        if self.get_user(admin_user):
            return
        with self._lock:
            self._users[admin_user.lower()] = {
                "username": admin_user.lower(),
                "email": admin_email.lower(),
                "full_name": os.getenv("ADMIN_FULL_NAME", "Administrator"),
                "hashed_password": self._hash_password(admin_pass),
                "disabled": False,
                "plan": "enterprise",
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "messages_this_month": 0,
                "usage_month": datetime.now(timezone.utc).strftime("%Y-%m"),
            }
            self._save()
            logger.info(f"Seeded admin user from env: {admin_user.lower()}")

    def get_user(self, username: str) -> Optional[dict]:
        return self._users.get(username.lower())

    def get_user_by_email(self, email: str) -> Optional[dict]:
        email_lower = email.lower()
        for user in self._users.values():
            if user.get("email", "").lower() == email_lower:
                return user
        return None

    def create_user(self, user_data: dict) -> dict:
        with self._lock:
            username = user_data["username"].lower()
            if username in self._users:
                raise ValueError(f"Username '{username}' already exists")
            if self.get_user_by_email(user_data["email"]):
                raise ValueError(f"Email '{user_data['email']}' already registered")
            user_data.setdefault("plan", "free")
            user_data.setdefault("role", "user")
            user_data.setdefault("disabled", False)
            user_data.setdefault("messages_this_month", 0)
            user_data.setdefault("usage_month", datetime.now(timezone.utc).strftime("%Y-%m"))
            user_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            user_data["username"] = username
            self._users[username] = user_data
            self._save()
            return user_data

    def update_user(self, username: str, updates: dict) -> Optional[dict]:
        with self._lock:
            user = self._users.get(username.lower())
            if not user:
                return None
            user.update(updates)
            self._save()
            return user

    def increment_message_count(self, username: str) -> dict:
        """Track monthly message usage; reset when calendar month changes."""
        with self._lock:
            user = self._users.get(username.lower())
            if not user:
                return {}
            month = datetime.now(timezone.utc).strftime("%Y-%m")
            if user.get("usage_month") != month:
                user["usage_month"] = month
                user["messages_this_month"] = 0
            user["messages_this_month"] = int(user.get("messages_this_month") or 0) + 1
            self._save()
            return user

    def blacklist_token(self, token: str):
        with self._lock:
            self._blacklisted_tokens.add(token)
            self._save()

    def is_token_blacklisted(self, token: str) -> bool:
        return token in self._blacklisted_tokens

    def get_all_users(self) -> Dict[str, dict]:
        return self._users.copy()

    def clear_blacklist(self):
        with self._lock:
            self._blacklisted_tokens.clear()
            self._save()

# Global database instance
user_db = UserDatabase()

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        return bool(bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8')))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user by username and password."""
    user = user_db.get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    if user.get("disabled", False):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire, 
        "iat": datetime.now(timezone.utc), 
        "jti": str(uuid.uuid4()),
        "type": "access"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire, 
        "iat": datetime.now(timezone.utc), 
        "type": "refresh", 
        "jti": str(uuid.uuid4())
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    if user_db.is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type", "access")

        if username is None or token_type != "access":
            raise credentials_exception

        # Check token expiry manually for better error messages
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError:
        raise credentials_exception

    user = user_db.get_user(username)
    if user is None or user.get("disabled", False):
        raise credentials_exception

    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current active user."""
    return current_user

# ==========================================================
# GOOGLE OAUTH SETUP
# ==========================================================
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5050/auth/google/callback")

google_oauth_available = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

if google_oauth_available:
    try:
        from authlib.integrations.starlette_client import OAuth
        oauth = OAuth()
        oauth.register(
            name="google",
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            client_kwargs={
                "scope": "openid email profile",
                "prompt": "select_account",
            },
        )
    except ImportError:
        logger.warning("authlib not installed. Google OAuth will be disabled.")
        oauth = None
else:
    oauth = None

# ==========================================================
# ROUTES
# ==========================================================

@router.get("/login/debug", tags=["debug"])
async def debug_google_config():
    """Debug endpoint to check Google OAuth configuration."""
    return {
        "client_id_configured": bool(GOOGLE_CLIENT_ID),
        "client_secret_configured": bool(GOOGLE_CLIENT_SECRET),
        "oauth_available": google_oauth_available and oauth is not None,
        "redirect_uri": GOOGLE_REDIRECT_URI
    }

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user: UserCreate):
    """
    Register a new user account.

    - **username**: Unique username (3-50 chars, alphanumeric + underscore)
    - **full_name**: Display name
    - **email**: Valid email address
    - **password**: Minimum 6 characters
    """
    try:
        hashed_password = get_password_hash(user.password)
        new_user = {
            "username": user.username.lower(),
            "full_name": user.full_name,
            "email": user.email.lower(),
            "hashed_password": hashed_password,
            "plan": "free",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "disabled": False,
        }
        user_db.create_user(new_user)

        return UserResponse(
            username=new_user["username"],
            full_name=new_user["full_name"],
            email=new_user["email"],
            plan=new_user["plan"],
            created_at=new_user["created_at"],
            disabled=new_user["disabled"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return JWT tokens.

    Use form-data with fields:
    - **username**: Your username
    - **password**: Your password
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        # Use generic error message to prevent user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["username"]})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        username=user["username"],
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    """Refresh an expired access token using a refresh token."""
    try:
        payload = jwt.decode(token_data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")

        if username is None or token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = user_db.get_user(username)
        if user is None or user.get("disabled"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        access_token = create_access_token(data={"sub": username})
        refresh_token = create_refresh_token(data={"sub": username})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            username=username,
        )

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    """Get current authenticated user profile."""
    # Added expires_in for frontend to know when token expires
    token_exp = current_user.get("exp")
    expires_in = int(token_exp - datetime.now(timezone.utc).timestamp()) if token_exp else None

    return UserResponse(
        username=current_user["username"],
        full_name=current_user["full_name"],
        email=current_user["email"],
        plan=current_user.get("plan", "free"),
        created_at=current_user.get("created_at", ""),
        disabled=current_user.get("disabled", False),
        expires_in=expires_in,
    )

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Logout user by blacklisting the token."""
    if token:
        user_db.blacklist_token(token)
    return {"message": "Logged out successfully", "success": True}

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Change user password."""
    if not verify_password(password_data.old_password, current_user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")

    user_db.update_user(current_user["username"], {"hashed_password": get_password_hash(password_data.new_password)})
    return {"message": "Password updated successfully", "success": True}

@router.post("/update-profile")
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Update user's full name."""
    user_db.update_user(current_user["username"], {"full_name": profile_data.full_name})
    return {"message": "Profile updated successfully", "success": True}

@router.post("/verify-email")
async def verify_email(token: str):
    """Placeholder for email verification."""
    return {"message": "Email verification not implemented yet", "success": False}

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(get_current_active_user)):
    """Get all users (admin only - placeholder)."""
    # This is a placeholder for admin functionality
    if current_user.get("role") != "admin" and current_user.get("username") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    users = user_db.get_all_users()
    return [
        UserResponse(
            username=user["username"],
            full_name=user["full_name"],
            email=user["email"],
            plan=user.get("plan", "free"),
            created_at=user.get("created_at", ""),
            disabled=user.get("disabled", False),
        )
        for user in users.values()
    ]

# ==========================================================
# GOOGLE OAUTH ROUTES (✅ SESSION-BASED, RELIABLE)
# ==========================================================

@router.get("/google")
async def login_via_google(request: Request):
    """Redirect to Google OAuth login page."""
    if not oauth:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
        )

    # 🔵 Generate a unique state and store it in the SESSION (persists across requests)
    state = str(uuid.uuid4())
    request.session["oauth_state"] = state

    redirect_uri = GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)

@router.get("/google/callback")
async def auth_google_callback(request: Request):
    """Handle Google OAuth callback."""
    if not oauth:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    try:
        # 🔵 Retrieve state from Google's callback
        returned_state = request.query_params.get("state")
        saved_state = request.session.get("oauth_state")

        # 🔵 Verify the state exists in the SESSION
        if not returned_state or not saved_state or returned_state != saved_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authentication failed: mismatching_state. State not found."
            )

        # 🔵 Delete the state from session so it cannot be reused
        request.session.pop("oauth_state", None)

        # Continue with normal OAuth flow
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get user info from Google")

        email = user_info.get("email", "").lower()
        name = user_info.get("name", email)
        google_id = user_info.get("sub", "")

        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not provided by Google")

        # Check if user exists
        existing_user = user_db.get_user_by_email(email)

        if not existing_user:
            # Create new user from Google data
            username = email.split("@")[0] + "_" + google_id[:6]
            new_user = {
                "username": username,
                "full_name": name,
                "email": email,
                "hashed_password": get_password_hash(os.urandom(32).hex()),
                "plan": "free",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "disabled": False,
                "google_id": google_id,
            }
            user_db.create_user(new_user)
            existing_user = new_user

        # Generate tokens
        access_token = create_access_token(data={"sub": existing_user["username"]})
        refresh_token = create_refresh_token(data={"sub": existing_user["username"]})

        # Redirect to frontend with tokens
        return RedirectResponse(
            url=f"/?token={access_token}&refresh={refresh_token}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Authentication failed: {str(e)}")

# ==========================================================
# HEALTH CHECK
# ==========================================================
@router.get("/health")
async def auth_health():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "user_count": len(user_db.get_all_users()),
        "blacklisted_tokens": len(user_db._blacklisted_tokens),
        "oauth_available": google_oauth_available and oauth is not None,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }

# ==========================================================
# EXPORT
# ==========================================================
# Export database for other modules
fake_users_db = user_db.get_all_users()

