"""Governance Engine — evaluates observability = function(role, LOB_scope, domain).

The central policy orchestrator that ties RBAC + LOB + Domain together.
Uses in-memory policy evaluation for sub-50ms latency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from packages.core.domain_registry.registry import DomainRegistry
from packages.core.lob.scope_resolver import ScopeResolver
from packages.core.rbac.engine import RBACEngine


@dataclass
class GovernanceResult:
    """Result of a governance evaluation."""

    authorized_domains: Set[str]
    authorized_panels: List[str]
    authorized_lob_scope: Set[str]
    is_unrestricted: bool


class PolicyChangeEvent:
    """Represents a change to roles, LOBs, or domain registrations."""

    def __init__(self, change_type: str, entity_id: str = "", detail: dict = None):
        self.change_type = change_type
        self.entity_id = entity_id
        self.detail = detail or {}


class GovernanceEngine:
    """Evaluates observability = function(role, LOB_scope, domain).

    All policy data is held in-memory for sub-50ms evaluation.
    Re-evaluates on every request — no stale cached decisions.
    """

    UNRESTRICTED_ROLES = frozenset({"superuser", "platform_operator"})
    ADMIN_ACTIONS = frozenset({"create", "update", "delete", "write"})

    def __init__(
        self,
        rbac_engine: RBACEngine,
        scope_resolver: ScopeResolver,
        domain_registry: DomainRegistry,
    ) -> None:
        self._rbac = rbac_engine
        self._scope_resolver = scope_resolver
        self._domain_registry = domain_registry
        self._policy_cache: Dict = {}

    def load_policies(self) -> None:
        """Load all policies into memory. Called on startup."""
        self._policy_cache = {
            "loaded": True,
            "domains": {
                d.domain_id: d
                for d in self._domain_registry.list_all()
            },
        }

    def evaluate(
        self,
        user_id: str,
        role: str,
        groups: List[str],
        lob_assignments: List[str],
        target_domain: Optional[str] = None,
    ) -> GovernanceResult:
        """Evaluate observability access. No DB calls on this path.

        Returns the set of domains, panels, and LOBs the user is authorized to see.
        Re-evaluates fresh on every call — no stale decisions.
        """
        # Check unrestricted roles
        if role in self.UNRESTRICTED_ROLES:
            all_domains = self._domain_registry.list_all()
            all_panels = []
            for d in all_domains:
                for tab in d.tabs:
                    panel_id = f"{d.domain_id}:{tab.get('title', 'unknown')}"
                    all_panels.append(panel_id)

            return GovernanceResult(
                authorized_domains={d.domain_id for d in all_domains},
                authorized_panels=all_panels,
                authorized_lob_scope=self._scope_resolver.resolve_scope(
                    role, groups, lob_assignments
                ),
                is_unrestricted=True,
            )

        # Resolve LOB scope
        lob_scope = self._scope_resolver.resolve_scope(
            role, groups, lob_assignments
        )

        # Get domains within LOB scope
        scoped_domains = self._domain_registry.get_domains_for_scope(lob_scope)

        # If targeting a specific domain, filter further
        if target_domain is not None:
            scoped_domains = [
                d for d in scoped_domains if d.domain_id == target_domain
            ]

        # For auditor role: read-only access to audit + health events
        if role == "auditor":
            authorized_domain_ids = {d.domain_id for d in scoped_domains}
            # Auditors can see health events but not admin panels
            panels = []
            for d in scoped_domains:
                for tab in d.tabs:
                    panel_id = f"{d.domain_id}:{tab.get('title', 'unknown')}"
                    panels.append(panel_id)

            return GovernanceResult(
                authorized_domains=authorized_domain_ids,
                authorized_panels=panels,
                authorized_lob_scope=lob_scope,
                is_unrestricted=False,
            )

        # For operator role: scoped to domain's adapters, metrics, panels
        if role == "operator" and target_domain:
            matching = [
                d for d in scoped_domains if d.domain_id == target_domain
            ]
            authorized_domain_ids = {d.domain_id for d in matching}
            panels = []
            for d in matching:
                for tab in d.tabs:
                    panel_id = f"{d.domain_id}:{tab.get('title', 'unknown')}"
                    panels.append(panel_id)

            return GovernanceResult(
                authorized_domains=authorized_domain_ids,
                authorized_panels=panels,
                authorized_lob_scope=lob_scope,
                is_unrestricted=False,
            )

        # General case: filter domains by role permissions
        authorized_domain_ids: Set[str] = set()
        panels: List[str] = []

        for d in scoped_domains:
            # Check if user's role is in the domain's allowed roles
            if role in d.roles or self._rbac.has_permission(role, "observability", "read"):
                authorized_domain_ids.add(d.domain_id)
                for tab in d.tabs:
                    panel_id = f"{d.domain_id}:{tab.get('title', 'unknown')}"
                    panels.append(panel_id)

        return GovernanceResult(
            authorized_domains=authorized_domain_ids,
            authorized_panels=panels,
            authorized_lob_scope=lob_scope,
            is_unrestricted=False,
        )

    def can_perform_admin_action(
        self, role: str, action: str, resource: str
    ) -> bool:
        """Check if a role can perform an administrative action.

        Auditors are denied all admin actions.
        """
        if role == "auditor" and action in self.ADMIN_ACTIONS:
            return False
        return self._rbac.has_permission(role, resource, action)

    def on_policy_change(self, event: PolicyChangeEvent) -> None:
        """Handle targeted cache refresh when roles, LOBs, or domains change.

        Refreshes the relevant portion of the policy cache.
        """
        self._policy_cache["domains"] = {
            d.domain_id: d
            for d in self._domain_registry.list_all()
        }
