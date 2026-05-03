/**
 * HealthStatusGrid — Grid of health check cards with status indicators.
 *
 * Renders a grid of health check results with color-coded status
 * indicators (healthy=green, degraded=amber, unhealthy=red).
 */

import React from 'react';

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface HealthCheckItem {
  name: string;
  status: HealthStatus;
  detail?: string;
}

export interface HealthStatusGridProps {
  /** Health check items to display */
  items: HealthCheckItem[];
  /** Title for the grid section */
  title?: string;
  /** Additional CSS class name */
  className?: string;
}

const STATUS_COLORS: Record<HealthStatus, string> = {
  healthy: 'green',
  degraded: 'amber',
  unhealthy: 'red',
};

const STATUS_LABELS: Record<HealthStatus, string> = {
  healthy: 'Healthy',
  degraded: 'Degraded',
  unhealthy: 'Unhealthy',
};

/**
 * Health status grid component.
 *
 * Displays health check results in a card grid with
 * color-coded status indicators.
 */
export const HealthStatusGrid: React.FC<HealthStatusGridProps> = ({
  items,
  title,
  className = '',
}) => {
  return (
    <div className={`openmesh-health-grid ${className}`}>
      {title && <h3 className="openmesh-health-grid__title">{title}</h3>}
      <div className="openmesh-health-grid__cards" role="list">
        {items.map((item) => (
          <div
            key={item.name}
            className={`openmesh-health-grid__card openmesh-health-grid__card--${item.status}`}
            role="listitem"
            aria-label={`${item.name}: ${STATUS_LABELS[item.status]}`}
          >
            <div className="openmesh-health-grid__indicator">
              <span
                className="openmesh-health-grid__dot"
                style={{ backgroundColor: STATUS_COLORS[item.status] }}
                aria-hidden="true"
              />
              <span className="openmesh-health-grid__status">
                {STATUS_LABELS[item.status]}
              </span>
            </div>
            <div className="openmesh-health-grid__name">{item.name}</div>
            {item.detail && (
              <div className="openmesh-health-grid__detail">{item.detail}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default HealthStatusGrid;
