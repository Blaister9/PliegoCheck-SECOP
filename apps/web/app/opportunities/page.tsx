"use client";

import type {
  CompanyProfileSnapshotSummary,
  CompanyProfileSummary,
  OpportunityAssessmentDetail,
  OpportunityOutcome,
  OpportunityReviewAction,
} from "@pliegocheck/schemas";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import {
  ApiClientError,
  createOpportunityDiscovery,
  getOpportunityDiscovery,
  importOpportunity,
  listCompanies,
  listOpportunities,
  listSnapshots,
  requestOpportunityDeepAnalysis,
  reviewOpportunity,
} from "../../lib/api";

const NOTICE =
  "La priorización expresa compatibilidad preliminar con el perfil empresarial y la información pública disponible. No recomienda presentar oferta ni reemplaza la revisión humana.";
const OUTCOMES: (OpportunityOutcome | "")[] = [
  "",
  "REVISAR_PRIMERO",
  "OPORTUNIDAD_POTENCIAL",
  "REQUIERE_ALIADO",
  "INFORMACION_INSUFICIENTE",
  "POCO_COMPATIBLE",
  "DESCARTAR",
];

export default function OpportunitiesPage() {
  const [companies, setCompanies] = useState<CompanyProfileSummary[]>([]);
  const [snapshots, setSnapshots] = useState<CompanyProfileSnapshotSummary[]>([]);
  const [companyId, setCompanyId] = useState("");
  const [snapshotId, setSnapshotId] = useState("");
  const [items, setItems] = useState<OpportunityAssessmentDetail[]>([]);
  const [selected, setSelected] = useState<OpportunityAssessmentDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [empty, setEmpty] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [deepStatus, setDeepStatus] = useState<string | null>(null);
  const [outcomeFilter, setOutcomeFilter] = useState("");
  const [sortOrder, setSortOrder] = useState("priority");

  useEffect(() => {
    listCompanies({ limit: 100 })
      .then((data) => setCompanies(data.items))
      .catch(showError);
  }, []);

  async function changeCompany(id: string) {
    setCompanyId(id);
    setSnapshotId("");
    setSnapshots([]);
    if (!id) return;
    try {
      const rows = await listSnapshots(id);
      setSnapshots(rows.filter((row) => row.status === "PUBLISHED"));
    } catch (cause) {
      showError(cause);
    }
  }

  async function changeSnapshot(id: string) {
    setSnapshotId(id);
    if (!id) {
      setItems([]);
      return;
    }
    try {
      const data = await listOpportunities({ company_snapshot_id: id, sort: "priority" });
      setItems(data.items);
      setEmpty(data.items.length === 0);
    } catch (cause) {
      showError(cause);
    }
  }

  async function discover(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!companyId || !snapshotId)
      return setError("Selecciona una empresa y un snapshot publicado.");
    const form = new FormData(event.currentTarget);
    setLoading(true);
    setError(null);
    setEmpty(false);
    try {
      const response = await createOpportunityDiscovery({
        company_profile_id: companyId,
        company_snapshot_id: snapshotId,
        search_requests: [
          {
            source_system: String(form.get("source")) as "SECOP_I" | "SECOP_II",
            query: String(form.get("query") || "") || null,
            department: String(form.get("department") || "") || null,
            limit: 50,
          },
        ],
      });
      setProgress(response.run.status);
      let run = response.run;
      for (
        let attempt = 0;
        attempt < 20 && ["PENDING", "PROCESSING"].includes(run.status);
        attempt += 1
      ) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        run = await getOpportunityDiscovery(run.id);
        setProgress(run.status);
      }
      if (!["COMPLETED", "COMPLETED_WITH_WARNINGS"].includes(run.status))
        throw new Error("El discovery no terminó dentro del tiempo esperado.");
      await refresh(String(form.get("outcome") || ""), String(form.get("sort") || "priority"));
    } catch (cause) {
      showError(cause);
    } finally {
      setLoading(false);
    }
  }

  async function refresh(outcome = "", sort = "priority") {
    const data = await listOpportunities({
      company_snapshot_id: snapshotId,
      outcome: (outcome || null) as OpportunityOutcome | null,
      sort,
    });
    setItems(data.items);
    setEmpty(data.items.length === 0);
  }

  async function action(id: string, reviewAction: OpportunityReviewAction) {
    try {
      await reviewOpportunity(id, { action: reviewAction });
      setItems((rows) =>
        rows.map((row) => (row.id === id ? { ...row, latest_review_action: reviewAction } : row)),
      );
    } catch (cause) {
      showError(cause);
    }
  }

  async function importOne(id: string) {
    try {
      await importOpportunity(id);
      await refresh();
    } catch (cause) {
      showError(cause);
    }
  }

  async function deep(id: string) {
    try {
      const result = await requestOpportunityDeepAnalysis(id);
      setDeepStatus(
        `Listos: ${result.steps_ready?.join(", ") || "ninguno"}. Bloqueados: ${result.steps_blocked?.join(", ") || "ninguno"}.`,
      );
    } catch (cause) {
      showError(cause);
    }
  }

  function showError(cause: unknown) {
    setError(
      cause instanceof ApiClientError
        ? cause.message
        : cause instanceof Error
          ? cause.message
          : "No fue posible completar la operación.",
    );
    setLoading(false);
  }

  return (
    <main className="container wide">
      <header className="page-header">
        <div>
          <h1>Oportunidades SECOP</h1>
          <p className="lead">
            Bandeja de conveniencia para revisión basada en un snapshot empresarial inmutable.
          </p>
        </div>
        <Link className="button secondary" href="/">
          Inicio
        </Link>
      </header>
      <aside className="notice" role="note">
        {NOTICE}
      </aside>
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      <form className="form-grid" onSubmit={discover}>
        <label>
          Empresa
          <select
            aria-label="Empresa"
            value={companyId}
            onChange={(event) => void changeCompany(event.target.value)}
          >
            <option value="">Seleccionar</option>
            {companies.map((company) => (
              <option key={company.id} value={company.id}>
                {company.legal_name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Snapshot publicado
          <select
            aria-label="Snapshot publicado"
            value={snapshotId}
            onChange={(event) => void changeSnapshot(event.target.value)}
          >
            <option value="">Seleccionar</option>
            {snapshots.map((snapshot) => (
              <option key={snapshot.id} value={snapshot.id}>
                Versión {snapshot.version} · {snapshot.completeness_status}
              </option>
            ))}
          </select>
        </label>
        <label>
          Fuente
          <select name="source">
            <option value="SECOP_II">SECOP II</option>
            <option value="SECOP_I">SECOP I</option>
          </select>
        </label>
        <label>
          Palabra clave
          <input name="query" />
        </label>
        <label>
          Departamento
          <input name="department" />
        </label>
        <label>
          Outcome
          <select
            name="outcome"
            value={outcomeFilter}
            onChange={(event) => {
              const value = event.target.value;
              setOutcomeFilter(value);
              if (snapshotId) void refresh(value, sortOrder);
            }}
          >
            {OUTCOMES.map((outcome) => (
              <option key={outcome || "all"} value={outcome}>
                {outcome || "Todos"}
              </option>
            ))}
          </select>
        </label>
        <label>
          Orden
          <select
            name="sort"
            value={sortOrder}
            onChange={(event) => {
              const value = event.target.value;
              setSortOrder(value);
              if (snapshotId) void refresh(outcomeFilter, value);
            }}
          >
            <option value="priority">Prioridad de revisión</option>
            <option value="compatibility">Compatibilidad</option>
            <option value="urgency">Urgencia</option>
            <option value="closing_date">Cierre</option>
          </select>
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Consultando…" : "Descubrir oportunidades"}
        </button>
      </form>
      {progress ? <p aria-live="polite">Estado del discovery: {progress}</p> : null}
      {empty ? <p>No se encontraron oportunidades con estos filtros.</p> : null}
      <section aria-label="Bandeja de oportunidades" className="card-grid">
        {items.map((item) => (
          <article className="card" key={item.id}>
            <p className="status-badge">{item.outcome}</p>
            <h2>{item.candidate.title}</h2>
            <p>{item.candidate.entity_name}</p>
            <p>
              <strong>Compatibilidad:</strong> {item.compatibility_score}/100 ·{" "}
              <strong>Urgencia:</strong> {item.urgency_status} · <strong>Completitud:</strong>{" "}
              {item.information_completeness}/100
            </p>
            <p>
              <strong>Cierre:</strong>{" "}
              {item.candidate.closing_date
                ? new Date(item.candidate.closing_date).toLocaleString("es-CO")
                : "No informado"}{" "}
              · <strong>Documentos:</strong> {item.candidate.document_status}
            </p>
            <p>
              <strong>Información faltante:</strong>{" "}
              {Object.values(item.missing_information ?? {})
                .flat()
                .join(", ") || "Ninguna registrada"}
            </p>
            <div className="actions">
              <button onClick={() => setSelected(item)}>Ver detalle</button>
              <button onClick={() => void action(item.id, "SHORTLIST")}>Shortlist</button>
              <button onClick={() => void action(item.id, "DISMISS")}>Descartar</button>
              <button onClick={() => void action(item.id, "SEEK_PARTNER")}>Revisar aliado</button>
              <button onClick={() => void importOne(item.id)}>Importar</button>
              <button onClick={() => void deep(item.id)}>Análisis profundo</button>
            </div>
          </article>
        ))}
      </section>
      {selected ? (
        <section className="card" aria-label="Detalle de oportunidad">
          <h2>Detalle</h2>
          <p>{selected.summary}</p>
          <h3>Componentes y razones</h3>
          <ul>
            {selected.components.map((component) => (
              <li key={component.component}>
                <strong>{component.component}</strong>: {component.status} · {component.explanation}
              </li>
            ))}
          </ul>
          <h3>Evidencias</h3>
          <p>
            {selected.components.flatMap((component) => component.evidence).length
              ? "Evidencias trazadas disponibles."
              : "Sin evidencias documentales en este nivel."}
          </p>
          <button onClick={() => setSelected(null)}>Cerrar detalle</button>
        </section>
      ) : null}
      {deepStatus ? (
        <p className="notice" aria-live="polite">
          {deepStatus}
        </p>
      ) : null}
    </main>
  );
}
