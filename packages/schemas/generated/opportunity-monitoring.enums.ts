// Archivo generado automaticamente por packages/schemas/scripts/generate.py.
// No editar a mano: la definicion canonica son los modelos Pydantic de
// packages/schemas/src/pliegocheck_schemas/.

export const OPPORTUNITY_MONITORING_SCHEMA_VERSION = "1.0.0";

export const OPPORTUNITY_MONITOR_STATUS_VALUES = ["ACTIVE", "PAUSED", "DISABLED", "ERROR"] as const;
export type OpportunityMonitorStatusValue = (typeof OPPORTUNITY_MONITOR_STATUS_VALUES)[number];

export const OPPORTUNITY_MONITOR_FREQUENCY_VALUES = [
  "HOURLY",
  "EVERY_3_HOURS",
  "EVERY_6_HOURS",
  "EVERY_12_HOURS",
  "DAILY",
  "WEEKDAYS",
] as const;
export type OpportunityMonitorFrequencyValue =
  (typeof OPPORTUNITY_MONITOR_FREQUENCY_VALUES)[number];

export const OPPORTUNITY_MONITOR_RUN_STATUS_VALUES = [
  "PENDING",
  "PROCESSING",
  "COMPLETED",
  "COMPLETED_WITH_WARNINGS",
  "FAILED",
  "CANCELLED",
  "SKIPPED",
] as const;
export type OpportunityMonitorRunStatusValue =
  (typeof OPPORTUNITY_MONITOR_RUN_STATUS_VALUES)[number];

export const OPPORTUNITY_MONITOR_TRIGGER_TYPE_VALUES = [
  "SCHEDULED",
  "MANUAL",
  "RETRY",
  "BASELINE",
] as const;
export type OpportunityMonitorTriggerTypeValue =
  (typeof OPPORTUNITY_MONITOR_TRIGGER_TYPE_VALUES)[number];

export const OPPORTUNITY_ALERT_TYPE_VALUES = [
  "NEW_REVIEW_FIRST",
  "NEW_POTENTIAL_OPPORTUNITY",
  "NEW_PARTNER_NEEDED",
  "OPPORTUNITY_NOW_URGENT",
  "OPPORTUNITY_NOW_CRITICAL",
  "OUTCOME_IMPROVED",
  "OUTCOME_WORSENED",
  "COMPATIBILITY_INCREASED",
  "COMPATIBILITY_DECREASED",
  "CLOSING_DATE_CHANGED",
  "PROCESS_CLOSED",
  "NEW_DOCUMENT_DISCOVERED",
  "DOCUMENT_UPDATED",
  "POTENTIAL_ADDENDUM_DISCOVERED",
  "CONFIRMED_ADDENDUM_DISCOVERED",
  "DEEP_ANALYSIS_BLOCKED",
  "MONITOR_FAILURE",
  "MONITOR_RECOVERED",
] as const;
export type OpportunityAlertTypeValue = (typeof OPPORTUNITY_ALERT_TYPE_VALUES)[number];

export const OPPORTUNITY_ALERT_SEVERITY_VALUES = [
  "INFO",
  "LOW",
  "MEDIUM",
  "HIGH",
  "CRITICAL",
] as const;
export type OpportunityAlertSeverityValue = (typeof OPPORTUNITY_ALERT_SEVERITY_VALUES)[number];

export const OPPORTUNITY_ALERT_STATUS_VALUES = ["UNREAD", "READ", "ARCHIVED", "RESOLVED"] as const;
export type OpportunityAlertStatusValue = (typeof OPPORTUNITY_ALERT_STATUS_VALUES)[number];

export const OPPORTUNITY_ALERT_ACTION_VALUES = [
  "MARK_READ",
  "MARK_UNREAD",
  "ARCHIVE",
  "RESTORE",
  "RESOLVE",
] as const;
export type OpportunityAlertActionValue = (typeof OPPORTUNITY_ALERT_ACTION_VALUES)[number];
