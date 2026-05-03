"""Property tests for Tenant Manager.

Feature: openmesh-framework, Property 10: SUB_CLIENT Parent Validation
Feature: openmesh-framework, Property 11: Suspended Tenant Write Blocking
Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (Tenant)
Validates: Requirements 5.3, 5.4, 5.5, 5.6
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from packages.core.tenant.manager import (
    InvalidParentError,
    TenantManager,
    TenantReferentialIntegrityError,
    TenantSuspendedError,
)
from packages.core.tenant.models import TenantType

_prop_settings = settings(
    max_examples=100, suppress_health_check=[HealthCheck.too_slow]
)

_name_st = st.from_regex(r"[A-Za-z][A-Za-z0-9 \-]{0,29}", fullmatch=True)
_key_st = st.from_regex(r"[a-z][a-z0-9_]{0,14}", fullmatch=True)
_value_st = st.from_regex(r"[a-zA-Z0-9]{1,20}", fullmatch=True)


# ── Property 10: SUB_CLIENT Parent Validation ───────────────────────


class TestSubClientParentValidation:
    """Property 10: SUB_CLIENT parent_tenant_id SHALL reference an existing
    PARENT tenant. Non-existent or non-PARENT parent SHALL be rejected.
    """

    # Feature: openmesh-framework, Property 10: SUB_CLIENT Parent Validation
    @given(name=_name_st)
    @_prop_settings
    def test_sub_client_without_parent_rejected(self, name: str):
        """Creating a SUB_CLIENT without parent_tenant_id fails."""
        mgr = TenantManager()
        with pytest.raises(InvalidParentError):
            mgr.create_tenant(name=name, tenant_type=TenantType.SUB_CLIENT)

    # Feature: openmesh-framework, Property 10: SUB_CLIENT Parent Validation
    @given(name=_name_st)
    @_prop_settings
    def test_sub_client_with_nonexistent_parent_rejected(self, name: str):
        """Creating a SUB_CLIENT with a non-existent parent fails."""
        mgr = TenantManager()
        with pytest.raises(InvalidParentError):
            mgr.create_tenant(
                name=name,
                tenant_type=TenantType.SUB_CLIENT,
                parent_tenant_id="nonexistent-id",
            )

    # Feature: openmesh-framework, Property 10: SUB_CLIENT Parent Validation
    @given(parent_name=_name_st, child_name=_name_st)
    @_prop_settings
    def test_sub_client_with_independent_parent_rejected(
        self, parent_name: str, child_name: str,
    ):
        """Creating a SUB_CLIENT whose parent is INDEPENDENT fails."""
        mgr = TenantManager()
        independent = mgr.create_tenant(
            name=parent_name, tenant_type=TenantType.INDEPENDENT
        )
        with pytest.raises(InvalidParentError):
            mgr.create_tenant(
                name=child_name,
                tenant_type=TenantType.SUB_CLIENT,
                parent_tenant_id=independent.tenant_id,
            )

    # Feature: openmesh-framework, Property 10: SUB_CLIENT Parent Validation
    @given(parent_name=_name_st, child_name=_name_st)
    @_prop_settings
    def test_sub_client_with_valid_parent_succeeds(
        self, parent_name: str, child_name: str,
    ):
        """Creating a SUB_CLIENT with a valid PARENT tenant succeeds."""
        mgr = TenantManager()
        parent = mgr.create_tenant(
            name=parent_name, tenant_type=TenantType.PARENT
        )
        child = mgr.create_tenant(
            name=child_name,
            tenant_type=TenantType.SUB_CLIENT,
            parent_tenant_id=parent.tenant_id,
        )
        assert child.tenant_type == TenantType.SUB_CLIENT
        assert child.parent_tenant_id == parent.tenant_id
        assert mgr.get_tenant(child.tenant_id) is not None

    # Feature: openmesh-framework, Property 10: SUB_CLIENT Parent Validation
    @given(
        parent_name=_name_st,
        child1_name=_name_st,
        child2_name=_name_st,
    )
    @_prop_settings
    def test_sub_client_with_sub_client_parent_rejected(
        self, parent_name: str, child1_name: str, child2_name: str,
    ):
        """Creating a SUB_CLIENT whose parent is also a SUB_CLIENT fails."""
        mgr = TenantManager()
        parent = mgr.create_tenant(
            name=parent_name, tenant_type=TenantType.PARENT
        )
        child1 = mgr.create_tenant(
            name=child1_name,
            tenant_type=TenantType.SUB_CLIENT,
            parent_tenant_id=parent.tenant_id,
        )
        with pytest.raises(InvalidParentError):
            mgr.create_tenant(
                name=child2_name,
                tenant_type=TenantType.SUB_CLIENT,
                parent_tenant_id=child1.tenant_id,
            )


# ── Property 11: Suspended Tenant Write Blocking ────────────────────


class TestSuspendedTenantWriteBlocking:
    """Property 11: For any suspended tenant, write operations SHALL be
    blocked while read operations SHALL succeed.
    """

    # Feature: openmesh-framework, Property 11: Suspended Tenant Write Blocking
    @given(name=_name_st, key=_key_st, value=_value_st)
    @_prop_settings
    def test_suspended_tenant_blocks_writes(
        self, name: str, key: str, value: str,
    ):
        """Write operations on a suspended tenant raise TenantSuspendedError."""
        mgr = TenantManager()
        tenant = mgr.create_tenant(
            name=name, tenant_type=TenantType.INDEPENDENT
        )
        mgr.suspend_tenant(tenant.tenant_id)

        with pytest.raises(TenantSuspendedError):
            mgr.write_data(tenant.tenant_id, key, value)

    # Feature: openmesh-framework, Property 11: Suspended Tenant Write Blocking
    @given(name=_name_st, key=_key_st, value=_value_st)
    @_prop_settings
    def test_suspended_tenant_blocks_updates(
        self, name: str, key: str, value: str,
    ):
        """Update operations on a suspended tenant raise TenantSuspendedError."""
        mgr = TenantManager()
        tenant = mgr.create_tenant(
            name=name, tenant_type=TenantType.INDEPENDENT
        )
        # Write before suspension
        mgr.write_data(tenant.tenant_id, key, "original")
        mgr.suspend_tenant(tenant.tenant_id)

        with pytest.raises(TenantSuspendedError):
            mgr.update_data(tenant.tenant_id, key, value)

    # Feature: openmesh-framework, Property 11: Suspended Tenant Write Blocking
    @given(name=_name_st, key=_key_st, value=_value_st)
    @_prop_settings
    def test_suspended_tenant_blocks_deletes(
        self, name: str, key: str, value: str,
    ):
        """Delete operations on a suspended tenant raise TenantSuspendedError."""
        mgr = TenantManager()
        tenant = mgr.create_tenant(
            name=name, tenant_type=TenantType.INDEPENDENT
        )
        mgr.write_data(tenant.tenant_id, key, value)
        mgr.suspend_tenant(tenant.tenant_id)

        with pytest.raises(TenantSuspendedError):
            mgr.delete_data(tenant.tenant_id, key)

    # Feature: openmesh-framework, Property 11: Suspended Tenant Write Blocking
    @given(name=_name_st, key=_key_st, value=_value_st)
    @_prop_settings
    def test_suspended_tenant_allows_reads(
        self, name: str, key: str, value: str,
    ):
        """Read operations on a suspended tenant succeed."""
        mgr = TenantManager()
        tenant = mgr.create_tenant(
            name=name, tenant_type=TenantType.INDEPENDENT
        )
        mgr.write_data(tenant.tenant_id, key, value)
        mgr.suspend_tenant(tenant.tenant_id)

        # Read should succeed and return the written value
        result = mgr.read_data(tenant.tenant_id, key)
        assert result == value

    # Feature: openmesh-framework, Property 11: Suspended Tenant Write Blocking
    @given(name=_name_st, key=_key_st, value=_value_st)
    @_prop_settings
    def test_unsuspended_tenant_allows_writes_again(
        self, name: str, key: str, value: str,
    ):
        """After unsuspension, write operations succeed again."""
        mgr = TenantManager()
        tenant = mgr.create_tenant(
            name=name, tenant_type=TenantType.INDEPENDENT
        )
        mgr.suspend_tenant(tenant.tenant_id)
        mgr.unsuspend_tenant(tenant.tenant_id)

        # Write should succeed after unsuspension
        mgr.write_data(tenant.tenant_id, key, value)
        assert mgr.read_data(tenant.tenant_id, key) == value


# ── Property 8: Referential Integrity on Deletion (Tenant) ──────────


class TestTenantReferentialIntegrityOnDeletion:
    """Property 8: PARENT tenant with active SUB_CLIENTs SHALL reject
    deletion and return the list of dependent tenant_ids.
    """

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (Tenant)
    @given(parent_name=_name_st, child_name=_name_st)
    @_prop_settings
    def test_parent_deletion_blocked_by_active_sub_clients(
        self, parent_name: str, child_name: str,
    ):
        """Cannot delete a PARENT tenant with active SUB_CLIENTs."""
        mgr = TenantManager()
        parent = mgr.create_tenant(
            name=parent_name, tenant_type=TenantType.PARENT
        )
        child = mgr.create_tenant(
            name=child_name,
            tenant_type=TenantType.SUB_CLIENT,
            parent_tenant_id=parent.tenant_id,
        )

        with pytest.raises(TenantReferentialIntegrityError) as exc_info:
            mgr.delete_tenant(parent.tenant_id)

        assert child.tenant_id in exc_info.value.dependent_ids

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (Tenant)
    @given(parent_name=_name_st, child_name=_name_st)
    @_prop_settings
    def test_parent_deletion_succeeds_after_sub_client_deleted(
        self, parent_name: str, child_name: str,
    ):
        """PARENT can be deleted after all SUB_CLIENTs are removed."""
        mgr = TenantManager()
        parent = mgr.create_tenant(
            name=parent_name, tenant_type=TenantType.PARENT
        )
        child = mgr.create_tenant(
            name=child_name,
            tenant_type=TenantType.SUB_CLIENT,
            parent_tenant_id=parent.tenant_id,
        )

        # Delete child first
        mgr.delete_tenant(child.tenant_id)
        # Now parent deletion should succeed
        mgr.delete_tenant(parent.tenant_id)
        assert mgr.get_tenant(parent.tenant_id) is None

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (Tenant)
    @given(name=_name_st)
    @_prop_settings
    def test_independent_tenant_deletion_succeeds(self, name: str):
        """INDEPENDENT tenant with no children can be deleted."""
        mgr = TenantManager()
        tenant = mgr.create_tenant(
            name=name, tenant_type=TenantType.INDEPENDENT
        )
        mgr.delete_tenant(tenant.tenant_id)
        assert mgr.get_tenant(tenant.tenant_id) is None

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (Tenant)
    @given(
        parent_name=_name_st,
        child1_name=_name_st,
        child2_name=_name_st,
    )
    @_prop_settings
    def test_multiple_sub_clients_all_reported(
        self, parent_name: str, child1_name: str, child2_name: str,
    ):
        """All active SUB_CLIENT IDs are reported on failed deletion."""
        mgr = TenantManager()
        parent = mgr.create_tenant(
            name=parent_name, tenant_type=TenantType.PARENT
        )
        child1 = mgr.create_tenant(
            name=child1_name,
            tenant_type=TenantType.SUB_CLIENT,
            parent_tenant_id=parent.tenant_id,
        )
        child2 = mgr.create_tenant(
            name=child2_name,
            tenant_type=TenantType.SUB_CLIENT,
            parent_tenant_id=parent.tenant_id,
        )

        with pytest.raises(TenantReferentialIntegrityError) as exc_info:
            mgr.delete_tenant(parent.tenant_id)

        dep_ids = exc_info.value.dependent_ids
        assert child1.tenant_id in dep_ids
        assert child2.tenant_id in dep_ids
