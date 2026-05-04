"""DomainRegistration schema — binds a Domain to its adapter, roles, and tabs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

VALID_RUNTIME_TYPES = frozenset(
    {"server", "serverless", "kubernetes", "gpu", "streaming"}
)


@dataclass
class DomainRegistration:
    """A registry entry binding a Domain to its runtime configuration.

    Fields:
        domain_id: Unique identifier for this domain (the product).
        runtime_type: Technical classification — one of server, serverless,
                      kubernetes, gpu, streaming.
        observability_adapter: Fully qualified adapter class name.
        roles: Roles that can view this domain.
        tabs: Dashboard tab definitions.
        entity_id: Which Entity this domain belongs to.
        lob_id: Which LOB this domain belongs to.
        metadata: Optional additional metadata.
        product_families: Optional list of product_type definitions under this product.
            Each entry is a dict with at least {family_id, name} and optional description.
    """

    domain_id: str
    runtime_type: str
    observability_adapter: str
    roles: List[str]
    tabs: List[Dict]
    entity_id: str = ""
    lob_id: str = ""
    metadata: Dict = field(default_factory=dict)
    product_families: List[Dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.domain_id or not self.domain_id.strip():
            raise ValueError("domain_id must be a non-empty string")
        if self.runtime_type not in VALID_RUNTIME_TYPES:
            raise ValueError(
                f"runtime_type '{self.runtime_type}' is not supported. "
                f"Must be one of: {', '.join(sorted(VALID_RUNTIME_TYPES))}"
            )
        if not self.observability_adapter or not self.observability_adapter.strip():
            raise ValueError("observability_adapter must be a non-empty string")
        if not isinstance(self.roles, list) or len(self.roles) == 0:
            raise ValueError("roles must be a non-empty list")
        if not isinstance(self.tabs, list):
            raise ValueError("tabs must be a list")
        if not isinstance(self.product_families, list):
            raise ValueError("product_families must be a list")
