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
    ClientMaintenanceManager,
    ProductCatalog,
    UnauthorizedEmailDomainError,
    SignupDestination,
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
        assert ids == {"bai", "cybersecurity-ai", "genai-platform", "rag-pipeline", "client-maintenance"}

    def test_client_maintenance_manager_initialized(self):
        assert isinstance(_pnp().client_maintenance, ClientMaintenanceManager)

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
        """@empirical-ais.com user gets all p-lobs + i-lobs."""
        pnp = _pnp()
        token = pnp.register_user(
            email="auto@empirical-ais.com", password="p", user_id="auto1",
        )
        claims = pnp.auth.get_user_claims(token)
        # Should include both p-lob and i-lob assignments
        assert "p-lob-bai" in claims.lob_assignments
        assert "i-lob-client-maintenance" in claims.lob_assignments
        result = pnp.evaluate_access(
            user_id="auto1", role=claims.role,
            lob_assignments=claims.lob_assignments,
        )
        # 4 p-lob domains + 1 i-lob domain
        assert len(result.authorized_domains) == 5

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
        assert len(snap.products) == 5   # 4 p-lob + 1 i-lob
        assert snap.total_verticals == 9  # 4 BAI + 2 cybersec + 3 client-maintenance

    def test_i_lob_product_has_correct_lob_type(self):
        pnp = _pnp()
        cm = pnp.catalog.get_product("client-maintenance")
        assert cm is not None
        assert cm.lob_type == "infrastructure"

    def test_p_lob_product_has_correct_lob_type(self):
        pnp = _pnp()
        bai = pnp.catalog.get_product("bai")
        assert bai is not None
        assert bai.lob_type == "product"

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

    def test_platform_operator_exists(self):
        assert _pnp().rbac.get_role("platform_operator") is not None

    def test_client_manager_exists(self):
        assert _pnp().rbac.get_role("client_manager") is not None

    def test_compliance_officer_read_only(self):
        pnp = _pnp()
        assert pnp.rbac.has_permission("compliance_officer", "audit", "read")
        assert not pnp.rbac.has_permission("compliance_officer", "audit", "write")

    def test_platform_operator_has_tenant_write(self):
        pnp = _pnp()
        assert pnp.rbac.has_permission("platform_operator", "tenants", "write")
        assert pnp.rbac.has_permission("platform_operator", "audit", "read")


# ── Client Maintenance (i-lob) ───────────────────────────────────────


class TestClientMaintenance:

    def test_manager_initialized(self):
        assert isinstance(_pnp().client_maintenance, ClientMaintenanceManager)

    def test_onboard_client(self):
        pnp = _pnp()
        record = pnp.client_maintenance.onboard_client(
            client_id="c1", company_name="Sports Avatar LLC",
            contact_email="ops@sports-avatar.ai", plan="growth",
            lob_assignments=["p-lob-bai"],
        )
        assert record.client_id == "c1"
        assert record.status == "active"
        assert pnp.client_maintenance.client_count == 1

    def test_duplicate_client_raises(self):
        pnp = _pnp()
        pnp.client_maintenance.onboard_client("c2", "Acme", "a@acme.com", "growth")
        with pytest.raises(ValueError, match="already exists"):
            pnp.client_maintenance.onboard_client("c2", "Acme", "a@acme.com", "growth")

    def test_update_client_status(self):
        pnp = _pnp()
        pnp.client_maintenance.onboard_client("c3", "Corp", "x@corp.com", "enterprise")
        record = pnp.client_maintenance.update_client_status("c3", "suspended")
        assert record.status == "suspended"

    def test_list_clients_by_status(self):
        pnp = _pnp()
        pnp.client_maintenance.onboard_client("c4", "A", "a@a.com", "growth")
        pnp.client_maintenance.onboard_client("c5", "B", "b@b.com", "growth")
        pnp.client_maintenance.update_client_status("c5", "offboarded")
        active = pnp.client_maintenance.list_clients(status="active")
        assert len(active) == 1 and active[0].client_id == "c4"

    def test_client_maintenance_domain_loaded(self):
        ids = {d.domain_id for d in _pnp().loaded_domains}
        assert "client-maintenance" in ids

    def test_client_maintenance_is_i_lob(self):
        pnp = _pnp()
        reg = next(d for d in pnp.loaded_domains if d.domain_id == "client-maintenance")
        assert reg.lob_id == "i-lob-client-maintenance"


# ── Cross-Product Queries ────────────────────────────────────────────


class TestCrossProductQueries:

    def test_compliance_summary_includes_environment(self):
        pnp = _pnp(env=EAISEnvironment.PRODUCTION)
        comp = pnp.get_compliance_summary()
        assert comp["environment"] == "production"
        assert comp["email_enforcement"] is True
        assert "empirical-ais.com" in comp["allowed_email_domains"]
        assert "client-maintenance" in comp["i_lob_domains"]
        assert "bai" in comp["p_lob_domains"]

    def test_user_verticals_superuser(self):
        verts = _pnp().get_user_verticals(user_id="u1", role="superuser")
        assert "bai" in verts and len(verts["bai"]) == 4


# ── Governance ───────────────────────────────────────────────────────


class TestGovernance:

    def test_superuser_unrestricted(self):
        r = _pnp().evaluate_access(user_id="u1", role="superuser")
        assert r.is_unrestricted and len(r.authorized_domains) == 5

    def test_auditor_denied_admin(self):
        pnp = _pnp()
        assert not pnp.governance.can_perform_admin_action("auditor", "delete", "domains")


