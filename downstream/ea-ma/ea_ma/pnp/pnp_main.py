"""EAIS PnP Main — Empirical-AiS Mesh Architecture orchestrator.

Extends the framework's PnPMain with EAIS-specific business logic:

1. BAIVerticalManager — lifecycle management for BAI product_types
   (Restaurant Intelligence, Supermarket Intelligence, IT-Consulting-100, etc.)
   Add/remove/list verticals at runtime with governance refresh.

2. ProductCatalog — aggregated view of all EA-MA products with health
   status, adapter status, and product_type counts.

3. EAIS RBAC policies — compliance-officer role, cross-product read
   permissions, BAI-specific operator scoping.

4. Cross-product intelligence routing — query which products a user
   can access, filtered by vertical.

Usage:
    from ea_ma.pnp import EAISPnPMain
    from ea_ma.preset import create_eais_config

    config = create_eais_config(jwt_secret="production-secret")
    pnp = EAISPnPMain(config)
    pnp.bootstrap()

    # BAI vertical management
    pnp.bai.add_vertical("bai-hospitality", "Hospitality Intelligence")
    verticals = pnp.bai.list_verticals()

    # Product catalog
    catalog = pnp.catalog.snapshot()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from packages.core.pnp.pnp_main import PnPConfig, PnPMain
from packages.core.domain_registry.models import ProductFamily, Resource
from packages.core.domain_registry.registration import DomainRegistration
from packages.core.rbac.models import Permission
from packages.observability.interface.adapter import ObservabilityAdapterInterface

logger = logging.getLogger("ea-ma.pnp")


# ── Environment ──────────────────────────────────────────────────────


class EAISEnvironment(Enum):
    """Deployment environment for EA-MA."""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class UnauthorizedEmailDomainError(Exception):
    """Raised when a user's email domain is not in the allowed list."""

# ── Data models ──────────────────────────────────────────────────────


@dataclass
class VerticalInfo:
    """Summary of a BAI vertical (product_type)."""
    family_id: str
    name: str
    description: str
    resource_count: int = 0


@dataclass
class ProductStatus:
    """Aggregated status for a single EA-MA product."""
    domain_id: str
    product_name: str
    runtime_type: str
    adapter_resolved: bool
    vertical_count: int
    verticals: List[str]
    lob_id: str


@dataclass
class CatalogSnapshot:
    """Point-in-time snapshot of the entire EA-MA product catalog."""
    entity_id: str
    entity_name: str
    timestamp: datetime
    products: List[ProductStatus]
    total_verticals: int
    total_adapters: int


# ── BAI Vertical Manager ────────────────────────────────────────────


