"""RBAC Engine — role-based access control with dual-path evaluation.

Evaluates access based on three dimensions: user role, group membership,
and LOB scope. Supports default hierarchy and custom roles.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from .models import (
    DefaultRole,
    GroupPolicy,
    Permission,
    ROLE_HIERARCHY,
    RoleDefinition,
)


class RoleNotFoundError(Exception):
    """Raised when a role is not found."""


class RoleInUseError(Exception):
    """Raised when deleting a role that has assigned users."""

    def __init__(self, message: str, user_count: int) -> None:
        super().__init__(message)
        self.user_count = user_count


class RBACEngine:
    """Role-based access control with dual-path evaluation.

    Access is granted if EITHER:
    1. The user's role permissions permit the action, OR
    2. The user's group-level policies permit the action.

    Access is denied only when neither path permits.
    """

    def __init__(self) -> None:
        self._roles: Dict[str, RoleDefinition] = {}
        self._user_roles: Dict[str, str] = {}  # user_id -> role_name
        self._user_groups: Dict[str, Set[str]] = {}  # user_id -> {group_ids}
        self._group_policies: Dict[str, GroupPolicy] = {}  # group_id -> policy
        self._init_default_roles()

    def _init_default_roles(self) -> None:
        """Initialize the default role hierarchy with base permissions."""
        # Superuser gets wildcard access
        self._roles[DefaultRole.SUPERUSER.value] = RoleDefinition(
            role_name=DefaultRole.SUPERUSER.value,
            permissions={Permission("*", "*")},
            is_system_role=True,
        )
        self._roles[DefaultRole.ADMIN.value] = RoleDefinition(
            role_name=DefaultRole.ADMIN.value,
            permissions={
                Permission("dashboard", "read"),
                Permission("dashboard", "write"),
                Permission("users", "read"),
                Permission("users", "write"),
                Permission("roles", "read"),
                Permission("roles", "write"),
                Permission("tenants", "read"),
                Permission("tenants", "write"),
                Permission("audit", "read"),
                Permission("domains", "read"),
                Permission("domains", "write"),
                Permission("observability", "read"),
                Permission("metrics", "read"),
            },
            is_system_role=True,
        )
        self._roles[DefaultRole.OPERATOR.value] = RoleDefinition(
            role_name=DefaultRole.OPERATOR.value,
            permissions={
                Permission("dashboard", "read"),
                Permission("observability", "read"),
                Permission("metrics", "read"),
                Permission("domains", "read"),
            },
            is_system_role=True,
        )
        self._roles[DefaultRole.AUDITOR.value] = RoleDefinition(
            role_name=DefaultRole.AUDITOR.value,
            permissions={
                Permission("audit", "read"),
                Permission("dashboard", "read"),
                Permission("observability", "read"),
            },
            is_system_role=True,
        )
        self._roles[DefaultRole.MANAGER.value] = RoleDefinition(
            role_name=DefaultRole.MANAGER.value,
            permissions={
                Permission("dashboard", "read"),
                Permission("users", "read"),
                Permission("observability", "read"),
            },
            is_system_role=True,
        )
        self._roles[DefaultRole.STAFF.value] = RoleDefinition(
            role_name=DefaultRole.STAFF.value,
            permissions={
                Permission("dashboard", "read"),
                Permission("observability", "read"),
            },
            is_system_role=True,
        )
        self._roles[DefaultRole.VIEWER.value] = RoleDefinition(
            role_name=DefaultRole.VIEWER.value,
            permissions={
                Permission("dashboard", "read"),
            },
            is_system_role=True,
        )

    # ── Role management ──────────────────────────────────────────────

    def get_role(self, role_name: str) -> Optional[RoleDefinition]:
        """Return a role definition, or None if not found."""
        return self._roles.get(role_name)

    def define_custom_role(
        self, role_name: str, permissions: Set[Permission]
    ) -> RoleDefinition:
        """Define a custom role with arbitrary permissions.

        Args:
            role_name: Unique name for the custom role.
            permissions: Set of Permission objects.

        Returns:
            The created RoleDefinition.
        """
        role = RoleDefinition(
            role_name=role_name,
            permissions=permissions,
            is_system_role=False,
            is_custom=True,
        )
        self._roles[role_name] = role
        return role

    def delete_role(self, role_name: str) -> None:
        """Delete a role. Rejects if users are assigned.

        Raises:
            RoleNotFoundError: If role does not exist.
            RoleInUseError: If users are assigned to this role.
        """
        if role_name not in self._roles:
            raise RoleNotFoundError(f"Role '{role_name}' not found")

        assigned_count = sum(
            1 for r in self._user_roles.values() if r == role_name
        )
        if assigned_count > 0:
            raise RoleInUseError(
                f"Cannot delete role '{role_name}': "
                f"{assigned_count} user(s) are assigned",
                user_count=assigned_count,
            )
        del self._roles[role_name]

    # ── User-role assignment ─────────────────────────────────────────

    def assign_role(self, user_id: str, role_name: str) -> None:
        """Assign a role to a user."""
        self._user_roles[user_id] = role_name

    def get_user_role(self, user_id: str) -> Optional[str]:
        """Return the role assigned to a user."""
        return self._user_roles.get(user_id)

    def unassign_role(self, user_id: str) -> None:
        """Remove role assignment from a user."""
        self._user_roles.pop(user_id, None)

    # ── Group management ─────────────────────────────────────────────

    def add_user_to_group(self, user_id: str, group_id: str) -> None:
        """Add a user to a group."""
        self._user_groups.setdefault(user_id, set()).add(group_id)

    def remove_user_from_group(self, user_id: str, group_id: str) -> None:
        """Remove a user from a group."""
        groups = self._user_groups.get(user_id)
        if groups:
            groups.discard(group_id)

    def set_group_policy(self, policy: GroupPolicy) -> None:
        """Set a policy for a group."""
        self._group_policies[policy.group_id] = policy

    # ── Access evaluation ────────────────────────────────────────────

    def has_permission(self, role: str, resource: str, action: str) -> bool:
        """Check if a role has permission for a resource/action.

        Wildcard '*' matches any resource or action.
        """
        role_def = self._roles.get(role)
        if role_def is None:
            return False

        target = Permission(resource, action)
        for perm in role_def.permissions:
            if perm == target:
                return True
            if perm.resource == "*" and perm.action == "*":
                return True
            if perm.resource == resource and perm.action == "*":
                return True
            if perm.resource == "*" and perm.action == action:
                return True
        return False

    def evaluate_access(
        self, user_id: str, resource: str, action: str
    ) -> bool:
        """Check access via dual-path: role OR group policies.

        Grant if either path permits. Deny only when neither permits.
        """
        # Path 1: Role permissions
        role = self._user_roles.get(user_id)
        if role and self.has_permission(role, resource, action):
            return True

        # Path 2: Group-level policies
        user_groups = self._user_groups.get(user_id, set())
        target = Permission(resource, action)
        for group_id in user_groups:
            policy = self._group_policies.get(group_id)
            if policy is None:
                continue
            for perm in policy.permissions:
                if perm == target:
                    return True
                if perm.resource == "*" and perm.action == "*":
                    return True
                if perm.resource == resource and perm.action == "*":
                    return True
                if perm.resource == "*" and perm.action == action:
                    return True

        return False

    def get_role_level(self, role_name: str) -> int:
        """Return the hierarchy level for a role (lower = more privileged).

        Custom roles default to level 99 (lowest privilege).
        """
        return ROLE_HIERARCHY.get(role_name, 99)
