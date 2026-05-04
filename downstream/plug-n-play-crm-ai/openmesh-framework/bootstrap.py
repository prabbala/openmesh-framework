"""Bootstrap — initializes the EA-MA PnP instance for plug-n-play-crm-ai.

This module provides a singleton PnP instance that the CRM-AI product
uses for governance, auth, dashboard rendering, and BAI vertical management.

Usage:
    from openmesh_framework.bootstrap import get_pnp

    pnp = get_pnp()                          # local dev
    pnp = get_pnp(environment="production")   # production
"""

from __future__ import annotations

import os
from typing import Optional

from ea_ma.pnp import EAISPnPMain, EAISEnvironment
from ea_ma.preset import create_eais_pnp

# Singleton PnP instance
_pnp_instance: Optional[EAISPnPMain] = None


def get_pnp(
    environment: str = "local",
    jwt_secret: Optional[str] = None,
    config_dir: Optional[str] = None,
) -> EAISPnPMain:
    """Get or create the singleton EA-MA PnP instance.

    On first call, bootstraps the full stack. Subsequent calls return
    the same instance.

    Args:
        environment: "local", "staging", or "production".
            Reads from EAMA_ENVIRONMENT env var if not specified.
        jwt_secret: JWT signing secret.
            Reads from EAMA_JWT_SECRET env var if not specified.
        config_dir: Path to domain YAML configs.
            Defaults to ea-ma's config/ directory.

    Returns:
        A bootstrapped EAISPnPMain instance.
    """
    global _pnp_instance
    if _pnp_instance is not None:
        return _pnp_instance

    # Resolve environment
    env_str = os.environ.get("EAMA_ENVIRONMENT", environment).lower()
    env_map = {
        "local": EAISEnvironment.LOCAL,
        "staging": EAISEnvironment.STAGING,
        "production": EAISEnvironment.PRODUCTION,
        "prod": EAISEnvironment.PRODUCTION,
    }
    env = env_map.get(env_str, EAISEnvironment.LOCAL)

    # Resolve JWT secret
    secret = jwt_secret or os.environ.get("EAMA_JWT_SECRET", "dev-secret-change-me")

    # Resolve log level
    log_level = "WARNING" if env == EAISEnvironment.PRODUCTION else "INFO"

    _pnp_instance = create_eais_pnp(
        jwt_secret=secret,
        config_dir=config_dir,
        log_level=log_level,
        environment=env,
    )

    return _pnp_instance


def reset_pnp() -> None:
    """Reset the singleton (for testing only)."""
    global _pnp_instance
    _pnp_instance = None