class BAIVerticalManager:
    """Manages BAI product_type verticals at runtime.

    Provides add/remove/list/get operations for BAI verticals,
    backed by the framework's HierarchyStore (ProductFamily).
    All mutations are audited and trigger governance refresh.
    """

    BAI_DOMAIN_ID = "bai"

    def __init__(self, pnp: PnPMain) -> None:
        self._pnp = pnp

    def list_verticals(self) -> List[VerticalInfo]:
        """List all BAI verticals with resource counts."""
        families = self._pnp.hierarchy.list_product_families(
            domain_id=self.BAI_DOMAIN_ID
        )
        result = []
        for f in families:
            resources = self._pnp.hierarchy.list_resources(family_id=f.family_id)
            result.append(VerticalInfo(
                family_id=f.family_id,
                name=f.name,
                description=f.description,
                resource_count=len(resources),
            ))
        return result

    def get_vertical(self, family_id: str) -> Optional[VerticalInfo]:
        """Get a single BAI vertical by family_id."""
        f = self._pnp.hierarchy.get_product_family(family_id)
        if f is None or f.domain_id != self.BAI_DOMAIN_ID:
            return None
        resources = self._pnp.hierarchy.list_resources(family_id=f.family_id)
        return VerticalInfo(
            family_id=f.family_id,
            name=f.name,
            description=f.description,
            resource_count=len(resources),
        )

    def add_vertical(
        self, family_id: str, name: str, description: str = ""
    ) -> VerticalInfo:
        """Add a new BAI vertical at runtime.

        Creates the ProductFamily in the hierarchy, audits the action,
        and refreshes governance policies.

        Raises:
            ValueError: If the BAI domain is not registered.
        """
        if self._pnp.hierarchy.get_domain(self.BAI_DOMAIN_ID) is None:
            raise ValueError(
                f"BAI domain '{self.BAI_DOMAIN_ID}' not found in hierarchy. "
                "Bootstrap must load bai.yaml first."
            )

        family = ProductFamily(
            family_id=family_id,
            domain_id=self.BAI_DOMAIN_ID,
            name=name,
            description=description,
        )
        self._pnp.hierarchy.create_product_family(family)

        # Also update the in-memory DomainRegistration's product_families
        for reg in self._pnp.loaded_domains:
            if reg.domain_id == self.BAI_DOMAIN_ID:
                reg.product_families.append({
                    "family_id": family_id,
                    "name": name,
                    "description": description,
                })
                break

        # Audit
        self._pnp.audit.record(
            entity_id="empirical-ais",
            tenant_id=self._pnp.default_tenant_id,
            actor_id="system",
            action_type="vertical_added",
            resource=family_id,
            detail={"name": name, "domain": self.BAI_DOMAIN_ID},
        )

        logger.info("BAI vertical added: %s (%s)", family_id, name)
        return VerticalInfo(
            family_id=family_id, name=name,
            description=description, resource_count=0,
        )

    def remove_vertical(self, family_id: str) -> None:
        """Remove a BAI vertical. Blocked if resources exist.

        Raises:
            packages.core.domain_registry.hierarchy.ReferentialIntegrityError:
                If the vertical has active resources.
            packages.core.domain_registry.hierarchy.NotFoundError:
                If the vertical does not exist.
        """
        self._pnp.hierarchy.delete_product_family(family_id)

        # Remove from in-memory registration
        for reg in self._pnp.loaded_domains:
            if reg.domain_id == self.BAI_DOMAIN_ID:
                reg.product_families = [
                    pf for pf in reg.product_families
                    if pf.get("family_id") != family_id
                ]
                break

        self._pnp.audit.record(
            entity_id="empirical-ais",
            tenant_id=self._pnp.default_tenant_id,
            actor_id="system",
            action_type="vertical_removed",
            resource=family_id,
            detail={"domain": self.BAI_DOMAIN_ID},
        )
        logger.info("BAI vertical removed: %s", family_id)

    def add_resource(
        self, family_id: str, resource_id: str, name: str,
        resource_type: str = "", metadata: Optional[Dict] = None,
    ) -> None:
        """Add a resource (node) under a BAI vertical."""
        resource = Resource(
            resource_id=resource_id,
            family_id=family_id,
            name=name,
            resource_type=resource_type,
            metadata=metadata or {},
        )
        self._pnp.hierarchy.create_resource(resource)
        logger.info("Resource '%s' added to vertical '%s'", resource_id, family_id)

    @property
    def vertical_count(self) -> int:
        return len(self._pnp.hierarchy.list_product_families(
            domain_id=self.BAI_DOMAIN_ID
        ))


# ── Product Catalog ──────────────────────────────────────────────────


