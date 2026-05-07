"""EA-MA PnP Main — re-exports from EAISPnPMain for backward compatibility.

The canonical implementation lives in ea_ma.pnp.EAISPnPMain.
"""

from ea_ma.pnp.EAISPnPMain import (  # noqa: F401
    EAISPnPMain,
    EAISEnvironment,
    BAIVerticalManager,
    ProductCatalog,
    CatalogSnapshot,
    ProductStatus,
    VerticalInfo,
    UnauthorizedEmailDomainError,
)

__all__ = [
    "EAISPnPMain",
    "EAISEnvironment",
    "BAIVerticalManager",
    "ProductCatalog",
    "CatalogSnapshot",
    "ProductStatus",
    "VerticalInfo",
    "UnauthorizedEmailDomainError",
]
