# EAIS-Mesh-Architecture (EA-MA)

Private downstream repo for Empirical-AiS Inc. built on the
[OpenMesh Framework](https://github.com/prabbala/openmesh-framework).

## Setup

```bash
git clone git@github.com:prabbala/ea-ma.git
cd ea-ma
pip install -e ".[dev]"
python -m ea_ma.main
```

## Architecture

```
Entity: Empirical-AiS Inc.
├── Product: Business Atomic Intelligence (BAI)     ← PnP/PnP_main
│   ├── product_type: Restaurant Intelligence
│   ├── product_type: Supermarket Intelligence
│   ├── product_type: IT-Consulting-100
│   └── product_type: Realestate
├── Product: Cybersecurity-AI
│   ├── product_type: zkp-zdv
│   └── product_type: DeCMMC
├── Product: GenAI Platform
└── Product: RAG Pipeline
```

## EA-MA extends OM-FW with

- `EAISPnPMain` — subclass of `PnPMain` with EAIS-specific business logic
- `BAIVerticalManager` — add/remove/list BAI product_types at runtime
- `ProductCatalog` — aggregated product views with health and adapter status
- EAIS RBAC roles: `compliance_officer`, `bai_analyst`
- Cross-product queries: `get_user_verticals()`, `get_compliance_summary()`

## Structure

```
ea-ma/
├── config/                    # Domain YAML registrations
│   ├── bai.yaml               # BAI with 4 product_types
│   ├── cybersecurity-ai.yaml  # Cybersecurity-AI with zkp-zdv, DeCMMC
│   ├── genai-platform.yaml
│   └── rag-pipeline.yaml
├── ea_ma/
│   ├── __init__.py
│   ├── main.py                # Entry point
│   ├── preset.py              # EAISPnPMain factory
│   └── pnp/
│       ├── __init__.py
│       └── pnp_main.py        # EAISPnPMain, BAIVerticalManager, ProductCatalog
├── tests/
│   └── test_ea_ma.py
├── pyproject.toml
└── README.md
```

## Usage

```python
from ea_ma.preset import create_eais_pnp

pnp = create_eais_pnp(jwt_secret="production-secret")

# BAI vertical management
verticals = pnp.bai.list_verticals()
pnp.bai.add_vertical("bai-hospitality", "Hospitality Intelligence")

# Product catalog
snap = pnp.catalog.snapshot()
print(f"{len(snap.products)} products, {snap.total_verticals} verticals")

# Cross-product queries
verts = pnp.get_user_verticals(user_id="u1", role="operator", lob_assignments=["p-lob-bai"])
comp = pnp.get_compliance_summary()

# Dashboard rendering
token = pnp.register_user(email="admin@eais.com", password="s", user_id="a1", role="superuser",
                           lob_assignments=["p-lob-bai", "p-lob-cybersecurity"])
panels = pnp.render_dashboard(token=token)
```
