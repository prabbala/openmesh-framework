"""Tests for SA-MA — Sports-Avatar Mesh Architecture.

Covers:
- Bootstrap: both products loaded, adapters resolved, hierarchy populated
- Product hierarchy: Animation Engine families, Cric-Avatar families
- Governance: superuser unrestricted, operator LOB-scoped, auditor read-only
- Dashboard: core panels, adapter panels, role-filtered rendering
- Auth: register, authenticate, JWT token flow
- Audit: bootstrap actions recorded
- Runtime: hot-register/unregister domains
- End-to-end flows
"""

from __future__ import annotations

import os

import pytest

from sa_ma.preset import create_sa_config, create_sa_pnp
from packages.core.domain_registry.registration import DomainRegistration
from packages.core.domain_registry.hierarchy import ReferentialIntegrityError

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")


def _pnp(**kw):
    return create_sa_pnp(jwt_secret="test", config_dir=CONFIG_DIR, log_level="WARNING", **kw)


# ── Bootstrap ────────────────────────────────────────────────────────


class TestBootstrap:

    def test_loads_all_domains(self):
        pnp = _pnp()
        ids = {d.domain_id for d in pnp.loaded_domains}
        assert ids == {"animation-engine", "cric-avatar"}

    def test_resolves_gpu_and_streaming_adapters(self):
        pnp = _pnp()
        paths = set(pnp.loaded_adapters.keys())
        assert any("GPUAdapter" in p for p in paths)
        assert any("StreamingAdapter" in p for p in paths)

    def test_creates_entity_in_hierarchy(self):
        pnp = _pnp()
        assert pnp.hierarchy.get_entity("sports-avatar") is not None

    def test_creates_default_tenant(self):
        pnp = _pnp()
        t = pnp.tenant_manager.get_tenant(pnp.default_tenant_id)
        assert t is not None and t.is_active

    def test_auto_creates_lobs(self):
        pnp = _pnp()
        assert pnp.lob_store.get_lob("p-lob-animation") is not None
        assert pnp.lob_store.get_lob("p-lob-cric-avatar") is not None

    def test_config_entity_id(self):
        cfg = create_sa_config(log_level="WARNING")
        assert cfg.entity_id == "sports-avatar"
        assert cfg.entity_name == "Sports-Avatar LLC"


# ── Product Hierarchy ────────────────────────────────────────────────


class TestProductHierarchy:

    def test_animation_engine_families(self):
        pnp = _pnp()
        fams = pnp.hierarchy.list_product_families(domain_id="animation-engine")
        ids = {f.family_id for f in fams}
        assert ids == {"anim-blender-pipeline", "anim-motion-capture"}

    def test_cric_avatar_families(self):
        pnp = _pnp()
        fams = pnp.hierarchy.list_product_families(domain_id="cric-avatar")
        ids = {f.family_id for f in fams}
        assert ids == {"cric-live-stream", "cric-replay-engine"}

    def test_family_parent_correct(self):
        pnp = _pnp()
        bp = pnp.hierarchy.get_product_family("anim-blender-pipeline")
        assert bp.domain_id == "animation-engine"
        assert bp.name == "Blender Pipeline"

    def test_cannot_delete_domain_with_families(self):
        pnp = _pnp()
        with pytest.raises(ReferentialIntegrityError):
            pnp.hierarchy.delete_domain("animation-engine")

    def test_both_domains_in_hierarchy(self):
        pnp = _pnp()
        ids = {d.domain_id for d in pnp.hierarchy.list_domains()}
        assert {"animation-engine", "cric-avatar"}.issubset(ids)


# ── Governance ───────────────────────────────────────────────────────


class TestGovernance:

    def test_superuser_unrestricted(self):
        pnp = _pnp()
        r = pnp.evaluate_access(user_id="u1", role="superuser")
        assert r.is_unrestricted and len(r.authorized_domains) == 2

    def test_operator_scoped_to_animation(self):
        pnp = _pnp()
        r = pnp.evaluate_access(user_id="u1", role="operator", lob_assignments=["p-lob-animation"])
        assert r.authorized_domains == {"animation-engine"}

    def test_operator_scoped_to_cric(self):
        pnp = _pnp()
        r = pnp.evaluate_access(user_id="u1", role="operator", lob_assignments=["p-lob-cric-avatar"])
        assert r.authorized_domains == {"cric-avatar"}

    def test_operator_both_lobs(self):
        pnp = _pnp()
        r = pnp.evaluate_access(
            user_id="u1", role="operator",
            lob_assignments=["p-lob-animation", "p-lob-cric-avatar"],
        )
        assert r.authorized_domains == {"animation-engine", "cric-avatar"}

    def test_operator_no_lobs_sees_nothing(self):
        pnp = _pnp()
        r = pnp.evaluate_access(user_id="u1", role="operator", lob_assignments=[])
        assert len(r.authorized_domains) == 0

    def test_auditor_denied_admin_actions(self):
        pnp = _pnp()
        for action in ["create", "update", "delete", "write"]:
            assert pnp.governance.can_perform_admin_action("auditor", action, "domains") is False

    def test_platform_operator_unrestricted(self):
        pnp = _pnp()
        r = pnp.evaluate_access(user_id="u1", role="platform_operator")
        assert r.is_unrestricted


