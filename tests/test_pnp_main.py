"""Tests for PnP Main — production bootstrap and orchestration.

Tests the generic PnP orchestrator using the sample-config examples.
No business-specific references — those live in downstream repos.
"""

from __future__ import annotations

import os

import pytest

from packages.core.pnp.pnp_main import PnPBootstrapError, PnPConfig, PnPMain
from packages.core.domain_registry.registration import DomainRegistration
from packages.core.domain_registry.hierarchy import ReferentialIntegrityError
from packages.core.tenant.models import TenantType
from packages.observability.adapters.server.adapter import ServerAdapter


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_CONFIG_DIR = os.path.join(REPO_ROOT, "examples", "sample-config")


def _make_pnp(config_dir: str = SAMPLE_CONFIG_DIR, **kwargs) -> PnPMain:
    config = PnPConfig(
        entity_id="test-entity",
        entity_name="Test Entity",
        config_dir=config_dir,
        jwt_secret="test-secret",
        log_level="WARNING",
        **kwargs,
    )
    pnp = PnPMain(config)
    pnp.bootstrap()
    return pnp


# ── Bootstrap ────────────────────────────────────────────────────────


class TestPnPBootstrap:

    def test_bootstrap_loads_sample_domains(self):
        pnp = _make_pnp()
        assert pnp.is_bootstrapped
        domain_ids = {d.domain_id for d in pnp.loaded_domains}
        assert "my-server-infra" in domain_ids
        assert "my-serverless-api" in domain_ids

    def test_bootstrap_resolves_adapters(self):
        pnp = _make_pnp()
        assert len(pnp.loaded_adapters) >= 2

    def test_bootstrap_creates_default_tenant(self):
        pnp = _make_pnp()
        assert pnp.default_tenant_id != ""
        tenant = pnp.tenant_manager.get_tenant(pnp.default_tenant_id)
        assert tenant is not None and tenant.is_active

    def test_bootstrap_creates_hierarchy_entity(self):
        pnp = _make_pnp()
        entity = pnp.hierarchy.get_entity("test-entity")
        assert entity is not None

    def test_bootstrap_auto_creates_lobs(self):
        pnp = _make_pnp()
        assert pnp.lob_store.get_lob("p-lob-infrastructure") is not None
        assert pnp.lob_store.get_lob("p-lob-api") is not None

    def test_bootstrap_audits_actions(self):
        pnp = _make_pnp()
        records = pnp.audit.query(tenant_id=pnp.default_tenant_id)
        action_types = {r.action_type for r in records}
        assert "tenant_created" in action_types
        assert "domain_registered" in action_types

    def test_bootstrap_without_config_dir(self):
        config = PnPConfig(
            entity_id="empty", entity_name="Empty",
            config_dir="", jwt_secret="test", log_level="WARNING",
        )
        pnp = PnPMain(config)
        pnp.bootstrap()
        assert pnp.is_bootstrapped and len(pnp.loaded_domains) == 0

    def test_bootstrap_with_nonexistent_config_dir(self):
        config = PnPConfig(
            entity_id="test", entity_name="Test",
            config_dir="/nonexistent/path", jwt_secret="test", log_level="WARNING",
        )
        pnp = PnPMain(config)
        pnp.bootstrap()
        assert pnp.is_bootstrapped and len(pnp.loaded_domains) == 0

    def test_not_bootstrapped_raises(self):
        config = PnPConfig(
            entity_id="test", entity_name="Test",
            jwt_secret="test", log_level="WARNING",
        )
        pnp = PnPMain(config)
        with pytest.raises(PnPBootstrapError):
            pnp.render_dashboard(user_id="u1", role="admin")


# ── Product Hierarchy ────────────────────────────────────────────────


class TestProductHierarchy:

    def test_product_families_created_from_yaml(self):
        pnp = _make_pnp()
        families = pnp.hierarchy.list_product_families(domain_id="my-server-infra")
        family_ids = {f.family_id for f in families}
        assert "web-tier" in family_ids
        assert "app-tier" in family_ids

    def test_hierarchy_domains_created(self):
        pnp = _make_pnp()
        domains = pnp.hierarchy.list_domains()
        domain_ids = {d.domain_id for d in domains}
        assert "my-server-infra" in domain_ids
        assert "my-serverless-api" in domain_ids

    def test_product_family_has_correct_parent(self):
        pnp = _make_pnp()
        wt = pnp.hierarchy.get_product_family("web-tier")
        assert wt is not None
        assert wt.domain_id == "my-server-infra"

    def test_domain_with_families_blocks_deletion(self):
        pnp = _make_pnp()
        with pytest.raises(ReferentialIntegrityError):
            pnp.hierarchy.delete_domain("my-server-infra")

    def test_domain_registration_carries_product_families(self):
        pnp = _make_pnp()
        reg = next(d for d in pnp.loaded_domains if d.domain_id == "my-server-infra")
        assert len(reg.product_families) == 2

    def test_auto_creates_entity_for_yaml_entity_id(self):
        """Hierarchy auto-creates Entity nodes for entity_ids in YAML configs."""
        pnp = _make_pnp()
        # sample configs use entity_id="my-company"
        entity = pnp.hierarchy.get_entity("my-company")
        assert entity is not None


# ── Governance ───────────────────────────────────────────────────────


