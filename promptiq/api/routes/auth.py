"""Authentication and user management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db, get_raw_token
from promptiq.core.exceptions import AuthenticationError, ConflictError
from promptiq.core.security import (
    generate_telegram_link_token,
    verify_telegram_link_token,
)
from promptiq.models.user import User
from promptiq.schemas.auth import (
    LogoutResponse,
    PasswordChangeRequest,
    RefreshTokenRequest,
    TelegramLinkRequest,
    TelegramLinkResponse,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from promptiq.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account and provision a default workspace."""
    try:
        user, _ = await AuthService.register_user(db, user_in)
        access_token, refresh_token = await AuthService.create_user_session(db, user)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in_minutes=1440,
            user=UserResponse.model_validate(user),
        )
    except ConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password to receive access and refresh tokens."""
    try:
        user = await AuthService.authenticate_user(db, credentials.email, credentials.password)
        access_token, refresh_token = await AuthService.create_user_session(db, user)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in_minutes=1440,
            user=UserResponse.model_validate(user),
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)


@router.post("/refresh", response_model=Token)
async def refresh_token_session(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Rotates refresh token and returns fresh access token."""
    try:
        new_access, new_refresh, user = await AuthService.refresh_session(db, req.refresh_token)
        return Token(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in_minutes=1440,
            user=UserResponse.model_validate(user),
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    raw_token: str = Depends(get_raw_token),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revokes the current JWT access token, ending the active session."""
    await AuthService.revoke_access_token(db, raw_token, user.id, reason="user_logout")
    return LogoutResponse(success=True, message="Session successfully revoked")


@router.post("/change-password", response_model=LogoutResponse)
async def change_password(
    req: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Changes user password and invalidates existing refresh sessions."""
    try:
        await AuthService.change_password(db, user.id, req.current_password, req.new_password)
        return LogoutResponse(
            success=True,
            message="Password successfully updated. Other sessions invalidated.",
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.delete("/me", response_model=LogoutResponse)
async def delete_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently deletes the current user account and invalidates tokens."""
    await AuthService.delete_user_account(db, user.id)
    return LogoutResponse(success=True, message="Account permanently deleted")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return UserResponse.model_validate(user)


@router.post("/telegram-token")
async def generate_telegram_token(user: User = Depends(get_current_user)):
    """Generates a secure, short-lived token to link a Telegram account."""
    link_token = generate_telegram_link_token(user.id)
    return {
        "link_token": link_token,
        "instructions": f"Send `/start {link_token}` to the PromptIQ Telegram bot to link your account.",
    }


@router.post("/telegram-link", response_model=TelegramLinkResponse)
async def link_telegram(req: TelegramLinkRequest, db: AsyncSession = Depends(get_db)):
    """Links a Telegram account to a user via signed link token."""
    try:
        user_id = verify_telegram_link_token(req.link_token)
        user = await AuthService.link_telegram_account(db, user_id, req.telegram_chat_id)
        return TelegramLinkResponse(
            success=True,
            message="Telegram account successfully linked.",
            user_id=user.id,
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
