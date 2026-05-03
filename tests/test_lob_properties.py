"""Property tests for LOB Hierarchy and Scope Resolver.

Feature: openmesh-framework, Property 6: Scope Resolution Intersection
Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (LOB)
Validates: Requirements 8.2, 8.3, 8.4, 8.5, 8.6
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from packages.core.lob.models import LOBCategory, LOBNode
from packages.core.lob.scope_resolver import ScopeResolver
from packages.core.lob.store import (
    LOBReferentialIntegrityError,
    LOBStore,
)
from packages.core.rbac.engine import RBACEngine
from packages.core.rbac.models import GroupPolicy, Permission

_prop_settings = settings(
    max_examples=100, suppress_health_check=[HealthCheck.too_slow]
)

_id_st = st.from_regex(r"[a-z][a-z0-9\-]{0,14}", fullmatch=True)
_name_st = st.from_regex(r"[A-Za-z][A-Za-z0-9 ]{0,19}", fullmatch=True)
_category_st = st.sampled_from(list(LOBCategory))


def _make_lob_store_with_lobs(lob_ids, category=LOBCategory.P_LOB):
    """Helper: create a LOBStore pre-populated with LOB nodes."""
    store = LOBStore()
    for lid in lob_ids:
        store.create_lob(LOBNode(
            lob_id=lid, name=f"LOB {lid}", category=category, entity_id="e1"
        ))
    return store


# ── Property 6: Scope Resolution Intersection ───────────────────────


class TestScopeResolutionIntersection:
    """Property 6: Effective LOB scope is the intersection of role-permitted
    LOBs, group LOB assignments, and tenant LOB configuration.
    For superuser/platform_operator, scope is unrestricted.
    """

    # Feature: openmesh-framework, Property 6: Scope Resolution Intersection
    @given(
        lob_ids=st.lists(_id_st, min_size=2, max_size=5, unique=True),
    )
    @_prop_settings
    def test_superuser_gets_unrestricted_scope(self, lob_ids):
        """Superuser gets all LOBs regardless of assignments."""
        store = _make_lob_store_with_lobs(lob_ids)
        engine = RBACEngine()
        resolver = ScopeResolver(store, engine)

        scope = resolver.resolve_scope(
            role="superuser", groups=[], lob_assignments=[]
        )
        assert scope == set(lob_ids)

    # Feature: openmesh-framework, Property 6: Scope Resolution Intersection
    @given(
        lob_ids=st.lists(_id_st, min_size=2, max_size=5, unique=True),
    )
    @_prop_settings
    def test_platform_operator_gets_unrestricted_scope(self, lob_ids):
        """Platform operator gets all LOBs regardless of assignments."""
        store = _make_lob_store_with_lobs(lob_ids)
        engine = RBACEngine()
        resolver = ScopeResolver(store, engine)

        scope = resolver.resolve_scope(
            role="platform_operator", groups=[], lob_assignments=[]
        )
        assert scope == set(lob_ids)

    # Feature: openmesh-framework, Property 6: Scope Resolution Intersection
    @given(
        all_lobs=st.lists(_id_st, min_size=3, max_size=6, unique=True),
    )
    @_prop_settings
    def test_user_scope_limited_to_assignments(self, all_lobs):
        """Non-superuser scope is limited to assigned LOBs."""
        store = _make_lob_store_with_lobs(all_lobs)
        engine = RBACEngine()
        resolver = ScopeResolver(store, engine)

        # Assign only a subset
        assigned = all_lobs[:2]
        scope = resolver.resolve_scope(
            role="operator", groups=[], lob_assignments=assigned
        )
        assert scope == set(assigned)
        assert scope.issubset(set(all_lobs))

    # Feature: openmesh-framework, Property 6: Scope Resolution Intersection
    @given(
        all_lobs=st.lists(_id_st, min_size=4, max_size=6, unique=True),
    )
    @_prop_settings
    def test_intersection_of_user_and_group_lobs(self, all_lobs):
        """When both user and group LOBs exist, scope is their intersection."""
        store = _make_lob_store_with_lobs(all_lobs)
        engine = RBACEngine()
        resolver = ScopeResolver(store, engine)

        # User has first 3, group has last 3 — overlap is middle elements
        user_lobs = all_lobs[:3]
        group_lobs = all_lobs[1:4]

        engine.set_group_policy(GroupPolicy(
            group_id="g1",
            permissions=set(),
            lob_ids=group_lobs,
        ))

        scope = resolver.resolve_scope(
            role="operator", groups=["g1"], lob_assignments=user_lobs
        )

        expected = set(user_lobs) & set(group_lobs)
        assert scope == expected

    # Feature: openmesh-framework, Property 6: Scope Resolution Intersection
    @given(
        all_lobs=st.lists(_id_st, min_size=2, max_size=5, unique=True),
    )
    @_prop_settings
    def test_group_only_lobs_when_no_user_assignments(self, all_lobs):
        """When user has no explicit LOBs, group LOBs are used."""
        store = _make_lob_store_with_lobs(all_lobs)
        engine = RBACEngine()
        resolver = ScopeResolver(store, engine)

        group_lobs = all_lobs[:2]
        engine.set_group_policy(GroupPolicy(
            group_id="g1",
            permissions=set(),
            lob_ids=group_lobs,
        ))

        scope = resolver.resolve_scope(
            role="operator", groups=["g1"], lob_assignments=[]
        )
        assert scope == set(group_lobs)

    # Feature: openmesh-framework, Property 6: Scope Resolution Intersection
    def test_empty_scope_when_no_assignments(self):
        """User with no LOB assignments and no groups gets empty scope."""
        store = _make_lob_store_with_lobs(["lob1", "lob2"])
        engine = RBACEngine()
        resolver = ScopeResolver(store, engine)

        scope = resolver.resolve_scope(
            role="operator", groups=[], lob_assignments=[]
        )
        assert scope == set()

    # Feature: openmesh-framework, Property 6: Scope Resolution Intersection
    @given(
        existing=st.lists(_id_st, min_size=2, max_size=4, unique=True),
        nonexistent=_id_st,
    )
    @_prop_settings
    def test_scope_filtered_to_existing_lobs(self, existing, nonexistent):
        """Scope only includes LOBs that exist in the store."""
        assume(nonexistent not in existing)
        store = _make_lob_store_with_lobs(existing)
        engine = RBACEngine()
        resolver = ScopeResolver(store, engine)

        # Assign existing + nonexistent
        scope = resolver.resolve_scope(
            role="operator",
            groups=[],
            lob_assignments=existing + [nonexistent],
        )
        assert nonexistent not in scope
        assert scope == set(existing)


# ── Property 8: Referential Integrity on Deletion (LOB) ─────────────


class TestLOBReferentialIntegrityOnDeletion:
    """Property 8: LOB with referencing domains or users SHALL reject
    deletion and return the list of referencing entities.
    """

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (LOB)
    @given(lob_id=_id_st, domain_id=_id_st)
    @_prop_settings
    def test_lob_deletion_blocked_by_domain_ref(self, lob_id, domain_id):
        """Cannot delete a LOB referenced by a domain."""
        store = LOBStore()
        store.create_lob(LOBNode(
            lob_id=lob_id, name="Test LOB",
            category=LOBCategory.P_LOB, entity_id="e1",
        ))
        store.add_domain_ref(lob_id, domain_id)

        with pytest.raises(LOBReferentialIntegrityError) as exc_info:
            store.delete_lob(lob_id)

        assert domain_id in exc_info.value.referencing_ids

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (LOB)
    @given(lob_id=_id_st, user_id=_id_st)
    @_prop_settings
    def test_lob_deletion_blocked_by_user_ref(self, lob_id, user_id):
        """Cannot delete a LOB referenced by a user."""
        store = LOBStore()
        store.create_lob(LOBNode(
            lob_id=lob_id, name="Test LOB",
            category=LOBCategory.I_LOB, entity_id="e1",
        ))
        store.add_user_ref(lob_id, user_id)

        with pytest.raises(LOBReferentialIntegrityError) as exc_info:
            store.delete_lob(lob_id)

        assert user_id in exc_info.value.referencing_ids

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (LOB)
    @given(lob_id=_id_st)
    @_prop_settings
    def test_lob_deletion_succeeds_when_no_refs(self, lob_id):
        """LOB with no references can be deleted."""
        store = LOBStore()
        store.create_lob(LOBNode(
            lob_id=lob_id, name="Test LOB",
            category=LOBCategory.P_LOB, entity_id="e1",
        ))
        store.delete_lob(lob_id)
        assert store.get_lob(lob_id) is None

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (LOB)
    @given(lob_id=_id_st, domain_id=_id_st)
    @_prop_settings
    def test_lob_deletion_succeeds_after_refs_removed(self, lob_id, domain_id):
        """LOB can be deleted after all references are removed."""
        store = LOBStore()
        store.create_lob(LOBNode(
            lob_id=lob_id, name="Test LOB",
            category=LOBCategory.P_LOB, entity_id="e1",
        ))
        store.add_domain_ref(lob_id, domain_id)
        store.remove_domain_ref(lob_id, domain_id)

        store.delete_lob(lob_id)
        assert store.get_lob(lob_id) is None

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (LOB)
    @given(
        lob_id=_id_st,
        domain_id=_id_st,
        user_id=_id_st,
    )
    @_prop_settings
    def test_both_domain_and_user_refs_reported(self, lob_id, domain_id, user_id):
        """Both domain and user references are reported on failed deletion."""
        assume(domain_id != user_id)
        store = LOBStore()
        store.create_lob(LOBNode(
            lob_id=lob_id, name="Test LOB",
            category=LOBCategory.P_LOB, entity_id="e1",
        ))
        store.add_domain_ref(lob_id, domain_id)
        store.add_user_ref(lob_id, user_id)

        with pytest.raises(LOBReferentialIntegrityError) as exc_info:
            store.delete_lob(lob_id)

        refs = exc_info.value.referencing_ids
        assert domain_id in refs
        assert user_id in refs
