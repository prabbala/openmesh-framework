# Getting Started

## Prerequisites

- Python 3.10+
- Node.js 18+ (for Admin Shell UI)
- pip or poetry for Python dependency management

## Installation

### Python Core (Backend)

```bash
pip install openmesh-core
```

Or install from source:

```bash
pip install git+https://github.com/empirical-ais/openmesh-framework.git#subdirectory=packages/core
```

### Admin Shell UI (Frontend)

```bash
npm install @openmesh/admin-shell-ui
```

## Quick Start

### 1. Define Your Domain Registration

Create a YAML file describing your business domain:

```yaml
# my-domain.yaml
domain_id: "my-service"
runtime_type: "server"
observability_adapter: "my_adapter.MyAdapter"
entity_id: "my-company"
lob_id: "p-lob-engineering"
roles:
    - superuser
    - admin
    - operator
tabs:
    - title: "Service Health"
      panel_type: "health_grid"
      data_source: "health_checks"
```

### 2. Implement Your Adapter

```python
from packages.observability.interface.adapter import (
    ObservabilityAdapterInterface,
    HealthCheck, HealthStatus,
    Metric, PanelDefinition, AdapterMetadata,
)
from datetime import datetime, timezone

class MyAdapter(ObservabilityAdapterInterface):
    def get_health_checks(self):
        return [
            HealthCheck(name="api_status", status=HealthStatus.HEALTHY,
                       detail="API responding normally")
        ]

    def get_metrics(self):
        return [
            Metric(metric_name="requests_per_sec", value=150.0,
                  unit="req/s", timestamp=datetime.now(timezone.utc))
        ]

    def get_panel_definitions(self):
        return [
            PanelDefinition(title="API Health", data_source_key="health",
                          visualization_type="health_grid", required_role="operator")
        ]

    def get_adapter_metadata(self):
        return AdapterMetadata(name="my-adapter", version="1.0.0",
                             supported_runtime_types=["server"],
                             description="My custom adapter")
```

### 3. Register and Run

```python
from packages.core.domain_registry.registry import DomainRegistry
from packages.core.domain_registry.serialization import deserialize_from_yaml

registry = DomainRegistry()

with open("my-domain.yaml") as f:
    registration = deserialize_from_yaml(f.read())
    registry.register(registration)
```

### 4. Validate Your Adapter

```python
from openmesh_sdk.validator import AdapterValidator

validator = AdapterValidator()
report = validator.validate(MyAdapter)
assert report.passed
```

## Using the Admin Shell UI

```tsx
import {
    Sidebar,
    TenantSwitcher,
    HealthStatusGrid,
} from "@openmesh/admin-shell-ui";

function Dashboard() {
    return (
        <div>
            <Sidebar items={navItems} userRole="operator" />
            <TenantSwitcher tenants={tenants} onTenantSwitch={handleSwitch} />
            <HealthStatusGrid items={healthChecks} title="Service Health" />
        </div>
    );
}
```