class ProductCatalog:
    """Aggregated view of all EA-MA products.

    Provides a snapshot of every product (domain) with its adapter
    status, vertical count, and LOB assignment.
    """

    def __init__(self, pnp: PnPMain) -> None:
        self._pnp = pnp

    def snapshot(self) -> CatalogSnapshot:
        """Take a point-in-time snapshot of the product catalog."""
        products = []
        total_verticals = 0

        for reg in self._pnp.loaded_domains:
            families = self._pnp.hierarchy.list_product_families(
                domain_id=reg.domain_id
            )
            vertical_names = [f.name for f in families]
            total_verticals += len(families)

            products.append(ProductStatus(
                domain_id=reg.domain_id,
                product_name=reg.metadata.get("product_name", reg.domain_id),
                runtime_type=reg.runtime_type,
                adapter_resolved=reg.observability_adapter in self._pnp.loaded_adapters,
                vertical_count=len(families),
                verticals=vertical_names,
                lob_id=reg.lob_id,
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
        """Get status for a single product."""
        for reg in self._pnp.loaded_domains:
            if reg.domain_id == domain_id:
                families = self._pnp.hierarchy.list_product_families(
                    domain_id=domain_id
                )
                return ProductStatus(
                    domain_id=reg.domain_id,
                    product_name=reg.metadata.get("product_name", reg.domain_id),
                    runtime_type=reg.runtime_type,
                    adapter_resolved=reg.observability_adapter in self._pnp.loaded_adapters,
                    vertical_count=len(families),
                    verticals=[f.name for f in families],
                    lob_id=reg.lob_id,
                )
        return None

    def list_products_for_user(
        self, user_id: str, role: str,
        groups: Optional[List[str]] = None,
        lob_assignments: Optional[List[str]] = None,
    ) -> List[ProductStatus]:
        """List products visible to a user based on governance."""
        result = self._pnp.evaluate_access(
            user_id=user_id, role=role,
            groups=groups, lob_assignments=lob_assignments,
        )
        return [
            self.get_product(did)
            for did in result.authorized_domains
            if self.get_product(did) is not None
        ]


# ── EAIS PnP Main ───────────────────────────────────────────────────


class EAISPnPMain(PnPMain):
    """EAIS-specific PnP orchestrator extending the framework's PnPMain.

    Adds:
    - Email domain enforcement: only @empirical-ais.com (and configured
      partner domains) can register. Enforced in prod, staging, and local.
    - Environment awareness: prod/staging/local with appropriate defaults.
    - Auto LOB assignment: @empirical-ais.com users get all EAIS LOBs by default.
    - bai: BAIVerticalManager for BAI product_type lifecycle
    - catalog: ProductCatalog for aggregated product views
    - EAIS-specific RBAC: compliance_officer, bai_analyst roles
    - Cross-product queries: get_user_verticals, get_compliance_summary
    """

    # Email domains allowed to register in EA-MA
    ALLOWED_EMAIL_DOMAINS: Set[str] = {"empirical-ais.com"}

    # Default LOBs assigned to @empirical-ais.com users
    DEFAULT_EAIS_LOBS: List[str] = [
        "p-lob-bai",
        "p-lob-cybersecurity",
        "p-lob-genai",
        "p-lob-rag",
    ]

    # Default role for new @empirical-ais.com users (can be overridden)
    DEFAULT_EAIS_ROLE: str = "operator"

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

        if allowed_email_domains is not None:
            self.ALLOWED_EMAIL_DOMAINS = allowed_email_domains

    @property
    def environment(self) -> EAISEnvironment:
        """Current deployment environment."""
        return self._environment

    @property
    def enforce_email_domain(self) -> bool:
        """Whether email domain enforcement is active."""
        return self._enforce_email_domain

    def bootstrap(self) -> None:
        """Bootstrap the framework, then initialize EAIS-specific layers."""
        super().bootstrap()
        self._bai = BAIVerticalManager(self)
        self._catalog = ProductCatalog(self)
        self._init_eais_rbac()
        logger.info(
            "EAIS layers initialized: env=%s, BAI verticals=%d, "
            "email_enforcement=%s, allowed_domains=%s",
            self._environment.value,
            self._bai.vertical_count,
            self._enforce_email_domain,
            self.ALLOWED_EMAIL_DOMAINS,
        )

    def _init_eais_rbac(self) -> None:
        """Define EAIS-specific RBAC roles on top of framework defaults."""
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
        logger.info("EAIS custom roles defined: compliance_officer, bai_analyst")

    # ── Email domain enforcement ─────────────────────────────────────

    def _validate_email_domain(self, email: str) -> str:
        """Extract and validate the email domain.

        Returns:
            The domain part of the email.

        Raises:
            UnauthorizedEmailDomainError: If the domain is not allowed.
        """
        if "@" not in email:
            raise UnauthorizedEmailDomainError(
                f"Invalid email format: '{email}'"
            )
        domain = email.rsplit("@", 1)[1].lower()

        if self._enforce_email_domain and domain not in self.ALLOWED_EMAIL_DOMAINS:
            raise UnauthorizedEmailDomainError(
                f"Email domain '@{domain}' is not authorized for EA-MA. "
                f"Allowed domains: {', '.join(sorted(self.ALLOWED_EMAIL_DOMAINS))}"
            )
        return domain

    def _get_default_lobs_for_domain(self, email_domain: str) -> List[str]:
        """Return default LOB assignments for an email domain.

        @empirical-ais.com users get all EAIS LOBs.
        Partner domains could get a subset (extensible).
        """
        if email_domain == "empirical-ais.com":
            return list(self.DEFAULT_EAIS_LOBS)
        # Partner domains get no default LOBs — must be assigned explicitly
        return []

    def _get_default_role_for_domain(self, email_domain: str) -> str:
        """Return default role for an email domain."""
        if email_domain == "empirical-ais.com":
            return self.DEFAULT_EAIS_ROLE
        return "viewer"

    # ── Override register_user ────────────────────────────────────────

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
        """Register a user with email domain enforcement.

        For @empirical-ais.com users:
        - Email domain is validated (always, in all environments)
        - If role is not specified, defaults to DEFAULT_EAIS_ROLE ("operator")
        - If lob_assignments is not specified, defaults to all EAIS LOBs
        - User is placed in the EAIS tenant

        For partner domains (if added to ALLOWED_EMAIL_DOMAINS):
        - Email domain is validated
        - No default LOBs — must be assigned explicitly
        - Default role is "viewer"

        Args:
            email: Must be from an allowed email domain.
            password: User password.
            user_id: Unique user identifier.
            role: Role to assign. Defaults based on email domain.
            groups: Group memberships.
            lob_assignments: LOB assignments. Defaults based on email domain.
            tenant_id: Tenant ID. Defaults to the EAIS tenant.

        Returns:
            JWT token for the registered user.

        Raises:
            UnauthorizedEmailDomainError: If email domain is not allowed.
        """
        self._assert_bootstrapped()

        # Validate email domain
        email_domain = self._validate_email_domain(email)

        # Apply defaults based on email domain
        effective_role = role if role is not None else self._get_default_role_for_domain(email_domain)
        effective_lobs = lob_assignments if lob_assignments is not None else self._get_default_lobs_for_domain(email_domain)

        # Delegate to framework's register_user
        return super().register_user(
            email=email,
            password=password,
            user_id=user_id,
            role=effective_role,
            groups=groups,
            lob_assignments=effective_lobs,
            tenant_id=tenant_id,
        )

    def authenticate(self, email: str, password: str) -> Optional[str]:
        """Authenticate with email domain check.

        Validates the email domain before attempting authentication.

        Raises:
            UnauthorizedEmailDomainError: If email domain is not allowed.
        """
        self._assert_bootstrapped()
        self._validate_email_domain(email)
        return super().authenticate(email, password)

    # ── EAIS Accessors ───────────────────────────────────────────────

    @property
    def bai(self) -> BAIVerticalManager:
        """Access the BAI Vertical Manager."""
        self._assert_bootstrapped()
        return self._bai

    @property
    def catalog(self) -> ProductCatalog:
        """Access the Product Catalog."""
        self._assert_bootstrapped()
        return self._catalog

    # ── Cross-product queries ────────────────────────────────────────

    def get_user_verticals(
        self, user_id: str, role: str,
        groups: Optional[List[str]] = None,
        lob_assignments: Optional[List[str]] = None,
    ) -> Dict[str, List[VerticalInfo]]:
        """Get all verticals visible to a user, grouped by product."""
        self._assert_bootstrapped()
        result = self.evaluate_access(
            user_id=user_id, role=role,
            groups=groups, lob_assignments=lob_assignments,
        )

        verticals_by_product: Dict[str, List[VerticalInfo]] = {}
        for domain_id in result.authorized_domains:
            families = self._hierarchy.list_product_families(domain_id=domain_id)
            if families:
                verticals_by_product[domain_id] = [
                    VerticalInfo(
                        family_id=f.family_id,
                        name=f.name,
                        description=f.description,
                        resource_count=len(
                            self._hierarchy.list_resources(family_id=f.family_id)
                        ),
                    )
                    for f in families
                ]
        return verticals_by_product

    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get a compliance summary across all EAIS products."""
        self._assert_bootstrapped()
        audit_count = self._audit.count
        domains = self.loaded_domains
        compliance_frameworks = {}
        for d in domains:
            fw = d.metadata.get("compliance_framework")
            if fw:
                compliance_frameworks[d.domain_id] = fw

        return {
            "entity_id": self._config.entity_id,
            "environment": self._environment.value,
            "total_audit_records": audit_count,
            "total_domains": len(domains),
            "compliance_frameworks": compliance_frameworks,
            "custom_roles": ["compliance_officer", "bai_analyst"],
            "email_enforcement": self._enforce_email_domain,
            "allowed_email_domains": sorted(self.ALLOWED_EMAIL_DOMAINS),
        }
