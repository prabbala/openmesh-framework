"""EAISPnPMain — Empirical-AiS Mesh Architecture PnP orchestrator.

Inherits from openmesh-framework (github.com/prabbala/openmesh-framework).
This is the pnp-prod entry point for ea-ma (private repo).

@empirical-ais.com users get the full om-fw stack:
  - p-lob: BAI, Cybersecurity-AI, GenAI Platform, RAG Pipeline
  - i-lob: Client Maintenance (platform ops, tenant lifecycle, observability infra)
  - RBAC: operator, compliance_officer, bai_analyst, platform_operator, client_manager
  - Governance, DashboardShell, AuditEngine, HierarchyStore — all wired via PnPMain

Outsiders → SubscriberPortal (scoped to their product_type LOB, email verification required).

Usage:
    from ea_ma.pnp.EAISPnPMain import EAISPnPMain, EAISEnvironment
    from ea_ma.preset import create_eais_pnp

    pnp = create_eais_pnp(jwt_secret="production-secret", environment=EAISEnvironment.PRODUCTION)

    # @empirical-ais.com → full pnp-prod access (p-lob + i-lob)
    token = pnp.register_user(email="alice@empirical-ais.com", password="s3cr3t", user_id="a1")
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from packages.core.pnp.pnp_main import PnPConfig, PnPMain
from packages.core.domain_registry.models import ProductFamily, Resource
from packages.core.domain_registry.registration import DomainRegistration
from packages.core.lob.models import LOBCategory, LOBNode
from packages.core.rbac.models import Permission
from packages.observability.interface.adapter import ObservabilityAdapterInterface

logger = logging.getLogger("ea-ma.pnp")


# ── Environment ──────────────────────────────────────────────────────


class EAISEnvironment(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class UnauthorizedEmailDomainError(Exception):
    """Raised when a user's email domain is not in the allowed list."""


