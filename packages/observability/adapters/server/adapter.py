"""Server Adapter — EC2, Docker, Nginx, Gunicorn health observability.

Reference adapter demonstrating the ObservabilityAdapterInterface
for traditional server infrastructure monitoring.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from packages.observability.interface.adapter import (
    AdapterMetadata,
    HealthCheck,
    HealthStatus,
    MeshHealthEvent,
    Metric,
    ObservabilityAdapterInterface,
    PanelDefinition,
    Severity,
)


class ServerAdapter(ObservabilityAdapterInterface):
    """Observability adapter for server infrastructure.

    Monitors EC2 instances, Docker containers, Nginx reverse proxies,
    and Gunicorn application servers.
    """

    def __init__(self, entity_id: str = "", domain: str = "") -> None:
        self._entity_id = entity_id
        self._domain = domain

    def get_health_checks(self) -> List[HealthCheck]:
        """Return health checks for server infrastructure components."""
        return [
            HealthCheck(
                name="ec2_instance_status",
                status=HealthStatus.HEALTHY,
                detail="EC2 instance running, all status checks passed",
            ),
            HealthCheck(
                name="docker_daemon",
                status=HealthStatus.HEALTHY,
                detail="Docker daemon responsive, 12 containers running",
            ),
            HealthCheck(
                name="nginx_upstream",
                status=HealthStatus.HEALTHY,
                detail="Nginx upstream servers all reachable",
            ),
            HealthCheck(
                name="gunicorn_workers",
                status=HealthStatus.HEALTHY,
                detail="4/4 Gunicorn workers active",
            ),
        ]

    def get_metrics(self) -> List[Metric]:
        """Return current metrics for server infrastructure."""
        now = datetime.now(timezone.utc)
        return [
            Metric(metric_name="cpu_utilization", value=42.5, unit="percent", timestamp=now),
            Metric(metric_name="memory_usage", value=68.3, unit="percent", timestamp=now),
            Metric(metric_name="disk_io_read", value=150.0, unit="MB/s", timestamp=now),
            Metric(metric_name="disk_io_write", value=85.0, unit="MB/s", timestamp=now),
            Metric(metric_name="network_in", value=250.0, unit="Mbps", timestamp=now),
            Metric(metric_name="network_out", value=180.0, unit="Mbps", timestamp=now),
            Metric(metric_name="active_connections", value=1250.0, unit="count", timestamp=now),
            Metric(metric_name="request_latency_p99", value=45.0, unit="ms", timestamp=now),
        ]

    def get_panel_definitions(self) -> List[PanelDefinition]:
        """Return dashboard panel definitions for server monitoring."""
        return [
            PanelDefinition(
                title="Server Health",
                data_source_key="health_checks",
                visualization_type="health_grid",
                required_role="operator",
            ),
            PanelDefinition(
                title="EC2 Metrics",
                data_source_key="metrics",
                visualization_type="metric_chart",
                required_role="operator",
            ),
            PanelDefinition(
                title="Docker Containers",
                data_source_key="docker_status",
                visualization_type="table",
                required_role="operator",
            ),
            PanelDefinition(
                title="Nginx Traffic",
                data_source_key="nginx_metrics",
                visualization_type="metric_chart",
                required_role="viewer",
            ),
        ]

    def get_adapter_metadata(self) -> AdapterMetadata:
        """Return metadata about the server adapter."""
        return AdapterMetadata(
            name="server-adapter",
            version="1.0.0",
            supported_runtime_types=["server"],
            description="Observability adapter for EC2, Docker, Nginx, and Gunicorn server infrastructure",
        )

    def emit_health_event(self, severity: Severity, message: str) -> MeshHealthEvent:
        """Emit a MeshHealthEvent for this adapter's domain."""
        return MeshHealthEvent(
            entity_id=self._entity_id,
            domain=self._domain,
            severity=severity,
            message=message,
            timestamp=datetime.now(timezone.utc),
        )
