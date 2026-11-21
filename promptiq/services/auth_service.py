"""Authentication and user management domain service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.exceptions import AuthenticationError, ConflictError
from promptiq.core.security import get_password_hash, verify_password
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
            raise ConflictError(expected_version=0, actual_version=1)  # Or raise PromptIQException with 409

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
