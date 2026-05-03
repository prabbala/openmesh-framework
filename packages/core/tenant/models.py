"""Tenant data models — Tenant, TenantType, and related types.

Tenants map to Entities in the 4-tier hierarchy and represent
isolated organizational units within the framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class TenantType(Enum):
    """Tenant hierarchy types."""

    INDEPENDENT = "independent"
    PARENT = "parent"
    SUB_CLIENT = "sub_client"


@dataclass
class Tenant:
    """An isolated organizational unit mapped to an Entity.

    Fields:
        tenant_id: Unique identifier (auto-generated on creation).
        name: Human-readable tenant name.
        tenant_type: INDEPENDENT, PARENT, or SUB_CLIENT.
        parent_tenant_id: Required for SUB_CLIENT, must reference a PARENT.
        entity_id: Maps to an Entity in the 4-tier hierarchy.
        is_active: Whether the tenant is active.
        is_suspended: Whether the tenant is suspended (reads OK, writes blocked).
        created_at: Creation timestamp.
    """

    tenant_id: str
    name: str
    tenant_type: TenantType
    parent_tenant_id: Optional[str] = None
    entity_id: str = ""
    is_active: bool = True
    is_suspended: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