class EmailVerificationRequiredError(Exception):
    """Raised when an outsider signup requires email verification."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Email verification required for '{email}'")
        self.email = email
        self.masked_email = _mask_email(email)


def _mask_email(email: str) -> str:
    local, domain = email.rsplit("@", 1)
    return f"{local[0]}****@{domain}"


# ── Signup models ────────────────────────────────────────────────────


class SignupDestination(Enum):
    SUBSCRIBER_PORTAL = "subscriber"
    EAIS_PNP = "pnp-prod/EAISPnPMain"   # @empirical-ais.com → full om-fw stack


class SubscriberPlan(Enum):
    GROWTH = "growth"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class SignupRequest:
    """Data from the plug-n-play-infra.ai/signup form."""
    email: str
    password: str
    company_name: str
    location: str
    product_type: str
    user_id: str = ""
    plan: SubscriberPlan = SubscriberPlan.GROWTH
    confirm_password: str = ""


@dataclass
class SubscriberProfile:
    """Profile for an outsider subscriber (non-@empirical-ais.com)."""
    user_id: str
    email: str
    company_name: str
    location: str
    product_type: str
    plan: SubscriberPlan
    tenant_id: str
    lob_id: str
    role: str = "subscriber"
    client_type: str = "Standalone"
    db_tier: str = "PostgreSQL (Free Tier)"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SignupResult:
    """Result of signup() — routes caller to the correct destination.

    destination=EAIS_PNP      → @empirical-ais.com, full pnp-prod access
    destination=SUBSCRIBER_PORTAL → outsider, scoped to product_type LOB
    """
    destination: SignupDestination
    token: Optional[str]
    user_id: str
    email: str
    role: str
    subscriber_profile: Optional[SubscriberProfile] = None
    requires_email_verification: bool = False
    masked_email: str = ""


# ── Subscriber Portal ────────────────────────────────────────────────


@dataclass
class SubscriberDashboard:
    user_id: str
    company_name: str
    email: str
    product_type: str
    plan: str
    lob_id: str
    tenant_id: str
    panels: List[Any] = field(default_factory=list)
    client_type: str = "Standalone"
    db_tier: str = "PostgreSQL (Free Tier)"


class SubscriberPortal:
    """Scoped portal for outsider subscribers — product_type-filtered view."""

    def __init__(self, pnp: "EAISPnPMain") -> None:
        self._pnp = pnp

    def render(self, token: str) -> SubscriberDashboard:
        claims = self._pnp.auth.get_user_claims(token)
        profile = self._pnp.get_subscriber_profile(claims.user_id)
        if profile is None:
            raise KeyError(f"No subscriber profile found for user '{claims.user_id}'")
        panels = self._pnp.render_dashboard(token=token, lob_assignments=[profile.lob_id])
        return SubscriberDashboard(
            user_id=claims.user_id,
            company_name=profile.company_name,
            email=claims.email,
            product_type=profile.product_type,
            plan=profile.plan.value,
            lob_id=profile.lob_id,
            tenant_id=claims.tenant_id,
            panels=panels,
            client_type=profile.client_type,
            db_tier=profile.db_tier,
        )

    def list_subscribers(self) -> List[SubscriberProfile]:
        return self._pnp.list_subscribers()


# ── Data models ──────────────────────────────────────────────────────


@dataclass
class VerticalInfo:
    family_id: str
    name: str
    description: str
    resource_count: int = 0


@dataclass
class ProductStatus:
    domain_id: str
    product_name: str
    runtime_type: str
    adapter_resolved: bool
    vertical_count: int
    verticals: List[str]
    lob_id: str
    lob_type: str = "product"   # "product" | "infrastructure"


@dataclass
class CatalogSnapshot:
    entity_id: str
    entity_name: str
    timestamp: datetime
    products: List[ProductStatus]
    total_verticals: int
    total_adapters: int


# ── Client record (i-lob) ────────────────────────────────────────────


@dataclass
class ClientRecord:
    """A client managed under the i-lob Client Maintenance domain."""
    client_id: str
    company_name: str
    contact_email: str
    tenant_id: str
    plan: str
    lob_assignments: List[str] = field(default_factory=list)
    status: str = "active"          # active | suspended | offboarded
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── BAI Vertical Manager ─────────────────────────────────────────────


class BAIVerticalManager:
    """Manages BAI product_type verticals at runtime via HierarchyStore."""

    BAI_DOMAIN_ID = "bai"

    def __init__(self, pnp: PnPMain) -> None:
        self._pnp = pnp

    def list_verticals(self) -> List[VerticalInfo]:
        families = self._pnp.hierarchy.list_product_families(domain_id=self.BAI_DOMAIN_ID)
        return [
            VerticalInfo(
                family_id=f.family_id,
                name=f.name,
                description=f.description,
                resource_count=len(self._pnp.hierarchy.list_resources(family_id=f.family_id)),
            )
            for f in families
        ]

    def get_vertical(self, family_id: str) -> Optional[VerticalInfo]:
        f = self._pnp.hierarchy.get_product_family(family_id)
        if f is None or f.domain_id != self.BAI_DOMAIN_ID:
            return None
        return VerticalInfo(
            family_id=f.family_id,
            name=f.name,
            description=f.description,
            resource_count=len(self._pnp.hierarchy.list_resources(family_id=f.family_id)),
        )

    def add_vertical(self, family_id: str, name: str, description: str = "") -> VerticalInfo:
        if self._pnp.hierarchy.get_domain(self.BAI_DOMAIN_ID) is None:
            raise ValueError(
                f"BAI domain '{self.BAI_DOMAIN_ID}' not found. Bootstrap must load bai.yaml first."
            )
        family = ProductFamily(family_id=family_id, domain_id=self.BAI_DOMAIN_ID, name=name, description=description)
        self._pnp.hierarchy.create_product_family(family)
        for reg in self._pnp.loaded_domains:
            if reg.domain_id == self.BAI_DOMAIN_ID:
                reg.product_families.append({"family_id": family_id, "name": name, "description": description})
                break
        self._pnp.audit.record(
            entity_id="empirical-ais", tenant_id=self._pnp.default_tenant_id,
            actor_id="system", action_type="vertical_added", resource=family_id,
            detail={"name": name, "domain": self.BAI_DOMAIN_ID},
        )
        logger.info("BAI vertical added: %s (%s)", family_id, name)
        return VerticalInfo(family_id=family_id, name=name, description=description, resource_count=0)

    def remove_vertical(self, family_id: str) -> None:
        self._pnp.hierarchy.delete_product_family(family_id)
        for reg in self._pnp.loaded_domains:
            if reg.domain_id == self.BAI_DOMAIN_ID:
                reg.product_families = [pf for pf in reg.product_families if pf.get("family_id") != family_id]
                break
        self._pnp.audit.record(
            entity_id="empirical-ais", tenant_id=self._pnp.default_tenant_id,
            actor_id="system", action_type="vertical_removed", resource=family_id,
            detail={"domain": self.BAI_DOMAIN_ID},
        )
        logger.info("BAI vertical removed: %s", family_id)

    def add_resource(self, family_id: str, resource_id: str, name: str, resource_type: str = "", metadata: Optional[Dict] = None) -> None:
        resource = Resource(resource_id=resource_id, family_id=family_id, name=name, resource_type=resource_type, metadata=metadata or {})
        self._pnp.hierarchy.create_resource(resource)
        logger.info("Resource '%s' added to vertical '%s'", resource_id, family_id)

    @property
    def vertical_count(self) -> int:
        return len(self._pnp.hierarchy.list_product_families(domain_id=self.BAI_DOMAIN_ID))


# ── Client Maintenance Manager (i-lob) ───────────────────────────────


class ClientMaintenanceManager:
    """Manages client lifecycle under the i-lob Client Maintenance domain.

    Provides onboarding, status updates, and offboarding for clients
    that subscribe to EA-MA products. Backed by the om-fw AuditEngine
    and HierarchyStore — all mutations are audited.

    This is the infrastructure-facing counterpart to BAIVerticalManager.
    """

    I_LOB_ID = "i-lob-client-maintenance"
    DOMAIN_ID = "client-maintenance"

    def __init__(self, pnp: PnPMain) -> None:
        self._pnp = pnp
        self._clients: Dict[str, ClientRecord] = {}

    def onboard_client(
        self,
        client_id: str,
        company_name: str,
        contact_email: str,
        plan: str,
        lob_assignments: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClientRecord:
        """Onboard a new client into the i-lob client maintenance domain.

        Creates a ClientRecord, assigns the client to the requested p-lobs,
        and records the event in the AuditEngine.
        """
        if client_id in self._clients:
            raise ValueError(f"Client '{client_id}' already exists")

        record = ClientRecord(
            client_id=client_id,
            company_name=company_name,
            contact_email=contact_email,
            tenant_id=self._pnp.default_tenant_id,
            plan=plan,
            lob_assignments=lob_assignments or [],
            metadata=metadata or {},
        )
        self._clients[client_id] = record

        self._pnp.audit.record(
            entity_id="empirical-ais",
            tenant_id=self._pnp.default_tenant_id,
            actor_id="system",
            action_type="client_onboarded",
            resource=client_id,
            detail={"company": company_name, "plan": plan, "lobs": lob_assignments or []},
        )
        logger.info("Client onboarded: %s (%s) plan=%s", client_id, company_name, plan)
        return record

    def update_client_status(self, client_id: str, status: str) -> ClientRecord:
        """Update a client's status: active | suspended | offboarded."""
        record = self._get_or_raise(client_id)
        old_status = record.status
        record.status = status
        self._pnp.audit.record(
            entity_id="empirical-ais",
            tenant_id=self._pnp.default_tenant_id,
            actor_id="system",
            action_type="client_status_updated",
            resource=client_id,
            detail={"old_status": old_status, "new_status": status},
        )
        logger.info("Client %s status: %s → %s", client_id, old_status, status)
        return record

    def get_client(self, client_id: str) -> Optional[ClientRecord]:
        return self._clients.get(client_id)

    def list_clients(self, status: Optional[str] = None) -> List[ClientRecord]:
        if status is not None:
            return [c for c in self._clients.values() if c.status == status]
        return list(self._clients.values())

    @property
    def client_count(self) -> int:
        return len(self._clients)

    def _get_or_raise(self, client_id: str) -> ClientRecord:
        record = self._clients.get(client_id)
        if record is None:
            raise KeyError(f"Client '{client_id}' not found")
        return record


