"use client";

import type { NotificationDeliverySummary } from "@pliegocheck/schemas";
import { useEffect, useState } from "react";
import { listNotificationDeliveries, operateNotificationDelivery } from "../../lib/api";

export default function NotificationDeliveriesPage() {
  const [items, setItems] = useState<NotificationDeliverySummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const refresh = () =>
    listNotificationDeliveries()
      .then((value) => setItems(value.items))
      .catch((cause) => setError(String(cause)));
  useEffect(() => {
    void refresh();
  }, []);
  return (
    <main className="container wide">
      <h1>Historial de entregas</h1>
      <aside className="notice" role="note">
        La alerta interna permanece disponible aunque falle un canal externo.
      </aside>
      {error ? <p role="alert">{error}</p> : null}
      {items.length ? (
        <ul className="cards">
          {items.map((item) => (
            <li key={item.id}>
              <strong>
                {item.channel} · {item.status}
              </strong>
              <p>
                {item.masked_destination} · intentos {item.attempt_count} · {item.created_at}
              </p>
              <p>Último error: {item.last_error_code ?? "ninguno"}</p>
              <div className="actions">
                <button
                  onClick={() => void operateNotificationDelivery(item.id, "retry").then(refresh)}
                >
                  Reintentar
                </button>
                <button
                  onClick={() => void operateNotificationDelivery(item.id, "cancel").then(refresh)}
                >
                  Cancelar
                </button>
                {item.alert_id ? <a href={`/alerts/${item.alert_id}`}>Abrir alerta</a> : null}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p>No hay entregas registradas.</p>
      )}
    </main>
  );
}
