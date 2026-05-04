"""Tests for EA-MA — Empirical-AiS Mesh Architecture.

Covers:
- EAISPnPMain bootstrap with EAIS-specific layers
- Email domain enforcement: @empirical-ais.com required, others rejected
- Environment awareness: local/staging/production
- Auto LOB assignment for @empirical-ais.com users
- Default role assignment
- BAIVerticalManager: add/remove/list/get verticals, resource management
- ProductCatalog: snapshot, get_product, list_products_for_user
- EAIS RBAC: compliance_officer, bai_analyst custom roles
- Cross-product queries: get_user_verticals, get_compliance_summary
- Governance, Dashboard, Auth, Audit, Runtime domains
- End-to-end flows
"""

from __future__ import annotations

import os

import pytest

from ea_ma.preset import create_eais_config, create_eais_pnp
from ea_ma.pnp import (
    EAISPnPMain,
    EAISEnvironment,
    BAIVerticalManager,
    ProductCatalog,
    UnauthorizedEmailDomainError,
)
from packages.core.pnp import PnPConfig
from packages.core.domain_registry.registration import DomainRegistration
from packages.core.domain_registry.hierarchy import ReferentialIntegrityError, NotFoundError

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")


def _pnp(env=EAISEnvironment.LOCAL, enforce=True, **kw) -> EAISPnPMain:
    return create_eais_pnp(
        jwt_secret="test", config_dir=CONFIG_DIR, log_level="WARNING",
        environment=env, enforce_email_domain=enforce, **kw,
    )


# ── Bootstrap ────────────────────────────────────────────────────────


class TestBootstrap:

    def test_is_eais_pnp_main(self):
        assert isinstance(_pnp(), EAISPnPMain)

    def test_loads_all_domains(self):
        ids = {d.domain_id for d in _pnp().loaded_domains}
        assert ids == {"bai", "cybersecurity-ai", "genai-platform", "rag-pipeline"}

    def test_bai_manager_initialized(self):
        assert isinstance(_pnp().bai, BAIVerticalManager)

    def test_catalog_initialized(self):
        assert isinstance(_pnp().catalog, ProductCatalog)

    def test_environment_local(self):
        assert _pnp(env=EAISEnvironment.LOCAL).environment == EAISEnvironment.LOCAL

    def test_environment_production(self):
        assert _pnp(env=EAISEnvironment.PRODUCTION).environment == EAISEnvironment.PRODUCTION

    def test_environment_staging(self):
        assert _pnp(env=EAISEnvironment.STAGING).environment == EAISEnvironment.STAGING


# ── Email Domain Enforcement ─────────────────────────────────────────


class TestEmailDomainEnforcement:

    def test_eais_email_accepted(self):
        """@empirical-ais.com users can register."""
        pnp = _pnp()
        token = pnp.register_user(
            email="alice@empirical-ais.com", password="pass", user_id="a1",
        )
        assert token is not None

    def test_non_eais_email_rejected(self):
        """Non-EAIS email domains are rejected."""
        pnp = _pnp()
        with pytest.raises(UnauthorizedEmailDomainError) as exc_info:
            pnp.register_user(
                email="hacker@evil.com", password="pass", user_id="h1",
            )
        assert "@evil.com" in str(exc_info.value)

    def test_gmail_rejected(self):
        pnp = _pnp()
        with pytest.raises(UnauthorizedEmailDomainError):
            pnp.register_user(email="user@gmail.com", password="p", user_id="g1")

    def test_enforcement_in_production(self):
        """Email enforcement works in production environment."""
        pnp = _pnp(env=EAISEnvironment.PRODUCTION)
        with pytest.raises(UnauthorizedEmailDomainError):
            pnp.register_user(email="user@other.com", password="p", user_id="o1")

    def test_enforcement_in_staging(self):
        """Email enforcement works in staging environment."""
        pnp = _pnp(env=EAISEnvironment.STAGING)
        with pytest.raises(UnauthorizedEmailDomainError):
            pnp.register_user(email="user@other.com", password="p", user_id="o1")

    def test_enforcement_in_local(self):
        """Email enforcement works in local environment."""
        pnp = _pnp(env=EAISEnvironment.LOCAL)
        with pytest.raises(UnauthorizedEmailDomainError):
            pnp.register_user(email="user@other.com", password="p", user_id="o1")

    def test_enforcement_disabled(self):
        """When enforcement is off, any email domain is accepted."""
        pnp = _pnp(enforce=False)
        token = pnp.register_user(
            email="anyone@anywhere.com", password="p", user_id="any1", role="viewer",
        )
        assert token is not None

    def test_partner_domain_added(self):
        """Partner domains can be added to the allowed list."""
        pnp = _pnp(allowed_email_domains={"empirical-ais.com", "partner.co"})
        token = pnp.register_user(
            email="bob@partner.co", password="p", user_id="b1", role="viewer",
        )
        assert token is not None

    def test_authenticate_rejects_bad_domain(self):
        """authenticate() also validates email domain."""
        pnp = _pnp()
        with pytest.raises(UnauthorizedEmailDomainError):
            pnp.authenticate("user@evil.com", "pass")

    def test_invalid_email_format_rejected(self):
        pnp = _pnp()
        with pytest.raises(UnauthorizedEmailDomainError):
            pnp.register_user(email="no-at-sign", password="p", user_id="bad1")

    def test_case_insensitive_domain(self):
        """Email domain check is case-insensitive."""
        pnp = _pnp()
        token = pnp.register_user(
            email="Alice@Empirical-AiS.COM", password="p", user_id="ci1",
        )
        assert token is not None


