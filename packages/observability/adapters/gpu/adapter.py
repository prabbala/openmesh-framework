"""GPU Adapter — GPU utilization and render pipeline health observability.

Reference adapter demonstrating the ObservabilityAdapterInterface
for GPU compute and rendering infrastructure monitoring.
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


class GPUAdapter(ObservabilityAdapterInterface):
    """Observability adapter for GPU infrastructure.

    Monitors GPU utilization, VRAM usage, temperature,
    and render pipeline throughput.
    """

    def __init__(self, entity_id: str = "", domain: str = "") -> None:
        self._entity_id = entity_id
        self._domain = domain

    def get_health_checks(self) -> List[HealthCheck]:
        return [
            HealthCheck(
                name="gpu_driver",
                status=HealthStatus.HEALTHY,
                detail="NVIDIA driver 535.129.03 loaded, CUDA 12.2 available",
            ),
            HealthCheck(
                name="gpu_temperature",
                status=HealthStatus.HEALTHY,
                detail="GPU temperature 62°C (threshold: 90°C)",
            ),
            HealthCheck(
                name="vram_availability",
                status=HealthStatus.HEALTHY,
                detail="18.2 GB / 24 GB VRAM available",
            ),
            HealthCheck(
                name="render_pipeline",
                status=HealthStatus.HEALTHY,
                detail="Render pipeline active, 0 stalled jobs",
            ),
        ]

    def get_metrics(self) -> List[Metric]:
        now = datetime.now(timezone.utc)
        return [
            Metric(metric_name="gpu_utilization", value=78.0, unit="percent", timestamp=now),
            Metric(metric_name="vram_used", value=5.8, unit="GB", timestamp=now),
            Metric(metric_name="gpu_temperature", value=62.0, unit="celsius", timestamp=now),
            Metric(metric_name="gpu_power_draw", value=220.0, unit="watts", timestamp=now),
            Metric(metric_name="render_fps", value=30.0, unit="fps", timestamp=now),
            Metric(metric_name="render_queue_depth", value=4.0, unit="count", timestamp=now),
            Metric(metric_name="tensor_core_utilization", value=65.0, unit="percent", timestamp=now),
            Metric(metric_name="pcie_bandwidth", value=12.5, unit="GB/s", timestamp=now),
        ]

    def get_panel_definitions(self) -> List[PanelDefinition]:
        return [
            PanelDefinition(
                title="GPU Health",
                data_source_key="gpu_health",
                visualization_type="health_grid",
                required_role="operator",
            ),
            PanelDefinition(
                title="GPU Utilization",
                data_source_key="gpu_metrics",
                visualization_type="metric_chart",
                required_role="operator",
            ),
            PanelDefinition(
                title="Render Pipeline",
                data_source_key="render_pipeline",
                visualization_type="metric_chart",
                required_role="operator",
            ),
            PanelDefinition(
                title="VRAM Usage",
                data_source_key="vram_metrics",
                visualization_type="stat_card",
                required_role="viewer",
            ),
        ]

    def get_adapter_metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name="gpu-adapter",
            version="1.0.0",
            supported_runtime_types=["gpu"],
            description="Observability adapter for GPU utilization and render pipeline health monitoring",
        )

    def emit_health_event(self, severity: Severity, message: str) -> MeshHealthEvent:
        return MeshHealthEvent(
            entity_id=self._entity_id,
            domain=self._domain,
            severity=severity,
            message=message,
            timestamp=datetime.now(timezone.utc),
        )
