/**
 * MetricCard — Single metric display with unit and trend indicator.
 *
 * Displays a single metric value with its unit, optional trend
 * direction, and change percentage.
 */

import React from 'react';

export type TrendDirection = 'up' | 'down' | 'stable';

export interface MetricCardProps {
  /** Metric display name */
  title: string;
  /** Current metric value */
  value: number;
  /** Unit of measurement */
  unit: string;
  /** Trend direction */
  trend?: TrendDirection;
  /** Percentage change */
  changePercent?: number;
  /** Additional CSS class name */
  className?: string;
}

const TREND_ICONS: Record<TrendDirection, string> = {
  up: '↑',
  down: '↓',
  stable: '→',
};

/**
 * Single metric display card component.
 *
 * Shows a metric value with unit and optional trend indicator.
 */
export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  trend,
  changePercent,
  className = '',
}) => {
  const formattedValue =
    value >= 1000000
      ? `${(value / 1000000).toFixed(1)}M`
      : value >= 1000
        ? `${(value / 1000).toFixed(1)}K`
        : value % 1 === 0
          ? value.toString()
          : value.toFixed(2);

  return (
    <div className={`openmesh-metric-card ${className}`}>
      <div className="openmesh-metric-card__title">{title}</div>
      <div className="openmesh-metric-card__value">
        <span className="openmesh-metric-card__number">{formattedValue}</span>
        <span className="openmesh-metric-card__unit">{unit}</span>
      </div>
      {trend && (
        <div
          className={`openmesh-metric-card__trend openmesh-metric-card__trend--${trend}`}
          aria-label={`Trend: ${trend}${changePercent !== undefined ? `, ${changePercent}%` : ''}`}
        >
          <span className="openmesh-metric-card__trend-icon" aria-hidden="true">
            {TREND_ICONS[trend]}
          </span>
          {changePercent !== undefined && (
            <span className="openmesh-metric-card__change">
              {changePercent > 0 ? '+' : ''}
              {changePercent.toFixed(1)}%
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default MetricCard;
