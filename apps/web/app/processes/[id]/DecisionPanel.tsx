"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  CompanyProfileList,
  CompanyProfileSnapshotSummary,
  DecisionReadiness,
  DecisionRunDetail,
  DecisionRunList,
  FinancialEvaluationList,
  NormalizationRunList,
} from "@pliegocheck/schemas";
import {
  ApiClientError,
  createDecision,
  getDecision,
  getDecisionReadiness,
  listCompanies,
  listDecisions,
  listFinancialEvaluations,
  listRequirementNormalizations,
  listSnapshots,
  retryDecision,
  reviewDecision,
  updateDecisionAction,
} from "../../../lib/api";

const REASON_MESSAGES: Record<string, string> = {
  FULL_MANDATORY_COVERAGE: "Cobertura obligatoria completa.",
  MANDATORY_REQUIREMENT_NOT_EVALUATED: "Hay requisitos obligatorios sin evaluar.",
  MANDATORY_REQUIREMENT_UNKNOWN: "Hay requisitos obligatorios con resultado desconocido.",
  MANDATORY_REQUIREMENT_PARTIAL: "Hay requisitos obligatorios con cumplimiento parcial.",
  MANDATORY_REQUIREMENT_UNRESOLVED: "Hay requisitos obligatorios sin resolucion verificable.",
  BLOCKING_REQUIREMENT_FAILED: "Un requisito bloqueante confirmado no se cumple.",
  NON_SUBSANABLE_REQUIREMENT_FAILED: "Un requisito obligatorio no subsanable no se cumple.",
  CRITICAL_EVIDENCE_CONFLICT: "Existe evidencia contradictoria en requisitos obligatorios.",
  PARTNER_SOLVABLE_GAP_CONFIRMED: "Existe una brecha marcada como resoluble mediante aliado.",
  REMEDIABLE_CONDITION_PENDING: "Existen condiciones de remediacion pendientes.",
  SUBMISSION_BLOCKER_CONFIRMED: "Existe un bloqueo operativo explicito para presentar la oferta.",
  ALL_MANDATORY_REQUIREMENTS_COMPLY: "Todos los requisitos obligatorios evaluados cumplen.",
  HUMAN_REVIEW_PENDING: "Hay revision humana pendiente.",
  ADAPTER_NOT_AVAILABLE: "Falta un evaluador especializado para una dimension requerida.",
};

const OUTCOME_LABELS: Record<string, string> = {
  GO: "GO",
  GO_CONDICIONADO: "GO condicionado",
  BUSCAR_ALIADO: "Buscar aliado",
  NO_GO: "NO GO",
  NO_CARGAR: "No cargar",
  PENDIENTE_INFORMACION: "Pendiente de informacion",
};

