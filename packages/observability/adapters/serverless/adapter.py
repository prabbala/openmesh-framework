"""Serverless Adapter — Lambda, AppSync, DynamoDB, KMS health observability.

Reference adapter demonstrating the ObservabilityAdapterInterface
for serverless infrastructure monitoring.
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


class ServerlessAdapter(ObservabilityAdapterInterface):
    """Observability adapter for serverless infrastructure.

    Monitors Lambda functions, AppSync APIs, DynamoDB tables,
    and KMS key operations.
    """

    def __init__(self, entity_id: str = "", domain: str = "") -> None:
        self._entity_id = entity_id
        self._domain = domain

    def get_health_checks(self) -> List[HealthCheck]:
        return [
            HealthCheck(
                name="lambda_invocations",
                status=HealthStatus.HEALTHY,
                detail="Lambda functions executing within timeout limits",
            ),
            HealthCheck(
                name="appsync_resolver",
                status=HealthStatus.HEALTHY,
                detail="AppSync resolvers responding normally",
            ),
            HealthCheck(
                name="dynamodb_capacity",
                status=HealthStatus.HEALTHY,
                detail="DynamoDB read/write capacity within provisioned limits",
            ),
            HealthCheck(
                name="kms_key_status",
                status=HealthStatus.HEALTHY,
                detail="KMS encryption keys enabled and accessible",
            ),
        ]

    def get_metrics(self) -> List[Metric]:
        now = datetime.now(timezone.utc)
        return [
            Metric(metric_name="lambda_invocations", value=15420.0, unit="count", timestamp=now),
            Metric(metric_name="lambda_duration_avg", value=120.0, unit="ms", timestamp=now),
            Metric(metric_name="lambda_errors", value=3.0, unit="count", timestamp=now),
            Metric(metric_name="lambda_throttles", value=0.0, unit="count", timestamp=now),
            Metric(metric_name="dynamodb_read_capacity", value=75.0, unit="percent", timestamp=now),
            Metric(metric_name="dynamodb_write_capacity", value=45.0, unit="percent", timestamp=now),
            Metric(metric_name="appsync_latency_p99", value=85.0, unit="ms", timestamp=now),
            Metric(metric_name="kms_requests", value=890.0, unit="count", timestamp=now),
        ]

    def get_panel_definitions(self) -> List[PanelDefinition]:
        return [
            PanelDefinition(
                title="Lambda Health",
                data_source_key="lambda_health",
                visualization_type="health_grid",
                required_role="operator",
            ),
            PanelDefinition(
                title="Serverless Metrics",
                data_source_key="metrics",
                visualization_type="metric_chart",
                required_role="operator",
            ),
            PanelDefinition(
                title="DynamoDB Capacity",
                data_source_key="dynamodb_metrics",
                visualization_type="metric_chart",
                required_role="operator",
            ),
            PanelDefinition(
                title="AppSync Performance",
                data_source_key="appsync_metrics",
                visualization_type="metric_chart",
                required_role="viewer",
            ),
        ]

    def get_adapter_metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name="serverless-adapter",
            version="1.0.0",
            supported_runtime_types=["serverless"],
            description="Observability adapter for Lambda, AppSync, DynamoDB, and KMS serverless infrastructure",
        )

    def emit_health_event(self, severity: Severity, message: str) -> MeshHealthEvent:
        return MeshHealthEvent(
            entity_id=self._entity_id,
            domain=self._domain,
            severity=severity,
            message=message,
            timestamp=datetime.now(timezone.utc),
        )
