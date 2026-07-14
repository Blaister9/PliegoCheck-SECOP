"use client";

import type {
  CompanyProfileSnapshotSummary,
  CompanyProfileSummary,
  OpportunityMonitorSummary,
} from "@pliegocheck/schemas";
import { FormEvent, useEffect, useState } from "react";
import {
  createMonitor,
  listCompanies,
  listMonitors,
  listSnapshots,
  pauseMonitor,
  resumeMonitor,
  runMonitor,
} from "../../lib/api";

const WARNING =
  "Las ejecuciones periódicas dependen de la disponibilidad de SECOP y de la información pública publicada.";

export default function MonitorsPage() {
  const [items, setItems] = useState<OpportunityMonitorSummary[]>([]);
  const [companies, setCompanies] = useState<CompanyProfileSummary[]>([]);
  const [snapshots, setSnapshots] = useState<CompanyProfileSnapshotSummary[]>([]);
  const [company, setCompany] = useState("");
  const [error, setError] = useState<string | null>(null);
  const refresh = () =>
    listMonitors()
      .then((x) => setItems(x.items))
      .catch(showError);
  useEffect(() => {
    void refresh();
    listCompanies({ limit: 100 })
      .then((x) => setCompanies(x.items))
      .catch(showError);
  }, []);
  function showError(cause: unknown) {
    setError(cause instanceof Error ? cause.message : "No fue posible completar la operación.");
  }
  async function changeCompany(id: string) {
    setCompany(id);
    setSnapshots(id ? (await listSnapshots(id)).filter((x) => x.status === "PUBLISHED") : []);
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      await createMonitor({
        name: String(data.get("name")),
        description: null,
        company_profile_id: company,
        company_snapshot_id: String(data.get("snapshot")),
        frequency: String(data.get("frequency")) as "HOURLY",
        timezone: "America/Bogota",
        source_systems: [String(data.get("source")) as "SECOP_I"],
        filters: {
          search_requests: [
            {
              source_system: String(data.get("source")) as "SECOP_I",
              query: String(data.get("query")),
              limit: 50,
            },
          ],
          candidate_ids: [],
        },
        alert_rules: {
          new_review_first: true,
          new_potential: true,
          partner_needed: true,
          urgent_deadline: true,
          critical_deadline: true,
          outcome_changes: true,
          compatibility_changes: true,
          closing_date_changes: true,
          process_closed: true,
          new_documents: true,
          document_updates: true,
          addenda: true,
          monitor_failures: true,
          compatibility_change_threshold: 10,
          minimum_compatibility_score: 0,
          minimum_information_completeness: 0,
          urgent_days: 5,
          critical_hours: 48,
          alert_on_initial_results: Boolean(data.get("initial")),
        },
      });
      await refresh();
      event.currentTarget.reset();
    } catch (cause) {
      showError(cause);
    }
  }
  async function action(item: OpportunityMonitorSummary, kind: "pause" | "resume" | "run") {
    try {
      if (kind === "pause") await pauseMonitor(item.id);
      else if (kind === "resume") await resumeMonitor(item.id);
      else await runMonitor(item.id);
      await refresh();
    } catch (cause) {
      showError(cause);
    }
  }
  return (
    <main className="container wide">
      <header>
        <h1>Monitores de oportunidades</h1>
        <p>Configura búsquedas periódicas vinculadas a un snapshot publicado.</p>
      </header>
      <aside className="notice" role="note">
        {WARNING}
      </aside>
      {error ? <p role="alert">{error}</p> : null}
      <section>
        <h2>Crear monitor</h2>
        <form onSubmit={submit} className="stack">
          <label>
            Nombre
            <input name="name" required />
          </label>
          <label>
            Empresa
            <select
              aria-label="Empresa"
              required
              value={company}
              onChange={(e) => void changeCompany(e.target.value)}
            >
              <option value="">Selecciona</option>
              {companies.map((x) => (
                <option key={x.id} value={x.id}>
                  {x.legal_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Snapshot publicado
            <select name="snapshot" required>
              <option value="">Selecciona</option>
              {snapshots.map((x) => (
                <option key={x.id} value={x.id}>
                  {x.version}
                </option>
              ))}
            </select>
          </label>
          <label>
            Fuente
            <select name="source">
              <option>SECOP_I</option>
              <option>SECOP_II</option>
            </select>
          </label>
          <label>
            Filtro SECOP
            <input name="query" required />
          </label>
          <label>
            Frecuencia
            <select name="frequency">
              <option>HOURLY</option>
              <option>EVERY_3_HOURS</option>
              <option>EVERY_6_HOURS</option>
              <option>EVERY_12_HOURS</option>
              <option>DAILY</option>
              <option>WEEKDAYS</option>
            </select>
          </label>
          <label>
            <input type="checkbox" name="initial" />
            Alertar resultados iniciales
          </label>
          <button type="submit">Crear monitor</button>
        </form>
      </section>
      <section>
        <h2>Monitores guardados</h2>
        {items.length === 0 ? (
          <p>No hay monitores configurados.</p>
        ) : (
          <ul className="cards">
            {items.map((x) => (
              <li key={x.id}>
                <strong>{x.name}</strong>
                <p>
                  {x.status} · {x.frequency} · próxima: {x.next_run_at ?? "sin programar"}
                </p>
                <div className="actions">
                  <button
                    onClick={() => void action(x, x.status === "PAUSED" ? "resume" : "pause")}
                  >
                    {x.status === "PAUSED" ? "Reanudar" : "Pausar"}
                  </button>
                  <button onClick={() => void action(x, "run")}>Ejecutar ahora</button>
                  <a href={`/alerts?monitor_id=${x.id}`}>Ver alertas</a>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
