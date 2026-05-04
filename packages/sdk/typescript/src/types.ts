/**
 * OpenMesh Framework TypeScript SDK — Type Definitions
 *
 * Core type definitions for MeshHealthEvent, DomainRegistration,
 * HealthCheck, Metric, PanelDefinition, and AdapterMetadata.
 */

// ── Severity ────────────────────────────────────────────────────────

export type Severity = 'Critical' | 'Warning' | 'Info';

export const VALID_SEVERITIES: readonly Severity[] = ['Critical', 'Warning', 'Info'] as const;

// ── Health Status ───────────────────────────────────────────────────

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export const VALID_HEALTH_STATUSES: readonly HealthStatus[] = ['healthy', 'degraded', 'unhealthy'] as const;

// ── Runtime Type ────────────────────────────────────────────────────

export type RuntimeType = 'server' | 'serverless' | 'kubernetes' | 'gpu' | 'streaming';

export const VALID_RUNTIME_TYPES: readonly RuntimeType[] = ['server', 'serverless', 'kubernetes', 'gpu', 'streaming'] as const;

// ── Severity Color Mapping ──────────────────────────────────────────

export const SEVERITY_COLORS: Record<Severity, string> = {
  Critical: 'red',
  Warning: 'amber',
  Info: 'blue',
} as const;

// ── MeshHealthEvent ─────────────────────────────────────────────────

export interface MeshHealthEvent {
  entity_id: string;
  domain: string;
  severity: Severity;
  message: string;
  timestamp: string; // ISO 8601
  metadata?: Record<string, unknown>;
}

// ── HealthCheck ─────────────────────────────────────────────────────

export interface HealthCheck {
  name: string;
  status: HealthStatus;
  detail?: string;
}

// ── Metric ──────────────────────────────────────────────────────────

export interface Metric {
  metric_name: string;
  value: number;
  unit: string;
  timestamp: string; // ISO 8601
}

// ── PanelDefinition ─────────────────────────────────────────────────

export interface PanelDefinition {
  title: string;
  data_source_key: string;
  visualization_type: string;
  required_role: string;
}

// ── AdapterMetadata ─────────────────────────────────────────────────

export interface AdapterMetadata {
  name: string;
  version: string;
  supported_runtime_types: RuntimeType[];
  description: string;
}

// ── TabDefinition ───────────────────────────────────────────────────

export interface TabDefinition {
  title: string;
  panel_type: string;
  data_source: string;
}

// ── DomainRegistration ──────────────────────────────────────────────

export interface ProductFamilyDefinition {
  family_id: string;
  name: string;
  description?: string;
}

export interface DomainRegistration {
  domain_id: string;
  runtime_type: RuntimeType;
  observability_adapter: string;
  roles: string[];
  tabs: TabDefinition[];
  entity_id: string;
  lob_id: string;
  metadata?: Record<string, unknown>;
  product_families?: ProductFamilyDefinition[];
}
