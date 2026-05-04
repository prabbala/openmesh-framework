# Step-By-Step Instructions To Implement OpenMesh Framework For YOUR Organization To Embrace AI, Collaborate, and Innovate

## What is the OpenMesh Framework (OM-FW)?

The OpenMesh Framework is an open-source Data Mesh Admin and Observability Control Plane. It scopes observability per role, per line of business, per domain:

```
observability = function(role, LOB_scope, domain)
```

Any organization can inherit OM-FW as a dependency and build a private Mesh Architecture on top of it — with RBAC-governed dashboards, immutable audit trails, multi-tenant isolation, and pluggable observability adapters.

## Architecture Overview

```
YOUR-ORG-Mesh-Architecture (private)
    └── depends on → OpenMesh Framework (public)

Your CRM / Product Repo (private)
    └── depends on → YOUR-ORG-Mesh-Architecture (private)
        └── depends on → OpenMesh Framework (public)
```

### Real-World Example (Empirical-AiS Inc.)

```
prabbala/openmesh-framework     PUBLIC    ← Generic framework (OM-FW)
prabbala/ea-ma                  PRIVATE   ← EAIS-Mesh-Architecture
prabbala/plug-n-play-crm-ai    PRIVATE   ← BAI CRM-AI product
```

### 4-Tier Data Model

| Layer | Generic Name   | Your Organization Example          |
|-------|----------------|------------------------------------|
| Root  | Entity         | Your Company Inc.                  |
| LOB   | Domain/Product | Your Product A, Your Product B     |
| Group | ProductFamily  | Product types / verticals          |
| Node  | Resource       | EC2 instances, Lambda functions    |

---

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- A GitHub account (or any Git hosting)

---

## Step 1: Install the OpenMesh Framework

The framework is public. Anyone can install it.

```bash
# Option A: Install directly from GitHub
pip install git+https://github.com/prabbala/openmesh-framework.git

# Option B: Clone and install locally (recommended for development)
cd ~/apps
git clone https://github.com/prabbala/openmesh-framework.git
cd openmesh-framework
python3 -m pip install -e ".[dev]"

# Verify installation — all 182 tests should pass
python3 -m pytest tests/ -q
```

What you get:
- RBAC engine with 7 default roles (superuser, admin, operator, auditor, manager, staff, viewer)
- Governance engine: real-time policy evaluation, no stale caches
- Tenant management with data isolation and suspension
- LOB hierarchy (I-LOB / P-LOB) with scope resolution
- Immutable append-only audit engine
- JWT authentication provider
- Dashboard shell with panel composition and adapter fault isolation
- 5 reference observability adapters (server, serverless, kubernetes, gpu, streaming)
- PnP orchestrator that bootstraps everything from YAML configs
- Python SDK (scaffold, validate, test harness)
- TypeScript SDK (types, guards, validation)
- React admin shell UI components

---

## Step 2: Create Your Organization's Mesh Architecture

This is your private repo that extends OM-FW with your business-specific logic.

### 2.1 Create the repo structure

```bash
cd ~/apps
mkdir your-org-ma
cd your-org-ma
git init
```

Create this directory structure:

```
your-org-ma/
├── config/                    # Your domain YAML registrations
│   └── your-product.yaml
├── your_org_ma/               # Python package
│   ├── __init__.py
│   ├── main.py                # Entry point
│   ├── preset.py              # PnPConfig factory
│   └── pnp/
│       ├── __init__.py
│       └── pnp_main.py        # Your extended PnPMain
├── tests/
│   ├── __init__.py
│   └── test_your_org.py
├── pyproject.toml
├── .gitignore
└── README.md
```

### 2.2 Create pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "your-org-ma"
version = "1.0.0"
description = "Your Organization Mesh Architecture on OpenMesh Framework"
license = {text = "Proprietary"}
requires-python = ">=3.10"
dependencies = [
    "openmesh-framework @ git+https://github.com/prabbala/openmesh-framework.git",
]

[project.optional-dependencies]
dev = ["pytest>=7.4"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.setuptools.packages.find]
include = ["your_org_ma*"]
```

### 2.3 Create your domain YAML config

Create `config/your-product.yaml`:

```yaml
domain_id: "your-product"
runtime_type: "server"
observability_adapter: "packages.observability.adapters.server.adapter.ServerAdapter"
entity_id: "your-org"
lob_id: "p-lob-your-product"
roles:
  - superuser
  - admin
  - operator
  - viewer
