"""JWT Auth Provider — default JWT-based authentication.

A simple JWT implementation that validates tokens without depending
on any specific identity provider. Suitable for development and
as a reference implementation.
"""

from __future__ import annotations

import json
import hashlib
import hmac
import base64
import time
from typing import Dict, Optional, Set

from .provider import AuthProviderInterface, UserClaims


class InvalidTokenError(Exception):
    """Raised when a token is invalid or expired."""

    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.status_code = status_code


class JWTAuthProvider(AuthProviderInterface):
    """Default JWT-based auth provider.

    Uses HMAC-SHA256 for signing. No dependency on external identity providers.
    Tokens are base64-encoded JSON with a signature.
    """

    def __init__(self, secret: str = "openmesh-dev-secret", ttl_seconds: int = 3600) -> None:
        self._secret = secret.encode()
        self._ttl = ttl_seconds
        self._revoked: Set[str] = set()
        self._user_store: Dict[str, dict] = {}  # email -> {password_hash, claims}

    def register_user(
        self,
        email: str,
        password: str,
        user_id: str,
        role: str,
        groups: list,
        tenant_id: str,
        lob_assignments: list,
    ) -> None:
        """Register a user for authentication (dev/test helper)."""
        self._user_store[email] = {
            "password_hash": hashlib.sha256(password.encode()).hexdigest(),
            "claims": {
                "user_id": user_id,
                "email": email,
                "role": role,
                "groups": groups,
                "tenant_id": tenant_id,
                "lob_assignments": lob_assignments,
            },
        }

    def authenticate(self, credentials: dict) -> Optional[str]:
        """Authenticate with email/password and return a JWT token."""
        email = credentials.get("email", "")
        password = credentials.get("password", "")

        user = self._user_store.get(email)
        if user is None:
            return None

        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        if pw_hash != user["password_hash"]:
            return None

        return self._create_token(user["claims"])

    def validate_token(self, token: str) -> bool:
        """Validate a JWT token. Returns True if valid and not expired."""
        try:
            self._decode_token(token)
            return True
        except InvalidTokenError:
            return False

    def get_user_claims(self, token: str) -> UserClaims:
        """Extract user claims from a valid token.

        Raises:
            InvalidTokenError: If token is invalid or expired.
        """
        payload = self._decode_token(token)
        return UserClaims(
            user_id=payload["user_id"],
            email=payload["email"],
            role=payload["role"],
            groups=payload.get("groups", []),
            tenant_id=payload["tenant_id"],
            lob_assignments=payload.get("lob_assignments", []),
        )

    def revoke_session(self, token: str) -> None:
        """Revoke a token so it can no longer be validated."""
        self._revoked.add(token)

    # ── Internal token operations ────────────────────────────────────

    def _create_token(self, claims: dict) -> str:
        """Create a signed JWT token."""
        payload = {**claims, "exp": time.time() + self._ttl, "iat": time.time()}
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode()
        signature = hmac.new(
            self._secret, payload_b64.encode(), hashlib.sha256
        ).hexdigest()
        return f"{payload_b64}.{signature}"

    def _decode_token(self, token: str) -> dict:
        """Decode and validate a JWT token.

        Raises:
            InvalidTokenError: If token is malformed, expired, or revoked.
        """
        if token in self._revoked:
            raise InvalidTokenError("Token has been revoked")

        parts = token.split(".")
        if len(parts) != 2:
            raise InvalidTokenError("Malformed token: expected 2 parts")

        payload_b64, signature = parts

        # Verify signature
        expected_sig = hmac.new(
            self._secret, payload_b64.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            raise InvalidTokenError("Invalid token signature")

        # Decode payload
        try:
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        except (json.JSONDecodeError, Exception) as e:
            raise InvalidTokenError(f"Cannot decode token payload: {e}")

        # Check expiration
        exp = payload.get("exp", 0)
        if time.time() > exp:
            raise InvalidTokenError("Token has expired")

        return payload
