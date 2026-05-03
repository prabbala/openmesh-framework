"""Kubernetes Adapter — Pod, node, and service health observability.

Reference adapter demonstrating the ObservabilityAdapterInterface
for Kubernetes cluster monitoring.
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


class KubernetesAdapter(ObservabilityAdapterInterface):
    """Observability adapter for Kubernetes infrastructure.

    Monitors pod health, node status, and service availability
    across Kubernetes clusters.
    """

    def __init__(self, entity_id: str = "", domain: str = "") -> None:
        self._entity_id = entity_id
        self._domain = domain

    def get_health_checks(self) -> List[HealthCheck]:
        return [
            HealthCheck(
                name="pod_readiness",
                status=HealthStatus.HEALTHY,
                detail="48/50 pods ready, 2 pending (scaling event)",
            ),
            HealthCheck(
                name="node_status",
                status=HealthStatus.HEALTHY,
                detail="All 5 nodes in Ready condition",
            ),
            HealthCheck(
                name="service_endpoints",
                status=HealthStatus.HEALTHY,
                detail="All service endpoints have healthy backends",
            ),
            HealthCheck(
                name="persistent_volumes",
                status=HealthStatus.HEALTHY,
                detail="All PVCs bound and accessible",
            ),
        ]

    def get_metrics(self) -> List[Metric]:
        now = datetime.now(timezone.utc)
        return [
            Metric(metric_name="pod_count", value=50.0, unit="count", timestamp=now),
            Metric(metric_name="pod_restarts", value=2.0, unit="count", timestamp=now),
            Metric(metric_name="node_cpu_avg", value=55.0, unit="percent", timestamp=now),
            Metric(metric_name="node_memory_avg", value=72.0, unit="percent", timestamp=now),
            Metric(metric_name="cluster_network_rx", value=500.0, unit="Mbps", timestamp=now),
            Metric(metric_name="cluster_network_tx", value=320.0, unit="Mbps", timestamp=now),
            Metric(metric_name="ingress_requests", value=8500.0, unit="req/s", timestamp=now),
            Metric(metric_name="hpa_replicas", value=12.0, unit="count", timestamp=now),
        ]

    def get_panel_definitions(self) -> List[PanelDefinition]:
        return [
            PanelDefinition(
                title="Cluster Health",
                data_source_key="cluster_health",
                visualization_type="health_grid",
                required_role="operator",
            ),
            PanelDefinition(
                title="Pod Status",
                data_source_key="pod_status",
                visualization_type="table",
                required_role="operator",
            ),
            PanelDefinition(
                title="Node Metrics",
                data_source_key="node_metrics",
                visualization_type="metric_chart",
                required_role="operator",
            ),
            PanelDefinition(
                title="Service Map",
                data_source_key="service_map",
                visualization_type="table",
                required_role="viewer",
            ),
        ]

    def get_adapter_metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name="kubernetes-adapter",
            version="1.0.0",
            supported_runtime_types=["kubernetes"],
            description="Observability adapter for Kubernetes pod, node, and service health monitoring",
        )

    def emit_health_event(self, severity: Severity, message: str) -> MeshHealthEvent:
        return MeshHealthEvent(
            entity_id=self._entity_id,
            domain=self._domain,
            severity=severity,
            message=message,
            timestamp=datetime.now(timezone.utc),
        )
