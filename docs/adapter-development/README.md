# Adapter Development Guide

## Overview

Adapters are the bridge between your infrastructure and the OpenMesh dashboard.
Each adapter implements the `ObservabilityAdapterInterface` to provide health checks,
metrics, and dashboard panels for a specific runtime type.

## Adapter Interface

Every adapter must implement four methods:

```python
from packages.observability.interface.adapter import ObservabilityAdapterInterface

class MyAdapter(ObservabilityAdapterInterface):
    def get_health_checks(self) -> List[HealthCheck]:
        """Return health probe results."""
        ...

    def get_metrics(self) -> List[Metric]:
        """Return current metric data points."""
        ...

    def get_panel_definitions(self) -> List[PanelDefinition]:
        """Return dashboard panel specifications."""
        ...

    def get_adapter_metadata(self) -> AdapterMetadata:
        """Return adapter name, version, runtime types, description."""
        ...
```

## Using the Scaffold Command

The fastest way to create a new adapter:

```python
from openmesh_sdk.scaffold import scaffold_adapter

scaffold_adapter(
    adapter_name="my-custom-adapter",
    output_dir="./adapters",
    runtime_type="server",
    description="Monitors my custom infrastructure"
)
```

This generates:

- `my_custom_adapter/__init__.py` — Package init with exports
- `my_custom_adapter/adapter.py` — Interface implementation stubs
- `my_custom_adapter/README.md` — Documentation template
- `my_custom_adapter/test_adapter.py` — Test harness integration

## Emitting MeshHealthEvents

Adapters emit telemetry using the universal `MeshHealthEvent` schema:

```python
from packages.observability.interface.adapter import MeshHealthEvent, Severity
from datetime import datetime, timezone

event = MeshHealthEvent(
    entity_id="my-entity",
    domain="my-domain",
    severity=Severity.WARNING,
    message="CPU utilization above 80%",
    timestamp=datetime.now(timezone.utc),
    metadata={"cpu_percent": 82.5}
)
```

Or use the SDK helpers:

```python
from openmesh_sdk.helpers import warning_event

event = warning_event("my-entity", "my-domain", "CPU utilization above 80%")
```

## Validation

Always validate your adapter before publishing:

```python
from openmesh_sdk.validator import AdapterValidator

validator = AdapterValidator()
report = validator.validate(MyAdapter)

for result in report.results:
    print(f"{'PASS' if result.passed else 'FAIL'}: {result.method_name}")
```

## Reference Adapters

Study the reference adapters in `packages/observability/adapters/`:

| Adapter       | Runtime Type | Monitors                         |
| ------------- | ------------ | -------------------------------- |
| `server/`     | server       | EC2, Docker, Nginx, Gunicorn     |
| `serverless/` | serverless   | Lambda, AppSync, DynamoDB, KMS   |
| `kubernetes/` | kubernetes   | Pod, node, service health        |
| `gpu/`        | gpu          | GPU utilization, render pipeline |
| `streaming/`  | streaming    | Video/media streaming            |

## Fault Isolation

If your adapter raises an exception, the framework catches it gracefully:

1. The exception is logged to the Audit Engine
2. Your adapter's status is set to "degraded"
3. Other adapters continue operating normally
4. The dashboard shows a degraded indicator for your panels