# ── End-to-End ───────────────────────────────────────────────────────


class TestEndToEnd:

    def test_full_eais_flow(self):
        """Bootstrap → register @empirical-ais.com → p-lob + i-lob → render → catalog."""
        pnp = _pnp(env=EAISEnvironment.PRODUCTION)

        token = pnp.register_user(
            email="newuser@empirical-ais.com", password="secure", user_id="new1",
        )

        claims = pnp.auth.get_user_claims(token)
        assert claims.role == "operator"
        # p-lobs + i-lob
        assert set(claims.lob_assignments) == {
            "p-lob-bai", "p-lob-cybersecurity", "p-lob-genai", "p-lob-rag",
            "i-lob-client-maintenance",
        }

        panels = pnp.render_dashboard(token=token)
        assert len(panels) > 3

        snap = pnp.catalog.snapshot()
        assert len(snap.products) == 5   # 4 p-lob + 1 i-lob

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


# ── Signup Routing ────────────────────────────────────────────────────


class TestSignupRouting:
    """Tests for plug-n-play-infra.ai/signup routing logic."""

    def test_eais_signup_routes_to_pnp(self):
        """@empirical-ais.com → destination=EAIS_PNP, token issued."""
        from ea_ma.pnp import SignupRequest, SignupDestination
        pnp = _pnp()
        result = pnp.signup(SignupRequest(
            email="alice@empirical-ais.com",
            password="Secure1!",
            company_name="Empirical-AiS",
            location="Charlotte, NC",
            product_type="BAI",
        ))
        assert result.destination == SignupDestination.EAIS_PNP
        assert result.destination.value == "pnp-prod/EAISPnPMain"
        assert result.token is not None
        assert result.role == "operator"
        assert result.subscriber_profile is None
        assert result.requires_email_verification is False

    def test_outsider_signup_routes_to_subscriber(self):
        """@sports-avatar.ai → destination=SUBSCRIBER_PORTAL, email verification required."""
        from ea_ma.pnp import SignupRequest, SignupDestination
        pnp = _pnp()
        result = pnp.signup(SignupRequest(
            email="info@sports-avatar.ai",
            password="Secure1!",
            company_name="Sports Avatar LLC",
            location="New York, NY",
            product_type="BAI",
        ))
        assert result.destination == SignupDestination.SUBSCRIBER_PORTAL
        assert result.role == "subscriber"
        assert result.requires_email_verification is True
        assert result.masked_email == "i****@sports-avatar.ai"
        assert result.subscriber_profile is not None
        assert result.subscriber_profile.product_type == "BAI"
        assert result.subscriber_profile.lob_id == "p-lob-bai"

    def test_outsider_subscriber_profile_stored(self):
        """Subscriber profile is retrievable after signup."""
        from ea_ma.pnp import SignupRequest
        pnp = _pnp()
        result = pnp.signup(SignupRequest(
            email="bob@outside-eais.com",
            password="Secure1!",
            company_name="Outside Corp",
            location="Austin, TX",
            product_type="BAI",
        ))
        profile = pnp.get_subscriber_profile(result.user_id)
        assert profile is not None
        assert profile.company_name == "Outside Corp"
        assert profile.product_type == "BAI"
        assert profile.lob_id == "p-lob-bai"
        assert profile.role == "subscriber"

    def test_list_subscribers_shows_outsiders_only(self):
        """list_subscribers() returns only outsider subscriber profiles."""
        from ea_ma.pnp import SignupRequest
        pnp = _pnp()
        pnp.signup(SignupRequest(
            email="sub1@outside.com", password="P1!", company_name="Co1",
            location="LA", product_type="BAI",
        ))
        pnp.signup(SignupRequest(
            email="internal@empirical-ais.com", password="P1!", company_name="EAIS",
            location="Charlotte", product_type="BAI",
        ))
        subs = pnp.list_subscribers()
        emails = {s.email for s in subs}
        assert "sub1@outside.com" in emails
        assert "internal@empirical-ais.com" not in emails

    def test_subscriber_role_defined(self):
        """subscriber RBAC role is defined after bootstrap."""
        assert _pnp().rbac.get_role("subscriber") is not None

    def test_product_type_bai_resolves_to_p_lob_bai(self):
        """product_type='BAI' always resolves to p-lob-bai."""
        pnp = _pnp()
        assert pnp._resolve_lob_for_product_type("BAI") == "p-lob-bai"
        assert pnp._resolve_lob_for_product_type("bai") == "p-lob-bai"

    def test_password_mismatch_raises(self):
        """Mismatched confirm_password raises ValueError."""
        from ea_ma.pnp import SignupRequest
        pnp = _pnp()
        with pytest.raises(ValueError, match="Passwords do not match"):
            pnp.signup(SignupRequest(
                email="x@empirical-ais.com", password="abc", confirm_password="xyz",
                company_name="X", location="X", product_type="BAI",
            ))

    def test_subscriber_portal_renders_scoped_dashboard(self):
        """Subscriber portal renders a dashboard scoped to BAI LOB."""
        from ea_ma.pnp import SignupRequest
        pnp = _pnp()
        result = pnp.signup(SignupRequest(
            email="portal@sports-avatar.ai", password="P1!",
            company_name="Sports Avatar", location="NYC", product_type="BAI",
        ))
        dashboard = pnp.subscriber_portal.render(result.token)
        assert dashboard.product_type == "BAI"
        assert dashboard.lob_id == "p-lob-bai"
        assert dashboard.company_name == "Sports Avatar"
