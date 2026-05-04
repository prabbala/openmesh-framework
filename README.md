# OpenMesh Framework (OM-FW)

**A Data Mesh Admin & Observability Control Plane with RBAC-governed domain observability.**

Open-source community framework. Businesses inherit OM-FW as a dependency and build private downstream repos with their own domain configurations.

```
observability = function(role, LOB_scope, domain)
```

The Governance Engine evaluates this function on every request, tying RBAC, LOB hierarchy, and Domain registration into a single policy evaluation — no stale caches, no global visibility leaks.

## What OM-FW Does

OM-FW is a **control plane** for admin dashboards and observability. It manages:

- Who can see what (RBAC + LOB-scoped governance)
- How observability data is organized (4-tier hierarchy: Entity → Domain → ProductFamily → Resource)
- How adapters plug in (abstract interface + runtime-specific implementations)
- How dashboards compose (core panels + adapter-provided panels, filtered by role)
- How businesses bootstrap (PnP orchestrator wires everything from YAML configs)

**What OM-FW is NOT:** OM-FW does not deploy, host, or manage your application. Adapters declare what observability data to surface — they don't manage the underlying infrastructure.

## Quick Start

```bash
# Install as dependency
pip install git+https://github.com/prabbala/openmesh-framework.git

# Bootstrap from your YAML configs
python -c "
from packages.core.pnp import PnPMain, PnPConfig

pnp = PnPMain(PnPConfig(
    entity_id='my-company',
    entity_name='My Company',
    config_dir='path/to/your/config',
    jwt_secret='your-secret',
))
pnp.bootstrap()
print(f'Loaded {len(pnp.loaded_domains)} domains')
"
```

## Downstream Repo Pattern

OM-FW is the public framework. Businesses create **private downstream repos** that inherit it:

```
github.com/prabbala/openmesh-framework     ← PUBLIC (this repo, OM-FW)
github.com/prabbala/ea-ma                  ← PRIVATE (Empirical-AiS Mesh Architecture)
github.com/prabbala/sa-ma                  ← PRIVATE (Sports-Avatar Mesh Architecture)
```

Each downstream repo:
1. Declares `openmesh-framework` as a pip dependency
2. Contains its own `config/` directory with domain YAML files
3. Has a `preset.py` that creates a `PnPConfig` for its entity
4. Has its own tests, CI, and deployment pipeline

See `downstream/` for complete scaffolds of EA-MA and SA-MA.

## Monorepo Structure

```
openmesh-framework/
├── packages/
│   ├── core/                          # Core Governance Layer (Python)
│   │   ├── rbac/                      # Role-based access control engine
│   │   ├── tenant/                    # Tenant management + hierarchy
│   │   ├── lob/                       # LOB hierarchy (I-LOB / P-LOB)
│   │   ├── audit/                     # Immutable audit engine
│   │   ├── auth/                      # Auth provider abstraction (JWT default)
│   │   ├── dashboard_shell/           # Generic admin dashboard frame
│   │   ├── domain_registry/           # Domain registration + adapter binding
│   │   ├── governance_engine/         # Policy evaluation orchestrator
│   │   └── pnp/                       # Plug-N-Play production orchestrator
│   │
│   ├── observability/                 # Observability Layer (Python)
│   │   ├── interface/                 # Base adapter ABC + MeshHealthEvent schema
│   │   └── adapters/                  # 5 reference adapters
│   │
│   ├── sdk/
│   │   ├── python/                    # Python SDK (scaffold, validate, test)
│   │   └── typescript/                # TypeScript types + guards + validation
│   │
│   └── admin-shell-ui/               # React Dashboard Frame
│
├── examples/sample-config/            # Generic sample YAML configs
├── downstream/                        # Downstream repo scaffolds
│   ├── ea-ma/                         # Empirical-AiS Mesh Architecture
│   └── sa-ma/                         # Sports-Avatar Mesh Architecture
├── docs/                              # Documentation
└── tests/                             # Framework test suite
```

## 4-Tier Data Model

| Layer | Generic Name   | Description                                    |
| ----- | -------------- | ---------------------------------------------- |
| Root  | Entity         | Business or organization                       |
| LOB   | Domain/Product | Line of business or product                    |
| Group | ProductFamily  | Product type or vertical within a product      |
| Node  | Resource       | Individual infrastructure or application node  |

## How Businesses Consume OM-FW

```yaml
# your-repo/config/my-product.yaml
domain_id: "my-product"
runtime_type: "server"
observability_adapter: "packages.observability.adapters.server.adapter.ServerAdapter"
entity_id: "my-company"
lob_id: "p-lob-my-product"
roles: [superuser, admin, operator]
tabs:
  - title: "Health"
    panel_type: "health_grid"
    data_source: "health_checks"
metadata:
  product_name: "My Product"
product_families:
  - family_id: "my-vertical-a"
    name: "Vertical A"
  - family_id: "my-vertical-b"
    name: "Vertical B"
```

```python
# your-repo/preset.py
from packages.core.pnp import PnPMain, PnPConfig

config = PnPConfig(
    entity_id="my-company",
    entity_name="My Company Inc.",
    config_dir="config/",
    jwt_secret="production-secret",
)
pnp = PnPMain(config)
pnp.bootstrap()
```

## Documentation

- [Architecture Overview](docs/architecture/README.md)
- [Getting Started](docs/getting-started/README.md)
- [Adapter Development](docs/adapter-development/README.md)
- [Governance Model](docs/governance-model/README.md)
- [Contributing](CONTRIBUTING.md)

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
