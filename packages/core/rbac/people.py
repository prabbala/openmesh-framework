"""People Management — User CRUD, group assignment, deactivation.

Manages users within tenants with role escalation prevention,
duplicate email rejection, and session revocation on deactivation.
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Set

from .engine import RBACEngine
from .models import Group, GroupMembership, User


class DuplicateEmailError(Exception):
    """Raised when an email already exists within the same tenant."""


class RoleEscalationError(Exception):
    """Raised when an admin tries to assign a role above their own level."""


class UserNotFoundError(Exception):
    """Raised when a user_id is not found."""


class PeopleManager:
    """Manages user lifecycle within tenants.

    Enforces:
    - Role escalation prevention (admin cannot assign above own level)
    - Duplicate email rejection within same tenant
    - Session revocation on user deactivation
    """

    def __init__(self, rbac_engine: RBACEngine) -> None:
        self._rbac = rbac_engine
        self._users: Dict[str, User] = {}
        self._groups: Dict[str, Group] = {}
        self._memberships: List[GroupMembership] = []
        self._active_sessions: Dict[str, Set[str]] = {}  # user_id -> {session_ids}

    # ── User CRUD ────────────────────────────────────────────────────

    def create_user(
        self,
        email: str,
        display_name: str,
        role: str,
        tenant_id: str,
        acting_admin_role: Optional[str] = None,
    ) -> User:
        """Create a user within a tenant.

        Args:
            email: User email (must be unique within tenant).
            display_name: Human-readable name.
            role: Role to assign.
            tenant_id: Tenant this user belongs to.
            acting_admin_role: Role of the admin performing this action
                               (for escalation check).

        Returns:
            The created User.

        Raises:
            DuplicateEmailError: If email exists in the same tenant.
            RoleEscalationError: If assigned role exceeds admin's level.
        """
        # Check duplicate email within tenant
        for u in self._users.values():
            if u.email == email and u.tenant_id == tenant_id:
                raise DuplicateEmailError(
                    f"Email '{email}' already exists in tenant '{tenant_id}'"
                )

        # Check role escalation
        if acting_admin_role is not None:
            admin_level = self._rbac.get_role_level(acting_admin_role)
            target_level = self._rbac.get_role_level(role)
            if target_level < admin_level:
                raise RoleEscalationError(
                    f"Cannot assign role '{role}' (level {target_level}) — "
                    f"exceeds admin role '{acting_admin_role}' (level {admin_level})"
                )

        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            email=email,
            display_name=display_name,
            role=role,
            tenant_id=tenant_id,
            is_active=True,
        )
        self._users[user_id] = user
        self._rbac.assign_role(user_id, role)
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Return a user by ID, or None if not found."""
        return self._users.get(user_id)

    def update_user(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        role: Optional[str] = None,
        acting_admin_role: Optional[str] = None,
    ) -> User:
        """Update a user's display name or role.

        Raises:
            UserNotFoundError: If user does not exist.
            RoleEscalationError: If new role exceeds admin's level.
        """
        user = self._users.get(user_id)
        if user is None:
            raise UserNotFoundError(f"User '{user_id}' not found")

        if role is not None and acting_admin_role is not None:
            admin_level = self._rbac.get_role_level(acting_admin_role)
            target_level = self._rbac.get_role_level(role)
            if target_level < admin_level:
                raise RoleEscalationError(
                    f"Cannot assign role '{role}' (level {target_level}) — "
                    f"exceeds admin role '{acting_admin_role}' (level {admin_level})"
                )

        if display_name is not None:
            user.display_name = display_name
        if role is not None:
            user.role = role
            self._rbac.assign_role(user_id, role)

        return user

    def deactivate_user(self, user_id: str) -> None:
        """Deactivate a user and revoke all active sessions.

        Raises:
            UserNotFoundError: If user does not exist.
        """
        user = self._users.get(user_id)
        if user is None:
            raise UserNotFoundError(f"User '{user_id}' not found")

        user.is_active = False
        # Revoke all active sessions
        self._active_sessions.pop(user_id, None)
        self._rbac.unassign_role(user_id)

    # ── Session management ───────────────────────────────────────────

    def create_session(self, user_id: str) -> str:
        """Create a session for a user. Returns session_id.

        Raises:
            UserNotFoundError: If user does not exist or is inactive.
        """
        user = self._users.get(user_id)
        if user is None:
            raise UserNotFoundError(f"User '{user_id}' not found")
        if not user.is_active:
            raise UserNotFoundError(
                f"User '{user_id}' is deactivated — cannot create session"
            )

        session_id = str(uuid.uuid4())
        self._active_sessions.setdefault(user_id, set()).add(session_id)
        return session_id

    def get_active_sessions(self, user_id: str) -> Set[str]:
        """Return the set of active session IDs for a user."""
        return self._active_sessions.get(user_id, set()).copy()

    # ── Group management ─────────────────────────────────────────────

    def create_group(self, name: str, tenant_id: str) -> Group:
        """Create a group within a tenant."""
        group_id = str(uuid.uuid4())
        group = Group(group_id=group_id, tenant_id=tenant_id, name=name)
        self._groups[group_id] = group
        return group

    def assign_group(self, user_id: str, group_id: str) -> None:
        """Assign a user to a group.

        Raises:
            UserNotFoundError: If user does not exist.
        """
        if user_id not in self._users:
            raise UserNotFoundError(f"User '{user_id}' not found")
        self._memberships.append(
            GroupMembership(user_id=user_id, group_id=group_id)
        )
        self._rbac.add_user_to_group(user_id, group_id)

    def remove_group(self, user_id: str, group_id: str) -> None:
        """Remove a user from a group."""
        self._memberships = [
            m
            for m in self._memberships
            if not (m.user_id == user_id and m.group_id == group_id)
        ]
        self._rbac.remove_user_from_group(user_id, group_id)
