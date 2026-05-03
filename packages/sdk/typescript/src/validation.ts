/**
 * OpenMesh Framework TypeScript SDK — Validation Functions
 *
 * Validation functions for DomainRegistration YAML parsing
 * and MeshHealthEvent construction with detailed error reporting.
 */

import {
  DomainRegistration,
  MeshHealthEvent,
  VALID_SEVERITIES,
  VALID_RUNTIME_TYPES,
  Severity,
  RuntimeType,
} from './types';

// ── Validation Error ────────────────────────────────────────────────

export interface FieldError {
  field: string;
  issue: string;
}

export interface ValidationResult<T> {
  valid: boolean;
  value?: T;
  errors: FieldError[];
}

// ── MeshHealthEvent Validation ──────────────────────────────────────

export function validateMeshHealthEvent(
  data: Record<string, unknown>
): ValidationResult<MeshHealthEvent> {
  const errors: FieldError[] = [];

  if (typeof data.entity_id !== 'string' || data.entity_id === '') {
    errors.push({ field: 'entity_id', issue: 'Required non-empty string' });
  }

  if (typeof data.domain !== 'string' || data.domain === '') {
    errors.push({ field: 'domain', issue: 'Required non-empty string' });
  }

  if (
    typeof data.severity !== 'string' ||
    !(VALID_SEVERITIES as readonly string[]).includes(data.severity)
  ) {
    errors.push({
      field: 'severity',
      issue: `Must be one of: ${VALID_SEVERITIES.join(', ')}. Got: '${String(data.severity)}'`,
    });
  }

  if (typeof data.message !== 'string' || data.message === '') {
    errors.push({ field: 'message', issue: 'Required non-empty string' });
  }

  if (typeof data.timestamp !== 'string' || data.timestamp === '') {
    errors.push({ field: 'timestamp', issue: 'Required ISO 8601 date string' });
  }

  if (data.metadata !== undefined && (typeof data.metadata !== 'object' || data.metadata === null || Array.isArray(data.metadata))) {
    errors.push({ field: 'metadata', issue: 'Must be an object if provided' });
  }

  if (errors.length > 0) {
    return { valid: false, errors };
  }

  return {
    valid: true,
    value: data as unknown as MeshHealthEvent,
    errors: [],
  };
}

// ── DomainRegistration Validation ───────────────────────────────────

export function validateDomainRegistration(
  data: Record<string, unknown>
): ValidationResult<DomainRegistration> {
  const errors: FieldError[] = [];

  if (typeof data.domain_id !== 'string' || data.domain_id === '') {
    errors.push({ field: 'domain_id', issue: 'Required non-empty string' });
  }

  if (
    typeof data.runtime_type !== 'string' ||
    !(VALID_RUNTIME_TYPES as readonly string[]).includes(data.runtime_type)
  ) {
    errors.push({
      field: 'runtime_type',
      issue: `Must be one of: ${VALID_RUNTIME_TYPES.join(', ')}. Got: '${String(data.runtime_type)}'`,
    });
  }

  if (typeof data.observability_adapter !== 'string' || data.observability_adapter === '') {
    errors.push({ field: 'observability_adapter', issue: 'Required non-empty string' });
  }

  if (!Array.isArray(data.roles)) {
    errors.push({ field: 'roles', issue: 'Required array of strings' });
  } else if (!data.roles.every((r: unknown) => typeof r === 'string')) {
    errors.push({ field: 'roles', issue: 'All items must be strings' });
  }

  if (!Array.isArray(data.tabs)) {
    errors.push({ field: 'tabs', issue: 'Required array of tab definitions' });
  } else {
    data.tabs.forEach((tab: unknown, i: number) => {
      if (typeof tab !== 'object' || tab === null) {
        errors.push({ field: `tabs[${i}]`, issue: 'Must be an object' });
      } else {
        const t = tab as Record<string, unknown>;
        if (typeof t.title !== 'string') {
          errors.push({ field: `tabs[${i}].title`, issue: 'Required string' });
        }
      }
    });
  }

  if (typeof data.entity_id !== 'string' || data.entity_id === '') {
    errors.push({ field: 'entity_id', issue: 'Required non-empty string' });
  }

  if (typeof data.lob_id !== 'string' || data.lob_id === '') {
    errors.push({ field: 'lob_id', issue: 'Required non-empty string' });
  }

  if (errors.length > 0) {
    return { valid: false, errors };
  }

  return {
    valid: true,
    value: data as unknown as DomainRegistration,
    errors: [],
  };
}
