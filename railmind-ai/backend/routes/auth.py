# ═══════════════════════════════════════════════════════════════
# RailMind AI — Authentication Routes
# JWT-based authentication for railway operations personnel
# ═══════════════════════════════════════════════════════════════
#
# SECURITY NOTE (SIH DEMO):
# This authentication uses employee_id-only validation (no password).
# The existing User model does not contain a password column.
# This is acceptable for a Smart India Hackathon demonstration
# but is NOT production-grade authentication.
#
# For production deployment, add:
# - password_hash column (bcrypt)
# - rate limiting
# - account lockout
# - audit logging
# - HTTPS enforcement
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from models import get_db
from models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ─── JWT Configuration ───
# In production, use a strong secret from environment variables
SECRET_KEY = "railmind-ai-sih-2026-jwt-secret-key-mumbai-division"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


# ─── Schemas ───

class LoginRequest(BaseModel):
    """Login request — employee ID based authentication."""
    employee_id: str = Field(
        ..., min_length=1, max_length=20,
        description="Railway employee ID",
        examples=["AK001"]
    )


class UserResponse(BaseModel):
    """Authenticated user profile."""
    id: int
    employee_id: str
    full_name: str
    email: str | None = None
    role: str
    department: str
    division: str | None = None
    is_active: bool
    can_approve_plans: bool
    can_submit_tasks: bool
    can_trigger_optimizer: bool


class LoginResponse(BaseModel):
    """Login response with JWT token and user profile."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds")
    user: UserResponse


# ─── Helpers ───

def create_access_token(user: User) -> str:
    """Create a JWT access token for an authenticated user."""
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user.id),
        "emp": user.employee_id,
        "role": user.role,
        "dept": user.department,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str, db: Session) -> User:
    """Decode JWT and return the current user, or raise 401."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", 0))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter_by(id=user_id, is_active=True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def _user_to_response(user: User) -> UserResponse:
    """Convert a User ORM object to a UserResponse schema."""
    return UserResponse(
        id=user.id,
        employee_id=user.employee_id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        department=user.department,
        division=user.division,
        is_active=user.is_active,
        can_approve_plans=user.can_approve_plans,
        can_submit_tasks=user.can_submit_tasks,
        can_trigger_optimizer=user.can_trigger_optimizer,
    )


# ─── Endpoints ───

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a railway employee by employee_id.

    Validates:
    - employee_id exists in the database
    - user account is active

    Returns a JWT access token and the user's profile.
    """
    user = db.query(User).filter_by(employee_id=request.employee_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Employee ID not found in the system."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact system administrator."
        )

    # Update last_login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(user)

    return LoginResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user=_user_to_response(user),
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(request: Request, db: Session = Depends(get_db)):
    """
    Get the currently authenticated user's profile.
    Expects: Authorization header with 'Bearer <token>'.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or malformed")

    token = auth_header.split("Bearer ", 1)[1]
    user = get_current_user(token, db)
    return _user_to_response(user)


@router.post("/logout")
def logout():
    """
    Logout endpoint.

    JWT is stateless — the client is responsible for discarding the token.
    This endpoint exists to provide a clean API surface and could be extended
    with token blacklisting if Redis is enabled.
    """
    return {"message": "Logged out successfully. Please discard the access token."}

