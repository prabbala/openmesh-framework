"""SA-MA Preset — Sports-Avatar Mesh Architecture configuration."""

from __future__ import annotations

import os
from typing import Optional

from packages.core.pnp import PnPConfig, PnPMain


def create_sa_config(
    jwt_secret: str = "openmesh-change-me-in-production",
    jwt_ttl_seconds: int = 3600,
    config_dir: Optional[str] = None,
    log_level: str = "INFO",
) -> PnPConfig:
    if config_dir is None:
        config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
        )
    return PnPConfig(
        entity_id="sports-avatar",
        entity_name="Sports-Avatar LLC",
        config_dir=config_dir,
        jwt_secret=jwt_secret,
        jwt_ttl_seconds=jwt_ttl_seconds,
        tenant_name="Sports-Avatar Primary",
        log_level=log_level,
    )


def create_sa_pnp(
    jwt_secret: str = "openmesh-change-me-in-production",
    jwt_ttl_seconds: int = 3600,
    config_dir: Optional[str] = None,
    log_level: str = "INFO",
    auto_bootstrap: bool = True,
) -> PnPMain:
    """Create and bootstrap a PnPMain for Sports-Avatar LLC."""
    config = create_sa_config(
        jwt_secret=jwt_secret, jwt_ttl_seconds=jwt_ttl_seconds,
        config_dir=config_dir, log_level=log_level,
    )
    pnp = PnPMain(config)
    if auto_bootstrap:
        pnp.bootstrap()
    return pnp
