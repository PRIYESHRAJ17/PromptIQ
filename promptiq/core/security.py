"""Security, authentication tokens, password hashing, and input sanitization."""

import hashlib
import hmac
import ipaddress
import secrets
import socket
import urllib.parse
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any

import anyio
import httpcore
import httpx
import jwt
from httpcore._backends.anyio import SOCKET_OPTION, AnyIOBackend, AnyIOStream
from httpcore._exceptions import ConnectError, ConnectTimeout, map_exceptions
from passlib.context import CryptContext

from promptiq.core.config import settings
from promptiq.core.exceptions import AuthenticationError, SecurityError

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
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.PROMPTIQ_ACCESS_TOKEN_EXPIRE_MINUTES)
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


def verify_host_and_resolve_safe_ips(host: str, port: int = 443) -> list[str]:
    """Validates host against SSRF/internal network rules and resolves to a list of verified safe public IPs.

    Guarantees that:
    1. Restricted hostnames (localhost, metadata, cloud endpoints) are blocked immediately.
    2. Internal network domain suffixes (.internal, .local, .corp, etc.) are blocked.
    3. Alternate integer/hex/octal IP representations are normalized and checked.
    4. Direct IP addresses in private, loopback, link-local, multicast, or metadata ranges are rejected.
    5. DNS resolution checks ALL returned records: if ANY returned IP is restricted, the request is blocked.
    """
    if not host or not isinstance(host, str):
        raise SecurityError("Host cannot be empty")

    host_clean = host.strip()
    if host_clean.startswith("[") and host_clean.endswith("]"):
        host_clean = host_clean[1:-1]

    host_lower = host_clean.lower()

    # Blocked domains and internal network suffixes
    blocked_hostnames = {
        "localhost",
        "metadata.google.internal",
        "metadata.internal",
        "instance-data",
        "169.254.169.254",
        "127.0.0.1",
        "::1",
        "0.0.0.0",  # nosec B104
        "::",
    }
    blocked_suffixes = (
        ".internal",
        ".local",
        ".corp",
        ".lan",
        ".home",
        ".localhost",
        ".arpa",
    )
    if host_lower in blocked_hostnames or any(host_lower.endswith(sfx) for sfx in blocked_suffixes):
        raise SecurityError(f"SSRF Protection: Access to restricted host '{host}' is blocked.")

    # 1. Normalize alternate IP representations (integer IP, hex, octal, dotted hex/octal)
    def _parse_c_int(s: str) -> int:
        s_clean = s.strip()
        if s_clean.startswith(("0x", "0X")):
            return int(s_clean, 16)
        if s_clean.startswith("0") and len(s_clean) > 1 and s_clean.isdigit():
            return int(s_clean, 8)
        return int(s_clean, 10)

    target_for_ip_check = host_lower
    try:
        if "." in host_lower:
            parts = [_parse_c_int(p) for p in host_lower.split(".")]
            if len(parts) == 4 and all(0 <= p <= 255 for p in parts):
                target_for_ip_check = ".".join(str(p) for p in parts)
        elif host_lower.isdigit() or host_lower.startswith(("0x", "0X")):
            val = _parse_c_int(host_lower)
            if 0 <= val <= 0xFFFFFFFF:
                target_for_ip_check = str(ipaddress.IPv4Address(val))
    except (ValueError, OverflowError):
        pass

    def _check_ip_address(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
            or str(ip_obj) == "169.254.169.254"
        ):
            raise SecurityError(
                f"SSRF Protection: IP '{ip_obj}' is in a private, loopback, or cloud-metadata range."
            )

    # 2. Check direct IP address literal
    try:
        ip_obj = ipaddress.ip_address(target_for_ip_check)
        _check_ip_address(ip_obj)
        return [str(ip_obj)]
    except ValueError:
        # 3. Not a raw IP literal; resolve DNS and verify EVERY returned IP address
        try:
            addr_info = socket.getaddrinfo(host_clean, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            safe_ips: list[str] = []
            for item in addr_info:
                ip_str = item[4][0]
                resolved_ip = ipaddress.ip_address(ip_str)
                _check_ip_address(resolved_ip)
                if ip_str not in safe_ips:
                    safe_ips.append(ip_str)
            if not safe_ips:
                raise SecurityError(
                    f"SSRF Protection: No safe IP addresses resolved for host '{host}'."
                )
            return safe_ips
        except socket.gaierror as e:
            raise SecurityError(f"DNS resolution failed for host '{host}': {e}")


def validate_and_sanitize_url(url: str) -> str:
    """Validates user-supplied external URLs against SSRF, internal network traversal, and protocol abuse.

    Strictly prohibits:
    - Non-HTTP/HTTPS protocols (e.g. file://, gopher://, ftp://)
    - Loopback addresses (127.0.0.0/8, ::1, localhost)
    - Private IPv4/IPv6 networks (RFC 1918, RFC 4193)
    - Link-local and cloud metadata services (169.254.169.254, metadata.google.internal)
    - Embedded user credentials in URLs
    """
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
        raise SecurityError(
            f"Unsupported URL protocol '{scheme}'. Only HTTP and HTTPS are permitted."
        )

    if not parsed.netloc:
        raise SecurityError("URL is missing a valid hostname")

    if parsed.username or parsed.password:
        raise SecurityError("User credentials embedded in URLs are strictly prohibited.")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityError("Unable to extract valid hostname from URL")

    port = parsed.port or (443 if scheme == "https" else 80)
    verify_host_and_resolve_safe_ips(hostname, port)
    return url


class SSRFSafeNetworkBackend(AnyIOBackend):
    """Network backend enforcing transport-level DNS validation and socket pinning.

    Eliminates TOCTOU DNS rebinding windows by resolving DNS once, verifying that ALL
    resolved records are safe public IPs, and connecting directly to the validated IP.
    """

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[SOCKET_OPTION] | None = None,
    ) -> AnyIOStream:
        safe_ips = verify_host_and_resolve_safe_ips(host, port)
        if not safe_ips:
            raise SecurityError(
                f"SSRF Protection: No verified safe IPs available for host '{host}'."
            )

        safe_ip = safe_ips[0]

        if socket_options is None:
            socket_options = []
        exc_map = {
            TimeoutError: ConnectTimeout,
            OSError: ConnectError,
            anyio.BrokenResourceError: ConnectError,
        }
        with map_exceptions(exc_map):
            with anyio.fail_after(timeout):
                stream: anyio.abc.ByteStream = await anyio.connect_tcp(
                    remote_host=safe_ip,
                    remote_port=port,
                    local_host=local_address,
                )
                for option in socket_options:
                    stream._raw_socket.setsockopt(*option)  # type: ignore[attr-defined]
        return AnyIOStream(stream)


