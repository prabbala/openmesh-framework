"""Property tests for Audit Engine.

Feature: openmesh-framework, Property 12: Audit Immutability
Feature: openmesh-framework, Property 13: Audit Tenant Isolation
Feature: openmesh-framework, Property 14: Audit Completeness
Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from packages.core.audit.engine import AuditEngine
from packages.core.audit.models import AuditRecord

_prop_settings = settings(
    max_examples=100, suppress_health_check=[HealthCheck.too_slow]
)

_id_st = st.from_regex(r"[a-z][a-z0-9\-]{0,14}", fullmatch=True)
_action_st = st.sampled_from([
    "role_assigned", "role_removed", "domain_registered",
    "domain_unregistered", "tenant_created", "tenant_suspended",
    "tenant_deleted", "user_created", "user_deactivated",
    "group_membership_changed", "lob_scope_modified",
    "adapter_error", "health_check_failure",
])
_resource_st = st.from_regex(r"[a-z][a-z0-9_/]{0,19}", fullmatch=True)


# ── Property 12: Audit Immutability ─────────────────────────────────


class TestAuditImmutability:
    """Property 12: Existing audit records cannot be modified or deleted.
    The audit log is strictly append-only.
    """

    # Feature: openmesh-framework, Property 12: Audit Immutability
    @given(
        tenant_id=_id_st,
        actor_id=_id_st,
        action_type=_action_st,
        resource=_resource_st,
    )
    @_prop_settings
    def test_record_fields_are_frozen(
        self, tenant_id, actor_id, action_type, resource,
    ):
        """AuditRecord fields cannot be modified after creation."""
        engine = AuditEngine()
        record = engine.record(
            entity_id="e1",
            tenant_id=tenant_id,
            actor_id=actor_id,
            action_type=action_type,
            resource=resource,
        )

        with pytest.raises(FrozenInstanceError):
            record.action_type = "tampered"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            record.actor_id = "hacker"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            record.record_id = "fake-id"  # type: ignore[misc]

    # Feature: openmesh-framework, Property 12: Audit Immutability
    @given(
        tenant_id=_id_st,
        actor_id=_id_st,
        action_type=_action_st,
    )
    @_prop_settings
    def test_records_persist_after_creation(
        self, tenant_id, actor_id, action_type,
    ):
        """Records remain in the log after creation — no deletion API."""
        engine = AuditEngine()
        r1 = engine.record(
            entity_id="e1", tenant_id=tenant_id,
            actor_id=actor_id, action_type=action_type,
            resource="res1",
        )
        r2 = engine.record(
            entity_id="e1", tenant_id=tenant_id,
            actor_id=actor_id, action_type=action_type,
            resource="res2",
        )

        assert engine.count == 2
        assert engine.get_record(r1.record_id) is not None
        assert engine.get_record(r2.record_id) is not None

    # Feature: openmesh-framework, Property 12: Audit Immutability
    @given(tenant_id=_id_st, actor_id=_id_st)
    @_prop_settings
    def test_each_record_has_unique_id(self, tenant_id, actor_id):
        """Each audit record gets a unique record_id."""
        engine = AuditEngine()
        records = [
            engine.record(
                entity_id="e1", tenant_id=tenant_id,
                actor_id=actor_id, action_type="test",
                resource=f"res{i}",
            )
            for i in range(5)
        ]
        ids = [r.record_id for r in records]
        assert len(set(ids)) == 5


# ── Property 13: Audit Tenant Isolation ──────────────────────────────


class TestAuditTenantIsolation:
    """Property 13: Querying audit records only returns records
    matching the querying tenant_id. No cross-tenant leakage.
    """

    # Feature: openmesh-framework, Property 13: Audit Tenant Isolation
    @given(
        tenant_a=_id_st,
        tenant_b=_id_st,
        actor_id=_id_st,
    )
    @_prop_settings
    def test_query_returns_only_own_tenant_records(
        self, tenant_a, tenant_b, actor_id,
    ):
        """Tenant A cannot see Tenant B's records."""
        assume(tenant_a != tenant_b)
        engine = AuditEngine()

        engine.record(
            entity_id="e1", tenant_id=tenant_a,
            actor_id=actor_id, action_type="action_a",
            resource="res_a",
        )
        engine.record(
            entity_id="e2", tenant_id=tenant_b,
            actor_id=actor_id, action_type="action_b",
            resource="res_b",
        )

        results_a = engine.query(tenant_id=tenant_a)
        results_b = engine.query(tenant_id=tenant_b)

        assert all(r.tenant_id == tenant_a for r in results_a)
        assert all(r.tenant_id == tenant_b for r in results_b)
        assert len(results_a) == 1
        assert len(results_b) == 1

    # Feature: openmesh-framework, Property 13: Audit Tenant Isolation
    @given(
        tenant_a=_id_st,
        tenant_b=_id_st,
        num_a=st.integers(min_value=1, max_value=5),
        num_b=st.integers(min_value=1, max_value=5),
    )
    @_prop_settings
    def test_tenant_isolation_with_multiple_records(
        self, tenant_a, tenant_b, num_a, num_b,
    ):
        """Each tenant sees exactly their own record count."""
        assume(tenant_a != tenant_b)
        engine = AuditEngine()

        for i in range(num_a):
            engine.record(
                entity_id="e1", tenant_id=tenant_a,
                actor_id="admin", action_type="test",
                resource=f"res_a_{i}",
            )
        for i in range(num_b):
            engine.record(
                entity_id="e2", tenant_id=tenant_b,
                actor_id="admin", action_type="test",
                resource=f"res_b_{i}",
            )

        assert len(engine.query(tenant_id=tenant_a)) == num_a
        assert len(engine.query(tenant_id=tenant_b)) == num_b

    # Feature: openmesh-framework, Property 13: Audit Tenant Isolation
    @given(tenant_id=_id_st)
    @_prop_settings
    def test_nonexistent_tenant_returns_empty(self, tenant_id):
        """Querying a tenant with no records returns empty list."""
        engine = AuditEngine()
        engine.record(
            entity_id="e1", tenant_id="other-tenant",
            actor_id="admin", action_type="test",
            resource="res",
        )
        assert engine.query(tenant_id=tenant_id) == [] or tenant_id == "other-tenant"


