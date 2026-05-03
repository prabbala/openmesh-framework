"""Audit Engine — immutable, append-only audit log with tenant isolation.

Records all administrative actions and enforces:
- Append-only semantics (no modify, no delete)
- Tenant isolation on queries
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import AuditRecord


class AuditImmutabilityError(Exception):
    """Raised when attempting to modify or delete an audit record."""


class AuditEngine:
    """Immutable, append-only audit log with tenant isolation.

    Provides:
    - record(): Append a new audit record
    - query(): Query records with tenant isolation
    - No modify or delete operations
    """

    def __init__(self) -> None:
        self._records: List[AuditRecord] = []
        self._record_ids: set = set()

    def record(
        self,
        entity_id: str,
        tenant_id: str,
        actor_id: str,
        action_type: str,
        resource: str,
        detail: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        """Append an audit record. Records cannot be modified or deleted.

        Args:
            entity_id: Which Entity this action relates to.
            tenant_id: Which Tenant (for isolation).
            actor_id: Who performed the action.
            action_type: Type of action (e.g. "role_assigned").
            resource: What was acted upon.
            detail: Action-specific payload.

        Returns:
            The created AuditRecord.
        """
        record = AuditRecord(
            record_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            entity_id=entity_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            action_type=action_type,
            resource=resource,
            detail=detail or {},
        )
        self._records.append(record)
        self._record_ids.add(record.record_id)
        return record

    def query(
        self,
        tenant_id: str,
        action_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        resource: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[AuditRecord]:
        """Query audit records with tenant isolation.

        Only returns records matching the given tenant_id.
        Additional filters can narrow results further.

        Args:
            tenant_id: Required — enforces tenant isolation.
            action_type: Optional filter by action type.
            actor_id: Optional filter by actor.
            resource: Optional filter by resource.
            limit: Optional max number of records to return.

        Returns:
            List of matching AuditRecords, newest first.
        """
        results = [r for r in self._records if r.tenant_id == tenant_id]

        if action_type is not None:
            results = [r for r in results if r.action_type == action_type]
        if actor_id is not None:
            results = [r for r in results if r.actor_id == actor_id]
        if resource is not None:
            results = [r for r in results if r.resource == resource]

        # Newest first
        results = list(reversed(results))

        if limit is not None:
            results = results[:limit]

        return results

    def get_record(self, record_id: str) -> Optional[AuditRecord]:
        """Return a specific record by ID, or None."""
        for r in self._records:
            if r.record_id == record_id:
                return r
        return None

    @property
    def count(self) -> int:
        """Total number of audit records."""
        return len(self._records)

    def _assert_no_modify(self) -> None:
        """Internal: audit records are immutable by design.

        The AuditRecord dataclass is frozen, so field assignment
        raises FrozenInstanceError automatically. This method
        exists for documentation clarity.
        """
        pass
