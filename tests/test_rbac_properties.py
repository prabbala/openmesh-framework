"""Property tests for RBAC Engine and People Management.

Feature: openmesh-framework, Property 5: RBAC Dual-Path Access Evaluation
Feature: openmesh-framework, Property 22: Custom Role Definition and Evaluation
Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (Role)
Feature: openmesh-framework, Property 15: Role Escalation Prevention
Feature: openmesh-framework, Property 16: Duplicate Email Rejection Within Tenant
Feature: openmesh-framework, Property 28: User Deactivation Session Revocation
Validates: Requirements 6.1, 6.3, 6.4, 6.5, 6.6, 12.3, 12.4, 12.5
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from packages.core.rbac.engine import RBACEngine, RoleInUseError
from packages.core.rbac.models import (
    DefaultRole,
    GroupPolicy,
    Permission,
    ROLE_HIERARCHY,
)
from packages.core.rbac.people import (
    DuplicateEmailError,
    PeopleManager,
    RoleEscalationError,
)

_prop_settings = settings(
    max_examples=100, suppress_health_check=[HealthCheck.too_slow]
)

_resource_st = st.sampled_from([
    "dashboard", "users", "roles", "tenants",
    "audit", "domains", "observability", "metrics",
])
_action_st = st.sampled_from(["read", "write", "delete", "create"])
_role_st = st.sampled_from([r.value for r in DefaultRole])
_name_st = st.from_regex(r"[A-Za-z][A-Za-z0-9 ]{0,19}", fullmatch=True)
_email_st = st.from_regex(
    r"[a-z]{3,8}@[a-z]{3,8}\.[a-z]{2,4}", fullmatch=True
)
_tenant_st = st.from_regex(r"tenant-[a-z0-9]{3,8}", fullmatch=True)
_custom_role_st = st.from_regex(r"custom-[a-z]{3,10}", fullmatch=True)


# ── Property 5: RBAC Dual-Path Access Evaluation ────────────────────


class TestRBACDualPathAccess:
    """Property 5: Access is granted if role permissions OR group policies
    permit the action. Denied only when neither permits.
    """

    # Feature: openmesh-framework, Property 5: RBAC Dual-Path Access Evaluation
    @given(resource=_resource_st, action=_action_st)
    @_prop_settings
    def test_superuser_role_grants_all(self, resource: str, action: str):
        """Superuser role grants access to any resource/action."""
        engine = RBACEngine()
        engine.assign_role("user1", "superuser")
        assert engine.evaluate_access("user1", resource, action) is True

    # Feature: openmesh-framework, Property 5: RBAC Dual-Path Access Evaluation
    @given(resource=_resource_st, action=_action_st)
    @_prop_settings
    def test_no_role_no_group_denies(self, resource: str, action: str):
        """User with no role and no group is denied."""
        engine = RBACEngine()
        assert engine.evaluate_access("unknown-user", resource, action) is False

    # Feature: openmesh-framework, Property 5: RBAC Dual-Path Access Evaluation
    @given(resource=_resource_st, action=_action_st)
    @_prop_settings
    def test_group_policy_grants_when_role_denies(
        self, resource: str, action: str,
    ):
        """Group policy can grant access even when role denies."""
        engine = RBACEngine()
        # Viewer role only has dashboard:read
        engine.assign_role("user1", "viewer")

        # Add group policy that grants the target permission
        engine.add_user_to_group("user1", "power-group")
        engine.set_group_policy(GroupPolicy(
            group_id="power-group",
            permissions={Permission(resource, action)},
        ))

        assert engine.evaluate_access("user1", resource, action) is True

    # Feature: openmesh-framework, Property 5: RBAC Dual-Path Access Evaluation
    @given(
        resource=_resource_st,
        action=_action_st,
        role=_role_st,
    )
    @_prop_settings
    def test_dual_path_consistency(self, resource: str, action: str, role: str):
        """Access is granted iff role OR group permits."""
        engine = RBACEngine()
        engine.assign_role("user1", role)

        role_permits = engine.has_permission(role, resource, action)

        # Add a group that does NOT grant this permission
        engine.add_user_to_group("user1", "empty-group")
        engine.set_group_policy(GroupPolicy(
            group_id="empty-group", permissions=set()
        ))

        result = engine.evaluate_access("user1", resource, action)
        # With empty group, result should match role_permits
        assert result == role_permits


# ── Property 22: Custom Role Definition and Evaluation ───────────────


class TestCustomRoleDefinition:
    """Property 22: Custom roles with arbitrary permissions SHALL be
    stored and correctly evaluated.
    """

    # Feature: openmesh-framework, Property 22: Custom Role Definition and Evaluation
    @given(
        role_name=_custom_role_st,
        resource=_resource_st,
        action=_action_st,
    )
    @_prop_settings
    def test_custom_role_grants_defined_permission(
        self, role_name: str, resource: str, action: str,
    ):
        """Custom role grants access for its defined permissions."""
        engine = RBACEngine()
        engine.define_custom_role(
            role_name, {Permission(resource, action)}
        )
        engine.assign_role("user1", role_name)

        assert engine.evaluate_access("user1", resource, action) is True

    # Feature: openmesh-framework, Property 22: Custom Role Definition and Evaluation
    @given(
        role_name=_custom_role_st,
        granted_resource=_resource_st,
        other_resource=_resource_st,
        action=_action_st,
    )
    @_prop_settings
    def test_custom_role_denies_undefined_permission(
        self, role_name: str, granted_resource: str,
        other_resource: str, action: str,
    ):
        """Custom role denies access for permissions not in its set."""
        assume(granted_resource != other_resource)
        engine = RBACEngine()
        engine.define_custom_role(
            role_name, {Permission(granted_resource, action)}
        )
        engine.assign_role("user1", role_name)

        assert engine.evaluate_access("user1", other_resource, action) is False


# ── Property 8: Referential Integrity on Deletion (Role) ────────────


class TestRoleReferentialIntegrity:
    """Property 8: Role with assigned users SHALL reject deletion
    and return the count of affected users.
    """

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (Role)
    @given(role_name=_custom_role_st)
    @_prop_settings
    def test_role_deletion_blocked_when_users_assigned(self, role_name: str):
        """Cannot delete a role with assigned users."""
        engine = RBACEngine()
        engine.define_custom_role(role_name, {Permission("x", "y")})
        engine.assign_role("user1", role_name)

        with pytest.raises(RoleInUseError) as exc_info:
            engine.delete_role(role_name)

        assert exc_info.value.user_count == 1

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (Role)
    @given(role_name=_custom_role_st)
    @_prop_settings
    def test_role_deletion_succeeds_when_no_users(self, role_name: str):
        """Role with no assigned users can be deleted."""
        engine = RBACEngine()
        engine.define_custom_role(role_name, {Permission("x", "y")})
        engine.delete_role(role_name)
        assert engine.get_role(role_name) is None

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (Role)
    @given(role_name=_custom_role_st)
    @_prop_settings
    def test_role_deletion_after_unassign(self, role_name: str):
        """Role can be deleted after all users are unassigned."""
        engine = RBACEngine()
        engine.define_custom_role(role_name, {Permission("x", "y")})
        engine.assign_role("user1", role_name)
        engine.unassign_role("user1")
        engine.delete_role(role_name)
        assert engine.get_role(role_name) is None


# ── Property 15: Role Escalation Prevention ──────────────────────────


class TestRoleEscalationPrevention:
    """Property 15: Admin cannot assign a role above their own level."""

    # Feature: openmesh-framework, Property 15: Role Escalation Prevention
    @given(
        admin_role=st.sampled_from(["admin", "operator", "manager", "staff"]),
        email=_email_st,
        name=_name_st,
        tenant=_tenant_st,
    )
    @_prop_settings
    def test_escalation_above_admin_level_rejected(
        self, admin_role: str, email: str, name: str, tenant: str,
    ):
        """Assigning a role higher than admin's own level is rejected."""
        engine = RBACEngine()
        mgr = PeopleManager(engine)

        admin_level = engine.get_role_level(admin_role)
        # Find a role that is higher privilege (lower level number)
        higher_roles = [
            r for r, lvl in ROLE_HIERARCHY.items() if lvl < admin_level
        ]
        assume(len(higher_roles) > 0)
        target_role = higher_roles[0]

        with pytest.raises(RoleEscalationError):
            mgr.create_user(
                email=email,
                display_name=name,
                role=target_role,
                tenant_id=tenant,
                acting_admin_role=admin_role,
            )

    # Feature: openmesh-framework, Property 15: Role Escalation Prevention
    @given(
        admin_role=st.sampled_from(["admin", "operator", "manager"]),
        email=_email_st,
        name=_name_st,
        tenant=_tenant_st,
    )
    @_prop_settings
    def test_assignment_at_or_below_admin_level_succeeds(
        self, admin_role: str, email: str, name: str, tenant: str,
    ):
        """Assigning a role at or below admin's level succeeds."""
        engine = RBACEngine()
        mgr = PeopleManager(engine)

        admin_level = engine.get_role_level(admin_role)
        lower_roles = [
            r for r, lvl in ROLE_HIERARCHY.items() if lvl >= admin_level
        ]
        assume(len(lower_roles) > 0)
        target_role = lower_roles[0]

        user = mgr.create_user(
            email=email,
            display_name=name,
            role=target_role,
            tenant_id=tenant,
            acting_admin_role=admin_role,
        )
        assert user.role == target_role