# ── Dashboard ────────────────────────────────────────────────────────


class TestDashboard:

    def test_core_panels_always_present(self):
        pnp = _pnp()
        panels = pnp.render_dashboard(user_id="u1", role="viewer", lob_assignments=[])
        core_ids = {p.panel_id for p in panels if p.source == "core"}
        assert "core:tenant-overview" in core_ids
        assert "core:audit-log" in core_ids

    def test_superuser_gets_adapter_panels(self):
        pnp = _pnp()
        panels = pnp.render_dashboard(user_id="u1", role="superuser")
        adapter = [p for p in panels if p.source != "core"]
        assert len(adapter) > 0

    def test_operator_animation_only(self):
        pnp = _pnp()
        panels = pnp.render_dashboard(
            user_id="u1", role="operator", lob_assignments=["p-lob-animation"],
        )
        adapter = [p for p in panels if p.source != "core"]
        for p in adapter:
            assert "animation" in p.panel_id or p.is_degraded


# ── Auth ─────────────────────────────────────────────────────────────


class TestAuth:

    def test_register_returns_token(self):
        pnp = _pnp()
        token = pnp.register_user(
            email="a@sa.com", password="s", user_id="a1", role="admin",
        )
        assert token and len(token) > 0

    def test_authenticate_valid(self):
        pnp = _pnp()
        pnp.register_user(email="u@sa.com", password="p", user_id="u1", role="operator")
        assert pnp.authenticate("u@sa.com", "p") is not None

    def test_authenticate_invalid(self):
        pnp = _pnp()
        assert pnp.authenticate("nobody@sa.com", "wrong") is None

    def test_rbac_role_assigned(self):
        pnp = _pnp()
        pnp.register_user(email="r@sa.com", password="p", user_id="r1", role="operator")
        assert pnp.rbac.get_user_role("r1") == "operator"


# ── Audit ────────────────────────────────────────────────────────────


class TestAudit:

    def test_bootstrap_records_tenant_created(self):
        pnp = _pnp()
        recs = pnp.audit.query(tenant_id=pnp.default_tenant_id, action_type="tenant_created")
        assert len(recs) == 1

    def test_bootstrap_records_domain_registered(self):
        pnp = _pnp()
        recs = pnp.audit.query(tenant_id=pnp.default_tenant_id, action_type="domain_registered")
        assert len(recs) == 2


# ── Runtime Domain Management ────────────────────────────────────────


class TestRuntimeDomains:

    def test_register_new_domain(self):
        pnp = _pnp()
        reg = DomainRegistration(
            domain_id="new-sport", runtime_type="gpu",
            observability_adapter="packages.observability.adapters.gpu.adapter.GPUAdapter",
            roles=["operator"], tabs=[{"title": "P"}],
            entity_id="sports-avatar", lob_id="p-lob-new-sport",
            product_families=[{"family_id": "ns-type", "name": "New Sport Type"}],
        )
        pnp.register_domain(reg)
        assert "new-sport" in {d.domain_id for d in pnp.loaded_domains}
        fams = pnp.hierarchy.list_product_families(domain_id="new-sport")
        assert {f.family_id for f in fams} == {"ns-type"}

    def test_unregister_domain(self):
        pnp = _pnp()
        pnp.unregister_domain("cric-avatar")
        r = pnp.evaluate_access(user_id="u1", role="superuser")
        assert "cric-avatar" not in r.authorized_domains


# ── End-to-End ───────────────────────────────────────────────────────


class TestEndToEnd:

    def test_full_flow(self):
        pnp = _pnp()

        token = pnp.register_user(
            email="admin@sports-avatar.com", password="secure",
            user_id="sa-admin", role="superuser",
            lob_assignments=["p-lob-animation", "p-lob-cric-avatar"],
        )

        panels = pnp.render_dashboard(token=token)
        assert len(panels) > 3

        result = pnp.evaluate_access(user_id="sa-admin", role="superuser")
        assert result.is_unrestricted
        assert len(result.authorized_domains) == 2

    def test_scoped_operator_flow(self):
        pnp = _pnp()

        token = pnp.register_user(
            email="op@sports-avatar.com", password="pass",
            user_id="sa-op", role="operator",
            lob_assignments=["p-lob-animation"],
        )

        panels = pnp.render_dashboard(token=token)
        adapter = [p for p in panels if p.source != "core"]
        for p in adapter:
            assert "animation" in p.panel_id or p.is_degraded
