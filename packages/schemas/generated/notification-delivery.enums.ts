// Archivo generado automaticamente por packages/schemas/scripts/generate.py.
// No editar a mano: la definicion canonica son los modelos Pydantic de
// packages/schemas/src/pliegocheck_schemas/.

export const NOTIFICATION_DELIVERY_SCHEMA_VERSION = "1.0.0";

export const NOTIFICATION_CHANNEL_VALUES = [
  "INTERNAL_ONLY",
  "EMAIL_SMTP",
  "SIGNED_WEBHOOK",
] as const;
export type NotificationChannelValue = (typeof NOTIFICATION_CHANNEL_VALUES)[number];

export const NOTIFICATION_DESTINATION_STATUS_VALUES = [
  "ACTIVE",
  "PAUSED",
  "DISABLED",
  "ERROR",
  "PENDING_VERIFICATION",
] as const;
export type NotificationDestinationStatusValue =
  (typeof NOTIFICATION_DESTINATION_STATUS_VALUES)[number];

export const NOTIFICATION_DELIVERY_MODE_VALUES = [
  "IMMEDIATE",
  "DAILY_DIGEST",
  "WEEKLY_DIGEST",
  "INTERNAL_ONLY",
] as const;
export type NotificationDeliveryModeValue = (typeof NOTIFICATION_DELIVERY_MODE_VALUES)[number];

export const NOTIFICATION_OUTBOX_STATUS_VALUES = [
  "PENDING",
  "PROCESSING",
  "DELIVERED",
  "FAILED_RETRYABLE",
  "FAILED_PERMANENT",
  "CANCELLED",
  "SUPPRESSED",
  "DRY_RUN",
] as const;
export type NotificationOutboxStatusValue = (typeof NOTIFICATION_OUTBOX_STATUS_VALUES)[number];

export const NOTIFICATION_ATTEMPT_STATUS_VALUES = [
  "DELIVERED",
  "RETRYABLE",
  "PERMANENT",
  "DRY_RUN",
] as const;
export type NotificationAttemptStatusValue = (typeof NOTIFICATION_ATTEMPT_STATUS_VALUES)[number];

export const NOTIFICATION_DIGEST_PERIOD_VALUES = ["DAILY", "WEEKLY"] as const;
export type NotificationDigestPeriodValue = (typeof NOTIFICATION_DIGEST_PERIOD_VALUES)[number];

export const NOTIFICATION_OPERATION_ACTION_VALUES = ["RETRY", "CANCEL", "SUPPRESS"] as const;
export type NotificationOperationActionValue =
  (typeof NOTIFICATION_OPERATION_ACTION_VALUES)[number];