# ── Property 14: Audit Completeness ─────────────────────────────────


class TestAuditCompleteness:
    """Property 14: Every administrative action creates an audit record
    containing timestamp, entity_id, tenant_id, actor_id, action_type,
    resource, and detail payload.
    """

    # Feature: openmesh-framework, Property 14: Audit Completeness
    @given(
        entity_id=_id_st,
        tenant_id=_id_st,
        actor_id=_id_st,
        action_type=_action_st,
        resource=_resource_st,
    )
    @_prop_settings
    def test_record_contains_all_required_fields(
        self, entity_id, tenant_id, actor_id, action_type, resource,
    ):
        """Every audit record has all required fields populated."""
        engine = AuditEngine()
        record = engine.record(
            entity_id=entity_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            action_type=action_type,
            resource=resource,
            detail={"key": "value"},
        )

        assert record.record_id  # non-empty UUID
        assert record.timestamp is not None
        assert record.entity_id == entity_id
        assert record.tenant_id == tenant_id
        assert record.actor_id == actor_id
        assert record.action_type == action_type
        assert record.resource == resource
        assert record.detail == {"key": "value"}

    # Feature: openmesh-framework, Property 14: Audit Completeness
    @given(action_type=_action_st)
    @_prop_settings
    def test_all_action_types_are_recordable(self, action_type):
        """All administrative action types can be recorded."""
        engine = AuditEngine()
        record = engine.record(
            entity_id="e1", tenant_id="t1",
            actor_id="admin", action_type=action_type,
            resource="target",
        )
        assert record.action_type == action_type

        results = engine.query(tenant_id="t1", action_type=action_type)
        assert len(results) == 1
        assert results[0].action_type == action_type

    # Feature: openmesh-framework, Property 14: Audit Completeness
    @given(
        tenant_id=_id_st,
        actor_id=_id_st,
    )
    @_prop_settings
    def test_detail_payload_preserved(self, tenant_id, actor_id):
        """Detail payload is preserved exactly as provided."""
        engine = AuditEngine()
        detail = {
            "old_role": "viewer",
            "new_role": "admin",
            "reason": "promotion",
        }
        record = engine.record(
            entity_id="e1", tenant_id=tenant_id,
            actor_id=actor_id, action_type="role_assigned",
            resource="user-123", detail=detail,
        )
        assert record.detail == detail

    # Feature: openmesh-framework, Property 14: Audit Completeness
    def test_query_filters_by_action_type(self):
        """Query can filter by action_type."""
        engine = AuditEngine()
        engine.record(
            entity_id="e1", tenant_id="t1",
            actor_id="admin", action_type="role_assigned",
            resource="user1",
        )
        engine.record(
            entity_id="e1", tenant_id="t1",
            actor_id="admin", action_type="tenant_created",
            resource="tenant1",
        )

        results = engine.query(tenant_id="t1", action_type="role_assigned")
        assert len(results) == 1
        assert results[0].action_type == "role_assigned"

    # Feature: openmesh-framework, Property 14: Audit Completeness
    def test_query_filters_by_actor(self):
        """Query can filter by actor_id."""
        engine = AuditEngine()
        engine.record(
            entity_id="e1", tenant_id="t1",
            actor_id="admin1", action_type="test",
            resource="res",
        )
        engine.record(
            entity_id="e1", tenant_id="t1",
            actor_id="admin2", action_type="test",
            resource="res",
        )

        results = engine.query(tenant_id="t1", actor_id="admin1")
        assert len(results) == 1
        assert results[0].actor_id == "admin1"
