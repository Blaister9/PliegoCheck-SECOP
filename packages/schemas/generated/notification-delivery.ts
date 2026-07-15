// Archivo generado automaticamente desde notification-delivery.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type NotificationAttemptStatus = "DELIVERED" | "RETRYABLE" | "PERMANENT" | "DRY_RUN";
export type NotificationChannel = "INTERNAL_ONLY" | "EMAIL_SMTP" | "SIGNED_WEBHOOK";
export type NotificationDeliveryMode =
  "IMMEDIATE" | "DAILY_DIGEST" | "WEEKLY_DIGEST" | "INTERNAL_ONLY";
export type NotificationOutboxStatus =
  | "PENDING"
  | "PROCESSING"
  | "DELIVERED"
  | "FAILED_RETRYABLE"
  | "FAILED_PERMANENT"
  | "CANCELLED"
  | "SUPPRESSED"
  | "DRY_RUN";
export type NotificationDestinationStatus =
  "ACTIVE" | "PAUSED" | "DISABLED" | "ERROR" | "PENDING_VERIFICATION";
export type NotificationDigestPeriod = "DAILY" | "WEEKLY";

export interface NotificationDelivery {
  delivery_detail: NotificationDeliveryDetail;
  delivery_list: NotificationDeliveryList;
  destination_create: NotificationDestinationCreateRequest;
  destination_detail: NotificationDestinationDetail;
  destination_list: NotificationDestinationList;
  digest: NotificationDigestSummary;
  operation: NotificationOperationResponse;
  readiness: NotificationReadiness;
  retention: NotificationRetentionResponse;
  statistics: NotificationStatistics;
  subscription_create: NotificationSubscriptionCreateRequest;
  subscription_detail: NotificationSubscriptionDetail;
  subscription_list: NotificationSubscriptionList;
  test_response: NotificationTestResponse;
}
export interface NotificationDeliveryDetail {
  alert_id: string | null;
  attempt_count: number;
  attempts?: NotificationAttemptSummary[];
  available_at: string;
  channel: NotificationChannel;
  created_at: string;
  delivered_at?: string | null;
  delivery_mode: NotificationDeliveryMode;
  destination_id: string;
  disclaimer?: string;
  id: string;
  last_error_code?: string | null;
  masked_destination: string;
  payload_metadata: {
    [k: string]: unknown;
  };
  status: NotificationOutboxStatus;
  subject: string;
  template_version: string;
}
export interface NotificationAttemptSummary {
  attempt_number: number;
  error_code?: string | null;
  error_message_sanitized?: string | null;
  finished_at?: string | null;
  http_status?: number | null;
  id: string;
  latency_ms?: number | null;
  smtp_response_code?: number | null;
  started_at: string;
  status: NotificationAttemptStatus;
}
export interface NotificationDeliveryList {
  items: NotificationDeliverySummary[];
  limit: number;
  offset: number;
  total: number;
}
export interface NotificationDeliverySummary {
  alert_id: string | null;
  attempt_count: number;
  available_at: string;
  channel: NotificationChannel;
  created_at: string;
  delivered_at?: string | null;
  delivery_mode: NotificationDeliveryMode;
  destination_id: string;
  id: string;
  last_error_code?: string | null;
  masked_destination: string;
  status: NotificationOutboxStatus;
}
export interface NotificationDestinationCreateRequest {
  channel: NotificationChannel;
  configuration?: {
    [k: string]: unknown;
  };
  email_address?: string | null;
  name: string;
  secret_reference?: string | null;
  webhook_url?: string | null;
}
export interface NotificationDestinationDetail {
  channel: NotificationChannel;
  configuration?: {
    [k: string]: unknown;
  };
  created_at: string;
  id: string;
  last_test_status?: string | null;
  last_tested_at?: string | null;
  masked_destination: string;
  name: string;
  owner_actor_id: string | null;
  secret_configured?: boolean;
  status: NotificationDestinationStatus;
  updated_at: string;
  verified_at?: string | null;
}
export interface NotificationDestinationList {
  items: NotificationDestinationSummary[];
  total: number;
}
export interface NotificationDestinationSummary {
  channel: NotificationChannel;
  created_at: string;
  id: string;
  last_test_status?: string | null;
  last_tested_at?: string | null;
  masked_destination: string;
  name: string;
  owner_actor_id: string | null;
  status: NotificationDestinationStatus;
  updated_at: string;
  verified_at?: string | null;
}
export interface NotificationDigestSummary {
  alert_count: number;
  destination_id: string;
  id: string;
  outbox_message_id?: string | null;
  period: NotificationDigestPeriod;
  period_end: string;
  period_start: string;
  status: string;
}
export interface NotificationOperationResponse {
  delivery_id: string;
  status: NotificationOutboxStatus;
}
export interface NotificationReadiness {
  delivered_last_24h?: number;
  digest_last_run?: string | null;
  dry_run: boolean;
  email_enabled: boolean;
  external_delivery_enabled: boolean;
  oldest_pending_age_seconds?: number | null;
  pending_count?: number;
  permanent_failure_count?: number;
  processing_count?: number;
  reasons?: string[];
  retention_last_run?: string | null;
  retryable_count?: number;
  suppressed_last_24h?: number;
  webhook_enabled: boolean;
  worker_last_seen?: string | null;
}
export interface NotificationRetentionResponse {
  attempts_deleted: number;
  dry_run: boolean;
  payloads_cleared: number;
}
export interface NotificationStatistics {
  by_channel: {
    [k: string]: number;
  };
  by_status: {
    [k: string]: number;
  };
  generated_at: string;
}
export interface NotificationSubscriptionCreateRequest {
  /**
   * @maxItems 100
   */
  alert_types?: string[];
  daily_digest_time?: string;
  delivery_mode?: "IMMEDIATE" | "DAILY_DIGEST" | "WEEKLY_DIGEST" | "INTERNAL_ONLY";
  destination_id: string;
  include_opportunity_link?: boolean;
  include_summary?: boolean;
  minimum_severity?: string;
  monitor_id?: string | null;
  quiet_hours?: NotificationQuietHours | null;
  timezone?: string;
  weekly_digest_day?: number;
}
export interface NotificationQuietHours {
  critical_bypass?: boolean;
  end: string;
  start: string;
}
export interface NotificationSubscriptionDetail {
  alert_types: string[];
  created_at: string;
  daily_digest_time: string;
  delivery_mode: NotificationDeliveryMode;
  destination_id: string;
  enabled: boolean;
  id: string;
  include_opportunity_link: boolean;
  include_summary: boolean;
  minimum_severity: string;
  monitor_id: string | null;
  owner_actor_id: string | null;
  quiet_hours?: NotificationQuietHours | null;
  timezone: string;
  updated_at: string;
  weekly_digest_day: number;
}
export interface NotificationSubscriptionList {
  items: NotificationSubscriptionSummary[];
  total: number;
}
export interface NotificationSubscriptionSummary {
  alert_types: string[];
  created_at: string;
  delivery_mode: NotificationDeliveryMode;
  destination_id: string;
  enabled: boolean;
  id: string;
  minimum_severity: string;
  monitor_id: string | null;
  owner_actor_id: string | null;
  timezone: string;
  updated_at: string;
}
export interface NotificationTestResponse {
  delivery_id: string;
  status: NotificationOutboxStatus;
}
