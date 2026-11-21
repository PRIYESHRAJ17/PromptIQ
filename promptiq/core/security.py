"""Security, authentication tokens, password hashing, and input sanitization."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from promptiq.core.config import settings
from promptiq.core.exceptions import AuthenticationError

# Password hashing context using standard pbkdf2_sha256
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a password using PBKDF2-SHA256."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta else timedelta(minutes=settings.PROMPTIQ_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    return jwt.encode(to_encode, settings.PROMPTIQ_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, settings.PROMPTIQ_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Session token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid session token")


def generate_api_key() -> str:
    """Generates a cryptographically secure random API key for integrations."""
    return f"piq_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hashes an API key using SHA-256 for secure storage."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def generate_telegram_link_token(user_id: str, expires_in_minutes: int = 15) -> str:
    """Generates a signed, short-lived HMAC token for linking a Telegram account to a user."""
    expires_at = int((datetime.now(UTC) + timedelta(minutes=expires_in_minutes)).timestamp())
    payload = f"{user_id}:{expires_at}"
    signature = hmac.new(
        settings.PROMPTIQ_SECRET_KEY.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{signature}"


def verify_telegram_link_token(token: str) -> str:
    """Validates a Telegram link token and returns the user_id if valid."""
    try:
        parts = token.split(":")
        if len(parts) != 3:
            raise AuthenticationError("Malformed link token")

        user_id, expires_at_str, signature = parts
        expires_at = int(expires_at_str)

        if datetime.now(UTC).timestamp() > expires_at:
            raise AuthenticationError("Telegram link token has expired")

        expected_payload = f"{user_id}:{expires_at_str}"
        expected_sig = hmac.new(
            settings.PROMPTIQ_SECRET_KEY.encode("utf-8"),
            expected_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            raise AuthenticationError("Invalid token signature")

        return user_id
    except (ValueError, IndexError):
        raise AuthenticationError("Invalid link token")


def sanitize_untrusted_input(text: str) -> str:
    """Sanitizes untrusted input, stripping non-printable control characters."""
    if not isinstance(text, str):
        return text
    # Strip null bytes and non-printable control characters except newline and tab
    clean = "".join(ch for ch in text if ch in "\n\r\t" or (ord(ch) >= 32 and ord(ch) != 127))
    return clean.strip()
