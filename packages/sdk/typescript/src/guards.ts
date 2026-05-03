/**
 * OpenMesh Framework TypeScript SDK — Type Guards
 *
 * Runtime type guard functions for validating unknown data
 * against the framework's type definitions.
 */

import {
  DomainRegistration,
  HealthCheck,
  MeshHealthEvent,
  Metric,
  PanelDefinition,
  AdapterMetadata,
  VALID_SEVERITIES,
  VALID_HEALTH_STATUSES,
  VALID_RUNTIME_TYPES,
  Severity,
  HealthStatus,
  RuntimeType,
} from './types';

// ── Helpers ─────────────────────────────────────────────────────────

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

// ── MeshHealthEvent Guard ───────────────────────────────────────────

export function isMeshHealthEvent(obj: unknown): obj is MeshHealthEvent {
  if (!isRecord(obj)) return false;

  return (
    isNonEmptyString(obj.entity_id) &&
    isNonEmptyString(obj.domain) &&
    typeof obj.severity === 'string' &&
    (VALID_SEVERITIES as readonly string[]).includes(obj.severity) &&
    isNonEmptyString(obj.message) &&
    isNonEmptyString(obj.timestamp) &&
    (obj.metadata === undefined || isRecord(obj.metadata))
  );
}

// ── DomainRegistration Guard ────────────────────────────────────────

export function isDomainRegistration(obj: unknown): obj is DomainRegistration {
  if (!isRecord(obj)) return false;

  return (
    isNonEmptyString(obj.domain_id) &&
    typeof obj.runtime_type === 'string' &&
    (VALID_RUNTIME_TYPES as readonly string[]).includes(obj.runtime_type) &&
    isNonEmptyString(obj.observability_adapter) &&
    Array.isArray(obj.roles) &&
    obj.roles.every((r: unknown) => typeof r === 'string') &&
    Array.isArray(obj.tabs) &&
    obj.tabs.every((t: unknown) => isTabDefinition(t)) &&
    isNonEmptyString(obj.entity_id) &&
    isNonEmptyString(obj.lob_id) &&
    (obj.metadata === undefined || isRecord(obj.metadata))
  );
}

// ── HealthCheck Guard ───────────────────────────────────────────────

export function isHealthCheck(obj: unknown): obj is HealthCheck {
  if (!isRecord(obj)) return false;

  return (
    isNonEmptyString(obj.name) &&
    typeof obj.status === 'string' &&
    (VALID_HEALTH_STATUSES as readonly string[]).includes(obj.status) &&
    (obj.detail === undefined || typeof obj.detail === 'string')
  );
}

// ── Metric Guard ────────────────────────────────────────────────────

export function isMetric(obj: unknown): obj is Metric {
  if (!isRecord(obj)) return false;

  return (
    isNonEmptyString(obj.metric_name) &&
    typeof obj.value === 'number' &&
    isNonEmptyString(obj.unit) &&
    isNonEmptyString(obj.timestamp)
  );
}

// ── PanelDefinition Guard ───────────────────────────────────────────

export function isPanelDefinition(obj: unknown): obj is PanelDefinition {
  if (!isRecord(obj)) return false;

  return (
    isNonEmptyString(obj.title) &&
    isNonEmptyString(obj.data_source_key) &&
    isNonEmptyString(obj.visualization_type) &&
    isNonEmptyString(obj.required_role)
  );
}

// ── AdapterMetadata Guard ───────────────────────────────────────────

export function isAdapterMetadata(obj: unknown): obj is AdapterMetadata {
  if (!isRecord(obj)) return false;

  return (
    isNonEmptyString(obj.name) &&
    isNonEmptyString(obj.version) &&
    Array.isArray(obj.supported_runtime_types) &&
    obj.supported_runtime_types.length > 0 &&
    obj.supported_runtime_types.every(
      (rt: unknown) =>
        typeof rt === 'string' &&
        (VALID_RUNTIME_TYPES as readonly string[]).includes(rt)
    ) &&
    isNonEmptyString(obj.description)
  );
}

// ── TabDefinition Guard ─────────────────────────────────────────────

export function isTabDefinition(obj: unknown): obj is { title: string; panel_type: string; data_source: string } {
  if (!isRecord(obj)) return false;

  return (
    isNonEmptyString(obj.title) &&
    isNonEmptyString(obj.panel_type) &&
    isNonEmptyString(obj.data_source)
  );
}