class TestPnPGovernance:

    def test_superuser_sees_all_domains(self):
        pnp = _make_pnp()
        result = pnp.evaluate_access(user_id="u1", role="superuser")
        assert result.is_unrestricted
        assert len(result.authorized_domains) == 2

    def test_operator_scoped_to_assigned_lobs(self):
        pnp = _make_pnp()
        result = pnp.evaluate_access(
            user_id="u1", role="operator",
            lob_assignments=["p-lob-infrastructure"],
        )
        assert "my-server-infra" in result.authorized_domains
        assert "my-serverless-api" not in result.authorized_domains

    def test_empty_lob_assignments_sees_nothing(self):
        pnp = _make_pnp()
        result = pnp.evaluate_access(user_id="u1", role="operator", lob_assignments=[])
        assert len(result.authorized_domains) == 0


# ── Dashboard ────────────────────────────────────────────────────────


class TestPnPDashboard:

    def test_render_includes_core_panels(self):
        pnp = _make_pnp()
        panels = pnp.render_dashboard(
            user_id="u1", role="operator",
            lob_assignments=["p-lob-infrastructure"],
        )
        core_ids = {p.panel_id for p in panels if p.source == "core"}
        assert "core:tenant-overview" in core_ids

    def test_render_includes_adapter_panels(self):
        pnp = _make_pnp()
        panels = pnp.render_dashboard(user_id="u1", role="superuser")
        adapter_panels = [p for p in panels if p.source != "core"]
        assert len(adapter_panels) > 0

    def test_render_with_jwt_token(self):
        pnp = _make_pnp()
        token = pnp.register_user(
            email="test@example.com", password="testpass",
            user_id="u1", role="superuser",
            lob_assignments=["p-lob-infrastructure", "p-lob-api"],
        )
        panels = pnp.render_dashboard(token=token)
        assert len(panels) > 3


# ── Auth ─────────────────────────────────────────────────────────────


class TestPnPAuth:

    def test_register_user_returns_token(self):
        pnp = _make_pnp()
        token = pnp.register_user(
            email="admin@test.com", password="secure",
            user_id="admin-1", role="admin",
        )
        assert token is not None and len(token) > 0

    def test_authenticate_valid(self):
        pnp = _make_pnp()
        pnp.register_user(email="u@t.com", password="p", user_id="u1", role="operator")
        assert pnp.authenticate("u@t.com", "p") is not None

    def test_authenticate_invalid(self):
        pnp = _make_pnp()
        assert pnp.authenticate("nobody@t.com", "wrong") is None

    def test_registered_user_has_rbac_role(self):
        pnp = _make_pnp()
        pnp.register_user(email="o@t.com", password="p", user_id="op-1", role="operator")
        assert pnp.rbac.get_user_role("op-1") == "operator"


# ── Runtime Domain Management ────────────────────────────────────────


class TestPnPRuntimeDomains:

    def test_register_domain_at_runtime(self):
        pnp = _make_pnp()
        initial = len(pnp.loaded_domains)
        reg = DomainRegistration(
            domain_id="runtime-domain", runtime_type="server",
            observability_adapter="packages.observability.adapters.server.adapter.ServerAdapter",
            roles=["operator"], tabs=[{"title": "Panel"}],
            entity_id="test-entity", lob_id="p-lob-runtime",
        )
        pnp.register_domain(reg)
        assert len(pnp.loaded_domains) == initial + 1
        result = pnp.evaluate_access(user_id="u1", role="superuser")
        assert "runtime-domain" in result.authorized_domains

    def test_unregister_domain_at_runtime(self):
        pnp = _make_pnp()
        pnp.unregister_domain("my-serverless-api")
        result = pnp.evaluate_access(user_id="u1", role="superuser")
        assert "my-serverless-api" not in result.authorized_domains

    def test_register_domain_with_adapter_override(self):
        pnp = _make_pnp()
        adapter = ServerAdapter(entity_id="test", domain="custom")
        reg = DomainRegistration(
            domain_id="custom-domain", runtime_type="server",
            observability_adapter="custom.ServerAdapter",
            roles=["operator"], tabs=[{"title": "Panel"}],
            entity_id="test-entity", lob_id="p-lob-custom",
        )
        pnp.register_domain(reg, adapter=adapter)
        assert "custom.ServerAdapter" in pnp.loaded_adapters

    def test_register_domain_with_product_families(self):
        pnp = _make_pnp()
        reg = DomainRegistration(
            domain_id="new-product", runtime_type="server",
            observability_adapter="packages.observability.adapters.server.adapter.ServerAdapter",
            roles=["operator"], tabs=[{"title": "Panel"}],
            entity_id="test-entity", lob_id="p-lob-new",
            product_families=[
                {"family_id": "type-a", "name": "Type A"},
                {"family_id": "type-b", "name": "Type B"},
            ],
        )
        pnp.register_domain(reg)
        families = pnp.hierarchy.list_product_families(domain_id="new-product")
        assert {f.family_id for f in families} == {"type-a", "type-b"}


# ── Adapter Overrides ────────────────────────────────────────────────


class TestPnPAdapterOverrides:

    def test_adapter_override_used(self):
        mock = ServerAdapter(entity_id="mock", domain="mock")
        config = PnPConfig(
            entity_id="test", entity_name="Test",
            config_dir=SAMPLE_CONFIG_DIR, jwt_secret="test", log_level="WARNING",
            adapter_overrides={
                "packages.observability.adapters.server.adapter.ServerAdapter": mock,
            },
        )
        pnp = PnPMain(config)
        pnp.bootstrap()
        assert pnp.loaded_adapters.get(
            "packages.observability.adapters.server.adapter.ServerAdapter"
        ) is mock