export function DecisionPanel({ processId }: { processId: string }) {
  const [normalizations, setNormalizations] = useState<NormalizationRunList | null>(null);
  const [financialEvaluations, setFinancialEvaluations] = useState<FinancialEvaluationList | null>(
    null,
  );
  const [companies, setCompanies] = useState<CompanyProfileList | null>(null);
  const [snapshots, setSnapshots] = useState<CompanyProfileSnapshotSummary[]>([]);
  const [decisions, setDecisions] = useState<DecisionRunList | null>(null);
  const [detail, setDetail] = useState<DecisionRunDetail | null>(null);
  const [readiness, setReadiness] = useState<DecisionReadiness | null>(null);
  const [normalizationRunId, setNormalizationRunId] = useState("");
  const [companyId, setCompanyId] = useState("");
  const [snapshotId, setSnapshotId] = useState("");
  const [financialRunId, setFinancialRunId] = useState("");
  const [reviewOutcome, setReviewOutcome] = useState("");
  const [reviewReason, setReviewReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const readinessAvailableAdapters = readiness?.available_adapters ?? [];
  const readinessInputErrors = readiness?.input_errors ?? [];
  const readinessCategories = readiness?.required_categories ?? [];
  const detailReasonCodes = detail?.reason_codes ?? [];
  const detailWarnings = detail?.warnings ?? [];
  const detailRules = detail?.rule_evaluations ?? [];
  const detailFindings = detail?.findings ?? [];
  const detailActions = detail?.actions ?? [];
  const detailReviews = detail?.reviews ?? [];
  const decisionItems = decisions?.items ?? [];

  const reload = useCallback(async () => {
    try {
      setDecisions(await listDecisions(processId, { limit: 20 }));
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError ? loadError.message : "Error consultando decisiones.",
      );
    }
  }, [processId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function prepareSelectors() {
    setError(null);
    try {
      setNormalizations(await listRequirementNormalizations(processId));
      setFinancialEvaluations(await listFinancialEvaluations(processId));
      setCompanies(await listCompanies({ limit: 100, offset: 0 }));
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError ? loadError.message : "Error consultando insumos.",
      );
    }
  }

  async function chooseCompany(nextCompanyId: string) {
    setCompanyId(nextCompanyId);
    setSnapshotId("");
    setSnapshots([]);
    if (!nextCompanyId) return;
    try {
      const payload = await listSnapshots(nextCompanyId);
      setSnapshots(payload.filter((snapshot) => snapshot.status === "PUBLISHED"));
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError ? loadError.message : "Error consultando snapshots.",
      );
    }
  }

  async function checkReadiness() {
    if (!normalizationRunId || !snapshotId || !financialRunId) return;
    setError(null);
    try {
      setReadiness(
        await getDecisionReadiness(processId, {
          normalization_run_id: normalizationRunId,
          company_profile_snapshot_id: snapshotId,
          financial_evaluation_run_id: financialRunId,
        }),
      );
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError ? loadError.message : "Error consultando readiness.",
      );
    }
  }

  async function submitDecision(force = false) {
    if (!normalizationRunId || !companyId || !snapshotId || !financialRunId || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await createDecision(processId, {
        normalization_run_id: normalizationRunId,
        company_id: companyId,
        company_profile_snapshot_id: snapshotId,
        financial_evaluation_run_id: financialRunId,
        force,
      });
      await reload();
    } catch (createError) {
      setError(
        createError instanceof ApiClientError ? createError.message : "Error creando decision.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function openDetail(decisionRunId: string) {
    setError(null);
    try {
      setDetail(await getDecision(processId, decisionRunId));
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError ? loadError.message : "Error consultando decision.",
      );
    }
  }

  async function retry(decisionRunId: string) {
    setError(null);
    try {
      await retryDecision(processId, decisionRunId);
      await reload();
    } catch (retryError) {
      setError(
        retryError instanceof ApiClientError ? retryError.message : "Error reintentando decision.",
      );
    }
  }

  async function submitReview(action: "CONFIRM" | "OVERRIDE" | "REJECT") {
    if (!detail) return;
    setError(null);
    try {
      await reviewDecision(processId, detail.id, {
        action,
        reviewed_outcome:
          action === "OVERRIDE" ? (reviewOutcome as DecisionRunDetail["engine_outcome"]) : null,
        reason: reviewReason || null,
      });
      await openDetail(detail.id);
      await reload();
    } catch (reviewError) {
      setError(
        reviewError instanceof ApiClientError
          ? reviewError.message
          : "Error registrando la revision.",
      );
    }
  }

  async function updateAction(actionId: string, status: "ACKNOWLEDGED" | "RESOLVED" | "DISMISSED") {
    if (!detail) return;
    try {
      await updateDecisionAction(processId, detail.id, actionId, status);
      await openDetail(detail.id);
    } catch (actionError) {
      setError(
        actionError instanceof ApiClientError
          ? actionError.message
          : "Error actualizando la accion.",
      );
    }
  }

  return (
    <section aria-labelledby="decision-preliminar">
      <div className="section-heading">
        <h2 id="decision-preliminar">Decisión preliminar</h2>
        <button type="button" className="button secondary" onClick={() => void prepareSelectors()}>
          Preparar insumos
        </button>
      </div>
      <aside className="notice" role="note" aria-label="Avisos de decision">
        <p>
          Esta es una decisión preliminar generada por reglas determinísticas y requiere revisión
          humana.
        </p>
        <p>La ausencia de evaluación en una dimensión nunca se interpreta como cumplimiento.</p>
        <p>
          Los adaptadores disponibles son financiero, jurídico, experiencia y técnico cuando sus
          evaluaciones determinísticas ya fueron completadas.
        </p>
        <p>
          El resultado no constituye un concepto jurídico ni garantiza habilitación o adjudicación.
        </p>
      </aside>

      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : null}

      {normalizations ? (
        <form
          className="toolbar"
          onSubmit={(event) => {
            event.preventDefault();
            void submitDecision(false);
          }}
        >
          <label>
            Normalización
            <select
              value={normalizationRunId}
              onChange={(event) => setNormalizationRunId(event.target.value)}
            >
              <option value="">Seleccione</option>
              {normalizations.items
                .filter((run) => run.status.startsWith("COMPLETED"))
                .map((run) => (
                  <option key={run.id} value={run.id}>
                    {run.id.slice(0, 8)} · {run.status}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Empresa
            <select value={companyId} onChange={(event) => void chooseCompany(event.target.value)}>
              <option value="">Seleccione</option>
              {(companies?.items ?? []).map((company) => (
                <option key={company.id} value={company.id}>
                  {company.legal_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Snapshot publicado
            <select value={snapshotId} onChange={(event) => setSnapshotId(event.target.value)}>
              <option value="">Seleccione</option>
              {snapshots.map((snapshot) => (
                <option key={snapshot.id} value={snapshot.id}>
                  v{snapshot.version} · {snapshot.digest.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Evaluación financiera
            <select
              value={financialRunId}
              onChange={(event) => setFinancialRunId(event.target.value)}
            >
              <option value="">Seleccione</option>
              {(financialEvaluations?.items ?? [])
                .filter((run) => run.status.startsWith("COMPLETED"))
                .map((run) => (
                  <option key={run.id} value={run.id}>
                    {run.id.slice(0, 8)} · {run.status}
                  </option>
                ))}
            </select>
          </label>
          <button
            type="button"
            className="button secondary"
            onClick={() => void checkReadiness()}
            disabled={!normalizationRunId || !snapshotId || !financialRunId}
          >
            Verificar readiness
          </button>
          <button
            type="submit"
            disabled={
              submitting || !normalizationRunId || !companyId || !snapshotId || !financialRunId
            }
          >
            {submitting ? "Encolando..." : "Ejecutar decisión"}
          </button>
        </form>
      ) : (
        <p>
          Use &quot;Preparar insumos&quot; para seleccionar normalización, empresa y evaluación.
        </p>
      )}

      {readiness ? (
        <div className="readiness" data-testid="decision-readiness">
          <p>
            Inputs válidos: {readiness.inputs_valid ? "sí" : "no"}. Adaptadores disponibles:{" "}
            {readinessAvailableAdapters.join(", ")}. Requisitos obligatorios sin evaluador:{" "}
            {readiness.not_evaluated_mandatory_count}.
          </p>
          <p>
            Resultado máximo posible:{" "}
            <strong>{OUTCOME_LABELS[readiness.max_possible_outcome]}</strong>
            {readiness.go_blocked_by_coverage
              ? " — GO está bloqueado por cobertura incompleta."
              : ""}
          </p>
          {readinessInputErrors.length > 0 ? (
            <ul>
              {readinessInputErrors.map((code) => (
                <li key={code} className="error">
                  {code}
                </li>
              ))}
            </ul>
          ) : null}
          <ul>
            {readinessCategories.map((category) => (
              <li key={category.category}>
                {category.category}: {category.requirements_total} requisitos (
                {category.mandatory_total} obligatorios) ·{" "}
                {category.adapter_available ? "adaptador disponible" : "sin adaptador"}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <h3>Histórico de decisiones</h3>
      {decisions && decisionItems.length === 0 ? <p>No hay decisiones ejecutadas.</p> : null}
      {decisionItems.map((run) => (
        <article className="document-row" key={run.id}>
          <div>
            <strong>
              {run.effective_outcome ? OUTCOME_LABELS[run.effective_outcome] : run.status}
            </strong>
            <p>
              Estado: {run.status} · Política: {run.policy_name} v{run.policy_version} · Motor v
              {run.engine_version}
            </p>
            <p title={run.input_digest}>
              Digest: {run.input_digest.slice(0, 12)}... · Hallazgos: {run.finding_count} ·
              Acciones: {run.action_count}
            </p>
            {run.reviewed_outcome && run.engine_outcome !== run.reviewed_outcome ? (
              <p>
                Motor: {OUTCOME_LABELS[run.engine_outcome ?? ""]} → Revisado:{" "}
                {OUTCOME_LABELS[run.reviewed_outcome]}
              </p>
            ) : null}
          </div>
          <div className="document-actions">
            <button type="button" onClick={() => void openDetail(run.id)}>
              Ver detalle
            </button>
            {run.status === "FAILED" ? (
              <button type="button" onClick={() => void retry(run.id)}>
                Reintentar
              </button>
            ) : null}
          </div>
        </article>
      ))}

      {detail ? (
        <div className="decision-detail" data-testid="decision-detail">
          <h3>
            Resultado del motor:{" "}
            {detail.engine_outcome ? OUTCOME_LABELS[detail.engine_outcome] : detail.status}
          </h3>
          {detail.requires_human_review ? (
            <p className="warning">Requiere revisión humana antes de considerarse definitiva.</p>
          ) : null}
          <ul aria-label="Razones">
            {detailReasonCodes.map((code) => (
              <li key={code}>{REASON_MESSAGES[code] ?? code}</li>
            ))}
          </ul>
          {detail.coverage ? (
            <p>
              Cobertura: {detail.coverage.evaluated_total} evaluados de{" "}
              {detail.coverage.requirements_total} requisitos ({detail.coverage.not_evaluated_total}{" "}
              sin evaluar, {detail.coverage.mandatory_applicable_total} obligatorios aplicables).
            </p>
          ) : null}
          {detailWarnings.length > 0 ? (
            <ul aria-label="Advertencias">
              {detailWarnings.map((warning) => (
                <li key={warning} className="warning">
                  {warning.startsWith("ADAPTER_NOT_AVAILABLE")
                    ? `Sin evaluador especializado: ${warning.split(":")[1] ?? ""}`
                    : warning}
                </li>
              ))}
            </ul>
          ) : null}
          <h4>Reglas evaluadas</h4>
          <table>
            <thead>
              <tr>
                <th>Regla</th>
                <th>Estado</th>
                <th>Resultado sugerido</th>
                <th>Requisitos</th>
              </tr>
            </thead>
            <tbody>
              {detailRules.map((rule) => (
                <tr key={rule.rule_code}>
                  <td>{rule.rule_code}</td>
                  <td>{rule.status}</td>
                  <td>{rule.suggested_outcome ?? "—"}</td>
                  <td>{(rule.requirement_ids ?? []).length}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h4>Hallazgos</h4>
          <table>
            <thead>
              <tr>
                <th>Categoría</th>
                <th>Resultado</th>
                <th>Aplicabilidad</th>
                <th>Origen</th>
                <th>Evidencia</th>
              </tr>
            </thead>
            <tbody>
              {detailFindings.map((finding) => (
                <tr key={finding.id}>
                  <td>{finding.category}</td>
                  <td>{finding.outcome}</td>
                  <td>{finding.applicability}</td>
                  <td>{finding.source_type}</td>
                  <td>{(finding.evidence_references ?? []).length} referencias</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h4>Acciones requeridas</h4>
          {detailActions.length === 0 ? <p>Sin acciones pendientes.</p> : null}
          <ul>
            {detailActions.map((action) => (
              <li key={action.id}>
                <strong>{action.action_type}</strong> · {action.priority} · {action.status}
                {action.status === "OPEN" || action.status === "ACKNOWLEDGED" ? (
                  <span>
                    {" "}
                    <button
                      type="button"
                      onClick={() => void updateAction(action.id, "ACKNOWLEDGED")}
                    >
                      Reconocer
                    </button>{" "}
                    <button type="button" onClick={() => void updateAction(action.id, "RESOLVED")}>
                      Resolver
                    </button>
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
          <h4>Revisión</h4>
          {detailReviews.length > 0 ? (
            <ul>
              {detailReviews.map((review) => (
                <li key={review.id}>
                  {review.action}: {OUTCOME_LABELS[review.original_outcome]}
                  {review.reviewed_outcome ? ` → ${OUTCOME_LABELS[review.reviewed_outcome]}` : ""} (
                  {review.reason ?? "sin razón"})
                </li>
              ))}
            </ul>
          ) : null}
          <form
            className="toolbar"
            onSubmit={(event) => {
              event.preventDefault();
              void submitReview("OVERRIDE");
            }}
          >
            <label>
              Nuevo resultado
              <select
                value={reviewOutcome}
                onChange={(event) => setReviewOutcome(event.target.value)}
              >
                <option value="">Seleccione</option>
                {Object.entries(OUTCOME_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Razón
              <input
                value={reviewReason}
                onChange={(event) => setReviewReason(event.target.value)}
              />
            </label>
            <button type="submit" disabled={!reviewOutcome || !reviewReason.trim()}>
              Override
            </button>
            <button type="button" onClick={() => void submitReview("CONFIRM")}>
              Confirmar
            </button>
            <button
              type="button"
              onClick={() => void submitReview("REJECT")}
              disabled={!reviewReason.trim()}
            >
              Rechazar
            </button>
          </form>
        </div>
      ) : null}
    </section>
  );
}
