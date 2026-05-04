"""EA-MA Preset — Empirical-AiS Mesh Architecture configuration.

Factory functions that create an EAISPnPMain pre-configured for
the Empirical-AiS Inc. product hierarchy with environment awareness.

Usage:
    from ea_ma.preset import create_eais_pnp, EAISEnvironment

    # Production — enforces @empirical-ais.com email domain
    pnp = create_eais_pnp(
        jwt_secret="production-secret",
        environment=EAISEnvironment.PRODUCTION,
    )

    # Local dev — still enforces email domain by default
    pnp = create_eais_pnp(jwt_secret="dev-secret")
"""

from __future__ import annotations

import os
from typing import Optional, Set

from packages.core.pnp import PnPConfig
from ea_ma.pnp import EAISPnPMain, EAISEnvironment


def create_eais_config(
    jwt_secret: str = "openmesh-change-me-in-production",
    jwt_ttl_seconds: int = 3600,
    config_dir: Optional[str] = None,
    log_level: str = "INFO",
) -> PnPConfig:
    """Create a PnPConfig for Empirical-AiS Inc. (EA-MA)."""
    if config_dir is None:
        config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
        )
    return PnPConfig(
        entity_id="empirical-ais",
        entity_name="Empirical-AiS Inc.",
        config_dir=config_dir,
        jwt_secret=jwt_secret,
        jwt_ttl_seconds=jwt_ttl_seconds,
        tenant_name="Empirical-AiS Primary",
        log_level=log_level,
    )


def create_eais_pnp(
    jwt_secret: str = "openmesh-change-me-in-production",
    jwt_ttl_seconds: int = 3600,
    config_dir: Optional[str] = None,
    log_level: str = "INFO",
    environment: EAISEnvironment = EAISEnvironment.LOCAL,
    enforce_email_domain: bool = True,
    allowed_email_domains: Optional[Set[str]] = None,
    auto_bootstrap: bool = True,
) -> EAISPnPMain:
    """Create and optionally bootstrap an EAISPnPMain for Empirical-AiS Inc.

    Email domain enforcement is ON by default in all environments.
    Any user with @empirical-ais.com gets auto-assigned to the EAIS
    tenant with all LOBs and the default operator role.

    Args:
        jwt_secret: JWT signing secret.
        jwt_ttl_seconds: Token TTL.
        config_dir: YAML config directory path.
        log_level: Logging level.
        environment: Deployment environment (local/staging/production).
        enforce_email_domain: Whether to reject non-EAIS email domains.
        allowed_email_domains: Override the set of allowed email domains.
        auto_bootstrap: If True, calls bootstrap() automatically.
    """
    config = create_eais_config(
        jwt_secret=jwt_secret,
        jwt_ttl_seconds=jwt_ttl_seconds,
        config_dir=config_dir,
        log_level=log_level,
    )
    pnp = EAISPnPMain(
        config,
        environment=environment,
        enforce_email_domain=enforce_email_domain,
        allowed_email_domains=allowed_email_domains,
    )
    if auto_bootstrap:
        pnp.bootstrap()
    return pnp
