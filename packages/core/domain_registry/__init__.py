"""Domain Registry — DomainRegistration storage, validation, and lookup.

Public API:
- Models: Entity, Domain, ProductFamily, Resource
- Hierarchy: HierarchyStore
- Registration: DomainRegistration
- Registry: DomainRegistry
- Serialization: serialize_to_yaml, deserialize_from_yaml
"""

from .hierarchy import (
    DuplicateIdError,
    HierarchyStore,
    NotFoundError,
    ParentNotFoundError,
    ReferentialIntegrityError,
)
from .models import Domain, Entity, ProductFamily, Resource
from .registration import VALID_RUNTIME_TYPES, DomainRegistration
from .registry import (
    DomainNotFoundError,
    DomainRegistry,
    DuplicateDomainError,
    InvalidAdapterError,
)
from .serialization import SerializationError, deserialize_from_yaml, serialize_to_yaml

__all__ = [
    # Models
    "Entity",
    "Domain",
    "ProductFamily",
    "Resource",
    # Hierarchy
    "HierarchyStore",
    "ReferentialIntegrityError",
    "ParentNotFoundError",
    "DuplicateIdError",
    "NotFoundError",
    # Registration
    "DomainRegistration",
    "VALID_RUNTIME_TYPES",
    # Registry
    "DomainRegistry",
    "DuplicateDomainError",
    "InvalidAdapterError",
    "DomainNotFoundError",
    # Serialization
    "serialize_to_yaml",
    "deserialize_from_yaml",
    "SerializationError",
]
