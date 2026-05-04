"""Plug-N-Play (PnP) — Production bootstrap and orchestration.

Provides the PnPMain orchestrator that wires all framework components
together from YAML domain configs into a running governance-evaluated
dashboard stack. This is the primary entry point for businesses
consuming the OpenMesh framework.
"""

from .pnp_main import PnPMain, PnPConfig, PnPBootstrapError

__all__ = [
    "PnPMain",
    "PnPConfig",
    "PnPBootstrapError",
]
