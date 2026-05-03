"""Scaffold Command — generates a new adapter package with required stubs.

Creates a complete adapter package with:
- ObservabilityAdapterInterface implementation stubs
- MeshHealthEvent emitter
- README template
- Test harness integration
"""

from __future__ import annotations

import os
from pathlib import Path


def scaffold_adapter(
    adapter_name: str,
    output_dir: str = ".",
    runtime_type: str = "server",
    description: str = "",
) -> str:
    """Generate a new adapter package with required stubs.

    Args:
        adapter_name: Name of the adapter (e.g., "my-custom-adapter").
        output_dir: Directory to create the adapter package in.
        runtime_type: The runtime_type this adapter supports.
        description: Human-readable description of the adapter.

    Returns:
        Path to the created adapter package directory.
    """
    # Normalize name for Python module
    module_name = adapter_name.replace("-", "_").replace(" ", "_").lower()
    class_name = "".join(word.capitalize() for word in adapter_name.replace("-", " ").replace("_", " ").split())
    class_name += "Adapter"

    if not description:
        description = f"Custom observability adapter for {adapter_name}"

    pkg_dir = Path(output_dir) / module_name
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # __init__.py
    init_content = f'"""OpenMesh Adapter: {adapter_name}"""\n\nfrom .adapter import {class_name}\n\n__all__ = ["{class_name}"]\n'
    (pkg_dir / "__init__.py").write_text(init_content, encoding="utf-8")

    # adapter.py
    adapter_content = f'''"""{adapter_name} - Custom observability adapter.

{description}
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


class {class_name}(ObservabilityAdapterInterface):
    """{description}"""

    def __init__(self, entity_id: str = "", domain: str = "") -> None:
        self._entity_id = entity_id
        self._domain = domain

    def get_health_checks(self) -> List[HealthCheck]:
        """Return health check results for this adapter\'s domain."""
        return [
            HealthCheck(
                name="default_check",
                status=HealthStatus.HEALTHY,
                detail="Default health check - customize for your domain",
            ),
        ]

    def get_metrics(self) -> List[Metric]:
        """Return current metrics for this adapter\'s domain."""
        now = datetime.now(timezone.utc)
        return [
            Metric(
                metric_name="default_metric",
                value=0.0,
                unit="count",
                timestamp=now,
            ),
        ]

    def get_panel_definitions(self) -> List[PanelDefinition]:
        """Return dashboard panel definitions for this adapter\'s domain."""
        return [
            PanelDefinition(
                title="{adapter_name} Health",
                data_source_key="health_checks",
                visualization_type="health_grid",
                required_role="operator",
            ),
            PanelDefinition(
                title="{adapter_name} Metrics",
                data_source_key="metrics",
                visualization_type="metric_chart",
                required_role="viewer",
            ),
        ]

    def get_adapter_metadata(self) -> AdapterMetadata:
        """Return metadata about this adapter."""
        return AdapterMetadata(
            name="{module_name}",
            version="1.0.0",
            supported_runtime_types=["{runtime_type}"],
            description="{description}",
        )

    def emit_health_event(
        self, severity: Severity, message: str
    ) -> MeshHealthEvent:
        """Emit a MeshHealthEvent for this adapter\'s domain."""
        return MeshHealthEvent(
            entity_id=self._entity_id,
            domain=self._domain,
            severity=severity,
            message=message,
            timestamp=datetime.now(timezone.utc),
        )
'''
    (pkg_dir / "adapter.py").write_text(adapter_content, encoding="utf-8")

    # README.md
    readme_content = f"""# {adapter_name}

{description}

## Overview

This adapter implements the `ObservabilityAdapterInterface` for the OpenMesh framework,
providing health checks, metrics, and dashboard panels for **{runtime_type}** infrastructure.

## Usage

```python
from {module_name} import {class_name}

adapter = {class_name}(entity_id="my-entity", domain="my-domain")

# Get health checks
checks = adapter.get_health_checks()

# Get metrics
metrics = adapter.get_metrics()

# Get panel definitions
panels = adapter.get_panel_definitions()
```

## Validation

Run the SDK validator to verify your adapter:

```python
from openmesh_sdk.test_harness import run_validation
from {module_name} import {class_name}

report = run_validation({class_name})
assert report.passed
```

## DomainRegistration

```yaml
domain_id: "{module_name}-domain"
runtime_type: "{runtime_type}"
observability_adapter: "{module_name}.{class_name}"
roles:
  - operator
  - viewer
tabs:
  - title: "{adapter_name} Health"
    panel_type: "health_grid"
    data_source: "health_checks"
```
"""
    (pkg_dir / "README.md").write_text(readme_content, encoding="utf-8")

    # test_adapter.py
    test_content = f'''"""Tests for {adapter_name} adapter."""

from {module_name}.adapter import {class_name}
from openmesh_sdk.validator import AdapterValidator


def test_{module_name}_passes_validation():
    """Verify the adapter passes SDK validation."""
    validator = AdapterValidator()
    report = validator.validate({class_name})
    assert report.passed, f"Validation failed: {{report.failures}}"


def test_{module_name}_health_checks():
    """Verify health checks return valid data."""
    adapter = {class_name}()
    checks = adapter.get_health_checks()
    assert len(checks) > 0


def test_{module_name}_metrics():
    """Verify metrics return valid data."""
    adapter = {class_name}()
    metrics = adapter.get_metrics()
    assert len(metrics) > 0


def test_{module_name}_metadata():
    """Verify adapter metadata is correct."""
    adapter = {class_name}()
    meta = adapter.get_adapter_metadata()
    assert meta.name == "{module_name}"
    assert "{runtime_type}" in meta.supported_runtime_types
'''
    (pkg_dir / "test_adapter.py").write_text(test_content, encoding="utf-8")

    return str(pkg_dir)
