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


def validate_and_sanitize_url(url: str) -> str:
    """Validates user-supplied external URLs against SSRF, internal network traversal, and protocol abuse.

    Strictly prohibits:
    - Non-HTTP/HTTPS protocols (e.g. file://, gopher://, ftp://)
    - Loopback addresses (127.0.0.0/8, ::1, localhost)
    - Private IPv4/IPv6 networks (RFC 1918, RFC 4193)
    - Link-local and cloud metadata services (169.254.169.254, metadata.google.internal)
    - Embedded user credentials in URLs
    """
    import ipaddress
    import socket
    import urllib.parse

    from promptiq.core.exceptions import SecurityError

    if not url or not isinstance(url, str):
        raise SecurityError("URL cannot be empty")

    url = url.strip()
    if len(url) > 2048:
        raise SecurityError("URL exceeds maximum allowed length (2048 characters)")

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        raise SecurityError(f"Malformed URL: {e}")

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise SecurityError(f"Unsupported URL protocol '{scheme}'. Only HTTP and HTTPS are permitted.")

    if not parsed.netloc:
        raise SecurityError("URL is missing a valid hostname")

    if parsed.username or parsed.password:
        raise SecurityError("User credentials embedded in URLs are strictly prohibited.")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityError("Unable to extract valid hostname from URL")

    hostname_lower = hostname.lower()

    # Explicit blacklist for well-known cloud metadata endpoints and local names
    BLOCKED_HOSTNAMES = {
        "localhost",
        "metadata.google.internal",
        "metadata.internal",
        "instance-data",
        "169.254.169.254",
        "127.0.0.1",
        "::1",
    }
    if hostname_lower in BLOCKED_HOSTNAMES or hostname_lower.endswith(".internal") or hostname_lower.endswith(".local"):
        raise SecurityError(f"SSRF Protection: Access to restricted host '{hostname}' is blocked.")

    # Check direct IP address literal
    try:
        ip_obj = ipaddress.ip_address(hostname_lower)
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or str(ip_obj) == "169.254.169.254"
        ):
            raise SecurityError(f"SSRF Protection: IP '{ip_obj}' is in a private, loopback, or cloud-metadata range.")
    except ValueError:
        # Not a raw IP literal; resolve DNS to check target IP address
        try:
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for item in addr_info:
                ip_str = item[4][0]
                resolved_ip = ipaddress.ip_address(ip_str)
                if (
                    resolved_ip.is_private
                    or resolved_ip.is_loopback
                    or resolved_ip.is_link_local
                    or resolved_ip.is_multicast
                    or resolved_ip.is_reserved
                    or str(resolved_ip) == "169.254.169.254"
                ):
                    raise SecurityError(f"SSRF Protection: Host '{hostname}' resolved to private/metadata IP '{resolved_ip}'.")
        except socket.gaierror as e:
            raise SecurityError(f"DNS resolution failed for host '{hostname}': {e}")

    return url
