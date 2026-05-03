"""Property tests for Governance Engine.

Feature: openmesh-framework, Property 3: Governance Engine Intersection
Feature: openmesh-framework, Property 4: System Admin Unrestricted Scope
Feature: openmesh-framework, Property 25: Operator Domain Scoping
Feature: openmesh-framework, Property 26: Auditor Read-Only Access
Feature: openmesh-framework, Property 21: Governance Policy Freshness
Validates: Requirements 7.1-7.6
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from packages.core.domain_registry.registration import DomainRegistration
from packages.core.domain_registry.registry import DomainRegistry
from packages.core.governance_engine.engine import (
    GovernanceEngine,
    PolicyChangeEvent,
)
from packages.core.lob.models import LOBCategory, LOBNode
from packages.core.lob.scope_resolver import ScopeResolver
from packages.core.lob.store import LOBStore
from packages.core.rbac.engine import RBACEngine

_prop_settings = settings(
    max_examples=100, suppress_health_check=[HealthCheck.too_slow]
)

_id_st = st.from_regex(r"[a-z][a-z0-9\-]{0,14}", fullmatch=True)


def _build_engine(lob_ids, domain_configs):
    """Helper: build a full governance stack with LOBs and domains.

    domain_configs: list of (domain_id, lob_id, roles, tabs)
    """
    rbac = RBACEngine()
    lob_store = LOBStore()
    for lid in lob_ids:
        lob_store.create_lob(LOBNode(
            lob_id=lid, name=f"LOB {lid}",
            category=LOBCategory.P_LOB, entity_id="e1",
        ))

    resolver = ScopeResolver(lob_store, rbac)
    registry = DomainRegistry()

    for domain_id, lob_id, roles, tabs in domain_configs:
        reg = DomainRegistration(
            domain_id=domain_id,
            runtime_type="server",
            observability_adapter="test.Adapter",
            roles=roles,
            tabs=tabs,
            entity_id="e1",
            lob_id=lob_id,
        )
        registry.register(reg)

    ge = GovernanceEngine(rbac, resolver, registry)
    ge.load_policies()
    return ge, rbac, lob_store, resolver, registry


# ── Property 3: Governance Engine Intersection ───────────────────────


class TestGovernanceIntersection:
    """Property 3: Governance returns only domains in the intersection
    of role permissions, LOB scope, and registered domains.
    """

    # Feature: openmesh-framework, Property 3: Governance Engine Intersection
    @given(
        lob_ids=st.lists(_id_st, min_size=3, max_size=5, unique=True),
    )
    @_prop_settings
    def test_only_scoped_domains_returned(self, lob_ids):
        """User only sees domains within their LOB scope."""
        domains = [
            (f"dom-{lid}", lid, ["operator"], [{"title": f"Panel {lid}"}])
            for lid in lob_ids
        ]
        ge, rbac, _, _, _ = _build_engine(lob_ids, domains)

        # User assigned to first 2 LOBs only
        assigned = lob_ids[:2]
        result = ge.evaluate(
            user_id="u1", role="operator",
            groups=[], lob_assignments=assigned,
        )

        for did in result.authorized_domains:
            # Each authorized domain should be in the assigned LOBs
            assert any(lid in did for lid in assigned)

    # Feature: openmesh-framework, Property 3: Governance Engine Intersection
    def test_empty_lob_scope_returns_no_domains(self):
        """User with no LOB assignments sees no domains."""
        ge, _, _, _, _ = _build_engine(
            ["lob1", "lob2"],
            [("d1", "lob1", ["operator"], [{"title": "P1"}])],
        )
        result = ge.evaluate(
            user_id="u1", role="operator",
            groups=[], lob_assignments=[],
        )
        assert len(result.authorized_domains) == 0


# ── Property 4: System Admin Unrestricted Scope ─────────────────────


class TestSystemAdminUnrestrictedScope:
    """Property 4: Superuser/platform_operator gets unrestricted scope
    across all entities, domains, and LOBs.
    """

    # Feature: openmesh-framework, Property 4: System Admin Unrestricted Scope
    @given(
        lob_ids=st.lists(_id_st, min_size=2, max_size=4, unique=True),
    )
    @_prop_settings
    def test_superuser_sees_all_domains(self, lob_ids):
        """Superuser sees all domains regardless of LOB assignments."""
        domains = [
            (f"dom-{lid}", lid, ["admin"], [{"title": f"P-{lid}"}])
            for lid in lob_ids
        ]
        ge, _, _, _, _ = _build_engine(lob_ids, domains)

        result = ge.evaluate(
            user_id="u1", role="superuser",
            groups=[], lob_assignments=[],
        )
        assert result.is_unrestricted is True
        assert len(result.authorized_domains) == len(lob_ids)

    # Feature: openmesh-framework, Property 4: System Admin Unrestricted Scope
    @given(
        lob_ids=st.lists(_id_st, min_size=2, max_size=4, unique=True),
    )
    @_prop_settings
    def test_platform_operator_sees_all_domains(self, lob_ids):
        """Platform operator sees all domains."""
        domains = [
            (f"dom-{lid}", lid, ["admin"], [{"title": f"P-{lid}"}])
            for lid in lob_ids
        ]
        ge, _, _, _, _ = _build_engine(lob_ids, domains)

        result = ge.evaluate(
            user_id="u1", role="platform_operator",
            groups=[], lob_assignments=[],
        )
        assert result.is_unrestricted is True
        assert len(result.authorized_domains) == len(lob_ids)


# ── Property 25: Operator Domain Scoping ─────────────────────────────


class TestOperatorDomainScoping:
    """Property 25: Operator scoped to a specific domain sees only
    that domain's adapters, metrics, and panels.
    """

    # Feature: openmesh-framework, Property 25: Operator Domain Scoping
    def test_operator_scoped_to_single_domain(self):
        """Operator targeting a domain sees only that domain."""
        ge, _, _, _, _ = _build_engine(
            ["lob1", "lob2"],
            [
                ("d1", "lob1", ["operator"], [{"title": "P1"}]),
                ("d2", "lob2", ["operator"], [{"title": "P2"}]),
            ],
        )
        result = ge.evaluate(
            user_id="u1", role="operator",
            groups=[], lob_assignments=["lob1", "lob2"],
            target_domain="d1",
        )
        assert result.authorized_domains == {"d1"}
        assert "d2" not in result.authorized_domains

    # Feature: openmesh-framework, Property 25: Operator Domain Scoping
    def test_operator_without_target_sees_all_scoped(self):
        """Operator without target_domain sees all domains in scope."""
        ge, _, _, _, _ = _build_engine(
            ["lob1", "lob2"],
            [
                ("d1", "lob1", ["operator"], [{"title": "P1"}]),
                ("d2", "lob2", ["operator"], [{"title": "P2"}]),
            ],
        )
        result = ge.evaluate(
            user_id="u1", role="operator",
            groups=[], lob_assignments=["lob1", "lob2"],
        )
        assert "d1" in result.authorized_domains
        assert "d2" in result.authorized_domains


# ── Property 26: Auditor Read-Only Access ────────────────────────────


class TestAuditorReadOnlyAccess:
    """Property 26: Auditor gets read-only access to audit logs and
    health events. Admin actions are denied.
    """

    # Feature: openmesh-framework, Property 26: Auditor Read-Only Access
    @given(
        action=st.sampled_from(["create", "update", "delete", "write"]),
        resource=st.sampled_from(["roles", "tenants", "domains", "users"]),
    )
    @_prop_settings
    def test_auditor_denied_admin_actions(self, action, resource):
        """Auditor cannot perform admin actions."""
        ge, _, _, _, _ = _build_engine(
            ["lob1"],
            [("d1", "lob1", ["auditor"], [{"title": "P1"}])],
        )
        assert ge.can_perform_admin_action("auditor", action, resource) is False

    # Feature: openmesh-framework, Property 26: Auditor Read-Only Access
    def test_auditor_can_read_within_scope(self):
        """Auditor can see domains within their LOB scope."""
        ge, _, _, _, _ = _build_engine(
            ["lob1", "lob2"],
            [
                ("d1", "lob1", ["auditor"], [{"title": "P1"}]),
                ("d2", "lob2", ["auditor"], [{"title": "P2"}]),
            ],
        )
        result = ge.evaluate(
            user_id="u1", role="auditor",
            groups=[], lob_assignments=["lob1"],
        )
        assert "d1" in result.authorized_domains
        assert "d2" not in result.authorized_domains


# ── Property 21: Governance Policy Freshness ─────────────────────────


class TestGovernancePolicyFreshness:
    """Property 21: Policy changes take effect on the very next evaluation.
    No stale cached decisions.
    """

    # Feature: openmesh-framework, Property 21: Governance Policy Freshness
    def test_new_domain_visible_after_registration(self):
        """A newly registered domain is visible on next evaluation."""
        ge, rbac, lob_store, resolver, registry = _build_engine(
            ["lob1"],
            [("d1", "lob1", ["operator"], [{"title": "P1"}])],
        )

        # Initially only d1
        result1 = ge.evaluate(
            user_id="u1", role="operator",
            groups=[], lob_assignments=["lob1"],
        )
        assert "d1" in result1.authorized_domains

        # Register d2
        registry.register(DomainRegistration(
            domain_id="d2", runtime_type="server",
            observability_adapter="test.Adapter",
            roles=["operator"], tabs=[{"title": "P2"}],
            entity_id="e1", lob_id="lob1",
        ))
        ge.on_policy_change(PolicyChangeEvent("domain_registered"))

        # d2 should be visible immediately
        result2 = ge.evaluate(
            user_id="u1", role="operator",
            groups=[], lob_assignments=["lob1"],
        )
        assert "d2" in result2.authorized_domains

    # Feature: openmesh-framework, Property 21: Governance Policy Freshness
    def test_unregistered_domain_invisible_after_removal(self):
        """An unregistered domain disappears on next evaluation."""
        ge, rbac, lob_store, resolver, registry = _build_engine(
            ["lob1"],
            [
                ("d1", "lob1", ["operator"], [{"title": "P1"}]),
                ("d2", "lob1", ["operator"], [{"title": "P2"}]),
            ],
        )

        # Both visible
        result1 = ge.evaluate(
            user_id="u1", role="operator",
            groups=[], lob_assignments=["lob1"],
        )
        assert "d1" in result1.authorized_domains
        assert "d2" in result1.authorized_domains

        # Unregister d2
        registry.unregister("d2")
        ge.on_policy_change(PolicyChangeEvent("domain_unregistered"))

        # d2 should be gone
        result2 = ge.evaluate(
            user_id="u1", role="operator",
            groups=[], lob_assignments=["lob1"],
        )
        assert "d1" in result2.authorized_domains
        assert "d2" not in result2.authorized_domains
