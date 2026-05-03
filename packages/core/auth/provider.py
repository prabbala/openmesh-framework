"""Auth Provider Interface — provider-agnostic authentication.

Defines the abstract interface for authentication providers.
Supports swapping providers (Cognito, Auth0, Keycloak) without code changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class UserClaims:
    """Extracted user identity from an authentication token."""

    user_id: str
    email: str
    role: str
    groups: List[str]
    tenant_id: str
    lob_assignments: List[str]


class AuthProviderInterface(ABC):
    """Provider-agnostic authentication interface.

    Implementations handle token validation, claim extraction,
    and session management for a specific identity provider.
    """

    @abstractmethod
    def authenticate(self, credentials: dict) -> Optional[str]:
        """Authenticate and return a token, or None on failure."""
        ...

    @abstractmethod
    def validate_token(self, token: str) -> bool:
        """Validate a token. Returns True if valid and not expired."""
        ...

    @abstractmethod
    def get_user_claims(self, token: str) -> UserClaims:
        """Extract user identity, role, groups from token."""
        ...

    @abstractmethod
    def revoke_session(self, token: str) -> None:
        """Revoke an active session."""
        ...
