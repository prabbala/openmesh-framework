# Getting Started

This guide walks you through setting up and consuming the OpenMesh Framework.

## Prerequisites

- Python 3.10+
- Node.js 18+
- pip and npm

## Installation

### Core Governance Layer (Python)

```bash
pip install git+https://github.com/{org}/openmesh-framework.git#subdirectory=packages/core
```

### Observability Layer (Python)

```bash
pip install git+https://github.com/{org}/openmesh-framework.git#subdirectory=packages/observability
```

### Admin Shell UI (npm)

```bash
npm install @openmesh/admin-shell-ui
```

## First Steps

1. Create a DomainRegistration YAML file describing your domain
2. Implement an adapter by extending `ObservabilityAdapterInterface`
3. Register your domain with the Domain Registry
4. Configure RBAC roles for your team
5. Launch the Admin Shell UI

See the `examples/` directory for complete consumption patterns.

_Detailed walkthrough coming soon._
