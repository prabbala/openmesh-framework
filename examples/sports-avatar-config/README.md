# Sports-Avatar LLC — Example Configuration

This directory demonstrates how **Sports-Avatar LLC** consumes the OpenMesh framework
as a dependency and registers its business domains for observability.

## Entity Structure (4-Tier Model)

```
Entity: Sports-Avatar LLC
├── Domain: Animation Engine            → runtime_type: gpu
│   ├── Product_Family: Render Farm
│   │   └── Resource: GPU render nodes (A100)
│   └── Product_Family: Asset Pipeline
│       └── Resource: Blender processing nodes
└── Domain: Cric-Avatar                 → runtime_type: streaming
    ├── Product_Family: Live Streaming
    │   └── Resource: CDN edge nodes
    └── Product_Family: Avatar Delivery
        └── Resource: Transcoding pipeline
```

## Domain Registrations

| File                    | Domain           | Runtime Type | Adapter          |
| ----------------------- | ---------------- | ------------ | ---------------- |
| `animation-engine.yaml` | Animation Engine | gpu          | GPUAdapter       |
| `cric-avatar.yaml`      | Cric-Avatar      | streaming    | StreamingAdapter |

## LOB Mapping

| LOB ID              | Category | Domains          |
| ------------------- | -------- | ---------------- |
| `p-lob-animation`   | P_LOB    | Animation Engine |
| `p-lob-cric-avatar` | P_LOB    | Cric-Avatar      |

## How to Use

1. Install the framework: `pip install openmesh-core`
2. Place these YAML files in your project's config directory
3. Load registrations on startup:

```python
from packages.core.domain_registry.serialization import deserialize_from_yaml
from packages.core.domain_registry.registry import DomainRegistry

registry = DomainRegistry()

with open("animation-engine.yaml") as f:
    reg = deserialize_from_yaml(f.read())
    registry.register(reg)
```