# ── Property 16: Duplicate Email Rejection Within Tenant ─────────────


class TestDuplicateEmailRejection:
    """Property 16: Same email within same tenant SHALL be rejected.
    Same email in different tenants MAY exist.
    """

    # Feature: openmesh-framework, Property 16: Duplicate Email Rejection Within Tenant
    @given(email=_email_st, name=_name_st, tenant=_tenant_st)
    @_prop_settings
    def test_duplicate_email_same_tenant_rejected(
        self, email: str, name: str, tenant: str,
    ):
        """Creating a user with duplicate email in same tenant fails."""
        engine = RBACEngine()
        mgr = PeopleManager(engine)

        mgr.create_user(email=email, display_name=name,
                        role="viewer", tenant_id=tenant)

        with pytest.raises(DuplicateEmailError) as exc_info:
            mgr.create_user(email=email, display_name="Other",
                            role="viewer", tenant_id=tenant)

        assert email in str(exc_info.value)

    # Feature: openmesh-framework, Property 16: Duplicate Email Rejection Within Tenant
    @given(
        email=_email_st,
        name=_name_st,
        tenant1=_tenant_st,
        tenant2=_tenant_st,
    )
    @_prop_settings
    def test_same_email_different_tenants_allowed(
        self, email: str, name: str, tenant1: str, tenant2: str,
    ):
        """Same email in different tenants is allowed."""
        assume(tenant1 != tenant2)
        engine = RBACEngine()
        mgr = PeopleManager(engine)

        u1 = mgr.create_user(email=email, display_name=name,
                              role="viewer", tenant_id=tenant1)
        u2 = mgr.create_user(email=email, display_name=name,
                              role="viewer", tenant_id=tenant2)

        assert u1.tenant_id != u2.tenant_id
        assert u1.email == u2.email


