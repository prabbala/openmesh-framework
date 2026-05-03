"""Dashboard Shell — Panel composition engine combining core and adapter-provided panels.

Composes core panels (tenant overview, people management, audit log) with
adapter-provided panels based on Governance Engine evaluation. Handles
adapter fault isolation and unrecognized visualization types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from packages.core.audit.engine import AuditEngine
from packages.core.domain_registry.registry import DomainRegistry
from packages.core.governance_engine.engine import GovernanceEngine
from packages.observability.interface.adapter import (
    ObservabilityAdapterInterface,
    PanelDefinition,
)


KNOWN_VISUALIZATION_TYPES = frozenset({
    "health_grid",
    "metric_chart",
    "severity_chart",
    "timeline",
    "table",
    "stat_card",
})


@dataclass
class RenderedPanel:
    """A panel ready for rendering in the dashboard."""

    panel_id: str
    title: str
    visualization_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "core"  # "core" or adapter name
    is_fallback: bool = False
    is_degraded: bool = False


class DashboardShell:
    """Composes core panels with adapter-provided panels based on governance evaluation.

    Responsibilities:
    - Query Governance Engine for authorized domains/panels
    - Render core panels (tenant overview, people management, audit log)
    - Load adapter panels for each authorized domain
    - Filter panels by required_role
    - Handle unrecognized visualization_type with fallback placeholder
    - Catch adapter exceptions and return degraded status
    """

    CORE_PANELS = [
        RenderedPanel(
            panel_id="core:tenant-overview",
            title="Tenant Overview",
            visualization_type="stat_card",
            data={"description": "Overview of tenant status and configuration"},
            source="core",
        ),
        RenderedPanel(
            panel_id="core:people-management",
            title="People Management",
            visualization_type="table",
            data={"description": "User and group management"},
            source="core",
        ),
        RenderedPanel(
            panel_id="core:audit-log",
            title="Audit Log",
            visualization_type="table",
            data={"description": "Immutable audit trail of all actions"},
            source="core",
        ),
    ]

    def __init__(
        self,
        governance_engine: GovernanceEngine,
        domain_registry: DomainRegistry,
        audit_engine: Optional[AuditEngine] = None,
        adapters: Optional[Dict[str, ObservabilityAdapterInterface]] = None,
    ) -> None:
        self._governance = governance_engine
        self._domain_registry = domain_registry
        self._audit = audit_engine
        self._adapters = adapters or {}

    def register_adapter(
        self, adapter_class_name: str, adapter: ObservabilityAdapterInterface
    ) -> None:
        """Register an adapter instance for use by the dashboard."""
        self._adapters[adapter_class_name] = adapter

    def render(
        self,
        user_id: str,
        role: str,
        groups: List[str],
        lob_assignments: List[str],
        tenant_id: str = "",
        entity_id: str = "",
    ) -> List[RenderedPanel]:
        """Render the dashboard for a user.

        1. Evaluate governance to get authorized domains/panels
        2. Render core panels (always shown)
        3. For each authorized domain, load adapter and render its panels
        4. Filter panels by required_role
        5. Handle unrecognized visualization_type with fallback placeholder
        6. Catch adapter exceptions, log to audit, return degraded status
        """
        # Step 1: Evaluate governance
        gov_result = self._governance.evaluate(
            user_id=user_id,
            role=role,
            groups=groups,
            lob_assignments=lob_assignments,
        )

        # Step 2: Always include core panels
        panels: List[RenderedPanel] = list(self.CORE_PANELS)

        # Step 3: Load adapter panels for each authorized domain
        for domain_id in gov_result.authorized_domains:
            domain = self._domain_registry.get_by_id(domain_id)
            if domain is None:
                continue

            adapter = self._adapters.get(domain.observability_adapter)
            if adapter is None:
                continue

            # Step 6: Fault isolation — catch adapter exceptions
            try:
                panel_defs = adapter.get_panel_definitions()
            except Exception as exc:
                # Log to audit engine if available
                if self._audit:
                    self._audit.record(
                        entity_id=entity_id or domain.entity_id,
                        tenant_id=tenant_id,
                        actor_id="system",
                        action_type="adapter_error",
                        resource=domain.observability_adapter,
                        detail={
                            "domain_id": domain_id,
                            "error": str(exc),
                            "method": "get_panel_definitions",
                        },
                    )
                # Return degraded panel for this adapter
                panels.append(
                    RenderedPanel(
                        panel_id=f"{domain_id}:degraded",
                        title=f"{domain_id} (Degraded)",
                        visualization_type="stat_card",
                        data={
                            "error": str(exc),
                            "status": "degraded",
                        },
                        source=domain.observability_adapter,
                        is_degraded=True,
                    )
                )
                continue

            # Step 4: Filter panels by required_role
            for panel_def in panel_defs:
                if not self._role_satisfies(role, panel_def.required_role):
                    continue

                viz_type = panel_def.visualization_type

                # Step 5: Handle unrecognized visualization_type
                if viz_type not in KNOWN_VISUALIZATION_TYPES:
                    panels.append(
                        RenderedPanel(
                            panel_id=f"{domain_id}:{panel_def.title}",
                            title=panel_def.title,
                            visualization_type="fallback",
                            data={
                                "original_type": viz_type,
                                "adapter": domain.observability_adapter,
                                "message": (
                                    f"Unrecognized visualization type "
                                    f"'{viz_type}' from adapter "
                                    f"'{domain.observability_adapter}'"
                                ),
                            },
                            source=domain.observability_adapter,
                            is_fallback=True,
                        )
                    )
                else:
                    panels.append(
                        RenderedPanel(
                            panel_id=f"{domain_id}:{panel_def.title}",
                            title=panel_def.title,
                            visualization_type=viz_type,
                            data={"data_source_key": panel_def.data_source_key},
                            source=domain.observability_adapter,
                        )
                    )

        return panels

    def _role_satisfies(self, user_role: str, required_role: str) -> bool:
        """Check if user_role satisfies the required_role for a panel.

        Uses the RBAC engine's role hierarchy. Higher-privilege roles
        satisfy lower-privilege requirements.
        """
        if user_role in ("superuser", "platform_operator"):
            return True
        if user_role == required_role:
            return True
        # Use RBAC hierarchy level — lower number = more privileged
        from packages.core.rbac.models import ROLE_HIERARCHY
        user_level = ROLE_HIERARCHY.get(user_role, 99)
        required_level = ROLE_HIERARCHY.get(required_role, 99)
        return user_level <= required_level
