"""RBAC Engine and People Management."""

from .engine import RBACEngine, RoleInUseError, RoleNotFoundError
from .models import (
    DefaultRole,
    Group,
    GroupMembership,
    GroupPolicy,
    Permission,
    ROLE_HIERARCHY,
    RoleDefinition,
    User,
)
from .people import (
    DuplicateEmailError,
    PeopleManager,
    RoleEscalationError,
    UserNotFoundError,
)

__all__ = [
    "DefaultRole",
    "Group",
    "GroupMembership",
    "GroupPolicy",
    "Permission",
    "ROLE_HIERARCHY",
    "RoleDefinition",
    "User",
    "RBACEngine",
    "RoleNotFoundError",
    "RoleInUseError",
    "PeopleManager",
    "DuplicateEmailError",
    "RoleEscalationError",
    "UserNotFoundError",
]
