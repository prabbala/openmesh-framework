"""Property tests for 4-Tier Hierarchy parent constraints and referential integrity.

Feature: openmesh-framework, Property 7: 4-Tier Hierarchy Parent Constraint
Feature: openmesh-framework, Property 8: Referential Integrity on Deletion (Entity/Domain)
Validates: Requirements 4.2, 4.3, 4.4, 4.5, 4.6
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

_prop_settings = settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])

from packages.core.domain_registry.hierarchy import (
    DuplicateIdError,
    HierarchyStore,
    NotFoundError,
    ParentNotFoundError,
    ReferentialIntegrityError,
)
from packages.core.domain_registry.models import (
    Domain,
    Entity,
    ProductFamily,
    Resource,
)

# ── Strategies ───────────────────────────────────────────────────────

_id_st = st.from_regex(r"[a-z][a-z0-9\-_]{0,19}", fullmatch=True)

_name_st = st.from_regex(r"[A-Za-z][A-Za-z0-9 \-_]{0,29}", fullmatch=True)


# ── Property 7: 4-Tier Hierarchy Parent Constraint ──────────────────


class TestHierarchyParentConstraint:
    """Property 7: Every Domain → Entity, ProductFamily → Domain, Resource → ProductFamily.

    Creating a node without a valid parent reference SHALL be rejected.
    """

    # Feature: openmesh-framework, Property 7: 4-Tier Hierarchy Parent Constraint
    @given(
        entity_id=_id_st,
        entity_name=_name_st,
        domain_id=_id_st,
        domain_name=_name_st,
    )
    @_prop_settings
    def test_domain_requires_existing_entity(
        self, entity_id, entity_name, domain_id, domain_name
    ):
        """A Domain cannot be created without an existing parent Entity."""
        store = HierarchyStore()

        # Creating a Domain without the Entity should fail
        domain = Domain(domain_id=domain_id, entity_id=entity_id, name=domain_name)
        with pytest.raises(ParentNotFoundError):
            store.create_domain(domain)

        # After creating the Entity, the Domain should succeed
        entity = Entity(entity_id=entity_id, name=entity_name)
        store.create_entity(entity)
        result = store.create_domain(domain)
        assert result.domain_id == domain_id
        assert result.entity_id == entity_id

    # Feature: openmesh-framework, Property 7: 4-Tier Hierarchy Parent Constraint
    @given(
        entity_id=_id_st,
        entity_name=_name_st,
        domain_id=_id_st,
        domain_name=_name_st,
        family_id=_id_st,
        family_name=_name_st,
    )
    @_prop_settings
    def test_product_family_requires_existing_domain(
        self, entity_id, entity_name, domain_id, domain_name,
        family_id, family_name,
    ):
        """A ProductFamily cannot be created without an existing parent Domain."""
        store = HierarchyStore()

        family = ProductFamily(family_id=family_id, domain_id=domain_id, name=family_name)
        with pytest.raises(ParentNotFoundError):
            store.create_product_family(family)

        # Set up the chain: Entity → Domain
        store.create_entity(Entity(entity_id=entity_id, name=entity_name))
        store.create_domain(Domain(domain_id=domain_id, entity_id=entity_id, name=domain_name))

        result = store.create_product_family(family)
        assert result.family_id == family_id
        assert result.domain_id == domain_id

    # Feature: openmesh-framework, Property 7: 4-Tier Hierarchy Parent Constraint
    @given(
        entity_id=_id_st,
        entity_name=_name_st,
        domain_id=_id_st,
        domain_name=_name_st,
        family_id=_id_st,
        family_name=_name_st,
        resource_id=_id_st,
        resource_name=_name_st,
    )
    @_prop_settings
    def test_resource_requires_existing_product_family(
        self, entity_id, entity_name, domain_id, domain_name,
        family_id, family_name, resource_id, resource_name,
    ):
        """A Resource cannot be created without an existing parent ProductFamily."""
        store = HierarchyStore()

        resource = Resource(resource_id=resource_id, family_id=family_id, name=resource_name)
        with pytest.raises(ParentNotFoundError):
            store.create_resource(resource)

        # Set up the chain: Entity → Domain → ProductFamily
        store.create_entity(Entity(entity_id=entity_id, name=entity_name))
        store.create_domain(Domain(domain_id=domain_id, entity_id=entity_id, name=domain_name))
        store.create_product_family(
            ProductFamily(family_id=family_id, domain_id=domain_id, name=family_name)
        )

        result = store.create_resource(resource)
        assert result.resource_id == resource_id
        assert result.family_id == family_id


# ── Property 8: Referential Integrity on Deletion (Entity/Domain) ───


class TestReferentialIntegrityOnDeletion:
    """Property 8: Deletion SHALL be rejected when active children exist,
    and the response SHALL include the list of dependent entity identifiers.
    """

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion
    @given(
        entity_id=_id_st,
        entity_name=_name_st,
        domain_id=_id_st,
        domain_name=_name_st,
    )
    @_prop_settings
    def test_entity_deletion_blocked_by_active_domains(
        self, entity_id, entity_name, domain_id, domain_name,
    ):
        """Cannot delete an Entity that has active Domains."""
        store = HierarchyStore()
        store.create_entity(Entity(entity_id=entity_id, name=entity_name))
        store.create_domain(Domain(domain_id=domain_id, entity_id=entity_id, name=domain_name))

        with pytest.raises(ReferentialIntegrityError) as exc_info:
            store.delete_entity(entity_id)

        assert domain_id in exc_info.value.dependent_ids

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion
    @given(
        entity_id=_id_st,
        entity_name=_name_st,
        domain_id=_id_st,
        domain_name=_name_st,
        family_id=_id_st,
        family_name=_name_st,
    )
    @_prop_settings
    def test_domain_deletion_blocked_by_active_families(
        self, entity_id, entity_name, domain_id, domain_name,
        family_id, family_name,
    ):
        """Cannot delete a Domain that has active ProductFamilies."""
        store = HierarchyStore()
        store.create_entity(Entity(entity_id=entity_id, name=entity_name))
        store.create_domain(Domain(domain_id=domain_id, entity_id=entity_id, name=domain_name))
        store.create_product_family(
            ProductFamily(family_id=family_id, domain_id=domain_id, name=family_name)
        )

        with pytest.raises(ReferentialIntegrityError) as exc_info:
            store.delete_domain(domain_id)

        assert family_id in exc_info.value.dependent_ids

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion
    @given(
        entity_id=_id_st,
        entity_name=_name_st,
        domain_id=_id_st,
        domain_name=_name_st,
        family_id=_id_st,
        family_name=_name_st,
        resource_id=_id_st,
        resource_name=_name_st,
    )
    @_prop_settings
    def test_product_family_deletion_blocked_by_active_resources(
        self, entity_id, entity_name, domain_id, domain_name,
        family_id, family_name, resource_id, resource_name,
    ):
        """Cannot delete a ProductFamily that has active Resources."""
        store = HierarchyStore()
        store.create_entity(Entity(entity_id=entity_id, name=entity_name))
        store.create_domain(Domain(domain_id=domain_id, entity_id=entity_id, name=domain_name))
        store.create_product_family(
            ProductFamily(family_id=family_id, domain_id=domain_id, name=family_name)
        )
        store.create_resource(
            Resource(resource_id=resource_id, family_id=family_id, name=resource_name)
        )

        with pytest.raises(ReferentialIntegrityError) as exc_info:
            store.delete_product_family(family_id)

        assert resource_id in exc_info.value.dependent_ids

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion
    @given(entity_id=_id_st, entity_name=_name_st)
    @_prop_settings
    def test_entity_deletion_succeeds_when_no_children(
        self, entity_id, entity_name,
    ):
        """An Entity with no Domains can be deleted successfully."""
        store = HierarchyStore()
        store.create_entity(Entity(entity_id=entity_id, name=entity_name))
        store.delete_entity(entity_id)
        assert store.get_entity(entity_id) is None

    # Feature: openmesh-framework, Property 8: Referential Integrity on Deletion
    @given(
        entity_id=_id_st,
        entity_name=_name_st,
        resource_id=_id_st,
        resource_name=_name_st,
    )
    @_prop_settings
    def test_resource_deletion_always_succeeds(
        self, entity_id, entity_name, resource_id, resource_name,
    ):
        """Resources are leaf nodes — deletion always succeeds."""
        store = HierarchyStore()
        store.create_entity(Entity(entity_id=entity_id, name=entity_name))
        store.create_domain(Domain(domain_id="d1", entity_id=entity_id, name="dom"))
        store.create_product_family(
            ProductFamily(family_id="f1", domain_id="d1", name="fam")
        )
        store.create_resource(
            Resource(resource_id=resource_id, family_id="f1", name=resource_name)
        )
        store.delete_resource(resource_id)
        assert store.get_resource(resource_id) is None
