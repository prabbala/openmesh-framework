"""4-Tier Hierarchy Data Models: Entity, Domain, ProductFamily, Resource.

Implements the generic 4-tier hierarchy:
  Entity (root) → Domain (LOB) → ProductFamily (group) → Resource (node)

Any business structure can be modeled without framework changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Entity:
    """Root organizational unit — represents a business or organization.

    Examples: Empirical-AiS Inc., Sports-Avatar LLC.
    """

    entity_id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.entity_id or not self.entity_id.strip():
            raise ValueError("entity_id must be a non-empty string")
        if not self.name or not self.name.strip():
            raise ValueError("name must be a non-empty string")


@dataclass
class Domain:
    """A Line of Business within an Entity — second tier.

    Examples: Cybersecurity (DeCMMC), Animation Engine.
    Every Domain belongs to exactly one Entity.
    """

    domain_id: str
    entity_id: str
    name: str
    lob_id: str = ""
    runtime_type: str = ""
    observability_adapter: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.domain_id or not self.domain_id.strip():
            raise ValueError("domain_id must be a non-empty string")
        if not self.entity_id or not self.entity_id.strip():
            raise ValueError("entity_id must be a non-empty string")
        if not self.name or not self.name.strip():
            raise ValueError("name must be a non-empty string")


@dataclass
class ProductFamily:
    """A logical grouping of Resources within a Domain — third tier.

    Examples: Plug-N-Play (PNP), Cric-Avatar.
    Every ProductFamily belongs to exactly one Domain.
    """

    family_id: str
    domain_id: str
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.family_id or not self.family_id.strip():
            raise ValueError("family_id must be a non-empty string")
        if not self.domain_id or not self.domain_id.strip():
            raise ValueError("domain_id must be a non-empty string")
        if not self.name or not self.name.strip():
            raise ValueError("name must be a non-empty string")


@dataclass
class Resource:
    """An individual infrastructure or application node — fourth tier.

    Examples: EC2 Instance, Blender Render Node, GPU.
    Every Resource belongs to exactly one ProductFamily.
    """

    resource_id: str
    family_id: str
    name: str
    resource_type: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.resource_id or not self.resource_id.strip():
            raise ValueError("resource_id must be a non-empty string")
        if not self.family_id or not self.family_id.strip():
            raise ValueError("family_id must be a non-empty string")
        if not self.name or not self.name.strip():
            raise ValueError("name must be a non-empty string")
