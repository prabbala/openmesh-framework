/**
 * OpenMesh Framework TypeScript SDK
 *
 * Type definitions, type guards, and validation functions for
 * DomainRegistration, MeshHealthEvent, and adapter interfaces.
 */

// Types
export {
  Severity,
  HealthStatus,
  RuntimeType,
  MeshHealthEvent,
  HealthCheck,
  Metric,
  PanelDefinition,
  AdapterMetadata,
  TabDefinition,
  DomainRegistration,
  ProductFamilyDefinition,
  VALID_SEVERITIES,
  VALID_HEALTH_STATUSES,
  VALID_RUNTIME_TYPES,
  SEVERITY_COLORS,
} from './types';

// Type Guards
export {
  isMeshHealthEvent,
  isDomainRegistration,
  isHealthCheck,
  isMetric,
  isPanelDefinition,
  isAdapterMetadata,
  isTabDefinition,
} from './guards';

// Validation
export {
  FieldError,
  ValidationResult,
  validateMeshHealthEvent,
  validateDomainRegistration,
} from './validation';