# ── Property 28: User Deactivation Session Revocation ────────────────


class TestUserDeactivationSessionRevocation:
    """Property 28: Deactivating a user SHALL revoke all active sessions
    and block new authentication attempts.
    """

    # Feature: openmesh-framework, Property 28: User Deactivation Session Revocation
    @given(email=_email_st, name=_name_st, tenant=_tenant_st)
    @_prop_settings
    def test_deactivation_revokes_all_sessions(
        self, email: str, name: str, tenant: str,
    ):
        """All active sessions are revoked on deactivation."""
        engine = RBACEngine()
        mgr = PeopleManager(engine)

        user = mgr.create_user(email=email, display_name=name,
                                role="viewer", tenant_id=tenant)

        # Create multiple sessions
        mgr.create_session(user.user_id)
        mgr.create_session(user.user_id)
        assert len(mgr.get_active_sessions(user.user_id)) == 2

        # Deactivate
        mgr.deactivate_user(user.user_id)

        # All sessions revoked
        assert len(mgr.get_active_sessions(user.user_id)) == 0
        assert user.is_active is False

    # Feature: openmesh-framework, Property 28: User Deactivation Session Revocation
    @given(email=_email_st, name=_name_st, tenant=_tenant_st)
    @_prop_settings
    def test_deactivated_user_cannot_create_session(
        self, email: str, name: str, tenant: str,
    ):
        """Deactivated user cannot create new sessions."""
        engine = RBACEngine()
        mgr = PeopleManager(engine)

        user = mgr.create_user(email=email, display_name=name,
                                role="viewer", tenant_id=tenant)
        mgr.deactivate_user(user.user_id)

        from packages.core.rbac.people import UserNotFoundError
        with pytest.raises(UserNotFoundError):
            mgr.create_session(user.user_id)
