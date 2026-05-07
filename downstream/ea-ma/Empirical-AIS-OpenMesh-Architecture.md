# Empirical-AIS OpenMesh Architecture

## Overview

Empirical-AiS Inc. operates a multi-product AI platform built on the OpenMesh Framework.
The architecture separates concerns across three independent repositories, each with
clear ownership boundaries and a single deployment surface.

---

## Repository Structure

```
openmesh-framework (public, github.com/prabbala/openmesh-framework)
├── PnPMain, RBAC, LOB, Governance, DashboardShell, Observability
│
├── ea-ma (private, github.com/prabbala/ea-ma)
│   └── EAISPnPMain → plug-n-play-infra.ai/EAISPnPMain
│       ├── Product: PNP
│       │   ├── Finance      (p-LOB officials, then i-LOB officials)
│       │   ├── Marketing    (p-LOB officials, then i-LOB officials)
│       │   ├── Sales        (p-LOB officials, then i-LOB officials)
│       │   ├── Compliance   (p-LOB officials, then i-LOB officials)
│       │   ├── Operations   (p-LOB officials, then i-LOB officials)
│       │   └── IT           (p-LOB officials, then i-LOB officials)
│       └── Product: ZKP-ZDV
│           ├── Finance      (p-LOB officials, then i-LOB officials)
│           ├── Marketing    (p-LOB officials, then i-LOB officials)
│           ├── Sales        (p-LOB officials, then i-LOB officials)
│           ├── Compliance   (p-LOB officials, then i-LOB officials)
│           ├── Operations   (p-LOB officials, then i-LOB officials)
│           └── IT           (p-LOB officials, then i-LOB officials)
│
└── plug-n-play-crm-ai (separate repo, NOT touched by ea-ma)
    └── its own PnP consumer — completely independent
```

---

## Repositories

### 1. openmesh-framework (Public)

| Field | Value |
|-------|-------|
| URL | github.com/prabbala/openmesh-framework |
| Visibility | Public |
| Purpose | Base framework — inherited by all downstream consumers |

Provides the foundational infrastructure that any organization can adopt:

- **PnPMain** — Production Plug-N-Play orchestrator (bootstrap, YAML config loading, adapter resolution)
- **RBAC Engine** — Role-based access control with dual-path evaluation (role + group policies)
- **LOB Store** — Two-tier LOB hierarchy: P_LOB (Product) and I_LOB (Infrastructure)
- **Governance Engine** — Policy evaluation, domain authorization, scope resolution
- **DashboardShell** — Governance-evaluated panel rendering
- **Observability Adapters** — Pluggable adapters for server/serverless runtime monitoring
- **Audit Engine** — Immutable audit trail for all system mutations
- **Tenant Manager** — Multi-tenant isolation and lifecycle
- **Domain Registry** — 4-tier hierarchy: Entity → Domain → ProductFamily → Resource
- **HierarchyStore** — Referential integrity for the domain hierarchy

### 2. ea-ma (Private)

| Field | Value |
|-------|-------|
| URL | github.com/prabbala/ea-ma |
| Visibility | Private |
| Purpose | Empirical-AiS Mesh Architecture — pnp-prod entry point |
| Deployment | plug-n-play-infra.ai/EAISPnPMain |
| Dependency | Inherits from openmesh-framework |

EAISPnPMain extends PnPMain with Empirical-AiS business logic:

- Email domain enforcement (@empirical-ais.com)
- Environment awareness (local / staging / production)
- Product-level organization (PNP, ZKP-ZDV)
- LOB-level structure with p-LOB and i-LOB tiers
- RBAC roles scoped to product and LOB responsibilities
- Subscriber portal for outsider clients
- Client maintenance lifecycle (i-LOB)

### 3. plug-n-play-crm-ai (Separate)

| Field | Value |
|-------|-------|
| URL | github.com/prabbala/plug-n-play-crm-ai |
| Visibility | Separate consumer |
| Purpose | Independent PnP consumer — NOT touched by ea-ma |

This repository is a completely independent consumer of openmesh-framework.
It has its own PnP configuration, its own domain registrations, and its own
deployment surface. Changes in ea-ma never affect plug-n-play-crm-ai.

---

## Boundary Rules

1. **ea-ma never modifies plug-n-play-crm-ai** — they are independent consumers of openmesh-framework
2. **ea-ma never modifies openmesh-framework** — it only inherits from it
3. **All ea-ma work contributes to plug-n-play-infra.ai/EAISPnPMain** — that is the single deployment surface
4. **@empirical-ais.com users** get full access to both products (PNP + ZKP-ZDV) across all LOBs
5. **Outsiders** are routed to the Subscriber Portal, scoped to their product_type LOB

---

## Products

EA-MA currently manages two products. Each product contains six LOBs,
and each LOB is divided into two tiers of officials.

### Product: PNP (Plug-N-Play)

The core orchestration product — full om-fw lifecycle management,
client onboarding, dashboard rendering, observability.

### Product: ZKP-ZDV (Zero-Knowledge Proof / Zero-Data Verification)

