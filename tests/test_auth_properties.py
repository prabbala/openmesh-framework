"""Property tests for Auth Provider.

Feature: openmesh-framework, Property 27: Invalid Token Rejection
Validates: Requirements 13.4
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from packages.core.auth.jwt_provider import InvalidTokenError, JWTAuthProvider

_prop_settings = settings(
    max_examples=100, suppress_health_check=[HealthCheck.too_slow]
)

_email_st = st.from_regex(r"[a-z]{3,8}@test\.com", fullmatch=True)
_password_st = st.from_regex(r"[a-zA-Z0-9]{6,12}", fullmatch=True)


class TestInvalidTokenRejection:
    """Property 27: Invalid or expired tokens SHALL be rejected
    with 401 status and descriptive error.
    """

    # Feature: openmesh-framework, Property 27: Invalid Token Rejection
    @given(garbage=st.from_regex(r"[a-zA-Z0-9]{5,30}", fullmatch=True))
    @_prop_settings
    def test_garbage_token_rejected(self, garbage: str):
        """Random string tokens are rejected."""
        provider = JWTAuthProvider()
        assert provider.validate_token(garbage) is False

    # Feature: openmesh-framework, Property 27: Invalid Token Rejection
    @given(email=_email_st, password=_password_st)
    @_prop_settings
    def test_valid_token_accepted(self, email: str, password: str):
        """Properly issued tokens are accepted."""
        provider = JWTAuthProvider()
        provider.register_user(
            email=email, password=password, user_id="u1",
            role="admin", groups=[], tenant_id="t1", lob_assignments=[],
        )
        token = provider.authenticate({"email": email, "password": password})
        assert token is not None
        assert provider.validate_token(token) is True

    # Feature: openmesh-framework, Property 27: Invalid Token Rejection
    @given(email=_email_st, password=_password_st)
    @_prop_settings
    def test_revoked_token_rejected(self, email: str, password: str):
        """Revoked tokens are rejected."""
        provider = JWTAuthProvider()
        provider.register_user(
            email=email, password=password, user_id="u1",
            role="admin", groups=[], tenant_id="t1", lob_assignments=[],
        )
        token = provider.authenticate({"email": email, "password": password})
        assert token is not None

        provider.revoke_session(token)
        assert provider.validate_token(token) is False

    # Feature: openmesh-framework, Property 27: Invalid Token Rejection
    @given(email=_email_st, password=_password_st)
    @_prop_settings
    def test_expired_token_rejected(self, email: str, password: str):
        """Expired tokens are rejected."""
        provider = JWTAuthProvider(ttl_seconds=-1)  # Already expired
        provider.register_user(
            email=email, password=password, user_id="u1",
            role="admin", groups=[], tenant_id="t1", lob_assignments=[],
        )
        token = provider.authenticate({"email": email, "password": password})
        assert token is not None
        assert provider.validate_token(token) is False

    # Feature: openmesh-framework, Property 27: Invalid Token Rejection
    @given(email=_email_st, password=_password_st)
    @_prop_settings
    def test_claims_extracted_from_valid_token(self, email: str, password: str):
        """User claims are correctly extracted from valid tokens."""
        provider = JWTAuthProvider()
        provider.register_user(
            email=email, password=password, user_id="u1",
            role="operator", groups=["g1"], tenant_id="t1",
            lob_assignments=["lob1"],
        )
        token = provider.authenticate({"email": email, "password": password})
        claims = provider.get_user_claims(token)

        assert claims.user_id == "u1"
        assert claims.email == email
        assert claims.role == "operator"
        assert claims.tenant_id == "t1"

    # Feature: openmesh-framework, Property 27: Invalid Token Rejection
    def test_wrong_password_returns_none(self):
        """Wrong password returns None (no token)."""
        provider = JWTAuthProvider()
        provider.register_user(
            email="test@test.com", password="correct",
            user_id="u1", role="admin", groups=[],
            tenant_id="t1", lob_assignments=[],
        )
        token = provider.authenticate({"email": "test@test.com", "password": "wrong"})
        assert token is None
