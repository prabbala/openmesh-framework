"""MeshHealthEvent construction helpers for adapter developers.

Provides convenient factory functions for creating MeshHealthEvent objects
with proper defaults and validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from packages.observability.interface.adapter import (
    MeshHealthEvent,
    Severity,
)


def create_health_event(
    entity_id: str,
    domain: str,
    severity: str | Severity,
    message: str,
    timestamp: Optional[datetime] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> MeshHealthEvent:
    """Create a MeshHealthEvent with validation and defaults.

    Args:
        entity_id: Which Entity this event relates to.
        domain: Which Domain this event relates to.
        severity: Severity level — "Critical", "Warning", "Info", or Severity enum.
        message: Human-readable event message.
        timestamp: Event timestamp. Defaults to now (UTC).
        metadata: Optional additional metadata dict.

    Returns:
        A validated MeshHealthEvent.

    Raises:
        ValueError: If severity is not a valid value.
    """
    if isinstance(severity, str):
        try:
            severity = Severity(severity)
        except ValueError:
            valid = [s.value for s in Severity]
            raise ValueError(
                f"Invalid severity '{severity}'. Must be one of: {valid}"
            )

    return MeshHealthEvent(
        entity_id=entity_id,
        domain=domain,
        severity=severity,
        message=message,
        timestamp=timestamp or datetime.now(timezone.utc),
        metadata=metadata or {},
    )


def critical_event(
    entity_id: str, domain: str, message: str, **kwargs: Any
) -> MeshHealthEvent:
    """Shortcut for creating a Critical severity event."""
    return create_health_event(entity_id, domain, Severity.CRITICAL, message, **kwargs)


def warning_event(
    entity_id: str, domain: str, message: str, **kwargs: Any
) -> MeshHealthEvent:
    """Shortcut for creating a Warning severity event."""
    return create_health_event(entity_id, domain, Severity.WARNING, message, **kwargs)


def info_event(
    entity_id: str, domain: str, message: str, **kwargs: Any
) -> MeshHealthEvent:
    """Shortcut for creating an Info severity event."""
    return create_health_event(entity_id, domain, Severity.INFO, message, **kwargs)
