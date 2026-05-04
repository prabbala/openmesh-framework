"""PnP Main — Production Plug-N-Play orchestrator for OpenMesh Framework.

Bootstraps the full OpenMesh stack from YAML domain configurations:
  1. Initializes RBAC, Tenant, LOB, Audit, Auth engines
  2. Loads domain registrations from YAML config directory
  3. Resolves and instantiates observability adapters
  4. Wires Governance Engine with all subsystems
  5. Composes DashboardShell with registered adapters
  6. Provides a single evaluate() entry point for dashboard rendering

Usage:
    config = PnPConfig(
        entity_id="my-company",
        entity_name="My Company Inc.",
        config_dir="config/domains",
        jwt_secret="production-secret-here",
    )
    pnp = PnPMain(config)
    pnp.bootstrap()
    panels = pnp.render_dashboard(token="<jwt>")
"""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type

import yaml

from packages.core.audit.engine import AuditEngine
from packages.core.auth.jwt_provider import JWTAuthProvider
from packages.core.auth.provider import AuthProviderInterface
from packages.core.dashboard_shell.shell import DashboardShell, RenderedPanel
from packages.core.domain_registry.hierarchy import HierarchyStore
from packages.core.domain_registry.models import Domain, Entity, ProductFamily
from packages.core.domain_registry.registration import DomainRegistration
from packages.core.domain_registry.registry import DomainRegistry
from packages.core.governance_engine.engine import (
    GovernanceEngine,
    GovernanceResult,
    PolicyChangeEvent,
)
from packages.core.lob.models import LOBCategory, LOBNode
from packages.core.lob.scope_resolver import ScopeResolver
from packages.core.lob.store import LOBStore
from packages.core.rbac.engine import RBACEngine
from packages.core.tenant.manager import TenantManager
from packages.core.tenant.models import TenantType
from packages.observability.interface.adapter import ObservabilityAdapterInterface

logger = logging.getLogger("openmesh.pnp")


