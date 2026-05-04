"""Dashboard Shell — Panel composition engine combining core and adapter-provided panels."""

from .shell import DashboardShell, RenderedPanel, KNOWN_VISUALIZATION_TYPES

__all__ = [
    "DashboardShell",
    "RenderedPanel",
    "KNOWN_VISUALIZATION_TYPES",
]