# ── Auto LOB & Role Assignment ───────────────────────────────────────


class TestAutoAssignment:

    def test_eais_user_gets_default_lobs(self):
        """@empirical-ais.com user with no explicit LOBs gets all EAIS LOBs."""
        pnp = _pnp()
        token = pnp.register_user(
            email="auto@empirical-ais.com", password="p", user_id="auto1",
        )
        # Verify they can see all 4 domains (because they got all LOBs)
        claims = pnp.auth.get_user_claims(token)
        result = pnp.evaluate_access(
            user_id="auto1", role=claims.role,
            lob_assignments=claims.lob_assignments,
        )
        assert len(result.authorized_domains) == 4

    def test_eais_user_gets_default_role(self):
        """@empirical-ais.com user with no explicit role gets 'operator'."""
        pnp = _pnp()
        pnp.register_user(
            email="def@empirical-ais.com", password="p", user_id="def1",
        )
        assert pnp.rbac.get_user_role("def1") == "operator"

    def test_explicit_role_overrides_default(self):
        """Explicit role overrides the default."""
        pnp = _pnp()
        pnp.register_user(
            email="admin@empirical-ais.com", password="p",
            user_id="adm1", role="admin",
        )
        assert pnp.rbac.get_user_role("adm1") == "admin"

    def test_explicit_lobs_override_default(self):
        """Explicit LOB assignments override the defaults."""
        pnp = _pnp()
        token = pnp.register_user(
            email="scoped@empirical-ais.com", password="p",
            user_id="sc1", lob_assignments=["p-lob-bai"],
        )
        claims = pnp.auth.get_user_claims(token)
        assert claims.lob_assignments == ["p-lob-bai"]

    def test_partner_domain_gets_viewer_role(self):
        """Partner domain users default to viewer role."""
        pnp = _pnp(allowed_email_domains={"empirical-ais.com", "partner.co"})
        pnp.register_user(
            email="bob@partner.co", password="p", user_id="p1",
        )
        assert pnp.rbac.get_user_role("p1") == "viewer"

    def test_partner_domain_gets_no_default_lobs(self):
        """Partner domain users get no default LOBs."""
        pnp = _pnp(
            enforce=True,
            allowed_email_domains={"empirical-ais.com", "partner.co"},
        )
        token = pnp.register_user(
            email="bob@partner.co", password="p", user_id="p2",
        )
        claims = pnp.auth.get_user_claims(token)
        result = pnp.evaluate_access(
            user_id="p2", role=claims.role,
            lob_assignments=claims.lob_assignments,
        )
        assert len(result.authorized_domains) == 0


# ── BAI Vertical Manager ────────────────────────────────────────────