# ── Product Catalog ──────────────────────────────────────────────────


class ProductCatalog:
    """Aggregated view of all EA-MA products (p-lob + i-lob)."""

    def __init__(self, pnp: PnPMain) -> None:
        self._pnp = pnp

    def snapshot(self) -> CatalogSnapshot:
        products = []
        total_verticals = 0
        for reg in self._pnp.loaded_domains:
            families = self._pnp.hierarchy.list_product_families(domain_id=reg.domain_id)
            total_verticals += len(families)
            lob_type = "infrastructure" if reg.lob_id.startswith("i-lob") else "product"
            products.append(ProductStatus(
                domain_id=reg.domain_id,
                product_name=reg.metadata.get("product_name", reg.domain_id),
                runtime_type=reg.runtime_type,
                adapter_resolved=reg.observability_adapter in self._pnp.loaded_adapters,
                vertical_count=len(families),
                verticals=[f.name for f in families],
                lob_id=reg.lob_id,
                lob_type=lob_type,
            ))
        return CatalogSnapshot(
            entity_id=self._pnp._config.entity_id,
            entity_name=self._pnp._config.entity_name,
            timestamp=datetime.now(timezone.utc),
            products=products,
            total_verticals=total_verticals,
            total_adapters=len(self._pnp.loaded_adapters),
        )

    def get_product(self, domain_id: str) -> Optional[ProductStatus]:
        for reg in self._pnp.loaded_domains:
            if reg.domain_id == domain_id:
                families = self._pnp.hierarchy.list_product_families(domain_id=domain_id)
                lob_type = "infrastructure" if reg.lob_id.startswith("i-lob") else "product"
                return ProductStatus(
                    domain_id=reg.domain_id,
                    product_name=reg.metadata.get("product_name", reg.domain_id),
                    runtime_type=reg.runtime_type,
                    adapter_resolved=reg.observability_adapter in self._pnp.loaded_adapters,
                    vertical_count=len(families),
                    verticals=[f.name for f in families],
                    lob_id=reg.lob_id,
                    lob_type=lob_type,
                )
        return None

    def list_products_for_user(
        self,
        user_id: str,
        role: str,
        groups: Optional[List[str]] = None,
        lob_assignments: Optional[List[str]] = None,
    ) -> List[ProductStatus]:
        result = self._pnp.evaluate_access(
            user_id=user_id, role=role, groups=groups, lob_assignments=lob_assignments,
        )
        return [p for did in result.authorized_domains if (p := self.get_product(did)) is not None]