class SSRFSafeAsyncTransport(httpx.AsyncHTTPTransport):
    """AsyncHTTPTransport configured with SSRFSafeNetworkBackend for verified socket pinning."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=self._pool._ssl_context,
            max_connections=self._pool._max_connections,
            max_keepalive_connections=self._pool._max_keepalive_connections,
            keepalive_expiry=self._pool._keepalive_expiry,
            http1=self._pool._http1,
            http2=self._pool._http2,
            retries=self._pool._retries,
            local_address=self._pool._local_address,
            uds=self._pool._uds,
            network_backend=SSRFSafeNetworkBackend(),
            socket_options=self._pool._socket_options,
        )


async def safe_fetch_url(
    url: str,
    timeout: float = 5.0,
    max_redirects: int = 3,
    headers: dict[str, str] | None = None,
) -> Any:
    """Fetches an external URL securely with strict SSRF validation at every redirect hop and transport-level DNS pinning."""
    current_url = validate_and_sanitize_url(url)
    redirect_count = 0
    transport = SSRFSafeAsyncTransport(verify=True)

    async with httpx.AsyncClient(
        transport=transport, timeout=timeout, follow_redirects=False
    ) as client:
        while True:
            resp = await client.get(current_url, headers=headers)
            if resp.status_code in (301, 302, 303, 307, 308):
                redirect_count += 1
                if redirect_count > max_redirects:
                    raise SecurityError(f"Too many redirects (exceeded limit of {max_redirects})")
                loc = resp.headers.get("location")
                if not loc:
                    return resp
                next_url = urllib.parse.urljoin(current_url, loc)
                current_url = validate_and_sanitize_url(next_url)
            else:
                return resp
