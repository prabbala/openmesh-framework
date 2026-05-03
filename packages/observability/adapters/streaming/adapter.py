"""Streaming Adapter — Video and media streaming health observability.

Reference adapter demonstrating the ObservabilityAdapterInterface
for video/media streaming infrastructure monitoring.
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


class StreamingAdapter(ObservabilityAdapterInterface):
    """Observability adapter for streaming infrastructure.

    Monitors video transcoding pipelines, CDN edge health,
    stream quality metrics, and viewer session counts.
    """

    def __init__(self, entity_id: str = "", domain: str = "") -> None:
        self._entity_id = entity_id
        self._domain = domain

    def get_health_checks(self) -> List[HealthCheck]:
        return [
            HealthCheck(
                name="transcoder_status",
                status=HealthStatus.HEALTHY,
                detail="All transcoding pipelines active, 0 failed jobs",
            ),
            HealthCheck(
                name="cdn_edge_health",
                status=HealthStatus.HEALTHY,
                detail="98/100 CDN edge nodes healthy",
            ),
            HealthCheck(
                name="origin_server",
                status=HealthStatus.HEALTHY,
                detail="Origin server responding, latency < 50ms",
            ),
            HealthCheck(
                name="drm_license_server",
                status=HealthStatus.HEALTHY,
                detail="DRM license server operational",
            ),
        ]

    def get_metrics(self) -> List[Metric]:
        now = datetime.now(timezone.utc)
        return [
            Metric(metric_name="active_streams", value=12500.0, unit="count", timestamp=now),
            Metric(metric_name="bitrate_avg", value=4.5, unit="Mbps", timestamp=now),
            Metric(metric_name="buffer_ratio", value=0.02, unit="ratio", timestamp=now),
            Metric(metric_name="startup_time_avg", value=1.2, unit="seconds", timestamp=now),
            Metric(metric_name="cdn_cache_hit_ratio", value=0.94, unit="ratio", timestamp=now),
            Metric(metric_name="transcode_queue", value=8.0, unit="count", timestamp=now),
            Metric(metric_name="error_rate", value=0.001, unit="ratio", timestamp=now),
            Metric(metric_name="concurrent_viewers", value=45000.0, unit="count", timestamp=now),
        ]

    def get_panel_definitions(self) -> List[PanelDefinition]:
        return [
            PanelDefinition(
                title="Stream Health",
                data_source_key="stream_health",
                visualization_type="health_grid",
                required_role="operator",
            ),
            PanelDefinition(
                title="Streaming Metrics",
                data_source_key="stream_metrics",
                visualization_type="metric_chart",
                required_role="operator",
            ),
            PanelDefinition(
                title="CDN Performance",
                data_source_key="cdn_metrics",
                visualization_type="metric_chart",
                required_role="operator",
            ),
            PanelDefinition(
                title="Viewer Analytics",
                data_source_key="viewer_analytics",
                visualization_type="stat_card",
                required_role="viewer",
            ),
        ]

    def get_adapter_metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name="streaming-adapter",
            version="1.0.0",
            supported_runtime_types=["streaming"],
            description="Observability adapter for video and media streaming health monitoring",
        )

    def emit_health_event(self, severity: Severity, message: str) -> MeshHealthEvent:
        return MeshHealthEvent(
            entity_id=self._entity_id,
            domain=self._domain,
            severity=severity,
            message=message,
            timestamp=datetime.now(timezone.utc),
        )
