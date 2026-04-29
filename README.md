# OpenMesh Framework (OMA)

**A Data Mesh Admin & Observability Control Plane with RBAC-governed domain observability.**

Most systems treat observability as global. OMA scopes it per role, per LOB, per domain:

```
observability = function(role, LOB_scope, domain)
```

The Governance Engine evaluates this function on every request, tying RBAC, LOB hierarchy, and Domain registration into a single policy evaluation — no stale caches, no global visibility leaks.

## What OMA Does

OMA is a **control plane** for admin dashboards and observability. It manages:

- Who can see what (RBAC + LOB-scoped governance)
- How observability data is organized (4-tier hierarchy: Entity → Domain → Product_Family → Resource)
- How adapters plug in (abstract interface + runtime-specific implementations)
- How dashboards compose (core panels + adapter-provided panels, filtered by role)

**What OMA is NOT:** OMA does not deploy, host, or manage your application. Product deployment is a separate concern. Adapters declare what observability data to surface — they don't manage the underlying infrastructure.

## Quick Start

### Install the Core Governance Layer (Python)

```bash
pip install git+https://github.com/{org}/openmesh-framework.git#subdirectory=packages/core
```

### Install the Observability Layer (Python)

```bash
pip install git+https://github.com/{org}/openmesh-framework.git#subdirectory=packages/observability
```

### Install the Admin Shell UI (npm)

```bash
npm install @openmesh/admin-shell-ui
```

### Development Setup

```bash
# Clone the repo
git clone https://github.com/{org}/openmesh-framework.git
cd openmesh-framework

# Python setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Node setup
npm install

# Run tests
pytest                # Python tests
npm test              # TypeScript tests
```

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
│   │   └── governance_engine/         # Policy evaluation orchestrator
│   │
│   ├── observability/                 # Observability Layer (Python)
│   │   ├── interface/                 # Base adapter ABC + MeshHealthEvent schema
│   │   └── adapters/
│   │       ├── server/                # EC2/Docker/Nginx/Gunicorn health
│   │       ├── serverless/            # Lambda/AppSync/DynamoDB/KMS health
│   │       ├── kubernetes/            # K8s pod/node/service health
│   │       ├── gpu/                   # GPU/render pipeline health
│   │       └── streaming/             # Video/media streaming health
│   │
│   ├── sdk/
│   │   ├── python/                    # Python SDK for adapter development
│   │   └── typescript/                # TypeScript type definitions + guards
│   │
│   └── admin-shell-ui/               # React/Next.js Dashboard Frame
│       ├── src/layout/                # Sidebar, tenant switcher, breadcrumbs
│       └── src/visualization/         # Health grids, severity charts, timelines
│
├── examples/                          # Business consumption examples
│   ├── empirical-ais-config/          # Empirical-AiS domain registrations
│   └── sports-avatar-config/          # Sports-Avatar domain registrations
│
├── docs/
│   ├── architecture/                  # Architecture overview
│   ├── getting-started/               # Quickstart guide
│   ├── adapter-development/           # Adapter development patterns
│   └── governance-model/              # Governance formula explained
│
└── tests/                             # Test suite
```

## How Businesses Consume OMA

Businesses do **not** fork or live inside this monorepo. They install OMA as a dependency and provide their own configuration:

```yaml
# your-business/openmesh-config/domains/my-domain.yaml
domain_id: "my-server-infra"
runtime_type: "server"
observability_adapter: "my_adapters.ServerAdapter"
entity_id: "my-company"
lob_id: "p-lob-infrastructure"
roles:
    - superuser
    - admin
    - operator
tabs:
    - title: "Server Health"
      panel_type: "health_grid"
      data_source: "health_checks"
```

See the `examples/` directory for complete consumption patterns.

## 4-Tier Data Model

OMA uses a generic hierarchy that models any business:

| Layer | Generic Name   | Example (Empirical-AiS)  | Example (Sports-Avatar)   |
| ----- | -------------- | ------------------------ | ------------------------- |
| Root  | Entity         | Empirical-AiS Inc.       | Sports-Avatar LLC         |
| LOB   | Domain         | Cybersecurity (DeCMMC)   | Animation Engine          |
| Group | Product_Family | Plug-N-Play (PNP)        | Cric-Avatar               |
| Node  | Resource       | EC2 Instance / S3 Bucket | Blender Render Node / GPU |

## Documentation

- [Architecture Overview](docs/architecture/README.md)
- [Getting Started](docs/getting-started/README.md)
- [Adapter Development](docs/adapter-development/README.md)
- [Governance Model](docs/governance-model/README.md)
- [Contributing](CONTRIBUTING.md)

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
