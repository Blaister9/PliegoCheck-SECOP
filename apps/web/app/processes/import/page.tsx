"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import type {
  ExternalProcurementSearchRequest,
  ExternalProcurementSearchResponse,
  ExternalProcurementSourceSummary,
} from "@pliegocheck/schemas";
import {
  ApiClientError,
  importExternalProcurementResult,
  listExternalProcurementSources,
  searchExternalProcurement,
} from "../../../lib/api";

export default function SecopImportPage() {
  const [sources, setSources] = useState<ExternalProcurementSourceSummary[]>([]);
  const [data, setData] = useState<ExternalProcurementSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState<string | null>(null);
  const [lastPayload, setLastPayload] = useState<ExternalProcurementSearchRequest | null>(null);

  useEffect(() => {
    listExternalProcurementSources()
      .then(setSources)
      .catch((loadError) =>
        setError(
          loadError instanceof ApiClientError
            ? loadError.message
            : "No fue posible cargar las fuentes.",
        ),
      );
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = buildPayload(form, 0);
    await executeSearch(payload);
  }

  async function executeSearch(payload: ExternalProcurementSearchRequest) {
    setLoading(true);
    setError(null);
    try {
      const response = await searchExternalProcurement(payload);
      setData(response);
      setLastPayload(payload);
    } catch (searchError) {
      setError(
        searchError instanceof ApiClientError
          ? searchError.message
          : "No fue posible consultar la fuente externa.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function importResult(resultId: string, sourceProcessId: string) {
    setImporting(resultId);
    setError(null);
    try {
      const imported = await importExternalProcurementResult(resultId, sourceProcessId);
      setData((current) =>
        current
          ? {
              ...current,
              items: current.items.map((item) =>
                item.id === resultId
                  ? { ...item, import_status: "IMPORTED", process_id: imported.process_id }
                  : item,
              ),
            }
          : current,
      );
    } catch (importError) {
      setError(
        importError instanceof ApiClientError
          ? importError.message
          : "No fue posible importar el proceso.",
      );
    } finally {
      setImporting(null);
    }
  }

  const sourceEnabled = sources.some((source) => source.enabled);
  const offset = lastPayload?.offset ?? 0;
  const limit = lastPayload?.limit ?? 20;

  return (
    <main className="container wide">
      <header className="page-header">
        <div>
          <h1>Buscar procesos SECOP</h1>
          <p className="lead">Consulta controlada de fuentes oficiales de Datos Abiertos.</p>
        </div>
        <Link className="button secondary" href="/processes">
          Volver a procesos
        </Link>
      </header>

      <aside className="notice" role="note" aria-label="Avisos de fuente externa">
        <p>
          Los datos provienen de fuentes públicas externas y pueden estar incompletos,
          desactualizados o sujetos a cambios.
        </p>
        <p>Importar un proceso no ejecuta evaluación automática ni reemplaza la revisión humana.</p>
        <p>PliegoCheck no presenta ofertas ni realiza trámites transaccionales en SECOP.</p>
      </aside>

      {!sourceEnabled && sources.length > 0 ? (
        <p className="warning">El conector SECOP está deshabilitado por configuración.</p>
      ) : null}
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : null}

      <form className="form-grid" onSubmit={submit}>
        <label>
          Fuente
          <select name="source_system" defaultValue="SECOP_II">
            {sources.map((source) => (
              <option key={source.id} value={source.source_system}>
                {source.name} · {source.status}
              </option>
            ))}
            {sources.length === 0 ? <option value="SECOP_II">SECOP II</option> : null}
          </select>
        </label>
        <Field name="query" label="Palabra clave" />
        <Field name="process_code" label="Código o referencia" />
        <Field name="entity_name" label="Entidad" />
        <Field name="modality" label="Modalidad" />
        <Field name="status" label="Estado" />
        <Field name="department" label="Departamento" />
        <Field name="municipality" label="Municipio" />
        <Field name="min_value" label="Cuantía mínima" type="number" />
        <Field name="max_value" label="Cuantía máxima" type="number" />
        <Field name="published_from" label="Publicado desde" type="date" />
        <Field name="published_to" label="Publicado hasta" type="date" />
        <Field name="closing_from" label="Cierre desde" type="date" />
        <Field name="closing_to" label="Cierre hasta" type="date" />
        <label>
          Resultados por página
          <select name="limit" defaultValue="20">
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </label>
        <button type="submit" disabled={loading || !sourceEnabled}>
          {loading ? "Buscando..." : "Buscar"}
        </button>
      </form>

      {data ? (
        <section>
          <div className="section-heading">
            <h2>Resultados ({data.search.result_count})</h2>
            <span className="status-badge">{data.search.status}</span>
          </div>
          {(data.search.unsupported_filters ?? []).length > 0 ? (
            <p className="warning">
              Filtros no soportados: {(data.search.unsupported_filters ?? []).join(", ")}.
            </p>
          ) : null}
          {data.items.length === 0 ? (
            <p className="empty-state">No se encontraron procesos.</p>
          ) : null}
          <div className="secop-results">
            {data.items.map((item) => (
              <article className="secop-result" key={item.id}>
                <div className="section-heading">
                  <h3>{item.title}</h3>
                  <span className="status-badge">{item.import_status}</span>
                </div>
                <p>
                  <strong>{item.entity_name}</strong>
                </p>
                <dl className="metadata-grid">
                  <div>
                    <dt>Referencia</dt>
                    <dd>{item.source_process_reference ?? item.source_process_id}</dd>
                  </div>
                  <div>
                    <dt>Modalidad</dt>
                    <dd>{item.modality ?? "No informada"}</dd>
                  </div>
                  <div>
                    <dt>Estado</dt>
                    <dd>{item.status ?? "No informado"}</dd>
                  </div>
                  <div>
                    <dt>Cuantía</dt>
                    <dd>{formatMoney(item.estimated_value, item.currency)}</dd>
                  </div>
                  <div>
                    <dt>Publicación</dt>
                    <dd>{formatDate(item.publication_date)}</dd>
                  </div>
                  <div>
                    <dt>Cierre</dt>
                    <dd>{formatDate(item.closing_date)}</dd>
                  </div>
                  <div>
                    <dt>Ubicación</dt>
                    <dd>
                      {[item.department, item.municipality].filter(Boolean).join(" · ") ||
                        "No informada"}
                    </dd>
                  </div>
                  <div>
                    <dt>Documentos</dt>
                    <dd>{item.documents_status}</dd>
                  </div>
                </dl>
                {(item.warnings ?? []).length > 0 ? (
                  <p className="warning">
                    Campos faltantes o normalizados: {(item.warnings ?? []).length}.
                  </p>
                ) : null}
                <div className="actions">
                  {item.source_url ? (
                    <a
                      className="button secondary"
                      href={item.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Abrir fuente oficial
                    </a>
                  ) : null}
                  {item.process_id ? (
                    <Link className="button" href={`/processes/${item.process_id}`}>
                      Ver proceso interno
                    </Link>
                  ) : (
                    <button
                      type="button"
                      disabled={importing === item.id}
                      onClick={() => void importResult(item.id, item.source_process_id)}
                    >
                      {importing === item.id ? "Importando..." : "Importar proceso"}
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
          <nav className="pagination" aria-label="Paginación de resultados SECOP">
            <button
              type="button"
              className="button secondary"
              disabled={offset === 0 || loading}
              onClick={() =>
                lastPayload &&
                void executeSearch({ ...lastPayload, offset: Math.max(0, offset - limit) })
              }
            >
              Anterior
            </button>
            <span>Desde {offset + 1}</span>
            <button
              type="button"
              className="button secondary"
              disabled={data.search.source_row_count < limit || loading}
              onClick={() =>
                lastPayload && void executeSearch({ ...lastPayload, offset: offset + limit })
              }
            >
              Siguiente
            </button>
          </nav>
        </section>
      ) : null}
    </main>
  );
}

function Field({ name, label, type = "text" }: { name: string; label: string; type?: string }) {
  return (
    <label>
      {label}
      <input name={name} type={type} min={type === "number" ? "0" : undefined} />
    </label>
  );
}

function buildPayload(form: FormData, offset: number): ExternalProcurementSearchRequest {
  const value = (name: string) => String(form.get(name) ?? "").trim() || null;
  const date = (name: string, end = false) => {
    const text = value(name);
    return text ? `${text}T${end ? "23:59:59" : "00:00:00"}-05:00` : null;
  };
  return {
    source_system: String(form.get("source_system") ?? "SECOP_II") as "SECOP_II" | "SECOP_I",
    query: value("query"),
    entity_name: value("entity_name"),
    modality: value("modality"),
    status: value("status"),
    department: value("department"),
    municipality: value("municipality"),
    process_code: value("process_code"),
    min_value: value("min_value"),
    max_value: value("max_value"),
    published_from: date("published_from"),
    published_to: date("published_to", true),
    closing_from: date("closing_from"),
    closing_to: date("closing_to", true),
    limit: Number(form.get("limit") ?? 20),
    offset,
  };
}

function formatDate(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("es-CO", { dateStyle: "medium" }).format(new Date(value))
    : "No informada";
}

function formatMoney(value: string | null, currency: string | null) {
  return value && currency
    ? new Intl.NumberFormat("es-CO", { style: "currency", currency }).format(Number(value))
    : value
      ? `${new Intl.NumberFormat("es-CO").format(Number(value))} · moneda no informada`
      : "No informada";
}
