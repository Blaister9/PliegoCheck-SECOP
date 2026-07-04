"use client";

import { useCallback, useState } from "react";
import type {
  DecisionReportPackageDetail,
  DecisionReportPackageList,
  DecisionReportPreview,
  DecisionRunList,
} from "@pliegocheck/schemas";
import {
  ApiClientError,
  createDecisionReport,
  decisionReportArtifactDownloadUrl,
  decisionReportZipDownloadUrl,
  getDecisionReport,
  getDecisionReportPreview,
  listDecisionReports,
  listDecisions,
  retryDecisionReport,
} from "../../../lib/api";

export function DecisionReportPanel({ processId }: { processId: string }) {
  const [decisions, setDecisions] = useState<DecisionRunList | null>(null);
  const [packages, setPackages] = useState<DecisionReportPackageList | null>(null);
  const [detail, setDetail] = useState<DecisionReportPackageDetail | null>(null);
  const [preview, setPreview] = useState<DecisionReportPreview | null>(null);
  const [decisionRunId, setDecisionRunId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setError(null);
    try {
      const decisionPayload = await listDecisions(processId, { limit: 20 });
      setDecisions(decisionPayload);
      const firstCompleted = decisionPayload.items.find((run) =>
        run.status.startsWith("COMPLETED"),
      );
      const selected = decisionRunId || firstCompleted?.id || "";
      setDecisionRunId(selected);
      setPackages(await listDecisionReports(processId, { decision_run_id: selected || undefined }));
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError ? loadError.message : "Error consultando reportes.",
      );
    }
  }, [processId, decisionRunId]);

  async function create(force = false) {
    if (!decisionRunId || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await createDecisionReport(processId, { decision_run_id: decisionRunId, force });
      await reload();
    } catch (createError) {
      setError(
        createError instanceof ApiClientError ? createError.message : "Error creando reporte.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function openPackage(packageId: string) {
    setError(null);
    try {
      const payload = await getDecisionReport(processId, packageId);
      setDetail(payload);
      setPreview(
        payload.status.startsWith("COMPLETED")
          ? await getDecisionReportPreview(processId, packageId)
          : null,
      );
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError ? loadError.message : "Error consultando paquete.",
      );
    }
  }

  async function retry(packageId: string) {
    setError(null);
    try {
      await retryDecisionReport(processId, packageId);
      await reload();
    } catch (retryError) {
      setError(retryError instanceof ApiClientError ? retryError.message : "Error reintentando.");
    }
  }

  const completedDecisions = (decisions?.items ?? []).filter((run) =>
    run.status.startsWith("COMPLETED"),
  );
  const packageItems = packages?.items ?? [];

  return (
    <section aria-labelledby="decision-report">
      <div className="section-heading">
        <h2 id="decision-report">Reporte ejecutivo</h2>
        <button type="button" className="button secondary" onClick={() => void reload()}>
          Actualizar
        </button>
      </div>
      <aside className="notice" role="note" aria-label="Avisos de reporte ejecutivo">
        <p>
          Este reporte no constituye concepto juridico ni recomendacion oficial de participacion.
        </p>
        <p>
          El paquete resume una decision preliminar existente; no recalcula evaluaciones ni modifica
          el resultado del motor.
        </p>
        <p>Los artefactos deben revisarse antes de cualquier uso externo.</p>
      </aside>
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : null}
      <form
        className="toolbar"
        onSubmit={(event) => {
          event.preventDefault();
          void create(false);
        }}
      >
        <label>
          Decision completada
          <select value={decisionRunId} onChange={(event) => setDecisionRunId(event.target.value)}>
            <option value="">Seleccione</option>
            {completedDecisions.map((run) => (
              <option key={run.id} value={run.id}>
                {run.effective_outcome ?? run.status} - {run.id.slice(0, 8)}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={!decisionRunId || submitting}>
          {submitting ? "Encolando..." : "Crear paquete"}
        </button>
        <button
          type="button"
          className="button secondary"
          onClick={() => void create(true)}
          disabled={!decisionRunId || submitting}
        >
          Crear nueva version
        </button>
      </form>

      <h3>Paquetes</h3>
      {packageItems.length === 0 ? <p>No hay paquetes de decision.</p> : null}
      {packageItems.map((item) => (
        <article className="document-row" key={item.id}>
          <div>
            <strong>{item.status}</strong>
            <p>
              Template v{item.template_version} - Artefactos: {item.artifact_count} - Warnings:{" "}
              {item.warning_count}
            </p>
            <p title={item.input_digest}>Input digest: {item.input_digest.slice(0, 12)}...</p>
            {item.package_digest ? (
              <p title={item.package_digest}>
                Package digest: {item.package_digest.slice(0, 12)}...
              </p>
            ) : null}
            {item.error_message ? <p className="error">{item.error_message}</p> : null}
          </div>
          <div className="document-actions">
            <button type="button" onClick={() => void openPackage(item.id)}>
              Ver paquete
            </button>
            {item.status.startsWith("COMPLETED") ? (
              <a
                className="button secondary"
                href={decisionReportZipDownloadUrl(processId, item.id)}
              >
                Descargar ZIP
              </a>
            ) : null}
            {item.status === "FAILED" ? (
              <button type="button" onClick={() => void retry(item.id)}>
                Reintentar
              </button>
            ) : null}
          </div>
        </article>
      ))}

      {detail ? (
        <div className="decision-detail">
          <h3>Artefactos</h3>
          <ul>
            {(detail.artifacts ?? []).map((artifact) => (
              <li key={artifact.id}>
                {artifact.filename} - {artifact.artifact_type} - {artifact.sha256.slice(0, 12)}...{" "}
                <a href={decisionReportArtifactDownloadUrl(processId, detail.id, artifact.id)}>
                  Descargar
                </a>
              </li>
            ))}
          </ul>
          <h3>Preview Markdown</h3>
          {preview ? (
            <pre>{preview.text}</pre>
          ) : (
            <p>Preview disponible cuando el paquete completa.</p>
          )}
        </div>
      ) : null}
    </section>
  );
}
