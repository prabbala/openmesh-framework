"""Tenant Manager — lifecycle management for tenants.

Manages tenant creation, suspension, deletion, and data isolation.
Enforces SUB_CLIENT parent validation and referential integrity.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from .models import Tenant, TenantType


class TenantNotFoundError(Exception):
    """Raised when a tenant_id is not found."""


class InvalidParentError(Exception):
    """Raised when a SUB_CLIENT references an invalid parent."""


class TenantReferentialIntegrityError(Exception):
    """Raised when deletion would violate referential integrity."""

    def __init__(self, message: str, dependent_ids: List[str]) -> None:
        super().__init__(message)
        self.dependent_ids = dependent_ids


class TenantSuspendedError(Exception):
    """Raised when a write operation is attempted on a suspended tenant."""


class TenantManager:
    """Manages tenant lifecycle: create, suspend, delete, get.

    Enforces:
    - SUB_CLIENT parent_tenant_id must reference an existing PARENT tenant
    - Suspended tenants block writes, allow reads
    - Deletion rejected if active SUB_CLIENTs reference the tenant
    """

    def __init__(self) -> None:
        self._tenants: Dict[str, Tenant] = {}
        self._data_namespaces: Dict[str, Dict[str, Any]] = {}

    def create_tenant(
        self,
        name: str,
        tenant_type: TenantType,
        parent_tenant_id: Optional[str] = None,
        entity_id: str = "",
    ) -> Tenant:
        """Create a tenant with an isolated data namespace.

        Args:
            name: Human-readable tenant name.
            tenant_type: INDEPENDENT, PARENT, or SUB_CLIENT.
            parent_tenant_id: Required for SUB_CLIENT type.
            entity_id: Maps to an Entity in the 4-tier model.

        Returns:
            The created Tenant.

        Raises:
            InvalidParentError: If SUB_CLIENT parent is missing or invalid.
        """
        if tenant_type == TenantType.SUB_CLIENT:
            if not parent_tenant_id:
                raise InvalidParentError(
                    "SUB_CLIENT tenant requires a parent_tenant_id"
                )
            parent = self._tenants.get(parent_tenant_id)
            if parent is None:
                raise InvalidParentError(
                    f"Parent tenant '{parent_tenant_id}' does not exist"
                )
            if parent.tenant_type != TenantType.PARENT:
                raise InvalidParentError(
                    f"Parent tenant '{parent_tenant_id}' has type "
                    f"'{parent.tenant_type.value}', expected 'parent'"
                )

        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            tenant_type=tenant_type,
            parent_tenant_id=parent_tenant_id,
            entity_id=entity_id,
            is_active=True,
            is_suspended=False,
        )
        self._tenants[tenant_id] = tenant
        # Provision isolated data namespace
        self._data_namespaces[tenant_id] = {}
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Return a Tenant by ID, or None if not found."""
        return self._tenants.get(tenant_id)

    def list_tenants(self) -> List[Tenant]:
        """Return all tenants."""
        return list(self._tenants.values())

    def suspend_tenant(self, tenant_id: str) -> None:
        """Suspend a tenant — blocks writes, allows reads.

        Raises:
            TenantNotFoundError: If tenant_id does not exist.
        """
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"Tenant '{tenant_id}' not found")
        tenant.is_suspended = True

    def unsuspend_tenant(self, tenant_id: str) -> None:
        """Remove suspension from a tenant.

        Raises:
            TenantNotFoundError: If tenant_id does not exist.
        """
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"Tenant '{tenant_id}' not found")
        tenant.is_suspended = False

    def delete_tenant(self, tenant_id: str) -> None:
        """Delete a tenant. Rejects if active SUB_CLIENTs reference it.

        Raises:
            TenantNotFoundError: If tenant_id does not exist.
            TenantReferentialIntegrityError: If active SUB_CLIENTs exist.
        """
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"Tenant '{tenant_id}' not found")

        # Check for active SUB_CLIENTs referencing this tenant as parent
        dependent_ids = [
            t.tenant_id
            for t in self._tenants.values()
            if t.parent_tenant_id == tenant_id
            and t.is_active
            and t.tenant_type == TenantType.SUB_CLIENT
        ]
        if dependent_ids:
            raise TenantReferentialIntegrityError(
                f"Cannot delete tenant '{tenant_id}': "
                f"{len(dependent_ids)} active SUB_CLIENT(s) reference it",
                dependent_ids=dependent_ids,
            )

        tenant.is_active = False
        del self._tenants[tenant_id]
        self._data_namespaces.pop(tenant_id, None)

    # ── Data namespace operations (read/write with suspension check) ──

    def write_data(self, tenant_id: str, key: str, value: Any) -> None:
        """Write data to a tenant's namespace. Blocked if suspended.

        Raises:
            TenantNotFoundError: If tenant_id does not exist.
            TenantSuspendedError: If tenant is suspended.
        """
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"Tenant '{tenant_id}' not found")
        if tenant.is_suspended:
            raise TenantSuspendedError(
                f"Tenant '{tenant_id}' is suspended — write operations are blocked"
            )
        self._data_namespaces.setdefault(tenant_id, {})[key] = value

    def read_data(self, tenant_id: str, key: str) -> Any:
        """Read data from a tenant's namespace. Allowed even if suspended.

        Raises:
            TenantNotFoundError: If tenant_id does not exist.
        """
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"Tenant '{tenant_id}' not found")
        return self._data_namespaces.get(tenant_id, {}).get(key)

    def update_data(self, tenant_id: str, key: str, value: Any) -> None:
        """Update data in a tenant's namespace. Blocked if suspended.

        Raises:
            TenantNotFoundError: If tenant_id does not exist.
            TenantSuspendedError: If tenant is suspended.
        """
        self.write_data(tenant_id, key, value)

    def delete_data(self, tenant_id: str, key: str) -> None:
        """Delete data from a tenant's namespace. Blocked if suspended.

        Raises:
            TenantNotFoundError: If tenant_id does not exist.
            TenantSuspendedError: If tenant is suspended.
        """
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"Tenant '{tenant_id}' not found")
        if tenant.is_suspended:
            raise TenantSuspendedError(
                f"Tenant '{tenant_id}' is suspended — write operations are blocked"
            )
        ns = self._data_namespaces.get(tenant_id, {})
        ns.pop(key, None)
