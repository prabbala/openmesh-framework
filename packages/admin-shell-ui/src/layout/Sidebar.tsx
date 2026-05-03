/**
 * Sidebar — Dynamic navigation based on user role and registered domains.
 *
 * Renders navigation items dynamically based on the user's role
 * and the Domains registered for the user's LOB scope.
 */

import React from 'react';

export interface SidebarItem {
  id: string;
  label: string;
  icon?: string;
  href?: string;
  children?: SidebarItem[];
}

export interface SidebarProps {
  /** Navigation items to render */
  items: SidebarItem[];
  /** Currently active item ID */
  activeItemId?: string;
  /** Callback when a navigation item is clicked */
  onItemClick?: (item: SidebarItem) => void;
  /** User's current role (used for conditional rendering) */
  userRole?: string;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Dynamic sidebar navigation component.
 *
 * Renders navigation items based on user role and registered domains.
 * Items are provided by the Dashboard Shell after Governance Engine evaluation.
 */
export const Sidebar: React.FC<SidebarProps> = ({
  items,
  activeItemId,
  onItemClick,
  userRole,
  className = '',
}) => {
  const handleClick = (item: SidebarItem) => {
    onItemClick?.(item);
  };

  return (
    <nav
      className={`openmesh-sidebar ${className}`}
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="openmesh-sidebar__header">
        <span className="openmesh-sidebar__logo">OpenMesh</span>
        {userRole && (
          <span className="openmesh-sidebar__role" aria-label={`Role: ${userRole}`}>
            {userRole}
          </span>
        )}
      </div>
      <ul className="openmesh-sidebar__list" role="menubar">
        {items.map((item) => (
          <li
            key={item.id}
            className={`openmesh-sidebar__item ${
              activeItemId === item.id ? 'openmesh-sidebar__item--active' : ''
            }`}
            role="none"
          >
            <button
              className="openmesh-sidebar__button"
              role="menuitem"
              aria-current={activeItemId === item.id ? 'page' : undefined}
              onClick={() => handleClick(item)}
            >
              {item.icon && (
                <span className="openmesh-sidebar__icon" aria-hidden="true">
                  {item.icon}
                </span>
              )}
              <span className="openmesh-sidebar__label">{item.label}</span>
            </button>
            {item.children && item.children.length > 0 && (
              <ul className="openmesh-sidebar__sublist" role="menu">
                {item.children.map((child) => (
                  <li key={child.id} role="none">
                    <button
                      className="openmesh-sidebar__button openmesh-sidebar__button--child"
                      role="menuitem"
                      aria-current={activeItemId === child.id ? 'page' : undefined}
                      onClick={() => handleClick(child)}
                    >
                      <span className="openmesh-sidebar__label">{child.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Sidebar;
