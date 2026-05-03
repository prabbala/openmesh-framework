"""Observability Adapter Interface — Abstract base class for all adapters.

Every adapter must implement this interface to plug observability data
into the OpenMesh framework.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Severity(Enum):
    """Severity levels for MeshHealthEvents."""

    CRITICAL = "Critical"
    WARNING = "Warning"
    INFO = "Info"


class HealthStatus(Enum):
    """Health status for individual health checks."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """A standardized health probe result."""

    name: str
    status: HealthStatus
    detail: Optional[str] = None


@dataclass
class Metric:
    """A single metric data point."""

    metric_name: str
    value: float
    unit: str
    timestamp: datetime


@dataclass
class PanelDefinition:
    """A declarative dashboard panel specification."""

    title: str
    data_source_key: str
    visualization_type: str
    required_role: str


@dataclass
class AdapterMetadata:
    """Metadata about an adapter."""

    name: str
    version: str
    supported_runtime_types: List[str]
    description: str


@dataclass
class MeshHealthEvent:
    """Universal telemetry schema emitted by all adapters."""

    entity_id: str
    domain: str
    severity: Severity
    message: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)


class ObservabilityAdapterInterface(ABC):
    """Abstract base class for all observability adapters.

    Adapters implement this interface to provide health checks, metrics,
    panel definitions, and metadata for their infrastructure domain.
    """

    @abstractmethod
    def get_health_checks(self) -> List[HealthCheck]:
        """Return health check results for this adapter's domain."""
        ...

    @abstractmethod
    def get_metrics(self) -> List[Metric]:
        """Return current metrics for this adapter's domain."""
        ...

    @abstractmethod
    def get_panel_definitions(self) -> List[PanelDefinition]:
        """Return dashboard panel definitions for this adapter's domain."""
        ...

    @abstractmethod
    def get_adapter_metadata(self) -> AdapterMetadata:
        """Return metadata about this adapter."""
        ...
