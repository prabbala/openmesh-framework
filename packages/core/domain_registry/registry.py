"""Domain Registry — runtime registry for DomainRegistrations.

Stores registered domains and provides lookup by domain_id and runtime_type.
Validates that adapters implement ObservabilityAdapterInterface on registration.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from packages.observability.interface.adapter import ObservabilityAdapterInterface

from .registration import DomainRegistration


class DuplicateDomainError(Exception):
    """Raised when a domain_id is already registered."""


class InvalidAdapterError(Exception):
    """Raised when an adapter does not implement ObservabilityAdapterInterface."""


class DomainNotFoundError(Exception):
    """Raised when a domain_id is not found in the registry."""


class DomainRegistry:
    """Runtime registry for DomainRegistrations.

    Provides:
    - register(): Add a domain with adapter validation
    - unregister(): Remove a domain and its tabs
    - get_by_id(): Lookup by domain_id
    - get_by_runtime_type(): Lookup by runtime_type
    - get_domains_for_scope(): Filter by LOB scope
    """

    def __init__(self) -> None:
        self._domains: Dict[str, DomainRegistration] = {}

    def register(
        self,
        registration: DomainRegistration,
        adapter_class: Optional[type] = None,
    ) -> None:
        """Register a domain.

        Validates that adapter_class implements ObservabilityAdapterInterface
        (when provided). Rejects duplicate domain_id with descriptive error.

        Args:
            registration: The DomainRegistration to register.
            adapter_class: The adapter class to validate. If None, adapter
                           validation is skipped (useful for YAML-only registration).

        Raises:
            DuplicateDomainError: If domain_id is already registered.
            InvalidAdapterError: If adapter_class does not implement the interface.
        """
        if registration.domain_id in self._domains:
            raise DuplicateDomainError(
                f"Domain '{registration.domain_id}' is already registered. "
                f"Each domain_id must be unique."
            )

        if adapter_class is not None:
            if not (
                isinstance(adapter_class, type)
                and issubclass(adapter_class, ObservabilityAdapterInterface)
            ):
                raise InvalidAdapterError(
                    f"Adapter '{registration.observability_adapter}' does not "
                    f"implement ObservabilityAdapterInterface"
                )

        self._domains[registration.domain_id] = registration

    def unregister(self, domain_id: str) -> None:
        """Unregister a domain and remove associated dashboard tabs.

        Raises:
            DomainNotFoundError: If domain_id is not registered.
        """
        if domain_id not in self._domains:
            raise DomainNotFoundError(
                f"Domain '{domain_id}' is not registered"
            )
        del self._domains[domain_id]

    def get_by_id(self, domain_id: str) -> Optional[DomainRegistration]:
        """Lookup a DomainRegistration by domain_id. Returns None if not found."""
        return self._domains.get(domain_id)

    def get_by_runtime_type(self, runtime_type: str) -> List[DomainRegistration]:
        """Return all DomainRegistrations matching the given runtime_type."""
        return [
            d for d in self._domains.values()
            if d.runtime_type == runtime_type
        ]

    def get_domains_for_scope(self, lob_scope: Set[str]) -> List[DomainRegistration]:
        """Return domains whose lob_id is in the given LOB scope set."""
        return [
            d for d in self._domains.values()
            if d.lob_id in lob_scope
        ]

    def list_all(self) -> List[DomainRegistration]:
        """Return all registered domains."""
        return list(self._domains.values())

    @property
    def count(self) -> int:
        """Return the number of registered domains."""
        return len(self._domains)
