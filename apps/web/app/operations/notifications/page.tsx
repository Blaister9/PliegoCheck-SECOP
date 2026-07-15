"use client";

import type { NotificationReadiness, NotificationStatistics } from "@pliegocheck/schemas";
import { useEffect, useState } from "react";
import {
  notificationReadiness,
  notificationStatistics,
  runNotificationRetention,
} from "../../../lib/api";

export default function NotificationOperationsPage() {
  const [ready, setReady] = useState<NotificationReadiness | null>(null);
  const [stats, setStats] = useState<NotificationStatistics | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    void Promise.all([notificationReadiness(), notificationStatistics()])
      .then(([r, s]) => {
        setReady(r);
        setStats(s);
      })
      .catch((cause) => setError(cause instanceof Error ? cause.message : String(cause)));
  }, []);
  return (
    <main className="container wide">
      <h1>Operación de notificaciones</h1>
      {error ? <p role="alert">{error}</p> : null}
      {!ready ? (
        <p>Cargando readiness…</p>
      ) : (
        <>
          <aside className="notice" role="note">
            {ready.external_delivery_enabled
              ? "Entrega externa habilitada."
              : "Entrega externa deshabilitada por configuración operativa."}{" "}
            Dry-run: {String(ready.dry_run)}
          </aside>
          <section className="metadata-grid">
            <h2>Cola</h2>
            <dl>
              <dt>Pendientes</dt>
              <dd>{ready.pending_count}</dd>
              <dt>Procesando</dt>
              <dd>{ready.processing_count}</dd>
              <dt>Retryable</dt>
              <dd>{ready.retryable_count}</dd>
              <dt>Fallos permanentes</dt>
              <dd>{ready.permanent_failure_count}</dd>
              <dt>Entregadas 24h</dt>
              <dd>{ready.delivered_last_24h}</dd>
              <dt>Suprimidas 24h</dt>
              <dd>{ready.suppressed_last_24h}</dd>
              <dt>Más antigua pendiente (segundos)</dt>
              <dd>{ready.oldest_pending_age_seconds ?? "N/A"}</dd>
              <dt>Último worker</dt>
              <dd>{ready.worker_last_seen ?? "N/A"}</dd>
              <dt>Último digest</dt>
              <dd>{ready.digest_last_run ?? "N/A"}</dd>
              <dt>Última retención</dt>
              <dd>{ready.retention_last_run ?? "N/A"}</dd>
            </dl>
            <p>
              Canales: correo {ready.email_enabled ? "habilitado" : "deshabilitado"}; webhook{" "}
              {ready.webhook_enabled ? "habilitado" : "deshabilitado"}.
            </p>
          </section>
        </>
      )}
      <section>
        <h2>Estadísticas</h2>
        <pre>{JSON.stringify(stats?.by_status ?? {}, null, 2)}</pre>
        <button
          onClick={() =>
            void runNotificationRetention(true).then((result) =>
              setMessage(
                `Dry-run: ${result.payloads_cleared} payloads, ${result.attempts_deleted} attempts`,
              ),
            )
          }
        >
          Simular retención
        </button>
        <p>{message}</p>
      </section>
    </main>
  );
}
