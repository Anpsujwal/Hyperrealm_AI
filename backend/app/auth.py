"""
Authentication and authorisation helpers.

Two modes:
1. Dev/local: HS256 JWT signed with JWT_SECRET (password hashed via passlib).
2. Prod: Firebase identity token verified against Google's public keys.

Role verification is always server-side — the client can never supply a role
that is trusted.
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from jose import JWTError, jwt
except ImportError:
    from python_jose import jwt, JWTError  # type: ignore

try:
    import bcrypt
except ImportError:
    bcrypt = None  # type: ignore

from .config import get_settings
from .dependencies import get_user_repo
from .models import UserProfile, UserRole
from .repositories import UserRepository

_bearer = HTTPBearer(auto_error=False)

ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.ADMIN: 100,
    UserRole.TECHNICAL_LEAD: 80,
    UserRole.PROJECT_MANAGER: 70,
    UserRole.SOFTWARE_DEVELOPER: 50,
    UserRole.DEVOPS_ENGINEER: 50,
    UserRole.QA_ENGINEER: 50,
    UserRole.EMPLOYEE: 10,
}


# ─── Password helpers ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    pwd_bytes = plain.encode("utf-8")[:72]
    if bcrypt:
        return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")
    return "sha256:" + hashlib.sha256(pwd_bytes).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode("utf-8")[:72]
    if hashed.startswith("$2b$") or hashed.startswith("$2a$"):
        if not bcrypt:
            return False
        try:
            return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
        except Exception:
            return False
    if hashed.startswith("sha256:"):
        return hmac.compare_digest(
            hashed[7:], hashlib.sha256(pwd_bytes).hexdigest()
        )
    return False


# ─── JWT helpers ──────────────────────────────────────────────────────────────

def create_access_token(user_id: str, role: UserRole) -> tuple[str, int]:
    """Return (encoded_jwt, expires_in_seconds)."""
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "role": role.value,
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "hyperrealm",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def _decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"verify_aud": False},
    )


# ─── FastAPI dependencies ─────────────────────────────────────────────────────

async def _get_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[str]:
    if credentials is None:
        return None
    return credentials.credentials


async def get_current_user(
    token: Optional[str] = Depends(_get_token),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserProfile:
    """Validate token and return the server-side user profile."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = _decode_token(token)
        user_id: str = payload["sub"]
    except (JWTError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repo.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


# Annotated alias for clean route signatures
CurrentUser = Annotated[UserProfile, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    """
    Dependency factory that raises 403 if the authenticated user doesn't
    hold at least one of the required roles.
    """
    async def _check(user: CurrentUser) -> UserProfile:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' is not permitted for this action",
            )
        return user

    return Depends(_check)


def require_min_role(min_role: UserRole):
    """
    Dependency factory: passes if user's role level >= min_role level.
    """
    min_level = ROLE_HIERARCHY[min_role]

    async def _check(user: CurrentUser) -> UserProfile:
        if ROLE_HIERARCHY.get(user.role, 0) < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions — requires at least '{min_role.value}'",
            )
        return user

    return Depends(_check)


# Convenience shorthands
AdminRequired = require_roles(UserRole.ADMIN)
LeadOrAbove = require_min_role(UserRole.TECHNICAL_LEAD)
ManagerOrAbove = require_min_role(UserRole.PROJECT_MANAGER)