Cybersecurity product — zero-knowledge proof verification,
CMMC compliance, decentralized verification protocols.

---

## LOB Structure (per Product)

Each product has six Lines of Business. Within each LOB, there are two tiers:

| LOB | p-LOB Officials | i-LOB Officials |
|-----|----------------|-----------------|
| **Finance** | Revenue, billing, forecasting | Cost management, infra billing |
| **Marketing** | Campaigns, analytics, growth | Platform tooling, data pipelines |
| **Sales** | Pipeline, CRM, deal management | CRM infra, integrations |
| **Compliance** | Audit, regulatory, policy | Audit infra, log retention |
| **Operations** | Delivery, SLA, workflow | Platform ops, monitoring |
| **Information-Technology** | Infrastructure, DevOps, security | Cloud infra, networking, IAM |

### p-LOB (Product Officials)

Product-facing roles. These officials own the business outcomes:
- Define product requirements
- Own revenue and customer metrics
- Drive go-to-market and compliance posture
- Manage product-level dashboards and observability

### i-LOB (Infrastructure Officials)

Infrastructure-facing roles. These officials own the platform:
- Manage cloud infrastructure and networking
- Own cost optimization and infra billing
- Maintain audit infrastructure and log retention
- Operate platform monitoring and incident response

---

## RBAC Roles

All roles are controlled by the om-fw RBAC Engine. Access is evaluated via
dual-path: role permissions OR group-level policies.

### System Roles (from openmesh-framework)

| Role | Level | Scope |
|------|-------|-------|
| superuser | 0 | Unrestricted — all products, all LOBs |
| admin | 1 | Full read/write across tenants, users, domains |
| operator | 2 | Dashboard, observability, metrics, domains (read) |
| auditor | 3 | Audit + dashboard + observability (read-only) |
| manager | 4 | Dashboard, users, observability (read) |
| staff | 5 | Dashboard + observability (read) |
| viewer | 6 | Dashboard (read-only) |

### EAIS Custom Roles (defined in ea-ma)

| Role | Tier | Responsibilities |
|------|------|-----------------|
| compliance_officer | p-LOB | Audit read, observability, domains, dashboard |
| bai_analyst | p-LOB | Dashboard, observability, metrics (read) |
| platform_operator | i-LOB | Tenants (read/write), domains, audit, observability |
| client_manager | i-LOB | Dashboard, observability, tenants, users (read) |
| subscriber | External | Dashboard + observability (read-only, scoped to single LOB) |

### Role Assignment Logic

- **@empirical-ais.com** users → default role: `operator`, all p-LOBs + i-LOBs assigned
- **Partner domains** (configured) → default role: `viewer`, no default LOBs
- **Outsiders** (subscriber signup) → role: `subscriber`, scoped to single product_type LOB

---

## Authentication and Access Flow

```
User signup at plug-n-play-infra.ai/EAISPnPMain
│
├── @empirical-ais.com
│   ├── Role: operator (or explicit override)
│   ├── LOBs: all p-LOBs + all i-LOBs for both products
│   ├── Destination: pnp-prod/EAISPnPMain (full dashboard)
│   └── No email verification required
│
└── Outsider (@other-domain.com)
    ├── Role: subscriber
    ├── LOBs: single p-LOB scoped to product_type
    ├── Destination: Subscriber Portal
    └── Email verification required
```

---

## Deployment Surface

| URL | Source | Owner |
|-----|--------|-------|
| plug-n-play-infra.ai/EAISPnPMain | ea-ma | Empirical-AiS |
| (plug-n-play-crm-ai deployment) | plug-n-play-crm-ai | Independent |

---

## Technical Dependencies

```
ea-ma
└── openmesh-framework @ git+https://github.com/prabbala/openmesh-framework.git
    └── pyyaml >= 6.0
```

Installation:
```bash
git clone git@github.com:prabbala/ea-ma.git
cd ea-ma
pip install -e ".[dev]"
python -m pytest tests/
```

---

## Configuration Files

Each product is defined by a YAML domain registration in `config/`:

```
config/
├── pnp.yaml          # Product: PNP — 12 product_families (6 LOBs × 2 tiers)
├── zkp-zdv.yaml      # Product: ZKP-ZDV — 12 product_families (6 LOBs × 2 tiers)
├── bai.yaml          # Legacy: BAI verticals (Restaurant, Supermarket, IT-Consulting, Realestate)
├── cybersecurity-ai.yaml
├── genai-platform.yaml
├── rag-pipeline.yaml
└── client-maintenance.yaml  # i-LOB: client lifecycle management
```

---

## Summary

- **openmesh-framework** = the engine (public, reusable)
- **ea-ma** = Empirical-AiS's private configuration and business logic on that engine
- **plug-n-play-crm-ai** = a separate, independent consumer — never touched by ea-ma
- All ea-ma work ships to **plug-n-play-infra.ai/EAISPnPMain**
- Products (PNP, ZKP-ZDV) each have 6 LOBs with p-LOB and i-LOB tiers
- RBAC controls who sees what, at every level
