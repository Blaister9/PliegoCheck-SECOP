"use client";

import type { OpportunityAlertActionValue, OpportunityAlertSummary } from "@pliegocheck/schemas";
import Link from "next/link";
import { useEffect, useState } from "react";
import { actOnAlert, listAlerts } from "../../lib/api";

const DISCLAIMER =
  "Las alertas señalan novedades o cambios relevantes según la política configurada. No constituyen una recomendación automática de presentar oferta.";

export default function AlertsPage() {
  const [items, setItems] = useState<OpportunityAlertSummary[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  async function refresh(next = status) {
    try {
      setItems((await listAlerts(next ? { status: next } : {})).items);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No fue posible cargar las alertas.");
    }
  }
  useEffect(() => {
    void refresh("");
  }, []);
  async function action(id: string, value: OpportunityAlertActionValue) {
    try {
      await actOnAlert(id, { action: value });
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No fue posible actualizar la alerta.");
    }
  }
  return (
    <main className="container wide">
      <header>
        <h1>Alertas de oportunidades</h1>
        <p>Revisa novedades deduplicadas y su explicación.</p>
      </header>
      <aside className="notice" role="note">
        {DISCLAIMER}
      </aside>
      {error ? <p role="alert">{error}</p> : null}
      <label>
        Estado
        <select
          aria-label="Estado"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            void refresh(e.target.value);
          }}
        >
          <option value="">Todos</option>
          <option>UNREAD</option>
          <option>READ</option>
          <option>ARCHIVED</option>
          <option>RESOLVED</option>
        </select>
      </label>
      {items.length === 0 ? (
        <p>No hay alertas para los filtros seleccionados.</p>
      ) : (
        <ul className="cards">
          {items.map((x) => (
            <li key={x.id}>
              <strong>{x.title}</strong>
              <p>
                {x.severity} · {x.status} · {x.alert_type}
              </p>
              <p>{x.summary}</p>
              <div className="actions">
                {x.opportunity_id ? (
                  <Link href={`/opportunities?selected=${x.opportunity_id}`}>
                    Abrir oportunidad
                  </Link>
                ) : null}
                <button
                  onClick={() =>
                    void action(x.id, x.status === "READ" ? "MARK_UNREAD" : "MARK_READ")
                  }
                >
                  {x.status === "READ" ? "Marcar no leída" : "Marcar leída"}
                </button>
                <button
                  onClick={() => void action(x.id, x.status === "ARCHIVED" ? "RESTORE" : "ARCHIVE")}
                >
                  {x.status === "ARCHIVED" ? "Restaurar" : "Archivar"}
                </button>
                <button onClick={() => void action(x.id, "RESOLVE")}>Resolver</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