# ── EAIS PnP Main (pnp-prod) ─────────────────────────────────────────


class EAISPnPMain(PnPMain):
    """pnp-prod/EAISPnPMain — Empirical-AiS production PnP orchestrator.

    Inherits the full om-fw stack from PnPMain (openmesh-framework):
      RBAC · Tenant · LOB · Audit · Auth · DomainRegistry · HierarchyStore
      GovernanceEngine · DashboardShell · ObservabilityAdapters

    @empirical-ais.com users get:
      p-lob: bai, cybersecurity-ai, genai-platform, rag-pipeline
      i-lob: client-maintenance (platform ops, tenant lifecycle, observability infra)

    Outsiders → SubscriberPortal (scoped to product_type LOB, email verification required).
    """

    ALLOWED_EMAIL_DOMAINS: Set[str] = {"empirical-ais.com"}

    # p-lob: product lines
    DEFAULT_P_LOBS: List[str] = [
        "p-lob-bai",
        "p-lob-cybersecurity",
        "p-lob-genai",
        "p-lob-rag",
    ]
    # i-lob: infrastructure / internal platform
    DEFAULT_I_LOBS: List[str] = [
        "i-lob-client-maintenance",
    ]

    DEFAULT_EAIS_ROLE: str = "operator"

    PRODUCT_TYPE = "BAI"
    PRODUCT_TYPE_LOB_MAP: Dict[str, str] = {
        "bai": "p-lob-bai",
        "cybersecurity": "p-lob-cybersecurity",
        "genai": "p-lob-genai",
        "rag": "p-lob-rag",
    }

    def __init__(
        self,
        config: PnPConfig,
        environment: EAISEnvironment = EAISEnvironment.LOCAL,
        allowed_email_domains: Optional[Set[str]] = None,
        enforce_email_domain: bool = True,
    ) -> None:
        super().__init__(config)
        self._environment = environment
        self._enforce_email_domain = enforce_email_domain
        self._bai: Optional[BAIVerticalManager] = None
        self._catalog: Optional[ProductCatalog] = None
        self._subscriber_portal: Optional[SubscriberPortal] = None
        self._client_maintenance: Optional[ClientMaintenanceManager] = None
        self._subscribers: Dict[str, SubscriberProfile] = {}
        if allowed_email_domains is not None:
            self.ALLOWED_EMAIL_DOMAINS = allowed_email_domains

    # ── Properties ───────────────────────────────────────────────────

    @property
    def environment(self) -> EAISEnvironment:
        return self._environment

    @property
    def enforce_email_domain(self) -> bool:
        return self._enforce_email_domain

    @property
    def bai(self) -> BAIVerticalManager:
        self._assert_bootstrapped()
        return self._bai

    @property
    def catalog(self) -> ProductCatalog:
        self._assert_bootstrapped()
        return self._catalog

    @property
    def subscriber_portal(self) -> SubscriberPortal:
        self._assert_bootstrapped()
        return self._subscriber_portal

    @property
    def client_maintenance(self) -> ClientMaintenanceManager:
        """Access the i-lob Client Maintenance manager."""
        self._assert_bootstrapped()
        return self._client_maintenance

    # ── Bootstrap ────────────────────────────────────────────────────

    def bootstrap(self) -> None:
        """Bootstrap the full om-fw stack, then initialize EAIS-specific layers."""
        super().bootstrap()
        self._bai = BAIVerticalManager(self)
        self._catalog = ProductCatalog(self)
        self._subscriber_portal = SubscriberPortal(self)
        self._client_maintenance = ClientMaintenanceManager(self)
        self._init_eais_rbac()
        logger.info(
            "pnp-prod/EAISPnPMain ready: env=%s, domains=%d, "
            "BAI verticals=%d, email_enforcement=%s, allowed_domains=%s",
            self._environment.value,
            len(self.loaded_domains),
            self._bai.vertical_count,
            self._enforce_email_domain,
            self.ALLOWED_EMAIL_DOMAINS,
        )

    def _init_eais_rbac(self) -> None:
        """Define EAIS-specific RBAC roles on top of om-fw defaults."""
        self._rbac.define_custom_role(
            "compliance_officer",
            {
                Permission("audit", "read"),
                Permission("observability", "read"),
                Permission("domains", "read"),
                Permission("dashboard", "read"),
            },
        )
        self._rbac.define_custom_role(
            "bai_analyst",
            {
                Permission("dashboard", "read"),
                Permission("observability", "read"),
                Permission("metrics", "read"),
            },
        )
        # platform_operator: i-lob access — client maintenance, tenant ops, infra observability
        self._rbac.define_custom_role(
            "platform_operator",
            {
                Permission("dashboard", "read"),
                Permission("observability", "read"),
                Permission("metrics", "read"),
                Permission("tenants", "read"),
                Permission("tenants", "write"),
                Permission("domains", "read"),
                Permission("audit", "read"),
            },
        )
        # client_manager: client lifecycle management under i-lob
        self._rbac.define_custom_role(
            "client_manager",
            {
                Permission("dashboard", "read"),
                Permission("observability", "read"),
                Permission("tenants", "read"),
                Permission("users", "read"),
            },
        )
        # subscriber: outsider read-only, scoped to their single p-lob
        self._rbac.define_custom_role(
            "subscriber",
            {
                Permission("dashboard", "read"),
                Permission("observability", "read"),
            },
        )
        logger.info(
            "EAIS custom roles defined: compliance_officer, bai_analyst, "
            "platform_operator, client_manager, subscriber"
        )


    # ── Email domain enforcement ──────────────────────────────────────

    def _validate_email_domain(self, email: str) -> str:
        if "@" not in email:
            raise UnauthorizedEmailDomainError(f"Invalid email format: '{email}'")
        domain = email.rsplit("@", 1)[1].lower()
        if self._enforce_email_domain and domain not in self.ALLOWED_EMAIL_DOMAINS:
            raise UnauthorizedEmailDomainError(
                f"Email domain '@{domain}' is not authorized for EA-MA. "
                f"Allowed domains: {', '.join(sorted(self.ALLOWED_EMAIL_DOMAINS))}"
            )
        return domain

    def _get_default_lobs_for_domain(self, email_domain: str) -> List[str]:
        """@empirical-ais.com → all p-lobs + all i-lobs (full om-fw access)."""
        if email_domain == "empirical-ais.com":
            return list(self.DEFAULT_P_LOBS) + list(self.DEFAULT_I_LOBS)
        return []

    def _get_default_role_for_domain(self, email_domain: str) -> str:
        if email_domain == "empirical-ais.com":
            return self.DEFAULT_EAIS_ROLE
        return "viewer"

    # ── Overrides ────────────────────────────────────────────────────

    def register_user(
        self,
        email: str,
        password: str,
        user_id: str,
        role: Optional[str] = None,
        groups: Optional[List[str]] = None,
        lob_assignments: Optional[List[str]] = None,
        tenant_id: str = "",
    ) -> str:
        """Register a user. @empirical-ais.com gets p-lob + i-lob access.

        Raises:
            UnauthorizedEmailDomainError: If email domain is not allowed.
        """
        self._assert_bootstrapped()
        email_domain = self._validate_email_domain(email)
        effective_role = role if role is not None else self._get_default_role_for_domain(email_domain)
        effective_lobs = lob_assignments if lob_assignments is not None else self._get_default_lobs_for_domain(email_domain)
        return super().register_user(
            email=email, password=password, user_id=user_id,
            role=effective_role, groups=groups,
            lob_assignments=effective_lobs, tenant_id=tenant_id,
        )

    def authenticate(self, email: str, password: str) -> Optional[str]:
        """Authenticate with email domain enforcement.

        Raises:
            UnauthorizedEmailDomainError: If email domain is not allowed.
        """
        self._assert_bootstrapped()
        self._validate_email_domain(email)
        return super().authenticate(email, password)

    # ── Cross-product queries ─────────────────────────────────────────

    def get_user_verticals(
        self,
        user_id: str,
        role: str,
        groups: Optional[List[str]] = None,
        lob_assignments: Optional[List[str]] = None,
    ) -> Dict[str, List[VerticalInfo]]:
        """Get all verticals visible to a user, grouped by domain."""
        self._assert_bootstrapped()
        result = self.evaluate_access(
            user_id=user_id, role=role, groups=groups, lob_assignments=lob_assignments,
        )
        return {
            domain_id: [
                VerticalInfo(
                    family_id=f.family_id,
                    name=f.name,
                    description=f.description,
                    resource_count=len(self._hierarchy.list_resources(family_id=f.family_id)),
                )
                for f in self._hierarchy.list_product_families(domain_id=domain_id)
            ]
            for domain_id in result.authorized_domains
            if self._hierarchy.list_product_families(domain_id=domain_id)
        }

    def get_compliance_summary(self) -> Dict[str, Any]:
        """Compliance summary across all EAIS products (p-lob + i-lob)."""
        self._assert_bootstrapped()
        domains = self.loaded_domains
        compliance_frameworks = {
            d.domain_id: d.metadata["compliance_framework"]
            for d in domains
            if d.metadata.get("compliance_framework")
        }
        p_lob_domains = [d.domain_id for d in domains if d.lob_id.startswith("p-lob")]
        i_lob_domains = [d.domain_id for d in domains if d.lob_id.startswith("i-lob")]
        return {
            "entity_id": self._config.entity_id,
            "environment": self._environment.value,
            "total_audit_records": self._audit.count,
            "total_domains": len(domains),
            "p_lob_domains": p_lob_domains,
            "i_lob_domains": i_lob_domains,
            "compliance_frameworks": compliance_frameworks,
            "custom_roles": ["compliance_officer", "bai_analyst", "platform_operator", "client_manager"],
            "email_enforcement": self._enforce_email_domain,
            "allowed_email_domains": sorted(self.ALLOWED_EMAIL_DOMAINS),
        }


    # ── Signup routing ────────────────────────────────────────────────

    def signup(self, request: SignupRequest) -> SignupResult:
        """Single entry point for plug-n-play-infra.ai/signup.

        @empirical-ais.com → pnp-prod/EAISPnPMain
            - operator role, all p-lobs + i-lobs, no email verification
        outsider → SubscriberPortal
            - subscriber role, scoped to product_type p-lob, email verification required
        """
        self._assert_bootstrapped()
        if request.confirm_password and request.password != request.confirm_password:
            raise ValueError("Passwords do not match")

        user_id = request.user_id or str(uuid.uuid4())
        email_domain = request.email.rsplit("@", 1)[1].lower() if "@" in request.email else ""

        # ── @empirical-ais.com → pnp-prod ────────────────────────────
        if email_domain in {d.lower() for d in self.ALLOWED_EMAIL_DOMAINS}:
            token = self.register_user(
                email=request.email, password=request.password, user_id=user_id,
            )
            logger.info("EAIS signup: %s → pnp-prod/EAISPnPMain", request.email)
            return SignupResult(
                destination=SignupDestination.EAIS_PNP,
                token=token,
                user_id=user_id,
                email=request.email,
                role=self.DEFAULT_EAIS_ROLE,
            )

        # ── Outsider → subscriber portal ─────────────────────────────
        lob_id = self._resolve_lob_for_product_type(self.PRODUCT_TYPE)
        token = super().register_user(
            email=request.email, password=request.password, user_id=user_id,
            role="subscriber", lob_assignments=[lob_id],
        )
        profile = SubscriberProfile(
            user_id=user_id, email=request.email,
            company_name=request.company_name, location=request.location,
            product_type=self.PRODUCT_TYPE, plan=request.plan,
            tenant_id=self._default_tenant_id, lob_id=lob_id,
        )
        self._subscribers[user_id] = profile
        self._audit.record(
            entity_id=self._config.entity_id, tenant_id=self._default_tenant_id,
            actor_id="system", action_type="subscriber_registered", resource=user_id,
            detail={"email": request.email, "company": request.company_name,
                    "product_type": self.PRODUCT_TYPE, "lob_id": lob_id, "plan": request.plan.value},
        )
        logger.info("Subscriber signup: %s (%s) → /subscriber [lob=%s]", request.email, request.company_name, lob_id)
        return SignupResult(
            destination=SignupDestination.SUBSCRIBER_PORTAL,
            token=token, user_id=user_id, email=request.email, role="subscriber",
            subscriber_profile=profile, requires_email_verification=True,
            masked_email=_mask_email(request.email),
        )

    def _resolve_lob_for_product_type(self, product_type: str) -> str:
        key = product_type.lower().strip()
        if key in self.PRODUCT_TYPE_LOB_MAP:
            return self.PRODUCT_TYPE_LOB_MAP[key]
        for map_key, lob_id in self.PRODUCT_TYPE_LOB_MAP.items():
            if key.startswith(map_key) or map_key.startswith(key):
                return lob_id
        return "p-lob-bai"

    def get_subscriber_profile(self, user_id: str) -> Optional[SubscriberProfile]:
        return self._subscribers.get(user_id)

    def list_subscribers(self) -> List[SubscriberProfile]:
        self._assert_bootstrapped()
        return list(self._subscribers.values())