tabs:
  - title: "Health"
    panel_type: "health_grid"
    data_source: "health_checks"
  - title: "Metrics"
    panel_type: "metric_chart"
    data_source: "metrics"
metadata:
  product_name: "Your Product"
  version: "1.0.0"

product_families:
  - family_id: "your-vertical-a"
    name: "Vertical A"
    description: "First product vertical"
  - family_id: "your-vertical-b"
    name: "Vertical B"
    description: "Second product vertical"
```

### 2.4 Create the preset (PnPConfig factory)

Create `your_org_ma/preset.py`:

```python
import os
from packages.core.pnp import PnPConfig, PnPMain

def create_your_org_pnp(
    jwt_secret="change-me-in-production",
    config_dir=None,
    log_level="INFO",
    auto_bootstrap=True,
):
    if config_dir is None:
        config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
        )
    config = PnPConfig(
        entity_id="your-org",
        entity_name="Your Organization Inc.",
        config_dir=config_dir,
        jwt_secret=jwt_secret,
        tenant_name="Your Org Primary",
        log_level=log_level,
    )
    pnp = PnPMain(config)
    if auto_bootstrap:
        pnp.bootstrap()
    return pnp
```

### 2.5 Create the entry point

Create `your_org_ma/main.py`:

```python
from .preset import create_your_org_pnp

def main():
    pnp = create_your_org_pnp(jwt_secret="dev-secret", log_level="INFO")
    print(f"Bootstrapped: {len(pnp.loaded_domains)} domains")
    for domain in pnp.loaded_domains:
        families = pnp.hierarchy.list_product_families(domain_id=domain.domain_id)
        print(f"  Product: {domain.domain_id}")
        for f in families:
            print(f"    product_type: {f.name}")

if __name__ == "__main__":
    main()
```

### 2.6 Install and run

```bash
# Install OM-FW (if not already installed)
pip install -e ~/apps/openmesh-framework

# Install your org's MA
pip install -e ".[dev]"

# Run
python -m your_org_ma.main

# Test
python3 -m pytest tests/ -q
```

### 2.7 Push to GitHub (private)

```bash
# Create a PRIVATE repo on GitHub: github.com/your-org/your-org-ma
git add -A
git commit -m "Your-Org-MA v1.0.0"
git remote add origin https://github.com/your-org/your-org-ma.git
git push -u origin main
```

---

## Step 3: Wire Your Product Repo to Use Your Mesh Architecture

If you have an existing product repo (like a CRM, analytics platform, etc.), wire it to use your Mesh Architecture.

### 3.1 Create the integration directory

In your product repo, create an `openmesh-framework/` directory with these files:

`openmesh-framework/bootstrap.py`:

```python
import os
from your_org_ma.preset import create_your_org_pnp

_pnp = None

def get_pnp(environment="local", jwt_secret=None):
    global _pnp
    if _pnp is not None:
        return _pnp
    secret = jwt_secret or os.environ.get("MA_JWT_SECRET", "dev-secret")
    log_level = "WARNING" if environment == "production" else "INFO"
    _pnp = create_your_org_pnp(jwt_secret=secret, log_level=log_level)
    return _pnp
```

### 3.2 Install the dependency chain

```bash
# Install in order — OM-FW first, then your MA, then your product
pip install -e ~/apps/openmesh-framework
pip install -e ~/apps/your-org-ma

# Verify
python openmesh-framework/verify.py
```

### 3.3 Use in your product code

```python
from openmesh_framework.bootstrap import get_pnp

pnp = get_pnp()

# Register a user
token = pnp.register_user(
    email="user@your-org.com",
    password="secure-password",
    user_id="user-1",
    role="operator",
    lob_assignments=["p-lob-your-product"],
)

# Render dashboard
panels = pnp.render_dashboard(token=token)

# Check governance
result = pnp.evaluate_access(
    user_id="user-1", role="operator",
    lob_assignments=["p-lob-your-product"],
)
print(f"Authorized domains: {result.authorized_domains}")
```

---

## Step 4: Extend with Business-Specific Logic (Optional)

For advanced use cases, subclass `PnPMain` to add your own business logic.

### Example: Email domain enforcement

```python
from packages.core.pnp import PnPMain, PnPConfig

class YourOrgPnPMain(PnPMain):
    ALLOWED_EMAIL_DOMAINS = {"your-org.com"}

    def register_user(self, email, password, user_id, role=None, **kwargs):
        domain = email.rsplit("@", 1)[1].lower()
        if domain not in self.ALLOWED_EMAIL_DOMAINS:
            raise ValueError(f"@{domain} not allowed. Use @your-org.com")
        role = role or "operator"  # default role
        return super().register_user(email, password, user_id, role=role, **kwargs)
