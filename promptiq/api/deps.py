"""FastAPI route dependencies for authentication, database sessions, and tenant context."""

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.database import get_db
from promptiq.core.exceptions import AuthenticationError
from promptiq.core.security import decode_access_token
from promptiq.gateway.eligibility import check_and_reject_byok
from promptiq.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_raw_token(
    token: str | None = Depends(oauth2_scheme),
    authorization: str | None = Header(default=None),
) -> str:
    """Extracts raw JWT bearer token from Authorization header or OAuth2 scheme."""
    raw_token = token
    if not raw_token and authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return raw_token


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolves and validates the authenticated user from JWT Bearer token."""
    raw_token = token
    if not raw_token and authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Check database-backed revocation blocklist
        from promptiq.services.auth_service import AuthService

        if await AuthService.is_token_revoked(db, raw_token):
            raise AuthenticationError("Session token has been revoked or logged out")

        payload = decode_access_token(raw_token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthenticationError("User does not exist or is inactive")

        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


def enforce_no_byok_middleware(payload: dict | None = None) -> None:
    """Dependency enforcing that no client requests contain prohibited BYOK fields."""
    if payload:
        check_and_reject_byok(payload)
