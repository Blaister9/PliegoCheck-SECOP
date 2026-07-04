"use client";

import { useState } from "react";
import type {
  CompanyProfileList,
  CompanyProfileSnapshotSummary,
  NormalizationRunList,
  SpecializedEvaluationDomain,
  SpecializedEvaluationList,
  SpecializedEvaluationReadiness,
  SpecializedEvaluationResultList,
} from "@pliegocheck/schemas";
import {
  ApiClientError,
  createSpecializedEvaluation,
  getSpecializedEvaluationReadiness,
  listSpecializedEvaluationResults,
  listSpecializedEvaluations,
  retrySpecializedEvaluation,
  reviewSpecializedEvaluationResult,
} from "../../../lib/api";

const SPECIALIZED_DOMAINS: SpecializedEvaluationDomain[] = ["LEGAL", "EXPERIENCE", "TECHNICAL"];

export function SpecializedEvaluationPanel({
  processId,
  normalizations,
  companies,
  snapshots,
  selectedNormalizationRunId,
  selectedCompanyId,
  selectedSnapshotId,
  onSelectNormalization,
  onSelectCompany,
  onSelectSnapshot,
  onLoadCompanies,
}: {
  processId: string;
  normalizations: NormalizationRunList | null;
  companies: CompanyProfileList | null;
  snapshots: CompanyProfileSnapshotSummary[];
  selectedNormalizationRunId: string;
  selectedCompanyId: string;
  selectedSnapshotId: string;
  onSelectNormalization: (runId: string) => void;
  onSelectCompany: (companyId: string) => void;
  onSelectSnapshot: (snapshotId: string) => void;
  onLoadCompanies: () => void;
}) {
  const [domain, setDomain] = useState<SpecializedEvaluationDomain>("LEGAL");
  const [evaluations, setEvaluations] = useState<SpecializedEvaluationList | null>(null);
  const [results, setResults] = useState<SpecializedEvaluationResultList | null>(null);
  const [readiness, setReadiness] = useState<SpecializedEvaluationReadiness | null>(null);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [reviewingResultId, setReviewingResultId] = useState("");
  const [reviewReason, setReviewReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const completedNormalizations = (normalizations?.items ?? []).filter((run) =>
    ["COMPLETED", "COMPLETED_WITH_WARNINGS"].includes(run.status),
  );
  const canCreate =
    Boolean(selectedNormalizationRunId) &&
    Boolean(selectedCompanyId) &&
    Boolean(selectedSnapshotId);

  async function refresh() {
    setError(null);
    try {
      setEvaluations(await listSpecializedEvaluations(processId, { domain, limit: 20 }));
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError
          ? loadError.message
          : "Error consultando evaluaciones especializadas.",
      );
    }
  }

  async function checkReadiness() {
    if (!selectedNormalizationRunId || !selectedSnapshotId) return;
    setError(null);
    try {
      setReadiness(
        await getSpecializedEvaluationReadiness(processId, {
          normalization_run_id: selectedNormalizationRunId,
          company_profile_snapshot_id: selectedSnapshotId,
          domain,
        }),
      );
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError
          ? loadError.message
          : "Error consultando readiness especializada.",
      );
    }
  }

  async function createEvaluation(force = false) {
    if (!canCreate || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await createSpecializedEvaluation(processId, {
        normalization_run_id: selectedNormalizationRunId,
        company_id: selectedCompanyId,
        company_profile_snapshot_id: selectedSnapshotId,
        domain,
        force,
      });
      await refresh();
    } catch (createError) {
      setError(
        createError instanceof ApiClientError
          ? createError.message
          : "Error creando evaluacion especializada.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function retry(runId: string) {
    setError(null);
    try {
      await retrySpecializedEvaluation(processId, runId);
      await refresh();
    } catch (retryError) {
      setError(
        retryError instanceof ApiClientError
          ? retryError.message
          : "Error reintentando evaluacion especializada.",
      );
    }
  }

  async function openResults(runId: string) {
    setSelectedRunId(runId);
    setError(null);
    try {
      setResults(await listSpecializedEvaluationResults(processId, runId));
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError
          ? loadError.message
          : "Error consultando resultados especializados.",
      );
    }
  }

  async function confirmResult(resultId: string) {
    if (!selectedRunId) return;
    setReviewingResultId(resultId);
    setError(null);
    try {
      await reviewSpecializedEvaluationResult(processId, selectedRunId, resultId, {
        review_status: "CONFIRMED",
        override_result: null,
        review_notes: reviewReason || "Revision humana confirmada desde la aplicacion web.",
      });
      setReviewReason("");
      await openResults(selectedRunId);
    } catch (reviewError) {
      setError(
        reviewError instanceof ApiClientError
          ? reviewError.message
          : "Error registrando revision especializada.",
      );
    } finally {
      setReviewingResultId("");
    }
  }

  return (
    <section aria-labelledby="specialized-evaluations">
      <div className="section-heading">
        <h2 id="specialized-evaluations">Evaluadores especializados</h2>
        <button type="button" className="button secondary" onClick={onLoadCompanies}>
          Cargar empresas
        </button>
      </div>
      <aside className="notice" role="note" aria-label="Avisos de evaluadores especializados">
        <p>Estas evaluaciones son determinísticas y no constituyen concepto jurídico definitivo.</p>
        <p>La ausencia de información o evidencia nunca se interpreta como cumplimiento.</p>
        <p>
          Los resultados especializados alimentan el motor de decisión, pero no producen por sí
          solos GO / NO GO.
        </p>
      </aside>
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : null}
      <div className="form-grid">
        <label>
          Dominio
          <select
            value={domain}
            onChange={(event) => {
              setDomain(event.target.value as SpecializedEvaluationDomain);
              setEvaluations(null);
              setResults(null);
              setReadiness(null);
            }}
          >
            {SPECIALIZED_DOMAINS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Normalizacion
          <select
            value={selectedNormalizationRunId}
            onChange={(event) => onSelectNormalization(event.target.value)}
          >
            <option value="">Seleccionar ejecucion</option>
            {completedNormalizations.map((run) => (
              <option key={run.id} value={run.id}>
                {run.id.slice(0, 8)} - {run.status}
              </option>
            ))}
          </select>
        </label>
        <label>
          Empresa
          <select
            value={selectedCompanyId}
            onChange={(event) => onSelectCompany(event.target.value)}
          >
            <option value="">Seleccionar empresa</option>
            {(companies?.items ?? []).map((company) => (
              <option key={company.id} value={company.id}>
                {company.legal_name} - {company.internal_reference}
              </option>
            ))}
          </select>
        </label>
        <label>
          Snapshot publicado
          <select
            value={selectedSnapshotId}
            onChange={(event) => onSelectSnapshot(event.target.value)}
            disabled={!selectedCompanyId}
          >
            <option value="">Seleccionar snapshot</option>
            {snapshots.map((snapshot) => (
              <option key={snapshot.id} value={snapshot.id}>
                v{snapshot.version} - {snapshot.completeness_status}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="document-actions">
        <button type="button" onClick={() => void checkReadiness()} disabled={!canCreate}>
          Ver readiness
        </button>
        <button type="button" onClick={() => void createEvaluation(false)} disabled={!canCreate}>
          {submitting ? "Encolando..." : "Crear evaluacion"}
        </button>
        <button
          type="button"
          className="button secondary"
          onClick={() => void createEvaluation(true)}
          disabled={!canCreate}
        >
          Forzar nueva evaluacion
        </button>
        <button type="button" className="button secondary" onClick={() => void refresh()}>
          Actualizar
        </button>
      </div>
      {readiness ? (
        <article className="run-summary">
          <strong>
            Readiness:{" "}
            {readiness.evaluable_count > 0 && readiness.unsupported_count === 0
              ? "READY"
              : "NO READY"}
          </strong>
          <p>
            Dominio: {readiness.domain}. Reglas evaluables: {readiness.evaluable_count}/
            {readiness.requirement_count}. Ambiguas: {readiness.ambiguous_count}. No soportadas:{" "}
            {readiness.unsupported_count}.
          </p>
          {(readiness.warnings ?? []).length > 0 ? (
            <ul>
              {(readiness.warnings ?? []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </article>
      ) : null}
      <SpecializedRunTable
        evaluations={evaluations}
        onRetry={(runId) => void retry(runId)}
        onResults={(runId) => void openResults(runId)}
      />
      <SpecializedResultTable
        results={results}
        reviewingResultId={reviewingResultId}
        reviewReason={reviewReason}
        onReviewReason={setReviewReason}
        onConfirm={(resultId) => void confirmResult(resultId)}
      />
    </section>
  );
}

function SpecializedRunTable({
  evaluations,
  onRetry,
  onResults,
}: {
  evaluations: SpecializedEvaluationList | null;
  onRetry: (runId: string) => void;
  onResults: (runId: string) => void;
}) {
  const runs = evaluations?.items ?? [];
  if (!evaluations) {
    return <p className="empty-state">Use Actualizar para consultar ejecuciones especializadas.</p>;
  }
  if (runs.length === 0) {
    return <p className="empty-state">No hay evaluaciones especializadas para este dominio.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Dominio</th>
            <th>Estado</th>
            <th>Resultados</th>
            <th>Snapshot</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id}>
              <td>{run.domain}</td>
              <td>{run.status}</td>
              <td>
                {run.complies_count} cumple, {run.does_not_comply_count} no cumple,{" "}
                {run.unknown_count} UNKNOWN, {run.conflicting_count} conflictos
              </td>
              <td>{run.company_profile_snapshot_id.slice(0, 8)}</td>
              <td>
                <div className="document-actions">
                  <button type="button" onClick={() => onResults(run.id)}>
                    Ver resultados
                  </button>
                  {run.status === "FAILED" ? (
                    <button type="button" onClick={() => onRetry(run.id)}>
                      Reintentar
                    </button>
                  ) : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SpecializedResultTable({
  results,
  reviewingResultId,
  reviewReason,
  onReviewReason,
  onConfirm,
}: {
  results: SpecializedEvaluationResultList | null;
  reviewingResultId: string;
  reviewReason: string;
  onReviewReason: (reason: string) => void;
  onConfirm: (resultId: string) => void;
}) {
  const items = results?.items ?? [];
  if (!results) return null;
  if (items.length === 0) {
    return <p className="empty-state">La ejecucion seleccionada no tiene resultados.</p>;
  }
  return (
    <>
      <div className="toolbar">
        <label>
          Motivo de revision
          <input value={reviewReason} onChange={(event) => onReviewReason(event.target.value)} />
        </label>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Resultado</th>
              <th>Regla</th>
              <th>Valor requerido</th>
              <th>Valor observado</th>
              <th>Evidencia</th>
              <th>Revision</th>
            </tr>
          </thead>
          <tbody>
            {items.map((result) => (
              <tr key={result.id}>
                <td>{result.status}</td>
                <td>
                  {result.rule_type ?? "UNKNOWN"} - {result.explanation_code}
                </td>
                <td>
                  {result.operator ?? "-"} {result.expected_value ?? "-"} {result.unit ?? ""}
                </td>
                <td>
                  {result.actual_value ?? "UNKNOWN"} {result.unit ?? ""}
                </td>
                <td>{result.requires_human_review ? "Requiere revision" : "Sin alerta"}</td>
                <td>
                  {result.review_status}
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() => onConfirm(result.id)}
                    disabled={reviewingResultId === result.id}
                  >
                    Confirmar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
