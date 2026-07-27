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
from typing import Optional, Dict, Set
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, Field, EmailStr
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address

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

class UserResponse(BaseModel):
    username: str
    full_name: str
    email: str
    plan: str = "free"
    created_at: str
    disabled: bool = False
    expires_in: Optional[int] = None  # 🔥 Added for token expiry info

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str

class TokenRefresh(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class UpdateProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)

# ==========================================================
# DATABASE (Production: Replace with PostgreSQL/MongoDB)
# ==========================================================
class UserDatabase:
    """In-memory user database with persistence option."""

    def __init__(self):
        self._users: Dict[str, dict] = {}
        self._blacklisted_tokens: Set[str] = set()
        self._load_default_user()

    def _load_default_user(self):
        """Load default admin user for testing."""
        self._users["aftab"] = {
            "username": "aftab",
            "full_name": "Aftab Ali",
            "email": "aftab@example.com",
            "hashed_password": self._hash_password("password123"),
            "plan": "free",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "disabled": False,
        }

    def _hash_password(self, password: str) -> str:
        """Helper to hash password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def get_user(self, username: str) -> Optional[dict]:
        return self._users.get(username.lower())

    def get_user_by_email(self, email: str) -> Optional[dict]:
        email_lower = email.lower()
        for user in self._users.values():
            if user.get("email", "").lower() == email_lower:
                return user
        return None

    def create_user(self, user_data: dict) -> dict:
        username = user_data["username"].lower()
        if username in self._users:
            raise ValueError(f"Username '{username}' already exists")
        if self.get_user_by_email(user_data["email"]):
            raise ValueError(f"Email '{user_data['email']}' already registered")

        self._users[username] = user_data
        return user_data

    def update_user(self, username: str, updates: dict) -> Optional[dict]:
        user = self._users.get(username.lower())
        if user:
            user.update(updates)
            return user
        return None

    def blacklist_token(self, token: str):
        self._blacklisted_tokens.add(token)

    def is_token_blacklisted(self, token: str) -> bool:
        return token in self._blacklisted_tokens

    def get_all_users(self) -> Dict[str, dict]:
        return self._users.copy()

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
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh", "jti": str(uuid.uuid4())})
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
else:
    oauth = None

# ==========================================================
# ROUTES
# ==========================================================

@router.get("/login/debug")
async def debug_google_config():
    """Debug endpoint to check Google OAuth configuration."""
    return {
        "client_id_configured": bool(GOOGLE_CLIENT_ID),
        "client_secret_configured": bool(GOOGLE_CLIENT_SECRET),
        "oauth_available": google_oauth_available,
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
    # 🔥 Added expires_in for frontend to know when token expires
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
    return {"message": "Logged out successfully"}

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Change user password."""
    if not verify_password(password_data.old_password, current_user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")

    user_db.update_user(current_user["username"], {"hashed_password": get_password_hash(password_data.new_password)})
    return {"message": "Password updated successfully"}

# 🔥 NEW: Update profile endpoint (needed by settings.js)
@router.post("/update-profile")
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Update user's full name."""
    user_db.update_user(current_user["username"], {"full_name": profile_data.full_name})
    return {"message": "Profile updated successfully"}

# 🔥 NEW: Email verification placeholder (for future expansion)
@router.post("/verify-email")
async def verify_email(token: str):
    """Placeholder for email verification."""
    return {"message": "Email verification not implemented yet"}

# ==========================================================
# GOOGLE OAUTH ROUTES
# ==========================================================

@router.get("/google")
async def login_via_google(request: Request):
    """Redirect to Google OAuth login page."""
    if not oauth:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
        )

    redirect_uri = GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def auth_google_callback(request: Request):
    """Handle Google OAuth callback."""
    if not oauth:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get user info from Google")

        email = user_info.get("email", "").lower()
        name = user_info.get("name", email)
        google_id = user_info.get("sub", "")

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

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Authentication failed: {str(e)}")

# ==========================================================
# EXPORT
# ==========================================================
# Export database for other modules
fake_users_db = user_db.get_all_users()