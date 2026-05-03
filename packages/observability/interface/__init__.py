"""Observability Interface — Base adapter ABC and MeshHealthEvent schema."""

from .adapter import (
    AdapterMetadata,
    HealthCheck,
    HealthStatus,
    MeshHealthEvent,
    Metric,
    ObservabilityAdapterInterface,
    PanelDefinition,
    Severity,
)
from .events import (
    EventSerializationError,
    deserialize_from_json,
    serialize_to_json,
)

__all__ = [
    "AdapterMetadata",
    "HealthCheck",
    "HealthStatus",
    "MeshHealthEvent",
    "Metric",
    "ObservabilityAdapterInterface",
    "PanelDefinition",
    "Severity",
    "EventSerializationError",
    "serialize_to_json",
    "deserialize_from_json",
]
