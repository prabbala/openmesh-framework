"""DomainRegistration YAML serialization and deserialization.

Provides round-trip YAML support for DomainRegistration objects.
Validates all required fields during deserialization and returns
descriptive errors listing all invalid fields on failure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import yaml

from .registration import VALID_RUNTIME_TYPES, DomainRegistration


class SerializationError(Exception):
    """Raised when serialization or deserialization fails."""

    def __init__(self, message: str, field_errors: List[Dict[str, str]] | None = None) -> None:
        super().__init__(message)
        self.field_errors = field_errors or []


def serialize_to_yaml(registration: DomainRegistration) -> str:
    """Serialize a DomainRegistration to YAML format.

    Args:
        registration: A valid DomainRegistration object.

    Returns:
        A YAML string representation.
    """
    data: Dict[str, Any] = {
        "domain_id": registration.domain_id,
        "runtime_type": registration.runtime_type,
        "observability_adapter": registration.observability_adapter,
        "roles": list(registration.roles),
        "tabs": list(registration.tabs),
    }

    # Include optional fields when present
    if registration.entity_id:
        data["entity_id"] = registration.entity_id
    if registration.lob_id:
        data["lob_id"] = registration.lob_id
    if registration.metadata:
        data["metadata"] = dict(registration.metadata)

    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def deserialize_from_yaml(yaml_str: str) -> DomainRegistration:
    """Deserialize a YAML string into a DomainRegistration.

    Validates all required fields and returns descriptive errors
    listing every invalid field on failure.

    Args:
        yaml_str: A YAML string to parse.

    Returns:
        A DomainRegistration object.

    Raises:
        SerializationError: If the YAML is invalid or required fields are missing/invalid.
    """
    # Parse YAML
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise SerializationError(
            f"Invalid YAML syntax: {e}",
            field_errors=[{"field": "yaml", "issue": str(e)}],
        )

    if not isinstance(data, dict):
        raise SerializationError(
            "YAML must deserialize to a mapping (dict), "
            f"got {type(data).__name__}",
            field_errors=[{"field": "root", "issue": "Expected a YAML mapping"}],
        )

    # Validate all required fields, collecting all errors
    field_errors: List[Dict[str, str]] = []

    # domain_id
    domain_id = data.get("domain_id")
    if domain_id is None:
        field_errors.append({"field": "domain_id", "issue": "Field is required but missing"})
    elif not isinstance(domain_id, str) or not domain_id.strip():
        field_errors.append({"field": "domain_id", "issue": "Must be a non-empty string"})

    # runtime_type
    runtime_type = data.get("runtime_type")
    if runtime_type is None:
        field_errors.append({"field": "runtime_type", "issue": "Field is required but missing"})
    elif runtime_type not in VALID_RUNTIME_TYPES:
        field_errors.append({
            "field": "runtime_type",
            "issue": f"Value '{runtime_type}' is not a supported runtime_type. "
                     f"Must be one of: {', '.join(sorted(VALID_RUNTIME_TYPES))}",
        })

    # observability_adapter
    adapter = data.get("observability_adapter")
    if adapter is None:
        field_errors.append({
            "field": "observability_adapter",
            "issue": "Field is required but missing",
        })
    elif not isinstance(adapter, str) or not adapter.strip():
        field_errors.append({
            "field": "observability_adapter",
            "issue": "Must be a non-empty string",
        })

    # roles
    roles = data.get("roles")
    if roles is None:
        field_errors.append({"field": "roles", "issue": "Field is required but missing"})
    elif not isinstance(roles, list) or len(roles) == 0:
        field_errors.append({"field": "roles", "issue": "Must be a non-empty list"})

    # tabs
    tabs = data.get("tabs")
    if tabs is None:
        field_errors.append({"field": "tabs", "issue": "Field is required but missing"})
    elif not isinstance(tabs, list):
        field_errors.append({"field": "tabs", "issue": "Must be a list"})

    if field_errors:
        raise SerializationError(
            f"DomainRegistration validation failed: "
            f"{len(field_errors)} field error(s)",
            field_errors=field_errors,
        )

    # Build the DomainRegistration
    return DomainRegistration(
        domain_id=data["domain_id"],
        runtime_type=data["runtime_type"],
        observability_adapter=data["observability_adapter"],
        roles=data["roles"],
        tabs=data.get("tabs", []),
        entity_id=data.get("entity_id", ""),
        lob_id=data.get("lob_id", ""),
        metadata=data.get("metadata", {}),
    )
