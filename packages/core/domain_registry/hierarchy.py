"""4-Tier Hierarchy Store with CRUD operations and referential integrity.

Manages the Entity → Domain → ProductFamily → Resource hierarchy.
Enforces parent constraints on creation and referential integrity on deletion.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .models import Domain, Entity, ProductFamily, Resource


class ReferentialIntegrityError(Exception):
    """Raised when a deletion would violate referential integrity."""

    def __init__(self, message: str, dependent_ids: List[str]) -> None:
        super().__init__(message)
        self.dependent_ids = dependent_ids


class ParentNotFoundError(Exception):
    """Raised when a required parent node does not exist."""


class DuplicateIdError(Exception):
    """Raised when an ID already exists in the store."""


class NotFoundError(Exception):
    """Raised when a requested node does not exist."""


class HierarchyStore:
    """In-memory store for the 4-tier hierarchy with CRUD and integrity checks.

    Enforces:
    - Parent constraints: Domain → Entity, ProductFamily → Domain, Resource → ProductFamily
    - Referential integrity on deletion: reject if active children exist
    """

    def __init__(self) -> None:
        self._entities: Dict[str, Entity] = {}
        self._domains: Dict[str, Domain] = {}
        self._families: Dict[str, ProductFamily] = {}
        self._resources: Dict[str, Resource] = {}

    # ── Entity CRUD ──────────────────────────────────────────────────

    def create_entity(self, entity: Entity) -> Entity:
        """Create an Entity. Raises DuplicateIdError if entity_id exists."""
        if entity.entity_id in self._entities:
            raise DuplicateIdError(
                f"Entity with id '{entity.entity_id}' already exists"
            )
        self._entities[entity.entity_id] = entity
        return entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Return an Entity by ID, or None if not found."""
        return self._entities.get(entity_id)

    def list_entities(self) -> List[Entity]:
        """Return all entities."""
        return list(self._entities.values())

    def delete_entity(self, entity_id: str) -> None:
        """Delete an Entity. Rejects if active Domains reference it.

        Raises:
            NotFoundError: If entity_id does not exist.
            ReferentialIntegrityError: If active Domains reference this Entity.
        """
        if entity_id not in self._entities:
            raise NotFoundError(f"Entity '{entity_id}' not found")

        dependent_ids = [
            d.domain_id
            for d in self._domains.values()
            if d.entity_id == entity_id
        ]
        if dependent_ids:
            raise ReferentialIntegrityError(
                f"Cannot delete Entity '{entity_id}': "
                f"{len(dependent_ids)} active Domain(s) reference it",
                dependent_ids=dependent_ids,
            )
        del self._entities[entity_id]

    # ── Domain CRUD ──────────────────────────────────────────────────

    def create_domain(self, domain: Domain) -> Domain:
        """Create a Domain. Parent Entity must exist.

        Raises:
            ParentNotFoundError: If entity_id does not reference an existing Entity.
            DuplicateIdError: If domain_id already exists.
        """
        if domain.entity_id not in self._entities:
            raise ParentNotFoundError(
                f"Parent Entity '{domain.entity_id}' not found for Domain '{domain.domain_id}'"
            )
        if domain.domain_id in self._domains:
            raise DuplicateIdError(
                f"Domain with id '{domain.domain_id}' already exists"
            )
        self._domains[domain.domain_id] = domain
        return domain

    def get_domain(self, domain_id: str) -> Optional[Domain]:
        """Return a Domain by ID, or None if not found."""
        return self._domains.get(domain_id)

    def list_domains(self, entity_id: Optional[str] = None) -> List[Domain]:
        """Return all domains, optionally filtered by entity_id."""
        if entity_id is not None:
            return [d for d in self._domains.values() if d.entity_id == entity_id]
        return list(self._domains.values())

    def delete_domain(self, domain_id: str) -> None:
        """Delete a Domain. Rejects if active ProductFamilies reference it.

        Raises:
            NotFoundError: If domain_id does not exist.
            ReferentialIntegrityError: If active ProductFamilies reference this Domain.
        """
        if domain_id not in self._domains:
            raise NotFoundError(f"Domain '{domain_id}' not found")

        dependent_ids = [
            f.family_id
            for f in self._families.values()
            if f.domain_id == domain_id
        ]
        if dependent_ids:
            raise ReferentialIntegrityError(
                f"Cannot delete Domain '{domain_id}': "
                f"{len(dependent_ids)} active ProductFamily(ies) reference it",
                dependent_ids=dependent_ids,
            )
        del self._domains[domain_id]

    # ── ProductFamily CRUD ───────────────────────────────────────────

    def create_product_family(self, family: ProductFamily) -> ProductFamily:
        """Create a ProductFamily. Parent Domain must exist.

        Raises:
            ParentNotFoundError: If domain_id does not reference an existing Domain.
            DuplicateIdError: If family_id already exists.
        """
        if family.domain_id not in self._domains:
            raise ParentNotFoundError(
                f"Parent Domain '{family.domain_id}' not found "
                f"for ProductFamily '{family.family_id}'"
            )
        if family.family_id in self._families:
            raise DuplicateIdError(
                f"ProductFamily with id '{family.family_id}' already exists"
            )
        self._families[family.family_id] = family
        return family

    def get_product_family(self, family_id: str) -> Optional[ProductFamily]:
        """Return a ProductFamily by ID, or None if not found."""
        return self._families.get(family_id)

    def list_product_families(self, domain_id: Optional[str] = None) -> List[ProductFamily]:
        """Return all product families, optionally filtered by domain_id."""
        if domain_id is not None:
            return [f for f in self._families.values() if f.domain_id == domain_id]
        return list(self._families.values())

    def delete_product_family(self, family_id: str) -> None:
        """Delete a ProductFamily. Rejects if active Resources reference it.

        Raises:
            NotFoundError: If family_id does not exist.
            ReferentialIntegrityError: If active Resources reference this ProductFamily.
        """
        if family_id not in self._families:
            raise NotFoundError(f"ProductFamily '{family_id}' not found")

        dependent_ids = [
            r.resource_id
            for r in self._resources.values()
            if r.family_id == family_id
        ]
        if dependent_ids:
            raise ReferentialIntegrityError(
                f"Cannot delete ProductFamily '{family_id}': "
                f"{len(dependent_ids)} active Resource(s) reference it",
                dependent_ids=dependent_ids,
            )
        del self._families[family_id]

    # ── Resource CRUD ────────────────────────────────────────────────

    def create_resource(self, resource: Resource) -> Resource:
        """Create a Resource. Parent ProductFamily must exist.

        Raises:
            ParentNotFoundError: If family_id does not reference an existing ProductFamily.
            DuplicateIdError: If resource_id already exists.
        """
        if resource.family_id not in self._families:
            raise ParentNotFoundError(
                f"Parent ProductFamily '{resource.family_id}' not found "
                f"for Resource '{resource.resource_id}'"
            )
        if resource.resource_id in self._resources:
            raise DuplicateIdError(
                f"Resource with id '{resource.resource_id}' already exists"
            )
        self._resources[resource.resource_id] = resource
        return resource

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Return a Resource by ID, or None if not found."""
        return self._resources.get(resource_id)

    def list_resources(self, family_id: Optional[str] = None) -> List[Resource]:
        """Return all resources, optionally filtered by family_id."""
        if family_id is not None:
            return [r for r in self._resources.values() if r.family_id == family_id]
        return list(self._resources.values())

    def delete_resource(self, resource_id: str) -> None:
        """Delete a Resource (leaf node — no children to check).

        Raises:
            NotFoundError: If resource_id does not exist.
        """
        if resource_id not in self._resources:
            raise NotFoundError(f"Resource '{resource_id}' not found")
        del self._resources[resource_id]