```

### Example: Custom RBAC roles

```python
from packages.core.rbac.models import Permission

class YourOrgPnPMain(PnPMain):
    def bootstrap(self):
        super().bootstrap()
        self._rbac.define_custom_role("data_analyst", {
            Permission("dashboard", "read"),
            Permission("metrics", "read"),
            Permission("observability", "read"),
        })
```

### Example: Product vertical management

```python
from packages.core.domain_registry.models import ProductFamily

# Add a new product vertical at runtime
family = ProductFamily(
    family_id="your-new-vertical",
    domain_id="your-product",
    name="New Vertical",
    description="A new product type",
)
pnp.hierarchy.create_product_family(family)
```

---

## Step 5: Deploy to Production

### Environment variables

```bash
export MA_ENVIRONMENT=production
export MA_JWT_SECRET=your-production-secret-here
```

### Production checklist

1. Change the JWT secret from the default — never use `dev-secret` in production
2. Set `log_level="WARNING"` for production
3. Enable email domain enforcement if applicable
4. Verify all tests pass: `python3 -m pytest tests/ -q`
5. Run the verify script: `python openmesh-framework/verify.py`

---

## What Each Layer Provides

### OpenMesh Framework (public, community)

| Component | What It Does |
|-----------|-------------|
| RBAC Engine | Role-based access with dual-path evaluation (role OR group) |
| Governance Engine | Real-time policy evaluation: `observability = f(role, LOB, domain)` |
| Tenant Manager | Multi-tenant isolation with suspension support |
| LOB Hierarchy | I-LOB / P-LOB scope resolution |
| Audit Engine | Immutable append-only audit trail |
| Auth Provider | JWT authentication (swappable for Cognito, Auth0, etc.) |
| Dashboard Shell | Panel composition with adapter fault isolation |
| Domain Registry | 4-tier hierarchy with referential integrity |
| PnP Orchestrator | Bootstrap everything from YAML configs |
| Adapters | Server, Serverless, Kubernetes, GPU, Streaming |
| SDKs | Python (scaffold, validate) + TypeScript (types, guards) |

### Your Mesh Architecture (private, your org)

| Component | What It Does |
|-----------|-------------|
| Preset | Pre-configured PnPConfig for your entity |
| Custom PnPMain | Email enforcement, custom roles, business logic |
| Domain YAMLs | Your products with product_type verticals |
| Tests | Your org-specific test coverage |

### Your Product Repo (private, your product)

| Component | What It Does |
|-----------|-------------|
| bootstrap.py | Singleton PnP instance with env var support |
| verify.py | Full chain verification script |
| Your app code | Uses `get_pnp()` for auth, governance, dashboards |

---

## Quick Reference: Key APIs

```python
from packages.core.pnp import PnPMain, PnPConfig

# Bootstrap
pnp = PnPMain(PnPConfig(entity_id="x", entity_name="X", config_dir="config/", jwt_secret="s"))
pnp.bootstrap()

# User management
token = pnp.register_user(email="u@x.com", password="p", user_id="u1", role="operator", lob_assignments=["lob1"])
token = pnp.authenticate("u@x.com", "p")

# Governance
result = pnp.evaluate_access(user_id="u1", role="operator", lob_assignments=["lob1"])
# result.authorized_domains, result.is_unrestricted

# Dashboard
panels = pnp.render_dashboard(token=token)
# or: panels = pnp.render_dashboard(user_id="u1", role="operator", lob_assignments=["lob1"])

# Hierarchy
domains = pnp.hierarchy.list_domains()
families = pnp.hierarchy.list_product_families(domain_id="your-product")

# Runtime domain management
pnp.register_domain(registration)
pnp.unregister_domain("domain-id")

# Audit
records = pnp.audit.query(tenant_id=pnp.default_tenant_id)

# Direct engine access
pnp.rbac, pnp.audit, pnp.auth, pnp.governance, pnp.domain_registry
pnp.lob_store, pnp.tenant_manager, pnp.hierarchy
```

---

## Support and Community

- GitHub: https://github.com/prabbala/openmesh-framework
- Issues: https://github.com/prabbala/openmesh-framework/issues
- License: Apache 2.0 (framework is free and open source)

Your organization's Mesh Architecture and product repos remain private and proprietary. Only the framework is public.
