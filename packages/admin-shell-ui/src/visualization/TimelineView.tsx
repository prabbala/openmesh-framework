/**
 * TimelineView — Chronological MeshHealthEvent timeline.
 *
 * Displays MeshHealthEvents in chronological order with
 * severity-coded indicators.
 */

import React from 'react';

export type Severity = 'Critical' | 'Warning' | 'Info';

export interface TimelineEvent {
  entity_id: string;
  domain: string;
  severity: Severity;
  message: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface TimelineViewProps {
  /** Events to display in chronological order */
  events: TimelineEvent[];
  /** Title for the timeline */
  title?: string;
  /** Maximum number of events to display */
  maxItems?: number;
  /** Additional CSS class name */
  className?: string;
}

const SEVERITY_COLORS: Record<Severity, string> = {
  Critical: 'red',
  Warning: 'amber',
  Info: 'blue',
};

/**
 * Chronological event timeline component.
 *
 * Renders MeshHealthEvents in a vertical timeline with
 * severity-coded indicators and timestamps.
 */
export const TimelineView: React.FC<TimelineViewProps> = ({
  events,
  title,
  maxItems,
  className = '',
}) => {
  const displayEvents = maxItems ? events.slice(0, maxItems) : events;

  return (
    <div className={`openmesh-timeline ${className}`}>
      {title && <h3 className="openmesh-timeline__title">{title}</h3>}
      <div className="openmesh-timeline__list" role="list">
        {displayEvents.map((event, index) => {
          const color = SEVERITY_COLORS[event.severity];
          const time = new Date(event.timestamp).toLocaleString();

          return (
            <div
              key={`${event.timestamp}-${index}`}
              className={`openmesh-timeline__item openmesh-timeline__item--${event.severity.toLowerCase()}`}
              role="listitem"
            >
              <div className="openmesh-timeline__marker">
                <span
                  className="openmesh-timeline__dot"
                  style={{ backgroundColor: color }}
                  aria-hidden="true"
                />
                <span className="openmesh-timeline__line" aria-hidden="true" />
              </div>
              <div className="openmesh-timeline__content">
                <div className="openmesh-timeline__header">
                  <span
                    className="openmesh-timeline__severity"
                    style={{ color }}
                  >
                    {event.severity}
                  </span>
                  <span className="openmesh-timeline__domain">
                    {event.domain}
                  </span>
                  <time className="openmesh-timeline__time" dateTime={event.timestamp}>
                    {time}
                  </time>
                </div>
                <div className="openmesh-timeline__message">{event.message}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TimelineView;
