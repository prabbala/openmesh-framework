# Adapter Development Guide

This guide explains how to build custom observability adapters for the OpenMesh Framework.

## Overview

An adapter implements the `ObservabilityAdapterInterface` to provide health checks, metrics, and dashboard panels for a specific runtime type (server, serverless, kubernetes, gpu, streaming).

## Quick Start

Use the SDK scaffold command to generate a starter adapter:

```bash
python -m openmesh_sdk.scaffold --name my-adapter --runtime-type server
```

## Interface Methods

Every adapter must implement:

- `get_health_checks()` — Return health check results
- `get_metrics()` — Return current metrics
- `get_panel_definitions()` — Return dashboard panel definitions
- `get_adapter_metadata()` — Return adapter metadata

## MeshHealthEvent

All adapters emit `MeshHealthEvent` objects with:

- `entity_id` — Which Entity
- `domain` — Which Domain
- `severity` — Critical, Warning, or Info
- `message` — Human-readable description
- `timestamp` — When the event occurred

## Validation

Run the SDK validation command to verify your adapter:

```bash
python -m openmesh_sdk.validator --adapter my_adapter.MyAdapter
```

_Full adapter development patterns and examples coming soon._
