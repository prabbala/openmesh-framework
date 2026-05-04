"""EA-MA PnP — EAIS-specific Plug-N-Play orchestrator.

Extends the framework's PnPMain with Empirical-AiS business logic:
- Email domain enforcement (@empirical-ais.com)
- Environment awareness (local/staging/production)
- BAI vertical management (product_type lifecycle)
- Cross-product intelligence routing
- EAIS-specific RBAC roles and compliance policies
- Product catalog with health aggregation
"""

from .pnp_main import (
    EAISPnPMain,
    EAISEnvironment,
    BAIVerticalManager,
    ProductCatalog,
    UnauthorizedEmailDomainError,
)

__all__ = [
    "EAISPnPMain",
    "EAISEnvironment",
    "BAIVerticalManager",
    "ProductCatalog",
    "UnauthorizedEmailDomainError",
]
