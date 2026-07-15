"use client";

import type {
  NotificationDestinationSummary,
  NotificationSubscriptionSummary,
} from "@pliegocheck/schemas";
import { FormEvent, useEffect, useState } from "react";
import {
  createNotificationDestination,
  createNotificationSubscription,
  listNotificationDestinations,
  listNotificationSubscriptions,
  setNotificationDestination,
  testNotificationDestination,
} from "../../../lib/api";

export default function NotificationSettingsPage() {
  const [destinations, setDestinations] = useState<NotificationDestinationSummary[]>([]);
  const [subscriptions, setSubscriptions] = useState<NotificationSubscriptionSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const refresh = async () => {
    const [d, s] = await Promise.all([
      listNotificationDestinations(),
      listNotificationSubscriptions(),
    ]);
    setDestinations(d.items);
    setSubscriptions(s.items);
  };
  useEffect(() => {
    void refresh().catch((cause) => setError(String(cause)));
  }, []);
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const channel = String(data.get("channel")) as "EMAIL_SMTP" | "SIGNED_WEBHOOK";
    try {
      await createNotificationDestination({
        channel,
        name: String(data.get("name")),
        email_address: channel === "EMAIL_SMTP" ? String(data.get("target")) : null,
        webhook_url: channel === "SIGNED_WEBHOOK" ? String(data.get("target")) : null,
        secret_reference:
          channel === "SIGNED_WEBHOOK" ? String(data.get("secret_reference")) : null,
        configuration: {},
      });
      form.reset();
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    }
  }
  async function subscribe(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      await createNotificationSubscription({
        destination_id: String(data.get("destination")),
        monitor_id: String(data.get("monitor_id") || "") || null,
        delivery_mode: String(data.get("mode")) as "IMMEDIATE" | "DAILY_DIGEST" | "WEEKLY_DIGEST",
        minimum_severity: String(data.get("severity")),
        alert_types: String(data.get("alert_types") || "")
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        quiet_hours: {
          start: String(data.get("quiet_start")),
          end: String(data.get("quiet_end")),
          critical_bypass: data.get("critical_bypass") === "on",
        },
        timezone: String(data.get("timezone")),
        daily_digest_time: String(data.get("daily_digest_time")),
        weekly_digest_day: Number(data.get("weekly_digest_day")),
        include_summary: true,
        include_opportunity_link: true,
      });
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    }
  }
  return (
    <main className="container wide">
      <header>
        <h1>Preferencias de notificaciones</h1>
      </header>
      <aside className="notice" role="note">
        La entrega externa está deshabilitada por defecto y depende de la configuración operativa.
      </aside>
      <aside className="notice" role="note">
        Una entrega aceptada por el servidor de correo o webhook no garantiza que el destinatario la
        haya leído o procesado.
      </aside>
      {error ? <p role="alert">{error}</p> : null}
      <section>
        <h2>Nuevo destino</h2>
        <form className="stack" onSubmit={create}>
          <label>
            Nombre
            <input name="name" required />
          </label>
          <label>
            Canal
            <select name="channel">
              <option>EMAIL_SMTP</option>
              <option>SIGNED_WEBHOOK</option>
            </select>
          </label>
          <label>
            Correo o URL
            <input name="target" required />
          </label>
          <label>
            Referencia de secreto (solo webhook)
            <input name="secret_reference" placeholder="PLIEGOCHECK_WEBHOOK_SECRET_LOCAL" />
          </label>
          <button>Crear destino</button>
        </form>
      </section>
      <section>
        <h2>Destinos</h2>
        {destinations.length ? (
          <ul className="cards">
            {destinations.map((item) => (
              <li key={item.id}>
                <strong>{item.name}</strong>
                <p>
                  {item.channel} · {item.masked_destination} · {item.status}
                </p>
                <div className="actions">
                  <button onClick={() => void testNotificationDestination(item.id)}>
                    Enviar prueba
                  </button>
                  <button
                    onClick={() =>
                      void setNotificationDestination(
                        item.id,
                        item.status === "PAUSED" ? "resume" : "pause",
                      ).then(refresh)
                    }
                  >
                    {item.status === "PAUSED" ? "Reanudar" : "Pausar"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p>No hay destinos configurados.</p>
        )}
      </section>
      <section>
        <h2>Suscripción</h2>
        <form className="inline-form" onSubmit={subscribe}>
          <label>
            Destino
            <select name="destination" required>
              <option value="">Destino</option>
              {destinations.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Modo
            <select name="mode">
              <option>IMMEDIATE</option>
              <option>DAILY_DIGEST</option>
              <option>WEEKLY_DIGEST</option>
            </select>
          </label>
          <label>
            Severidad mínima
            <select name="severity">
              <option>INFO</option>
              <option>MEDIUM</option>
              <option>HIGH</option>
              <option>CRITICAL</option>
            </select>
          </label>
          <label>
            Monitor (UUID opcional)
            <input name="monitor_id" />
          </label>
          <label>
            Tipos de alerta (separados por coma)
            <input name="alert_types" />
          </label>
          <label>
            Inicio silencioso
            <input name="quiet_start" type="time" defaultValue="20:00" required />
          </label>
          <label>
            Fin silencioso
            <input name="quiet_end" type="time" defaultValue="07:00" required />
          </label>
          <label>
            Zona horaria
            <input name="timezone" defaultValue="America/Bogota" required />
          </label>
          <label>
            Hora digest diario
            <input name="daily_digest_time" type="time" defaultValue="08:00" required />
          </label>
          <label>
            Día digest semanal (0=lunes)
            <input name="weekly_digest_day" type="number" min="0" max="6" defaultValue="0" />
          </label>
          <label>
            <input name="critical_bypass" type="checkbox" defaultChecked /> CRITICAL atraviesa quiet
            hours
          </label>
          <button>Crear suscripción</button>
        </form>
        <p>{subscriptions.length} suscripciones configuradas.</p>
      </section>
    </main>
  );
}
