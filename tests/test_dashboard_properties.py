"""Property tests for Dashboard Shell — panel composition and adapter fault isolation.

Tests:
- Property 20: Dashboard Panel Filtering
- Property 17: Adapter Exception Resilience
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from packages.core.audit.engine import AuditEngine
from packages.core.dashboard_shell.shell import DashboardShell, RenderedPanel, KNOWN_VISUALIZATION_TYPES
from packages.core.domain_registry.registration import DomainRegistration
from packages.core.domain_registry.registry import DomainRegistry
from packages.core.governance_engine.engine import GovernanceEngine
from packages.core.lob.models import LOBCategory, LOBNode
from packages.core.lob.scope_resolver import ScopeResolver
from packages.core.lob.store import LOBStore
from packages.core.rbac.engine import RBACEngine
from packages.core.rbac.models import ROLE_HIERARCHY
from packages.observability.interface.adapter import (
    AdapterMetadata,
    HealthCheck,
    HealthStatus,
    Metric,
    MeshHealthEvent,
    ObservabilityAdapterInterface,
    PanelDefinition,
    Severity,
)

from datetime import datetime, timezone
from typing import List


# ── Test Adapters ────────────────────────────────────────────────────

class GoodAdapter(ObservabilityAdapterInterface):
    """A well-behaved adapter for testing."""

    def __init__(self, panels: List[PanelDefinition] = None):
        self._panels = panels or [
            PanelDefinition(
                title="Test Panel",
                data_source_key="test",
                visualization_type="health_grid",
                required_role="operator",
            ),
        ]

    def get_health_checks(self) -> List[HealthCheck]:
        return [HealthCheck(name="test", status=HealthStatus.HEALTHY)]

    def get_metrics(self) -> List[Metric]:
        return [Metric(metric_name="test", value=1.0, unit="count", timestamp=datetime.now(timezone.utc))]

    def get_panel_definitions(self) -> List[PanelDefinition]:
        return self._panels

    def get_adapter_metadata(self) -> AdapterMetadata:
        return AdapterMetadata(name="good-adapter", version="1.0.0", supported_runtime_types=["server"], description="Test")


class CrashingAdapter(ObservabilityAdapterInterface):
    """An adapter that raises exceptions."""

    def get_health_checks(self) -> List[HealthCheck]:
        raise RuntimeError("Health check explosion")

    def get_metrics(self) -> List[Metric]:
        raise RuntimeError("Metrics explosion")

    def get_panel_definitions(self) -> List[PanelDefinition]:
        raise RuntimeError("Panel definitions explosion")

    def get_adapter_metadata(self) -> AdapterMetadata:
        return AdapterMetadata(name="crashing-adapter", version="1.0.0", supported_runtime_types=["server"], description="Crashes")


# ── Helpers ──────────────────────────────────────────────────────────

def _build_shell(
    role: str = "operator",
    adapter: ObservabilityAdapterInterface = None,
    adapter_class_name: str = "test.GoodAdapter",
    domain_id: str = "test-domain",
    lob_id: str = "test-lob",
    entity_id: str = "test-entity",
    with_audit: bool = False,
) -> tuple:
    """Build a DashboardShell with a single domain and adapter."""
    rbac = RBACEngine()
    lob_store = LOBStore()
    scope_resolver = ScopeResolver(lob_store, rbac)
    registry = DomainRegistry()
    governance = GovernanceEngine(rbac, scope_resolver, registry)
    audit = AuditEngine() if with_audit else None

    # Create LOB
    lob_store.create_lob(LOBNode(
        lob_id=lob_id, name="Test LOB",
        category=LOBCategory.P_LOB, parent_lob_id=None, entity_id=entity_id,
    ))

    # Register domain
    reg = DomainRegistration(
        domain_id=domain_id,
        runtime_type="server",
        observability_adapter=adapter_class_name,
        roles=[role, "superuser"],
        tabs=[{"title": "Test Tab", "panel_type": "health_grid", "data_source": "test"}],
        entity_id=entity_id,
        lob_id=lob_id,
    )
    registry.register(reg)

    shell = DashboardShell(governance, registry, audit)
    if adapter:
        shell.register_adapter(adapter_class_name, adapter)

    return shell, audit


# ── Property 20: Dashboard Panel Filtering ───────────────────────────

# Feature: openmesh-framework, Property 20: Dashboard Panel Filtering
class TestDashboardPanelFiltering:
    """Dashboard Shell renders only panels whose required_role is satisfied."""

    def test_core_panels_always_present(self):
        """Core panels (tenant overview, people mgmt, audit log) always render."""
        shell, _ = _build_shell(role="viewer")
        panels = shell.render(
            user_id="u1", role="viewer", groups=[], lob_assignments=["test-lob"],
        )
        core_ids = {p.panel_id for p in panels if p.source == "core"}
        assert "core:tenant-overview" in core_ids
        assert "core:people-management" in core_ids
        assert "core:audit-log" in core_ids

    def test_no_adapters_renders_only_core(self):
        """When no adapters are registered, only core panels render."""
        shell, _ = _build_shell(role="operator")
        # Don't register any adapter
        panels = shell.render(
            user_id="u1", role="operator", groups=[], lob_assignments=["test-lob"],
        )
        # All panels should be core panels
        for p in panels:
            assert p.source == "core"

    def test_operator_sees_operator_panels(self):
        """Operator role sees panels with required_role=operator."""
        adapter = GoodAdapter(panels=[
            PanelDefinition(title="Op Panel", data_source_key="test",
                          visualization_type="health_grid", required_role="operator"),
        ])
        shell, _ = _build_shell(role="operator", adapter=adapter)
        panels = shell.render(
            user_id="u1", role="operator", groups=[], lob_assignments=["test-lob"],
        )
        adapter_panels = [p for p in panels if p.source != "core"]
        assert len(adapter_panels) == 1
        assert adapter_panels[0].title == "Op Panel"

    def test_viewer_cannot_see_operator_panels(self):
        """Viewer role cannot see panels requiring operator role."""
        adapter = GoodAdapter(panels=[
            PanelDefinition(title="Op Only", data_source_key="test",
                          visualization_type="health_grid", required_role="operator"),
        ])
        shell, _ = _build_shell(role="viewer", adapter=adapter)
        panels = shell.render(
            user_id="u1", role="viewer", groups=[], lob_assignments=["test-lob"],
        )
        adapter_panels = [p for p in panels if p.source != "core"]
        assert len(adapter_panels) == 0

    def test_superuser_sees_all_panels(self):
        """Superuser sees all panels regardless of required_role."""
        adapter = GoodAdapter(panels=[
            PanelDefinition(title="Admin Panel", data_source_key="test",
                          visualization_type="health_grid", required_role="admin"),
            PanelDefinition(title="Op Panel", data_source_key="test",
                          visualization_type="metric_chart", required_role="operator"),
        ])
        shell, _ = _build_shell(role="superuser", adapter=adapter)
        panels = shell.render(
            user_id="u1", role="superuser", groups=[], lob_assignments=["test-lob"],
        )
        adapter_panels = [p for p in panels if p.source != "core"]
        assert len(adapter_panels) == 2

    def test_unrecognized_viz_type_renders_fallback(self):
        """Unrecognized visualization_type renders as fallback placeholder."""
        adapter = GoodAdapter(panels=[
            PanelDefinition(title="Weird Panel", data_source_key="test",
                          visualization_type="hologram_3d", required_role="operator"),
        ])
        shell, _ = _build_shell(role="operator", adapter=adapter)
        panels = shell.render(
            user_id="u1", role="operator", groups=[], lob_assignments=["test-lob"],
        )
        adapter_panels = [p for p in panels if p.source != "core"]
        assert len(adapter_panels) == 1
        assert adapter_panels[0].is_fallback is True
        assert adapter_panels[0].visualization_type == "fallback"
        assert "hologram_3d" in adapter_panels[0].data.get("original_type", "")

    @given(
        viz_type=st.sampled_from(sorted(KNOWN_VISUALIZATION_TYPES)),
    )
    @settings(max_examples=20)
    def test_known_viz_types_not_fallback(self, viz_type):
        """Known visualization types render normally, not as fallback."""
        adapter = GoodAdapter(panels=[
            PanelDefinition(title="Panel", data_source_key="test",
                          visualization_type=viz_type, required_role="operator"),
        ])
        shell, _ = _build_shell(role="operator", adapter=adapter)
        panels = shell.render(
            user_id="u1", role="operator", groups=[], lob_assignments=["test-lob"],
        )
        adapter_panels = [p for p in panels if p.source != "core"]
        assert len(adapter_panels) == 1
        assert adapter_panels[0].is_fallback is False
        assert adapter_panels[0].visualization_type == viz_type


# ── Property 17: Adapter Exception Resilience ────────────────────────

# Feature: openmesh-framework, Property 17: Adapter Exception Resilience
class TestAdapterExceptionResilience:
    """Framework catches adapter exceptions and returns degraded status."""

    def test_crashing_adapter_returns_degraded(self):
        """Adapter that raises exception produces degraded panel."""
        shell, _ = _build_shell(
            role="operator",
            adapter=CrashingAdapter(),
            adapter_class_name="test.CrashingAdapter",
            with_audit=False,
        )
        panels = shell.render(
            user_id="u1", role="operator", groups=[], lob_assignments=["test-lob"],
        )
        degraded = [p for p in panels if p.is_degraded]
        assert len(degraded) == 1
        assert "degraded" in degraded[0].data.get("status", "").lower()

    def test_crashing_adapter_logs_to_audit(self):
        """Adapter exception is logged to the Audit Engine."""
        shell, audit = _build_shell(
            role="operator",
            adapter=CrashingAdapter(),
            adapter_class_name="test.CrashingAdapter",
            with_audit=True,
        )
        panels = shell.render(
            user_id="u1", role="operator", groups=[], lob_assignments=["test-lob"],
            tenant_id="t1", entity_id="e1",
        )
        # Check audit has an adapter_error record
        records = audit.query(tenant_id="t1", action_type="adapter_error")
        assert len(records) >= 1
        assert "explosion" in records[0].detail.get("error", "").lower()

    def test_good_adapter_not_degraded(self):
        """Well-behaved adapter does not produce degraded panels."""
        shell, _ = _build_shell(role="operator", adapter=GoodAdapter())
        panels = shell.render(
            user_id="u1", role="operator", groups=[], lob_assignments=["test-lob"],
        )
        degraded = [p for p in panels if p.is_degraded]
        assert len(degraded) == 0

    def test_framework_continues_after_adapter_crash(self):
        """Framework continues operating after adapter exception — core panels still render."""
        shell, _ = _build_shell(
            role="operator",
            adapter=CrashingAdapter(),
            adapter_class_name="test.CrashingAdapter",
        )
        panels = shell.render(
            user_id="u1", role="operator", groups=[], lob_assignments=["test-lob"],
        )
        core_panels = [p for p in panels if p.source == "core"]
        assert len(core_panels) == 3  # tenant overview, people mgmt, audit log
