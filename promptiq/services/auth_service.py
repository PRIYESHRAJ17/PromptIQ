"""Authentication and user management domain service."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.exceptions import AuthenticationError, PromptIQException
from promptiq.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from promptiq.models.auth import RefreshToken, RevokedToken
from promptiq.models.user import User, Workspace, WorkspaceMembership
from promptiq.schemas.auth import UserCreate


class AuthService:
    """Manages user registration, authentication, workspace provisioning, and Telegram account binding."""

    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserCreate) -> tuple[User, Workspace]:
        """Registers a new user and provisions their default workspace."""
        # Check if email is already taken
        stmt = select(User).where(User.email == user_in.email)
        res = await db.execute(stmt)
        if res.scalar_one_or_none() is not None:
            raise PromptIQException(
                message=f"User with email '{user_in.email}' already exists",
                error_code="USER_ALREADY_EXISTS",
                status_code=409,
            )

        hashed_pw = get_password_hash(user_in.password)
        user = User(
            email=user_in.email,
            hashed_password=hashed_pw,
            full_name=user_in.full_name or user_in.email.split("@")[0],
            is_active=True,
        )
        db.add(user)
        await db.flush()

        # Create default personal workspace
        workspace_name = f"{user.full_name}'s Workspace"
        workspace = Workspace(
            name=workspace_name,
            owner_id=user.id,
        )
        db.add(workspace)
        await db.flush()

        # Assign user as owner of default workspace
        membership = WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
        )
        db.add(membership)
        await db.flush()

        return user, workspace

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
        """Validates user credentials."""
        stmt = select(User).where(User.email == email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        return user

    @staticmethod
    async def link_telegram_account(db: AsyncSession, user_id: str, telegram_chat_id: str) -> User:
        """Associates a Telegram Chat ID with an authenticated user account."""
        # Check if chat ID is already linked to another user
        stmt = select(User).where(User.telegram_chat_id == telegram_chat_id)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing and existing.id != user_id:
            raise AuthenticationError("This Telegram account is already linked to another user")

        stmt_user = select(User).where(User.id == user_id)
        res_user = await db.execute(stmt_user)
        user = res_user.scalar_one_or_none()
        if not user:
            raise AuthenticationError("User not found")

        user.telegram_chat_id = telegram_chat_id
        await db.flush()
        return user

    @staticmethod
    async def get_user_by_telegram_id(db: AsyncSession, telegram_chat_id: str) -> User | None:
        """Resolves a user from their linked Telegram Chat ID."""
        stmt = select(User).where(User.telegram_chat_id == telegram_chat_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def create_user_session(db: AsyncSession, user: User) -> tuple[str, str]:
        """Issues an access token and persists a new durable refresh token."""
        access_token = create_access_token({"sub": user.id})
        raw_refresh, token_hash, expires_at = create_refresh_token()

        refresh_record = RefreshToken(
            token_hash=token_hash,
            user_id=user.id,
            is_revoked=False,
            expires_at=expires_at,
        )
        db.add(refresh_record)
        await db.flush()
        return access_token, raw_refresh

    @staticmethod
    async def refresh_session(db: AsyncSession, raw_refresh_token: str) -> tuple[str, str, User]:
        """Rotates a refresh token: invalidates old token, creates new token, issues fresh access token."""
        old_hash = hash_token(raw_refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == old_hash)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        if not existing or existing.is_revoked:
            raise AuthenticationError("Refresh token is invalid or has already been used")

        now = datetime.now(UTC)
        expires_at = existing.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < now:
            existing.is_revoked = True
            await db.flush()
            raise AuthenticationError("Refresh token has expired")

        # Resolve user
        user_stmt = select(User).where(User.id == existing.user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthenticationError("User is inactive or deleted")

        # Issue new tokens and rotate
        new_access = create_access_token({"sub": user.id})
        new_raw_refresh, new_hash, new_expires = create_refresh_token()

        new_refresh = RefreshToken(
            token_hash=new_hash,
            user_id=user.id,
            is_revoked=False,
            expires_at=new_expires,
        )
        db.add(new_refresh)
        await db.flush()

        # Mark old token as revoked and rotated
        existing.is_revoked = True
        existing.rotated_to_id = new_refresh.id
        await db.flush()

        return new_access, new_raw_refresh, user

    @staticmethod
    async def revoke_access_token(
        db: AsyncSession,
        raw_token: str,
        user_id: str,
        reason: str = "logout",
    ) -> None:
        """Adds an access token to the database-backed revocation blocklist."""
        token_h = hash_token(raw_token)
        # Check if already revoked
        stmt = select(RevokedToken).where(RevokedToken.token_hash == token_h)
        res = await db.execute(stmt)
        if res.scalar_one_or_none() is not None:
            return

        try:
            payload = decode_access_token(raw_token)
            exp_ts = payload.get("exp")
            expires_at = (
                datetime.fromtimestamp(exp_ts, tz=UTC)
                if exp_ts
                else datetime.now(UTC) + timedelta(hours=24)
            )
        except Exception:
            expires_at = datetime.now(UTC) + timedelta(hours=24)

        rev_record = RevokedToken(
            token_hash=token_h,
            user_id=user_id,
            revoked_at=datetime.now(UTC),
            expires_at=expires_at,
            reason=reason,
        )
        db.add(rev_record)
        await db.flush()

    @staticmethod
    async def is_token_revoked(db: AsyncSession, raw_token: str) -> bool:
        """Verifies whether an access token is in the database revocation blocklist."""
        token_h = hash_token(raw_token)
        stmt = select(RevokedToken).where(RevokedToken.token_hash == token_h)
        res = await db.execute(stmt)
        return res.scalar_one_or_none() is not None

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> User:
        """Changes user password and revokes all active refresh tokens."""
        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise AuthenticationError("User not found")

        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Incorrect current password")

        user.hashed_password = get_password_hash(new_password)
        # Invalidate all active refresh tokens for this user
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)  # noqa: E712
            .values(is_revoked=True)
        )
        await db.flush()
        return user

    @staticmethod
    async def delete_user_account(db: AsyncSession, user_id: str) -> bool:
        """Permanently deletes a user account and associated memberships."""
        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise AuthenticationError("User not found")

        # Invalidate refresh tokens
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
        await db.delete(user)
        await db.flush()
        return True
