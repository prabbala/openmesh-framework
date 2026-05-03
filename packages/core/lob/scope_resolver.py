"""Scope Resolver — resolves effective LOB scope for a user.

Resolves scope by intersecting role permissions, group LOB assignments,
and tenant LOB configuration. Superuser/platform_operator get unrestricted scope.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from packages.core.rbac.engine import RBACEngine
from packages.core.rbac.models import GroupPolicy

from .store import LOBStore


class ScopeResolver:
    """Resolves a user's effective LOB scope.

    The effective scope is the intersection of:
    1. Role-permitted LOBs (from RBAC)
    2. Group LOB assignments (from group policies)
    3. User's explicit LOB assignments

    Superuser and platform_operator roles get unrestricted scope.
    """

    UNRESTRICTED_ROLES = frozenset({"superuser", "platform_operator"})

    def __init__(self, lob_store: LOBStore, rbac_engine: RBACEngine) -> None:
        self._lob_store = lob_store
        self._rbac = rbac_engine

    def resolve_scope(
        self,
        role: str,
        groups: List[str],
        lob_assignments: List[str],
    ) -> Set[str]:
        """Resolve the effective LOB scope for a user.

        Args:
            role: The user's role name.
            groups: List of group IDs the user belongs to.
            lob_assignments: Explicit LOB IDs assigned to the user.

        Returns:
            Set of LOB IDs the user has access to.
            For unrestricted roles, returns ALL LOB IDs.
        """
        # Superuser / platform_operator: unrestricted
        if role in self.UNRESTRICTED_ROLES:
            return self._lob_store.get_all_lob_ids()

        # Start with the user's explicit LOB assignments
        user_lobs = set(lob_assignments)

        # Collect group LOB assignments
        group_lobs: Set[str] = set()
        for group_id in groups:
            policy = self._rbac._group_policies.get(group_id)
            if policy is not None and hasattr(policy, "lob_ids"):
                group_lobs.update(policy.lob_ids)

        # If user has both explicit and group assignments, intersect them
        # If only one source exists, use that source
        if user_lobs and group_lobs:
            effective = user_lobs & group_lobs
        elif user_lobs:
            effective = user_lobs
        elif group_lobs:
            effective = group_lobs
        else:
            effective = set()

        # Filter to only LOBs that actually exist in the store
        all_lobs = self._lob_store.get_all_lob_ids()
        return effective & all_lobs
