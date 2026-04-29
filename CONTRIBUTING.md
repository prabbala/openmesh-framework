# Contributing to OpenMesh Framework

Thank you for your interest in contributing to the OpenMesh Admin and Observability Management Architecture (OMA). This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch from `main`
4. Make your changes
5. Run the test suite
6. Submit a pull request

## Development Setup

### Python (Core + Observability)

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### TypeScript (SDK + Admin Shell UI)

```bash
# Install dependencies
npm install

# Run tests
npm test

# Build
npm run build
```

## Project Structure

- `packages/core/` — Core governance layer (Python)
- `packages/observability/` — Observability adapters and interface (Python)
- `packages/sdk/` — Developer SDKs (Python + TypeScript)
- `packages/admin-shell-ui/` — React dashboard frame (TypeScript)
- `examples/` — Business consumption examples
- `docs/` — Documentation
- `tests/` — Test suite

## Coding Standards

### Python

- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Write docstrings for all public classes and methods
- Use `dataclasses` for data models
- Target Python 3.10+

### TypeScript

- Use strict TypeScript configuration
- Prefer interfaces over type aliases for object shapes
- Use explicit return types on exported functions

## Writing Adapters

The most common contribution is a new observability adapter. Use the SDK scaffold command to generate a starter:

```bash
python -m openmesh_sdk.scaffold --name my-adapter --runtime-type server
```

Your adapter must:

1. Implement `ObservabilityAdapterInterface`
2. Return valid `HealthCheck`, `Metric`, and `PanelDefinition` objects
3. Emit `MeshHealthEvent` objects conforming to the universal schema
4. Pass the SDK validation command

## Testing

- Write property-based tests using Hypothesis (Python) or fast-check (TypeScript)
- Write unit tests for edge cases and specific examples
- All tests must pass before submitting a PR
- Minimum 100 iterations for property-based tests

## Pull Request Process

1. Ensure all tests pass locally
2. Update documentation if your change affects public APIs
3. Add a clear description of what your PR does and why
4. Reference any related issues
5. Request review from a maintainer

## Code of Conduct

Be respectful, inclusive, and constructive. We are building a community-driven project and welcome contributors of all experience levels.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