class TestBAIVerticalManager:

    def test_list_verticals(self):
        ids = {v.family_id for v in _pnp().bai.list_verticals()}
        assert ids == {
            "bai-restaurant-intelligence", "bai-supermarket-intelligence",
            "bai-it-consulting-100", "bai-realestate",
        }

    def test_add_and_remove_vertical(self):
        pnp = _pnp()
        pnp.bai.add_vertical("bai-temp", "Temporary")
        assert pnp.bai.vertical_count == 5
        pnp.bai.remove_vertical("bai-temp")
        assert pnp.bai.vertical_count == 4

    def test_remove_with_resources_blocked(self):
        pnp = _pnp()
        pnp.bai.add_vertical("bai-blocked", "Blocked")
        pnp.bai.add_resource("bai-blocked", "r1", "Resource 1")
        with pytest.raises(ReferentialIntegrityError):
            pnp.bai.remove_vertical("bai-blocked")

    def test_get_vertical_wrong_domain(self):
        assert _pnp().bai.get_vertical("cybersec-zkp-zdv") is None


# ── Product Catalog ──────────────────────────────────────────────────


class TestProductCatalog:

    def test_snapshot(self):
        snap = _pnp().catalog.snapshot()
        assert len(snap.products) == 4
        assert snap.total_verticals == 6

    def test_list_products_for_scoped_user(self):
        pnp = _pnp()
        products = pnp.catalog.list_products_for_user(
            user_id="u1", role="operator", lob_assignments=["p-lob-bai"],
        )
        assert len(products) == 1 and products[0].domain_id == "bai"


# ── EAIS RBAC ────────────────────────────────────────────────────────


class TestEAISRBAC:

    def test_compliance_officer_exists(self):
        assert _pnp().rbac.get_role("compliance_officer") is not None

    def test_bai_analyst_exists(self):
        assert _pnp().rbac.get_role("bai_analyst") is not None

    def test_compliance_officer_read_only(self):
        pnp = _pnp()
        assert pnp.rbac.has_permission("compliance_officer", "audit", "read")
        assert not pnp.rbac.has_permission("compliance_officer", "audit", "write")


# ── Cross-Product Queries ────────────────────────────────────────────


class TestCrossProductQueries:

    def test_compliance_summary_includes_environment(self):
        pnp = _pnp(env=EAISEnvironment.PRODUCTION)
        comp = pnp.get_compliance_summary()
        assert comp["environment"] == "production"
        assert comp["email_enforcement"] is True
        assert "empirical-ais.com" in comp["allowed_email_domains"]

    def test_user_verticals_superuser(self):
        verts = _pnp().get_user_verticals(user_id="u1", role="superuser")
        assert "bai" in verts and len(verts["bai"]) == 4


# ── Governance ───────────────────────────────────────────────────────


class TestGovernance:

    def test_superuser_unrestricted(self):
        r = _pnp().evaluate_access(user_id="u1", role="superuser")
        assert r.is_unrestricted and len(r.authorized_domains) == 4

    def test_auditor_denied_admin(self):
        pnp = _pnp()
        assert not pnp.governance.can_perform_admin_action("auditor", "delete", "domains")


# ── End-to-End ───────────────────────────────────────────────────────


class TestEndToEnd:

    def test_full_eais_flow(self):
        """Bootstrap → register @empirical-ais.com user → auto LOBs → render → catalog."""
        pnp = _pnp(env=EAISEnvironment.PRODUCTION)

        # Register — no explicit role or LOBs
        token = pnp.register_user(
            email="newuser@empirical-ais.com", password="secure", user_id="new1",
        )

        # Should have operator role and all LOBs
        claims = pnp.auth.get_user_claims(token)
        assert claims.role == "operator"
        assert set(claims.lob_assignments) == {"p-lob-bai", "p-lob-cybersecurity", "p-lob-genai", "p-lob-rag"}

        # Render dashboard — should see all 4 domains
        panels = pnp.render_dashboard(token=token)
        assert len(panels) > 3

        # Catalog shows all products
        snap = pnp.catalog.snapshot()
        assert len(snap.products) == 4

        # Non-EAIS email rejected
        with pytest.raises(UnauthorizedEmailDomainError):
            pnp.register_user(email="outsider@gmail.com", password="p", user_id="out1")

    def test_scoped_operator_flow(self):
        """Operator with explicit LOBs sees only their products."""
        pnp = _pnp()
        token = pnp.register_user(
            email="op@empirical-ais.com", password="p",
            user_id="op1", lob_assignments=["p-lob-cybersecurity"],
        )
        panels = pnp.render_dashboard(token=token)
        adapter = [p for p in panels if p.source != "core"]
        for p in adapter:
            assert "cybersecurity" in p.panel_id or p.is_degraded
