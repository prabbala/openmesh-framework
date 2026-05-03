/**
 * SeverityChart — Aggregated severity distribution chart.
 *
 * Displays MeshHealthEvent severity distribution with
 * color-coded indicators: Critical=red, Warning=amber, Info=blue.
 */

import React from 'react';

export type Severity = 'Critical' | 'Warning' | 'Info';

export interface SeverityCount {
  severity: Severity;
  count: number;
}

export interface SeverityChartProps {
  /** Severity distribution data */
  data: SeverityCount[];
  /** Title for the chart */
  title?: string;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Severity color mapping — matches the MeshHealthEvent spec.
 * Critical = red, Warning = amber, Info = blue.
 */
export const SEVERITY_COLORS: Record<Severity, string> = {
  Critical: 'red',
  Warning: 'amber',
  Info: 'blue',
} as const;

export function getSeverityColor(severity: Severity): string {
  return SEVERITY_COLORS[severity];
}

/**
 * Severity distribution chart component.
 *
 * Renders a horizontal bar chart showing the distribution
 * of MeshHealthEvent severities with proper color coding.
 */
export const SeverityChart: React.FC<SeverityChartProps> = ({
  data,
  title,
  className = '',
}) => {
  const total = data.reduce((sum, d) => sum + d.count, 0);

  return (
    <div className={`openmesh-severity-chart ${className}`}>
      {title && <h3 className="openmesh-severity-chart__title">{title}</h3>}
      <div className="openmesh-severity-chart__bars" role="img" aria-label="Severity distribution">
        {data.map((item) => {
          const percentage = total > 0 ? (item.count / total) * 100 : 0;
          const color = SEVERITY_COLORS[item.severity];

          return (
            <div
              key={item.severity}
              className="openmesh-severity-chart__bar-group"
            >
              <div className="openmesh-severity-chart__label">
                <span
                  className="openmesh-severity-chart__dot"
                  style={{ backgroundColor: color }}
                  aria-hidden="true"
                />
                <span>{item.severity}</span>
                <span className="openmesh-severity-chart__count">
                  {item.count}
                </span>
              </div>
              <div className="openmesh-severity-chart__track">
                <div
                  className="openmesh-severity-chart__fill"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: color,
                  }}
                  role="progressbar"
                  aria-valuenow={item.count}
                  aria-valuemin={0}
                  aria-valuemax={total}
                  aria-label={`${item.severity}: ${item.count} of ${total}`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SeverityChart;
