# Governance Model

## Core Formula

```
observability = function(role, LOB_scope, domain)
```

The Governance Engine evaluates this formula on every request to determine
what observability data a user can see. There are no stale cached decisions.

## How It Works

### Three Inputs

1. **Role** (from RBAC Engine): What permissions does the user have?
2. **LOB Scope** (from Scope Resolver): Which Lines of Business can the user see?
3. **Domain** (from Domain Registry): Which registered domains match the scope?

### Evaluation

The Governance Engine returns the **intersection** of all three:

```
authorized_data = role_permissions ∩ LOB_scope ∩ registered_domains
```

A user only sees data that satisfies ALL three conditions.

## Role Hierarchy

| Role      | Level | Scope                                                     |
| --------- | ----- | --------------------------------------------------------- |
| superuser | 0     | Unrestricted — all entities, all domains, all LOBs        |
| admin     | 1     | Entity-scoped — all domains within their entity           |
| operator  | 2     | Domain-scoped — specific domain's adapters and metrics    |
| auditor   | 3     | Read-only — audit logs and health events within LOB scope |
| manager   | 4     | Dashboard and user visibility within LOB scope            |
| staff     | 5     | Dashboard and observability within LOB scope              |
| viewer    | 6     | Dashboard read-only                                       |

## Concrete Examples

### Example 1: Empirical-AiS System Admin

```
User: Alice (superuser)
Role permissions: * (all)
LOB scope: unrestricted
Domains visible: ALL (cybersecurity-decmmc, genai-platform, rag-pipeline)

Result: Alice sees everything across all Empirical-AiS domains.
```

### Example 2: Empirical-AiS Cybersecurity Operator

```
User: Bob (operator, LOB: p-lob-cybersecurity)
Role permissions: dashboard:read, observability:read, metrics:read
LOB scope: {p-lob-cybersecurity}
Domains in scope: {cybersecurity-decmmc}

Result: Bob sees only the Cybersecurity DeCMMC domain's health checks,
        metrics, and panels. GenAI and RAG domains are invisible.
```

### Example 3: Sports-Avatar Auditor

```
User: Carol (auditor, LOB: p-lob-animation)
Role permissions: audit:read, dashboard:read, observability:read
LOB scope: {p-lob-animation}
Domains in scope: {animation-engine}

Result: Carol can read audit logs and health events for the Animation Engine
        domain. She cannot create, update, or delete anything.
        The Cric-Avatar domain is invisible (different LOB).
```

### Example 4: Cross-Entity Visibility

```
User: Dave (superuser, platform_operator)
Entities visible: Empirical-AiS AND Sports-Avatar

Result: Dave sees all domains across both entities.
        This is the "god mode" for platform operators.
```

## LOB Categories

| Category               | Purpose                            | Example                               |
| ---------------------- | ---------------------------------- | ------------------------------------- |
| I_LOB (Infrastructure) | Shared infrastructure concerns     | Servers, networking, databases        |
| P_LOB (Product)        | Product-specific business concerns | Cybersecurity metrics, streaming KPIs |

LOBs are **business hierarchy categories**. They are NOT the same as `runtime_type`,
which is a technical classification of the adapter.

## Policy Freshness

The Governance Engine re-evaluates on every request. When roles, LOB assignments,
or domain registrations change, the very next evaluation reflects the change.
No stale cached decisions persist.
