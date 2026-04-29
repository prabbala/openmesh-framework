# Architecture Overview

This document describes the high-level architecture of the OpenMesh Framework (OMA).

## Layers

The framework is organized into four layers:

1. **Core Governance Layer** (`packages/core/`) — RBAC, tenant management, LOB hierarchy, audit, auth, dashboard shell, domain registry, and governance engine
2. **Observability Layer** (`packages/observability/`) — Abstract adapter interface, MeshHealthEvent schema, and runtime-specific adapters
3. **SDKs** (`packages/sdk/`) — Python SDK for adapter development, TypeScript SDK for type definitions
4. **Admin Shell UI** (`packages/admin-shell-ui/`) — React dashboard frame with pluggable layout and visualization

## Core Innovation

```
observability = function(role, LOB_scope, domain)
```

The Governance Engine evaluates this function on every request, combining RBAC permissions, LOB scope resolution, and domain registration to determine what observability data a user can see.

## Consumption Model

Businesses install the framework as a dependency and provide their own DomainRegistration YAML and adapter configuration. The framework owns the "How" (governance, dashboard layout); each business owns the "What" (data, metrics, domain config).

_Full architecture diagrams and component interaction details coming soon._
