/**
 * TenantSwitcher — Dropdown to switch tenant context.
 *
 * When a user switches tenants, all dashboard panels reload
 * with data scoped to the selected tenant.
 */

import React, { useState } from 'react';

export interface TenantOption {
  tenant_id: string;
  name: string;
  is_active: boolean;
}

export interface TenantSwitcherProps {
  /** Available tenants for the current user */
  tenants: TenantOption[];
  /** Currently selected tenant ID */
  activeTenantId?: string;
  /** Callback when tenant is switched — triggers panel reload */
  onTenantSwitch: (tenantId: string) => void;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Tenant context switcher component.
 *
 * Provides a dropdown for switching between tenants.
 * Triggers a full panel reload when the tenant changes.
 */
export const TenantSwitcher: React.FC<TenantSwitcherProps> = ({
  tenants,
  activeTenantId,
  onTenantSwitch,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const activeTenant = tenants.find((t) => t.tenant_id === activeTenantId);

  const handleSelect = (tenantId: string) => {
    if (tenantId !== activeTenantId) {
      onTenantSwitch(tenantId);
    }
    setIsOpen(false);
  };

  return (
    <div className={`openmesh-tenant-switcher ${className}`}>
      <button
        className="openmesh-tenant-switcher__trigger"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-label="Switch tenant"
      >
        <span className="openmesh-tenant-switcher__current">
          {activeTenant ? activeTenant.name : 'Select Tenant'}
        </span>
        <span className="openmesh-tenant-switcher__arrow" aria-hidden="true">
          {isOpen ? '▲' : '▼'}
        </span>
      </button>
      {isOpen && (
        <ul
          className="openmesh-tenant-switcher__dropdown"
          role="listbox"
          aria-label="Available tenants"
        >
          {tenants
            .filter((t) => t.is_active)
            .map((tenant) => (
              <li
                key={tenant.tenant_id}
                className={`openmesh-tenant-switcher__option ${
                  tenant.tenant_id === activeTenantId
                    ? 'openmesh-tenant-switcher__option--active'
                    : ''
                }`}
                role="option"
                aria-selected={tenant.tenant_id === activeTenantId}
                onClick={() => handleSelect(tenant.tenant_id)}
              >
                {tenant.name}
              </li>
            ))}
        </ul>
      )}
    </div>
  );
};

export default TenantSwitcher;