class PnPBootstrapError(Exception):
    """Raised when PnP bootstrap fails."""

    def __init__(self, message: str, errors: List[Dict[str, str]] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


@dataclass
class PnPConfig:
    """Configuration for PnP bootstrap.

    Attributes:
        entity_id: Root entity identifier (e.g. "empirical-ais").
        entity_name: Human-readable entity name.
        config_dir: Path to directory containing domain YAML files.
        jwt_secret: Secret for JWT token signing. Use a strong secret in production.
        jwt_ttl_seconds: JWT token time-to-live in seconds.
        tenant_name: Default tenant name to create on bootstrap.
        tenant_type: Default tenant type.
        auth_provider: Optional custom auth provider. Defaults to JWTAuthProvider.
        adapter_overrides: Map of adapter class path -> adapter instance for testing.
        log_level: Logging level for the PnP orchestrator.
    """

    entity_id: str
    entity_name: str
    config_dir: str = ""
    jwt_secret: str = "openmesh-change-me-in-production"
    jwt_ttl_seconds: int = 3600
    tenant_name: str = ""
    tenant_type: TenantType = TenantType.INDEPENDENT
    auth_provider: Optional[AuthProviderInterface] = None
    adapter_overrides: Dict[str, ObservabilityAdapterInterface] = field(default_factory=dict)
    log_level: str = "INFO"


class PnPMain:
    """Production Plug-N-Play orchestrator for OpenMesh Framework.

    Wires all OpenMesh framework components together from YAML domain
    configurations into a fully operational governance-evaluated dashboard.

    Lifecycle:
        1. __init__: Store config, create empty engine references
        2. bootstrap(): Initialize all engines, load configs, wire everything
        3. render_dashboard(): Evaluate governance and render panels for a user
        4. evaluate_access(): Check governance for a user without rendering
    """

    def __init__(self, config: PnPConfig) -> None:
        self._config = config
        self._bootstrapped = False

        # Engines — initialized during bootstrap
        self._rbac: Optional[RBACEngine] = None
        self._audit: Optional[AuditEngine] = None
        self._auth: Optional[AuthProviderInterface] = None
        self._lob_store: Optional[LOBStore] = None
        self._scope_resolver: Optional[ScopeResolver] = None
        self._domain_registry: Optional[DomainRegistry] = None
        self._hierarchy: Optional[HierarchyStore] = None
        self._governance: Optional[GovernanceEngine] = None
        self._dashboard: Optional[DashboardShell] = None
        self._tenant_manager: Optional[TenantManager] = None

        # Adapter instances keyed by adapter class path
        self._adapters: Dict[str, ObservabilityAdapterInterface] = {}

        # Loaded domain configs
        self._domain_configs: List[DomainRegistration] = []

        # Default tenant ID (created during bootstrap)
        self._default_tenant_id: str = ""

    # ── Bootstrap ────────────────────────────────────────────────────

    def bootstrap(self) -> None:
        """Initialize all engines, load YAML configs, wire the full stack.

        Raises:
            PnPBootstrapError: If bootstrap fails (invalid configs, missing adapters, etc.)
        """
        logging.basicConfig(level=getattr(logging, self._config.log_level, logging.INFO))
        logger.info("PnP bootstrap starting for entity '%s'", self._config.entity_id)

        errors: List[Dict[str, str]] = []

        try:
            self._init_engines()
            self._init_hierarchy()
            self._init_default_tenant()
            self._load_domain_configs(errors)
            self._resolve_adapters(errors)
            self._populate_hierarchy(errors)
            self._wire_governance()
            self._wire_dashboard()
        except Exception as exc:
            errors.append({"component": "bootstrap", "error": str(exc)})

        if errors:
            logger.error("PnP bootstrap completed with %d error(s)", len(errors))
            for err in errors:
                logger.error("  %s: %s", err.get("component", "unknown"), err.get("error", ""))
            # Non-fatal errors: log but continue (degraded mode)
            # Fatal errors would have raised before reaching here

        self._bootstrapped = True
        logger.info(
            "PnP bootstrap complete: %d domains, %d adapters loaded",
            len(self._domain_configs),
            len(self._adapters),
        )

    def _init_engines(self) -> None:
        """Initialize core engines."""
        self._rbac = RBACEngine()
        self._audit = AuditEngine()
        self._lob_store = LOBStore()
        self._scope_resolver = ScopeResolver(self._lob_store, self._rbac)
        self._domain_registry = DomainRegistry()
        self._hierarchy = HierarchyStore()
        self._tenant_manager = TenantManager()

        # Auth provider
        if self._config.auth_provider is not None:
            self._auth = self._config.auth_provider
        else:
            self._auth = JWTAuthProvider(
                secret=self._config.jwt_secret,
                ttl_seconds=self._config.jwt_ttl_seconds,
            )

    def _init_hierarchy(self) -> None:
        """Create the root Entity in the 4-tier hierarchy."""
        entity = Entity(
            entity_id=self._config.entity_id,
            name=self._config.entity_name,
        )
        self._hierarchy.create_entity(entity)
        logger.info("Created root entity: %s", self._config.entity_id)

    def _init_default_tenant(self) -> None:
        """Create a default tenant for the entity."""
        tenant_name = self._config.tenant_name or f"{self._config.entity_name} Tenant"
        tenant = self._tenant_manager.create_tenant(
            name=tenant_name,
            tenant_type=self._config.tenant_type,
            entity_id=self._config.entity_id,
        )
        self._default_tenant_id = tenant.tenant_id
        logger.info("Created default tenant: %s (%s)", tenant.tenant_id, tenant_name)

        # Audit the tenant creation
        self._audit.record(
            entity_id=self._config.entity_id,
            tenant_id=tenant.tenant_id,
            actor_id="system",
            action_type="tenant_created",
            resource=tenant.tenant_id,
            detail={"name": tenant_name, "type": self._config.tenant_type.value},
        )

    def _load_domain_configs(self, errors: List[Dict[str, str]]) -> None:
        """Load domain registrations from YAML files in config_dir."""
        config_dir = self._config.config_dir
        if not config_dir:
            logger.info("No config_dir specified — skipping YAML domain loading")
            return

        config_path = Path(config_dir)
        if not config_path.is_dir():
            errors.append({
                "component": "config_loader",
                "error": f"Config directory '{config_dir}' does not exist or is not a directory",
            })
            return

        yaml_files = sorted(config_path.glob("*.yaml")) + sorted(config_path.glob("*.yml"))
        if not yaml_files:
            logger.warning("No YAML files found in '%s'", config_dir)
            return

        for yaml_file in yaml_files:
            try:
                self._load_single_domain(yaml_file, errors)
            except Exception as exc:
                errors.append({
                    "component": f"config_loader:{yaml_file.name}",
                    "error": str(exc),
                })

    def _load_single_domain(self, yaml_file: Path, errors: List[Dict[str, str]]) -> None:
        """Load a single domain registration from a YAML file."""
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            errors.append({
                "component": f"config_loader:{yaml_file.name}",
                "error": "YAML file must contain a mapping",
            })
            return

        domain_id = data.get("domain_id", "")
        runtime_type = data.get("runtime_type", "")
        adapter_path = data.get("observability_adapter", "")
        roles = data.get("roles", [])
        tabs = data.get("tabs", [])
        entity_id = data.get("entity_id", self._config.entity_id)
        lob_id = data.get("lob_id", "")
        metadata = data.get("metadata", {})
        product_families = data.get("product_families", [])

        # Ensure LOB exists
        if lob_id and self._lob_store.get_lob(lob_id) is None:
            self._lob_store.create_lob(LOBNode(
                lob_id=lob_id,
                name=lob_id,
                category=LOBCategory.P_LOB,
                entity_id=entity_id,
            ))
            logger.info("Auto-created LOB: %s", lob_id)

        try:
            registration = DomainRegistration(
                domain_id=domain_id,
                runtime_type=runtime_type,
                observability_adapter=adapter_path,
                roles=roles,
                tabs=tabs,
                entity_id=entity_id,
                lob_id=lob_id,
                metadata=metadata,
                product_families=product_families,
            )
            self._domain_registry.register(registration)
            self._domain_configs.append(registration)
            logger.info("Registered domain: %s (runtime=%s)", domain_id, runtime_type)

            # Track LOB → domain reference
            if lob_id:
                self._lob_store.add_domain_ref(lob_id, domain_id)

            # Audit
            self._audit.record(
                entity_id=entity_id,
                tenant_id=self._default_tenant_id,
                actor_id="system",
                action_type="domain_registered",
                resource=domain_id,
                detail={"runtime_type": runtime_type, "source": str(yaml_file)},
            )
        except Exception as exc:
            errors.append({
                "component": f"domain_registration:{domain_id or yaml_file.name}",
                "error": str(exc),
            })

    def _resolve_adapters(self, errors: List[Dict[str, str]]) -> None:
        """Resolve and instantiate adapters for all registered domains."""
        for reg in self._domain_configs:
            adapter_path = reg.observability_adapter

            # Check overrides first
            if adapter_path in self._config.adapter_overrides:
                self._adapters[adapter_path] = self._config.adapter_overrides[adapter_path]
                logger.info("Using adapter override for: %s", adapter_path)
                continue

            # Already resolved
            if adapter_path in self._adapters:
                continue

            # Dynamic import
            try:
                adapter_instance = self._import_adapter(
                    adapter_path, reg.entity_id, reg.domain_id
                )
                self._adapters[adapter_path] = adapter_instance
                logger.info("Resolved adapter: %s", adapter_path)
            except Exception as exc:
                errors.append({
                    "component": f"adapter_resolver:{adapter_path}",
                    "error": str(exc),
                })

    def _import_adapter(
        self, adapter_path: str, entity_id: str, domain: str
    ) -> ObservabilityAdapterInterface:
        """Dynamically import and instantiate an adapter class.

        Args:
            adapter_path: Fully qualified class path (e.g. "packages.observability.adapters.server.adapter.ServerAdapter")
            entity_id: Entity ID to pass to the adapter constructor.
            domain: Domain ID to pass to the adapter constructor.

        Returns:
            An instantiated adapter.

        Raises:
            ImportError: If the module or class cannot be found.
            TypeError: If the class doesn't implement ObservabilityAdapterInterface.
        """
        parts = adapter_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ImportError(f"Invalid adapter path '{adapter_path}': expected 'module.ClassName'")

        module_path, class_name = parts
        module = importlib.import_module(module_path)
        adapter_class = getattr(module, class_name)

        if not (isinstance(adapter_class, type) and issubclass(adapter_class, ObservabilityAdapterInterface)):
            raise TypeError(
                f"'{adapter_path}' does not implement ObservabilityAdapterInterface"
            )

        return adapter_class(entity_id=entity_id, domain=domain)

    def _populate_hierarchy(self, errors: List[Dict[str, str]]) -> None:
        """Populate the 4-tier hierarchy from loaded domain configs.

        Creates Entity nodes for referenced entity_ids, Domain nodes for
        each DomainRegistration, and ProductFamily nodes for each
        product_family entry.
        """
        # Collect all unique entity_ids from domain configs and ensure they exist
        seen_entities = set()
        for reg in self._domain_configs:
            eid = reg.entity_id or self._config.entity_id
            if eid not in seen_entities and self._hierarchy.get_entity(eid) is None:
                try:
                    entity = Entity(entity_id=eid, name=eid)
                    self._hierarchy.create_entity(entity)
                    logger.info("Hierarchy: auto-created Entity '%s'", eid)
                except Exception as exc:
                    errors.append({
                        "component": f"hierarchy:entity:{eid}",
                        "error": str(exc),
                    })
            seen_entities.add(eid)

        for reg in self._domain_configs:
            # Create Domain in hierarchy if not already present
            if self._hierarchy.get_domain(reg.domain_id) is None:
                try:
                    domain = Domain(
                        domain_id=reg.domain_id,
                        entity_id=reg.entity_id or self._config.entity_id,
                        name=reg.metadata.get("product_name", reg.domain_id),
                        lob_id=reg.lob_id,
                        runtime_type=reg.runtime_type,
                        observability_adapter=reg.observability_adapter,
                    )
                    self._hierarchy.create_domain(domain)
                    logger.info("Hierarchy: created Domain '%s'", reg.domain_id)
                except Exception as exc:
                    errors.append({
                        "component": f"hierarchy:domain:{reg.domain_id}",
                        "error": str(exc),
                    })

            # Create ProductFamily nodes for each product_family entry
            for pf in reg.product_families:
                family_id = pf.get("family_id", "")
                family_name = pf.get("name", "")
                if not family_id or not family_name:
                    continue
                if self._hierarchy.get_product_family(family_id) is not None:
                    continue
                try:
                    family = ProductFamily(
                        family_id=family_id,
                        domain_id=reg.domain_id,
                        name=family_name,
                        description=pf.get("description", ""),
                    )
                    self._hierarchy.create_product_family(family)
                    logger.info(
                        "Hierarchy: created ProductFamily '%s' under Domain '%s'",
                        family_id, reg.domain_id,
                    )
                except Exception as exc:
                    errors.append({
                        "component": f"hierarchy:family:{family_id}",
                        "error": str(exc),
                    })

        families_count = len(self._hierarchy.list_product_families())
        domains_count = len(self._hierarchy.list_domains())
        logger.info(
            "Hierarchy populated: %d domains, %d product families",
            domains_count, families_count,
        )

    def _wire_governance(self) -> None:
        """Wire the Governance Engine with all subsystems."""
        self._governance = GovernanceEngine(
            rbac_engine=self._rbac,
            scope_resolver=self._scope_resolver,
            domain_registry=self._domain_registry,
        )
        self._governance.load_policies()
        logger.info("Governance Engine initialized with %d domains", self._domain_registry.count)

    def _wire_dashboard(self) -> None:
        """Wire the Dashboard Shell with governance and adapters."""
        self._dashboard = DashboardShell(
            governance_engine=self._governance,
            domain_registry=self._domain_registry,
            audit_engine=self._audit,
            adapters=dict(self._adapters),
        )
        logger.info("Dashboard Shell wired with %d adapters", len(self._adapters))

    # ── Runtime API ──────────────────────────────────────────────────

    def render_dashboard(
        self,
        token: Optional[str] = None,
        user_id: str = "",
        role: str = "",
        groups: Optional[List[str]] = None,
        lob_assignments: Optional[List[str]] = None,
        tenant_id: str = "",
    ) -> List[RenderedPanel]:
        """Render the dashboard for a user.

        Accepts either a JWT token (extracts claims automatically) or
        explicit user_id/role/groups/lob_assignments.

        Args:
            token: JWT token to authenticate and extract claims from.
            user_id: Explicit user ID (used if no token).
            role: Explicit role (used if no token).
            groups: Explicit group list (used if no token).
            lob_assignments: Explicit LOB assignments (used if no token).
            tenant_id: Tenant context. Defaults to the bootstrap tenant.

        Returns:
            List of RenderedPanel objects for the dashboard.

        Raises:
            PnPBootstrapError: If PnP has not been bootstrapped.
        """
        self._assert_bootstrapped()

        if token is not None:
            claims = self._auth.get_user_claims(token)
            user_id = claims.user_id
            role = claims.role
            groups = claims.groups
            lob_assignments = claims.lob_assignments
            tenant_id = tenant_id or claims.tenant_id

        return self._dashboard.render(
            user_id=user_id,
            role=role,
            groups=groups or [],
            lob_assignments=lob_assignments or [],
            tenant_id=tenant_id or self._default_tenant_id,
            entity_id=self._config.entity_id,
        )

    def evaluate_access(
        self,
        user_id: str,
        role: str,
        groups: Optional[List[str]] = None,
        lob_assignments: Optional[List[str]] = None,
        target_domain: Optional[str] = None,
    ) -> GovernanceResult:
        """Evaluate governance access for a user without rendering.

        Returns:
            GovernanceResult with authorized domains, panels, and LOB scope.
        """
        self._assert_bootstrapped()
        return self._governance.evaluate(
            user_id=user_id,
            role=role,
            groups=groups or [],
            lob_assignments=lob_assignments or [],
            target_domain=target_domain,
        )

    def register_user(
        self,
        email: str,
        password: str,
        user_id: str,
        role: str,
        groups: Optional[List[str]] = None,
        lob_assignments: Optional[List[str]] = None,
        tenant_id: str = "",
    ) -> str:
        """Register a user and return a JWT token.

        Convenience method that registers the user with the auth provider
        and assigns their role in RBAC.

        Returns:
            JWT token for the registered user.
        """
        self._assert_bootstrapped()
        tid = tenant_id or self._default_tenant_id
        grps = groups or []
        lobs = lob_assignments or []

        # Register with auth provider
        if isinstance(self._auth, JWTAuthProvider):
            self._auth.register_user(
                email=email, password=password, user_id=user_id,
                role=role, groups=grps, tenant_id=tid,
                lob_assignments=lobs,
            )

        # Assign role in RBAC
        self._rbac.assign_role(user_id, role)

        # Assign LOBs
        for lob_id in lobs:
            self._lob_store.add_user_ref(lob_id, user_id)

        # Audit
        self._audit.record(
            entity_id=self._config.entity_id,
            tenant_id=tid,
            actor_id="system",
            action_type="user_created",
            resource=user_id,
            detail={"email": email, "role": role},
        )

        # Authenticate to get token
        token = self._auth.authenticate({"email": email, "password": password})
        return token

    def authenticate(self, email: str, password: str) -> Optional[str]:
        """Authenticate a user and return a JWT token, or None on failure."""
        self._assert_bootstrapped()
        return self._auth.authenticate({"email": email, "password": password})

    # ── Domain management at runtime ─────────────────────────────────

    def register_domain(self, registration: DomainRegistration, adapter: Optional[ObservabilityAdapterInterface] = None) -> None:
        """Register a new domain at runtime (hot-reload).

        Args:
            registration: The domain registration.
            adapter: Optional adapter instance. If not provided, will attempt dynamic import.
        """
        self._assert_bootstrapped()

        # Ensure LOB exists
        if registration.lob_id and self._lob_store.get_lob(registration.lob_id) is None:
            self._lob_store.create_lob(LOBNode(
                lob_id=registration.lob_id,
                name=registration.lob_id,
                category=LOBCategory.P_LOB,
                entity_id=registration.entity_id or self._config.entity_id,
            ))

        self._domain_registry.register(registration)
        self._domain_configs.append(registration)

        # Resolve adapter
        if adapter is not None:
            self._adapters[registration.observability_adapter] = adapter
            self._dashboard.register_adapter(registration.observability_adapter, adapter)
        elif registration.observability_adapter not in self._adapters:
            try:
                instance = self._import_adapter(
                    registration.observability_adapter,
                    registration.entity_id,
                    registration.domain_id,
                )
                self._adapters[registration.observability_adapter] = instance
                self._dashboard.register_adapter(registration.observability_adapter, instance)
            except Exception as exc:
                logger.warning("Could not resolve adapter '%s': %s", registration.observability_adapter, exc)

        # Track LOB ref
        if registration.lob_id:
            self._lob_store.add_domain_ref(registration.lob_id, registration.domain_id)

        # Refresh governance
        self._governance.on_policy_change(PolicyChangeEvent("domain_registered", registration.entity_id))

        # Populate hierarchy for this domain
        if self._hierarchy.get_domain(registration.domain_id) is None:
            try:
                domain = Domain(
                    domain_id=registration.domain_id,
                    entity_id=registration.entity_id or self._config.entity_id,
                    name=registration.metadata.get("product_name", registration.domain_id),
                    lob_id=registration.lob_id,
                    runtime_type=registration.runtime_type,
                    observability_adapter=registration.observability_adapter,
                )
                self._hierarchy.create_domain(domain)
            except Exception:
                pass  # Entity may not exist in hierarchy for runtime domains

        for pf in registration.product_families:
            family_id = pf.get("family_id", "")
            family_name = pf.get("name", "")
            if not family_id or not family_name:
                continue
            if self._hierarchy.get_product_family(family_id) is not None:
                continue
            try:
                family = ProductFamily(
                    family_id=family_id,
                    domain_id=registration.domain_id,
                    name=family_name,
                    description=pf.get("description", ""),
                )
                self._hierarchy.create_product_family(family)
            except Exception:
                pass

        # Audit
        self._audit.record(
            entity_id=registration.entity_id or self._config.entity_id,
            tenant_id=self._default_tenant_id,
            actor_id="system",
            action_type="domain_registered",
            resource=registration.domain_id,
            detail={"runtime_type": registration.runtime_type, "source": "runtime"},
        )

    def unregister_domain(self, domain_id: str) -> None:
        """Unregister a domain at runtime."""
        self._assert_bootstrapped()
        self._domain_registry.unregister(domain_id)
        self._domain_configs = [d for d in self._domain_configs if d.domain_id != domain_id]
        self._governance.on_policy_change(PolicyChangeEvent("domain_unregistered"))

        self._audit.record(
            entity_id=self._config.entity_id,
            tenant_id=self._default_tenant_id,
            actor_id="system",
            action_type="domain_unregistered",
            resource=domain_id,
        )

    # ── Accessors ────────────────────────────────────────────────────

    @property
    def rbac(self) -> RBACEngine:
        """Access the RBAC engine."""
        self._assert_bootstrapped()
        return self._rbac

    @property
    def audit(self) -> AuditEngine:
        """Access the Audit engine."""
        self._assert_bootstrapped()
        return self._audit

    @property
    def auth(self) -> AuthProviderInterface:
        """Access the Auth provider."""
        self._assert_bootstrapped()
        return self._auth

    @property
    def governance(self) -> GovernanceEngine:
        """Access the Governance engine."""
        self._assert_bootstrapped()
        return self._governance

    @property
    def domain_registry(self) -> DomainRegistry:
        """Access the Domain registry."""
        self._assert_bootstrapped()
        return self._domain_registry

    @property
    def lob_store(self) -> LOBStore:
        """Access the LOB store."""
        self._assert_bootstrapped()
        return self._lob_store

    @property
    def tenant_manager(self) -> TenantManager:
        """Access the Tenant manager."""
        self._assert_bootstrapped()
        return self._tenant_manager

    @property
    def hierarchy(self) -> HierarchyStore:
        """Access the Hierarchy store."""
        self._assert_bootstrapped()
        return self._hierarchy

    @property
    def default_tenant_id(self) -> str:
        """Return the default tenant ID created during bootstrap."""
        return self._default_tenant_id

    @property
    def is_bootstrapped(self) -> bool:
        """Whether bootstrap() has been called."""
        return self._bootstrapped

    @property
    def loaded_domains(self) -> List[DomainRegistration]:
        """Return all loaded domain registrations."""
        return list(self._domain_configs)

    @property
    def loaded_adapters(self) -> Dict[str, ObservabilityAdapterInterface]:
        """Return all resolved adapter instances."""
        return dict(self._adapters)

    # ── Internal ─────────────────────────────────────────────────────

    def _assert_bootstrapped(self) -> None:
        if not self._bootstrapped:
            raise PnPBootstrapError(
                "PnPMain has not been bootstrapped. Call bootstrap() first."
            )
