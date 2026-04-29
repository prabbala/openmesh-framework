# Governance Model

This document explains the OMA governance formula and how it controls observability access.

## The Formula

```
observability = function(role, LOB_scope, domain)
```

The Governance Engine evaluates this function on every request. It combines three inputs:

1. **Role** — The user's RBAC role (from the RBAC Engine)
2. **LOB Scope** — The user's effective Line of Business scope (from the Scope Resolver)
3. **Domain** — The target domain (from the Domain Registry)

The result is the intersection: only observability data that matches all three dimensions is returned.

## Examples

### Empirical-AiS: System Admin

A System Admin (superuser) at Empirical-AiS sees all domains across all LOBs — both PNP server infrastructure and ZDV serverless infrastructure.

### Empirical-AiS: Domain Operator

An operator scoped to the Cybersecurity LOB sees only ZDV-related domains. They cannot see PNP server health data.

### Sports-Avatar: Entity Admin

An Entity Admin at Sports-Avatar sees all Sports-Avatar domains (Animation Engine, Streaming Delivery) but cannot see any Empirical-AiS data.

## LOB vs runtime_type

LOBs are business categories (Infrastructure, Product). `runtime_type` is a technical classification of the adapter (server, serverless, gpu). They do not overlap.

_Detailed governance scenarios and policy configuration coming soon._
