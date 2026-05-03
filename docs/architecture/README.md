# Architecture Overview

## OpenMesh Admin and Observability Management Architecture (OMA)

OMA is an open-source admin dashboard management and observability control plane. Its core innovation is **governed observability**:

```
observability = function(role, LOB_scope, domain)
```

Unlike systems that treat observability as global, OMA scopes it per role, per LOB, per domain through a Governance Engine.

## Monorepo Structure

```
openmesh-framework/
├── packages/
│   ├── core/                    # Core Governance Layer (Python)
│   │   ├── rbac/                # Role-based access control
│   │   ├── tenant/              # Tenant lifecycle management
│   │   ├── lob/                 # LOB hierarchy and scope resolution
│   │   ├── audit/               # Immutable audit engine
│   │   ├── auth/                # Auth provider abstraction
│   │   ├── dashboard_shell/     # Panel composition engine
│   │   ├── domain_registry/     # Domain registration and 4-tier model
│   │   └── governance_engine/   # Policy evaluation orchestrator
│   ├── observability/           # Observability Layer (Python)
│   │   ├── interface/           # Adapter ABC + MeshHealthEvent schema
│   │   └── adapters/            # Reference adapters
│   │       ├── server/          # EC2, Docker, Nginx, Gunicorn
│   │       ├── serverless/      # Lambda, AppSync, DynamoDB, KMS
│   │       ├── kubernetes/      # Pod, node, service health
│   │       ├── gpu/             # GPU utilization, render pipeline
│   │       └── streaming/       # Video/media streaming
│   ├── sdk/
│   │   ├── python/              # Python SDK for adapter development
│   │   └── typescript/          # TypeScript SDK for type definitions
│   └── admin-shell-ui/          # React dashboard frame
│       └── src/
│           ├── layout/          # Sidebar, TenantSwitcher, Breadcrumbs
│           └── visualization/   # HealthStatusGrid, SeverityChart, etc.
├── examples/                    # Business consumption examples
│   ├── empirical-ais-config/    # Empirical-AiS domain registrations
│   └── sports-avatar-config/    # Sports-Avatar domain registrations
├── docs/                        # Documentation
└── tests/                       # Property-based and unit tests
```

## 4-Tier Data Model

| Layer | Generic Name   | Example (Empirical-AiS)  | Example (Sports-Avatar)   |
| ----- | -------------- | ------------------------ | ------------------------- |
| Root  | Entity         | Empirical-AiS Inc.       | Sports-Avatar LLC         |
| LOB   | Domain         | Cybersecurity (DeCMMC)   | Animation Engine          |
| Group | Product_Family | Plug-N-Play (PNP)        | Cric-Avatar               |
| Node  | Resource       | EC2 Instance / S3 Bucket | Blender Render Node / GPU |

## Request Flow

1. User sends request with auth token
2. Auth Provider validates token and extracts claims
3. Governance Engine evaluates `observability = function(role, LOB_scope, domain)`
4. RBAC Engine checks role permissions
5. Scope Resolver resolves effective LOB scope
6. Domain Registry returns matching domains
7. Dashboard Shell composes authorized panels
8. Adapters provide health checks, metrics, and panel data
9. User sees only the observability data they are authorized to view

## Key Design Decisions

- **In-memory policy evaluation**: Sub-50ms latency, no database lookups per request
- **YAML for config, JSON for telemetry**: YAML is human-friendly for version-controlled configs; JSON is machine-friendly for telemetry
- **Framework as dependency**: Businesses `pip install` / `npm install` the framework, never live inside the monorepo
- **Adapter fault isolation**: Adapter exceptions are caught, logged, and degraded — the framework never crashes
