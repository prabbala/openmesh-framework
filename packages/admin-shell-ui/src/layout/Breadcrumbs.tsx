/**
 * Breadcrumbs — Context-aware breadcrumb navigation.
 *
 * Renders a breadcrumb trail reflecting the current navigation
 * context within the admin dashboard.
 */

import React from 'react';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface BreadcrumbsProps {
  /** Ordered list of breadcrumb items (first = root, last = current) */
  items: BreadcrumbItem[];
  /** Callback when a breadcrumb is clicked */
  onNavigate?: (item: BreadcrumbItem, index: number) => void;
  /** Separator character between breadcrumbs */
  separator?: string;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Context-aware breadcrumb navigation component.
 *
 * Renders a breadcrumb trail for the current dashboard context.
 * The last item is rendered as the current page (not clickable).
 */
export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({
  items,
  onNavigate,
  separator = '/',
  className = '',
}) => {
  if (items.length === 0) return null;

  return (
    <nav
      className={`openmesh-breadcrumbs ${className}`}
      aria-label="Breadcrumb"
    >
      <ol className="openmesh-breadcrumbs__list">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li
              key={`${item.label}-${index}`}
              className="openmesh-breadcrumbs__item"
            >
              {!isLast ? (
                <>
                  <button
                    className="openmesh-breadcrumbs__link"
                    onClick={() => onNavigate?.(item, index)}
                  >
                    {item.label}
                  </button>
                  <span
                    className="openmesh-breadcrumbs__separator"
                    aria-hidden="true"
                  >
                    {separator}
                  </span>
                </>
              ) : (
                <span
                  className="openmesh-breadcrumbs__current"
                  aria-current="page"
                >
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default Breadcrumbs;
