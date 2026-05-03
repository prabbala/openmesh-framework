"""MeshHealthEvent JSON serialization and deserialization.

Provides round-trip JSON support for MeshHealthEvent objects.
Validates severity and all required fields during deserialization,
returning descriptive errors listing all invalid fields on failure.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .adapter import MeshHealthEvent, Severity

VALID_SEVERITIES = frozenset({s.value for s in Severity})


class EventSerializationError(Exception):
    """Raised when MeshHealthEvent serialization or deserialization fails."""

    def __init__(
        self, message: str, field_errors: List[Dict[str, str]] | None = None
    ) -> None:
        super().__init__(message)
        self.field_errors = field_errors or []


def serialize_to_json(event: MeshHealthEvent) -> str:
    """Serialize a MeshHealthEvent to JSON format.

    Args:
        event: A valid MeshHealthEvent object.

    Returns:
        A JSON string representation.
    """
    data: Dict[str, Any] = {
        "entity_id": event.entity_id,
        "domain": event.domain,
        "severity": event.severity.value,
        "message": event.message,
        "timestamp": event.timestamp.isoformat(),
    }
    if event.metadata:
        data["metadata"] = event.metadata
    return json.dumps(data)


def deserialize_from_json(json_str: str) -> MeshHealthEvent:
    """Deserialize a JSON string into a MeshHealthEvent.

    Validates all required fields and severity enum. Returns descriptive
    errors listing every invalid field on failure.

    Args:
        json_str: A JSON string to parse.

    Returns:
        A MeshHealthEvent object.

    Raises:
        EventSerializationError: If JSON is invalid or fields are missing/invalid.
    """
    # Parse JSON
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        raise EventSerializationError(
            f"Invalid JSON syntax: {e}",
            field_errors=[{"field": "json", "issue": str(e)}],
        )

    if not isinstance(data, dict):
        raise EventSerializationError(
            f"JSON must deserialize to an object, got {type(data).__name__}",
            field_errors=[{"field": "root", "issue": "Expected a JSON object"}],
        )

    # Validate all required fields, collecting all errors
    field_errors: List[Dict[str, str]] = []

    # entity_id
    entity_id = data.get("entity_id")
    if entity_id is None:
        field_errors.append(
            {"field": "entity_id", "issue": "Field is required but missing"}
        )
    elif not isinstance(entity_id, str) or not entity_id.strip():
        field_errors.append(
            {"field": "entity_id", "issue": "Must be a non-empty string"}
        )

    # domain
    domain = data.get("domain")
    if domain is None:
        field_errors.append(
            {"field": "domain", "issue": "Field is required but missing"}
        )
    elif not isinstance(domain, str) or not domain.strip():
        field_errors.append(
            {"field": "domain", "issue": "Must be a non-empty string"}
        )

    # severity
    severity_val = data.get("severity")
    if severity_val is None:
        field_errors.append(
            {"field": "severity", "issue": "Field is required but missing"}
        )
    elif severity_val not in VALID_SEVERITIES:
        field_errors.append({
            "field": "severity",
            "issue": (
                f"Value '{severity_val}' is not valid. "
                f"Must be one of: {', '.join(sorted(VALID_SEVERITIES))}"
            ),
        })

    # message
    message = data.get("message")
    if message is None:
        field_errors.append(
            {"field": "message", "issue": "Field is required but missing"}
        )
    elif not isinstance(message, str):
        field_errors.append(
            {"field": "message", "issue": "Must be a string"}
        )

    # timestamp
    timestamp_val = data.get("timestamp")
    parsed_ts: Optional[datetime] = None
    if timestamp_val is None:
        field_errors.append(
            {"field": "timestamp", "issue": "Field is required but missing"}
        )
    elif not isinstance(timestamp_val, str):
        field_errors.append(
            {"field": "timestamp", "issue": "Must be an ISO 8601 string"}
        )
    else:
        try:
            parsed_ts = datetime.fromisoformat(timestamp_val)
        except ValueError:
            field_errors.append({
                "field": "timestamp",
                "issue": f"Cannot parse '{timestamp_val}' as ISO 8601 datetime",
            })

    if field_errors:
        raise EventSerializationError(
            f"MeshHealthEvent validation failed: "
            f"{len(field_errors)} field error(s)",
            field_errors=field_errors,
        )

    return MeshHealthEvent(
        entity_id=data["entity_id"],
        domain=data["domain"],
        severity=Severity(data["severity"]),
        message=data["message"],
        timestamp=parsed_ts,  # type: ignore[arg-type]
        metadata=data.get("metadata", {}),
    )
