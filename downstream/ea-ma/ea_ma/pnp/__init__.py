"""EA-MA PnP — pnp-prod/EAISPnPMain entry point.

Inherits from openmesh-framework (github.com/prabbala/openmesh-framework).
Canonical implementation: ea_ma.pnp.EAISPnPMain
"""

from ea_ma.pnp.EAISPnPMain import (
    EAISPnPMain,
    EAISEnvironment,
    BAIVerticalManager,
    ClientMaintenanceManager,
    ClientRecord,
    ProductCatalog,
    CatalogSnapshot,
    ProductStatus,
    VerticalInfo,
    UnauthorizedEmailDomainError,
    EmailVerificationRequiredError,
    SignupRequest,
    SignupResult,
    SignupDestination,
    SubscriberPlan,
    SubscriberProfile,
    SubscriberPortal,
    SubscriberDashboard,
)

__all__ = [
    "EAISPnPMain",
    "EAISEnvironment",
    "BAIVerticalManager",
    "ClientMaintenanceManager",
    "ClientRecord",
    "ProductCatalog",
    "CatalogSnapshot",
    "ProductStatus",
    "VerticalInfo",
    "UnauthorizedEmailDomainError",
    "EmailVerificationRequiredError",
    "SignupRequest",
    "SignupResult",
    "SignupDestination",
    "SubscriberPlan",
    "SubscriberProfile",
    "SubscriberPortal",
    "SubscriberDashboard",
]
