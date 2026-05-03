"""Audit Engine data models — AuditRecord.

Defines the immutable audit record schema for tracking all
administrative actions, permission changes, and observability events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
import uuid


@dataclass(frozen=True)
class AuditRecord:
    """An immutable audit log entry.

    Fields:
        record_id: Unique identifier (UUID, immutable).
        timestamp: When the action occurred.
        entity_id: Which Entity.
        tenant_id: Which Tenant (for isolation).
        actor_id: Who performed the action.
        action_type: e.g. "role_assigned", "domain_registered", "tenant_suspended".
        resource: What was acted upon.
        detail: Action-specific payload.

    Frozen dataclass ensures immutability after creation.
    """

    record_id: str
    timestamp: datetime
    entity_id: str
    tenant_id: str
    actor_id: str
    action_type: str
    resource: str
    detail: Dict[str, Any]
