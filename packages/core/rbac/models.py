"""RBAC data models — roles, permissions, users, groups.

Defines the role hierarchy, permission model, and people management types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set


class DefaultRole(Enum):
    """Default role hierarchy (highest to lowest privilege)."""

    SUPERUSER = "superuser"
    ADMIN = "admin"
    OPERATOR = "operator"
    AUDITOR = "auditor"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"


# Role hierarchy level — lower number = higher privilege
ROLE_HIERARCHY: Dict[str, int] = {
    DefaultRole.SUPERUSER.value: 0,
    DefaultRole.ADMIN.value: 1,
    DefaultRole.OPERATOR.value: 2,
    DefaultRole.AUDITOR.value: 3,
    DefaultRole.MANAGER.value: 4,
    DefaultRole.STAFF.value: 5,
    DefaultRole.VIEWER.value: 6,
}


@dataclass(frozen=True)
class Permission:
    """A single resource-action permission."""

    resource: str
    action: str


@dataclass
class RoleDefinition:
    """A role with its permission set."""

    role_name: str
    permissions: Set[Permission] = field(default_factory=set)
    is_system_role: bool = False
    is_custom: bool = False


@dataclass
class User:
    """A user within a tenant."""

    user_id: str
    email: str
    display_name: str
    role: str
    tenant_id: str
    is_active: bool = True
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class Group:
    """A group within a tenant for policy-based access."""

    group_id: str
    tenant_id: str
    name: str


@dataclass
class GroupMembership:
    """Links a user to a group."""

    user_id: str
    group_id: str


@dataclass
class GroupPolicy:
    """A policy granting permissions to a group."""

    group_id: str
    permissions: Set[Permission] = field(default_factory=set)
    lob_ids: List[str] = field(default_factory=list)
