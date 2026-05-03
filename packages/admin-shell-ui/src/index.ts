/**
 * @openmesh/admin-shell-ui
 *
 * Generic React dashboard frame with pluggable layout
 * and standardized visualization components.
 */

// Layout components
export { Sidebar, TenantSwitcher, Breadcrumbs } from './layout';
export type {
  SidebarProps,
  SidebarItem,
  TenantSwitcherProps,
  TenantOption,
  BreadcrumbsProps,
  BreadcrumbItem,
} from './layout';

// Visualization components
export {
  HealthStatusGrid,
  SeverityChart,
  TimelineView,
  MetricCard,
  SEVERITY_COLORS,
  getSeverityColor,
} from './visualization';
export type {
  HealthStatusGridProps,
  HealthCheckItem,
  SeverityChartProps,
  SeverityCount,
  TimelineViewProps,
  TimelineEvent,
  MetricCardProps,
  TrendDirection,
} from './visualization';
