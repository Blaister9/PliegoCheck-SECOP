"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import type {
  CompanyProfileList,
  CompanyProfileSnapshotSummary,
  DocumentUploadResponse,
  ExtractedSegmentList,
  ExtractedSegmentType,
  FinancialEvaluationList,
  FinancialEvaluationResultList,
  NormalizationRunList,
  NormalizedRequirement,
  ProcessDetail,
  ProcessInventory,
  RequirementDetail,
  RequirementList,
} from "@pliegocheck/schemas";
import { EXTRACTED_SEGMENT_TYPE_VALUES } from "@pliegocheck/schemas";
import { DecisionPanel } from "./DecisionPanel";
import { DecisionReportPanel } from "./DecisionReportPanel";
import { ExternalLinksPanel } from "./ExternalLinksPanel";
import { SpecializedEvaluationPanel } from "./SpecializedEvaluationPanel";
import {
  ApiClientError,
  createFinancialEvaluation,
  createRequirementNormalization,
  downloadUrl,
  enqueueDocumentExtraction,
  enqueueProcessExtractions,
  getExtractionSegments,
  getInventory,
  getProcess,
  getRequirement,
  listCompanies,
  listFinancialEvaluationResults,
  listFinancialEvaluations,
  listRequirementNormalizations,
  listRequirements,
  listSnapshots,
  retryFinancialEvaluation,
  retryRequirementNormalization,
  uploadDocuments,
} from "../../../lib/api";

export function ProcessDetailClient({ processId }: { processId: string }) {
  const [process, setProcess] = useState<ProcessDetail | null>(null);
  const [inventory, setInventory] = useState<ProcessInventory | null>(null);
  const [normalizations, setNormalizations] = useState<NormalizationRunList | null>(null);
  const [requirements, setRequirements] = useState<RequirementList | null>(null);
  const [financialEvaluations, setFinancialEvaluations] = useState<FinancialEvaluationList | null>(
    null,
  );
  const [financialResults, setFinancialResults] = useState<FinancialEvaluationResultList | null>(
    null,
  );
  const [companies, setCompanies] = useState<CompanyProfileList | null>(null);
  const [snapshots, setSnapshots] = useState<CompanyProfileSnapshotSummary[]>([]);
  const [selectedFinancialRunId, setSelectedFinancialRunId] = useState("");
  const [selectedCompanyId, setSelectedCompanyId] = useState("");
  const [selectedSnapshotId, setSelectedSnapshotId] = useState("");
  const [selectedRequirement, setSelectedRequirement] = useState<RequirementDetail | null>(null);
  const [segments, setSegments] = useState<ExtractedSegmentList | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  const [segmentType, setSegmentType] = useState<ExtractedSegmentType | "">("");
  const [pageNumber, setPageNumber] = useState("");
  const [sheetName, setSheetName] = useState("");
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [normalizing, setNormalizing] = useState(false);
  const [financialSubmitting, setFinancialSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [processPayload, inventoryPayload] = await Promise.all([
        getProcess(processId),
        getInventory(processId),
      ]);
      const normalizationsPayload = await listRequirementNormalizations(processId).catch(
        () => null,
      );
      const latestRun = normalizationsPayload?.items[0];
      const requirementsPayload = await listRequirements(processId, latestRun?.id).catch(
        () => null,
      );
      const financialEvaluationsPayload = await listFinancialEvaluations(processId).catch(
        () => null,
      );
      const latestFinancialRun = financialEvaluationsPayload?.items[0];
      const financialResultsPayload = latestFinancialRun
        ? await listFinancialEvaluationResults(processId, latestFinancialRun.id).catch(() => null)
        : null;
      setProcess(processPayload);
      setInventory(inventoryPayload);
      setNormalizations(normalizationsPayload);
      setRequirements(requirementsPayload);
      setFinancialEvaluations(financialEvaluationsPayload);
      setFinancialResults(financialResultsPayload);
      setSelectedFinancialRunId((current) => current || latestRun?.id || "");
    } catch (loadError) {
      setError(loadError instanceof ApiClientError ? loadError.message : "Error consultando API.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [processId]);

  function chooseFiles(event: ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(event.target.files ?? []));
  }

  async function submitUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (files.length === 0) return;
    setUploading(true);
    setUploadResult(null);
    setError(null);
    try {
      setUploadResult(await uploadDocuments(processId, files));
      await load();
    } catch (uploadError) {
      setError(
        uploadError instanceof ApiClientError ? uploadError.message : "Error cargando archivos.",
      );
    } finally {
      setUploading(false);
    }
  }

  async function queueAll() {
    setError(null);
    try {
      await enqueueProcessExtractions(processId);
      await load();
    } catch (queueError) {
      setError(queueError instanceof ApiClientError ? queueError.message : "Error encolando.");
    }
  }

  async function retryDocument(documentId: string) {
    setError(null);
    try {
      await enqueueDocumentExtraction(processId, documentId, true);
      await load();
    } catch (queueError) {
      setError(queueError instanceof ApiClientError ? queueError.message : "Error reintentando.");
    }
  }

  async function loadSegments(documentId = selectedDocument, offset = 0) {
    if (!documentId) return;
    setError(null);
    setSelectedDocument(documentId);
    try {
      setSegments(
        await getExtractionSegments(processId, documentId, {
          offset,
          segment_type: segmentType,
          page_number: pageNumber,
          sheet_name: sheetName,
        }),
      );
    } catch (segmentError) {
      setSegments(null);
      setError(
        segmentError instanceof ApiClientError
          ? segmentError.message
          : "Error consultando segmentos.",
      );
    }
  }

  async function startNormalization(force = false) {
    setNormalizing(true);
    setError(null);
    try {
      await createRequirementNormalization(processId, { force, document_ids: null });
      await load();
    } catch (normalizationError) {
      setError(
        normalizationError instanceof ApiClientError
          ? normalizationError.message
          : "Error creando normalizacion.",
      );
    } finally {
      setNormalizing(false);
    }
  }

  async function retryRun(runId: string) {
    setError(null);
    try {
      await retryRequirementNormalization(processId, runId);
      await load();
    } catch (retryError) {
      setError(
        retryError instanceof ApiClientError
          ? retryError.message
          : "Error reintentando normalizacion.",
      );
    }
  }

  async function openRequirement(requirementId: string) {
    setError(null);
    try {
      setSelectedRequirement(await getRequirement(processId, requirementId));
    } catch (detailError) {
      setError(
        detailError instanceof ApiClientError
          ? detailError.message
          : "Error consultando requisito.",
      );
    }
  }

  async function loadCompaniesForFinancial() {
    setError(null);
    try {
      setCompanies(await listCompanies({ limit: 100, offset: 0 }));
    } catch (companyError) {
      setError(
        companyError instanceof ApiClientError
          ? companyError.message
          : "Error consultando empresas.",
      );
    }
  }

  async function chooseCompanyForFinancial(companyId: string) {
    setSelectedCompanyId(companyId);
    setSelectedSnapshotId("");
    setSnapshots([]);
    if (!companyId) return;
    setError(null);
    try {
      const snapshotPayload = await listSnapshots(companyId);
      setSnapshots(snapshotPayload.filter((snapshot) => snapshot.status === "PUBLISHED"));
    } catch (snapshotError) {
      setError(
        snapshotError instanceof ApiClientError
          ? snapshotError.message
          : "Error consultando snapshots.",
      );
    }
  }

  async function startFinancialEvaluation(force = false) {
    if (!selectedFinancialRunId || !selectedCompanyId || !selectedSnapshotId) return;
    setFinancialSubmitting(true);
    setError(null);
    try {
      await createFinancialEvaluation(processId, {
        normalization_run_id: selectedFinancialRunId,
        company_id: selectedCompanyId,
        company_profile_snapshot_id: selectedSnapshotId,
        force,
      });
      await load();
    } catch (financialError) {
      setError(
        financialError instanceof ApiClientError
          ? financialError.message
          : "Error creando evaluacion financiera.",
      );
    } finally {
      setFinancialSubmitting(false);
    }
  }

  async function retryFinancialRun(runId: string) {
    setError(null);
    try {
      await retryFinancialEvaluation(processId, runId);
      await load();
    } catch (retryError) {
      setError(
        retryError instanceof ApiClientError
          ? retryError.message
          : "Error reintentando evaluacion financiera.",
      );
    }
  }

  if (loading)
    return (
      <main className="container">
        <p>Cargando proceso...</p>
      </main>
    );
  if (error && !process)
    return (
      <main className="container">
        <p role="alert" className="error">
          {error}
        </p>
      </main>
    );
  if (!process) return null;

  return (
    <main className="container wide">
      <h1>{process.title}</h1>
      <p className="status-badge">{process.status}</p>
      <section className="metadata-grid">
        <p>
          <strong>Referencia interna:</strong> {process.internal_reference}
        </p>
        <p>
          <strong>SECOP:</strong> {process.secop_reference ?? "Sin referencia"}
        </p>
        <p>
          <strong>Entidad:</strong> {process.contracting_entity}
        </p>
        <p>
          <strong>Moneda:</strong> {process.currency ?? "No informada"}
        </p>
        <p>
          <strong>Valor estimado:</strong> {process.estimated_value ?? "No informado"}
        </p>
        <p>
          <strong>Cierre:</strong> {formatDate(process.closing_at)}
        </p>
      </section>

      {process.source === "SECOP_IMPORT" ? <ExternalLinksPanel processId={processId} /> : null}

      <aside className="notice" role="note">
        La extraccion es deterministica y todavia no evalua requisitos ni produce una decision GO /
        NO GO.
      </aside>

      <section>
        <div className="section-heading">
          <h2>Requisitos normalizados</h2>
          <button type="button" onClick={() => startNormalization(false)} disabled={normalizing}>
            {normalizing ? "Encolando..." : "Normalizar requisitos"}
          </button>
        </div>
        <aside className="notice" role="note" aria-label="Avisos de normalizacion">
          <p>Los requisitos fueron propuestos por un modelo de IA y requieren revision humana.</p>
          <p>
            La normalizacion no determina si una empresa cumple ni produce una decision GO / NO GO.
          </p>
          <p>
            El texto documental se trata como informacion no confiable, no como instrucciones para
            el sistema.
          </p>
        </aside>
        <NormalizationRuns
          normalizations={normalizations}
          inventory={inventory}
          onRetry={(runId) => void retryRun(runId)}
          onForce={() => void startNormalization(true)}
        />
        <RequirementTable
          requirements={requirements}
          onSelect={(requirementId) => void openRequirement(requirementId)}
        />
        {selectedRequirement ? <RequirementDetailPanel requirement={selectedRequirement} /> : null}
      </section>

      <section>
        <FinancialEvaluationPanel
          normalizations={normalizations}
          evaluations={financialEvaluations}
          results={financialResults}
          companies={companies}
          snapshots={snapshots}
          selectedNormalizationRunId={selectedFinancialRunId}
          selectedCompanyId={selectedCompanyId}
          selectedSnapshotId={selectedSnapshotId}
          submitting={financialSubmitting}
          onLoadCompanies={() => void loadCompaniesForFinancial()}
          onSelectNormalization={setSelectedFinancialRunId}
          onSelectCompany={(companyId) => void chooseCompanyForFinancial(companyId)}
          onSelectSnapshot={setSelectedSnapshotId}
          onCreate={() => void startFinancialEvaluation(false)}
          onForce={() => void startFinancialEvaluation(true)}
          onRetry={(runId) => void retryFinancialRun(runId)}
        />
      </section>

      <SpecializedEvaluationPanel
        processId={processId}
        normalizations={normalizations}
        companies={companies}
        snapshots={snapshots}
        selectedNormalizationRunId={selectedFinancialRunId}
        selectedCompanyId={selectedCompanyId}
        selectedSnapshotId={selectedSnapshotId}
        onLoadCompanies={() => void loadCompaniesForFinancial()}
        onSelectNormalization={setSelectedFinancialRunId}
        onSelectCompany={(companyId) => void chooseCompanyForFinancial(companyId)}
        onSelectSnapshot={setSelectedSnapshotId}
      />

      <DecisionPanel processId={processId} />

      <DecisionReportPanel processId={processId} />

      <section>
        <div className="section-heading">
          <h2>Inventario documental</h2>
          <button type="button" className="button secondary" onClick={queueAll}>
            Procesar pendientes
          </button>
        </div>
        {inventory?.documents.length === 0 ? <p>No hay documentos cargados.</p> : null}
        {(inventory?.documents ?? []).map((document) => (
          <article className="document-row" key={document.document_id}>
            <div>
              <strong>{document.original_filename}</strong>
              <p>
                {document.document_type} · {formatBytes(document.size_bytes)} · {document.extension}
              </p>
              <p>Estado: {document.processing_status}</p>
              <p>
                Formato: {document.detected_format ?? "Pendiente"} · Paginas:{" "}
                {document.page_count ?? "-"} · Hojas: {document.sheet_count ?? "-"} · Segmentos:{" "}
                {document.segment_count} · Caracteres: {document.character_count}
              </p>
              <p title={document.sha256}>SHA-256: {document.sha256.slice(0, 12)}...</p>
              {(document.warnings ?? []).length > 0 ? (
                <ul>
                  {(document.warnings ?? []).map((warning) => (
                    <li key={`${document.document_id}-${warning.code}`}>{warning.message}</li>
                  ))}
                </ul>
              ) : null}
              {document.needs_ocr ? (
                <p className="warning">
                  El documento no contiene texto digital suficiente. OCR no esta habilitado en esta
                  fase.
                </p>
              ) : null}
              {document.processing_status === "UNSUPPORTED" ? (
                <p className="warning">
                  El formato se conserva en el inventario, pero necesita conversion a un formato
                  compatible antes de extraer contenido.
                </p>
              ) : null}
              {document.latest_extraction?.error_message ? (
                <p className="error">{document.latest_extraction.error_message}</p>
              ) : null}
            </div>
            <div className="document-actions">
              <a className="button secondary" href={downloadUrl(process.id, document.document_id)}>
                Descargar
              </a>
              <button type="button" onClick={() => retryDocument(document.document_id)}>
                Reintentar
              </button>
              <button type="button" onClick={() => loadSegments(document.document_id)}>
                Ver segmentos
              </button>
            </div>
          </article>
        ))}
      </section>

      <section>
        <h2>Previsualizacion de texto</h2>
        <form
          className="toolbar"
          onSubmit={(event) => {
            event.preventDefault();
            void loadSegments();
          }}
        >
          <label>
            Tipo
            <select
              value={segmentType}
              onChange={(event) => setSegmentType(event.target.value as ExtractedSegmentType | "")}
            >
              <option value="">Todos</option>
              {EXTRACTED_SEGMENT_TYPE_VALUES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label>
            Pagina
            <input value={pageNumber} onChange={(event) => setPageNumber(event.target.value)} />
          </label>
          <label>
            Hoja
            <input value={sheetName} onChange={(event) => setSheetName(event.target.value)} />
          </label>
          <button type="submit" disabled={!selectedDocument}>
            Filtrar
          </button>
        </form>
        {segments ? (
          <SegmentPreview
            segments={segments}
            onPage={(offset) => void loadSegments(selectedDocument, offset)}
          />
        ) : (
          <p>Sin preview.</p>
        )}
      </section>

      <section>
        <h2>Cargar documentos</h2>
        <form className="upload-form" onSubmit={submitUpload}>
          <input
            aria-label="Documentos"
            type="file"
            multiple
            onChange={chooseFiles}
            accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg"
          />
          <button type="submit" disabled={uploading || files.length === 0}>
            {uploading ? "Cargando..." : "Cargar"}
          </button>
        </form>
        {error ? (
          <p role="alert" className="error">
            {error}
          </p>
        ) : null}
        {uploadResult ? (
          <div className="upload-results">
            <p>
              Almacenados: {uploadResult.stored_count}. Rechazados: {uploadResult.rejected_count}.
            </p>
            <ul>
              {uploadResult.results.map((result) => (
                <li key={result.original_filename}>
                  {result.original_filename}: {result.upload_status}
                  {result.error ? ` (${result.error.code})` : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>
    </main>
  );
}

function SegmentPreview({
  segments,
  onPage,
}: {
  segments: ExtractedSegmentList;
  onPage: (offset: number) => void;
}) {
  const canPrev = segments.offset > 0;
  const nextOffset = segments.offset + segments.limit;
  const canNext = nextOffset < segments.total;
  return (
    <div className="segment-preview">
      <p>
        Segmentos {segments.total === 0 ? 0 : segments.offset + 1}-
        {Math.min(nextOffset, segments.total)} de {segments.total}
      </p>
      {segments.segments.map((segment) => (
        <article key={segment.id} className="segment-row">
          <p>
            {segment.segment_type} · {locationLabel(segment)}
          </p>
          <pre>{segment.text}</pre>
        </article>
      ))}
      <div className="pagination">
        <button
          type="button"
          disabled={!canPrev}
          onClick={() => onPage(segments.offset - segments.limit)}
        >
          Anterior
        </button>
        <button type="button" disabled={!canNext} onClick={() => onPage(nextOffset)}>
          Siguiente
        </button>
      </div>
    </div>
  );
}

function NormalizationRuns({
  normalizations,
  inventory,
  onRetry,
  onForce,
}: {
  normalizations: NormalizationRunList | null;
  inventory: ProcessInventory | null;
  onRetry: (runId: string) => void;
  onForce: () => void;
}) {
  const eligible = (inventory?.documents ?? []).filter(
    (document) =>
      ["COMPLETED", "COMPLETED_WITH_WARNINGS"].includes(document.processing_status) &&
      document.segment_count > 0,
  );
  const omitted = (inventory?.documents ?? []).filter(
    (document) =>
      !["COMPLETED", "COMPLETED_WITH_WARNINGS"].includes(document.processing_status) ||
      document.segment_count === 0,
  );
  const latest = normalizations?.items[0];
  return (
    <div className="normalization-panel">
      <p>
        Documentos elegibles: {eligible.length}. Omitidos: {omitted.length}.
      </p>
      {omitted.length > 0 ? (
        <ul>
          {omitted.map((document) => (
            <li key={document.document_id}>
              {document.original_filename}: {document.processing_status}
            </li>
          ))}
        </ul>
      ) : null}
      {latest ? (
        <article className="run-summary">
          <strong>Ultima ejecucion: {latest.status}</strong>
          <p>
            Modelo: {latest.model} · Prompt: {latest.prompt_version_id} · Lotes:{" "}
            {latest.batch_count} · Segmentos: {latest.segment_count}
          </p>
          <p>
            Requisitos: {latest.accepted_requirement_count} · Rechazados:{" "}
            {latest.rejected_candidate_count} · Warnings: {latest.warning_count}
          </p>
          <p>
            Tokens: entrada {latest.input_tokens}, salida {latest.output_tokens}, razonamiento{" "}
            {latest.reasoning_tokens}
          </p>
          {latest.error_message ? <p className="error">{latest.error_message}</p> : null}
          <div className="document-actions">
            {latest.status === "FAILED" ? (
              <button type="button" onClick={() => onRetry(latest.id)}>
                Reintentar
              </button>
            ) : null}
            <button type="button" className="button secondary" onClick={onForce}>
              Nueva ejecucion forzada
            </button>
          </div>
        </article>
      ) : (
        <p className="empty-state">No hay normalizaciones creadas.</p>
      )}
    </div>
  );
}

function RequirementTable({
  requirements,
  onSelect,
}: {
  requirements: RequirementList | null;
  onSelect: (requirementId: string) => void;
}) {
  const items = requirements?.items ?? [];
  if (items.length === 0) {
    return <p className="empty-state">Sin requisitos normalizados para mostrar.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Categoria</th>
            <th>Descripcion</th>
            <th>Scope</th>
            <th>Modalidad</th>
            <th>Criticidad</th>
            <th>Subsanabilidad</th>
            <th>Revision</th>
          </tr>
        </thead>
        <tbody>
          {items.map((requirement) => (
            <tr key={requirement.id}>
              <td>{requirement.category}</td>
              <td>
                <button
                  type="button"
                  className="link-button"
                  onClick={() => onSelect(requirement.id)}
                >
                  {requirement.description}
                </button>
                <p>Valor esperado: {expectedValue(requirement)}</p>
              </td>
              <td>{requirement.scope}</td>
              <td>{requirement.modality}</td>
              <td>
                {requirement.criticality} ({requirement.criticality_basis})
              </td>
              <td>
                {requirement.subsanability} ({requirement.subsanability_basis})
              </td>
              <td>
                {requirement.review_status}
                {requirement.requires_human_review ? " · requiere revision" : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RequirementDetailPanel({ requirement }: { requirement: RequirementDetail }) {
  return (
    <article className="requirement-detail">
      <h3>Detalle del requisito</h3>
      <p>
        {requirement.category} · {requirement.scope} · {requirement.modality}
      </p>
      <p>{requirement.description}</p>
      {requirement.condition_text ? <p>Condicion: {requirement.condition_text}</p> : null}
      <p>
        Ejecucion: {requirement.run.id} · Modelo: {requirement.run.model} · Prompt:{" "}
        {requirement.prompt_version.semantic_version}
      </p>
      <h4>Evidencias</h4>
      {requirement.evidence.map((evidence) => (
        <div key={evidence.id} className="segment-row">
          <p>
            {evidence.evidence_role} · {evidence.validation_status} · Segmento {evidence.segment_id}
          </p>
          <pre>{evidence.quoted_text}</pre>
          <p>
            {evidence.source_location.page_number
              ? `Pagina ${evidence.source_location.page_number}`
              : ""}
            {evidence.source_location.sheet_name
              ? ` Hoja ${evidence.source_location.sheet_name}`
              : ""}
            {evidence.source_location.line_start
              ? ` Lineas ${evidence.source_location.line_start}-${evidence.source_location.line_end}`
              : ""}
          </p>
        </div>
      ))}
      {requirement.relations.length > 0 ? (
        <>
          <h4>Relaciones</h4>
          <ul>
            {requirement.relations.map((relation) => (
              <li key={relation.id}>
                {relation.relation_type}: {relation.explanation}
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </article>
  );
}

function FinancialEvaluationPanel({
  normalizations,
  evaluations,
  results,
  companies,
  snapshots,
  selectedNormalizationRunId,
  selectedCompanyId,
  selectedSnapshotId,
  submitting,
  onLoadCompanies,
  onSelectNormalization,
  onSelectCompany,
  onSelectSnapshot,
  onCreate,
  onForce,
  onRetry,
}: {
  normalizations: NormalizationRunList | null;
  evaluations: FinancialEvaluationList | null;
  results: FinancialEvaluationResultList | null;
  companies: CompanyProfileList | null;
  snapshots: CompanyProfileSnapshotSummary[];
  selectedNormalizationRunId: string;
  selectedCompanyId: string;
  selectedSnapshotId: string;
  submitting: boolean;
  onLoadCompanies: () => void;
  onSelectNormalization: (runId: string) => void;
  onSelectCompany: (companyId: string) => void;
  onSelectSnapshot: (snapshotId: string) => void;
  onCreate: () => void;
  onForce: () => void;
  onRetry: (runId: string) => void;
}) {
  const completedNormalizations = (normalizations?.items ?? []).filter((run) =>
    ["COMPLETED", "COMPLETED_WITH_WARNINGS"].includes(run.status),
  );
  const canCreate =
    Boolean(selectedNormalizationRunId) &&
    Boolean(selectedCompanyId) &&
    Boolean(selectedSnapshotId);
  const latest = evaluations?.items[0];
  return (
    <div className="financial-panel">
      <div className="section-heading">
        <h2>Evaluacion financiera</h2>
        <button type="button" className="button secondary" onClick={onLoadCompanies}>
          Cargar empresas
        </button>
      </div>
      <aside className="notice" role="note" aria-label="Avisos de evaluacion financiera">
        <p>
          La evaluacion financiera compara requisitos individuales contra un snapshot especifico de
          la empresa.
        </p>
        <p>Este resultado no constituye una decision global GO / NO GO.</p>
        <p>Los datos faltantes o no soportados producen UNKNOWN, no cumplimiento.</p>
        <p>
          Las revisiones manuales quedan auditadas y no alteran el resultado automatico original.
        </p>
      </aside>
      <div className="form-grid">
        <label>
          Normalizacion
          <select
            value={selectedNormalizationRunId}
            onChange={(event) => onSelectNormalization(event.target.value)}
          >
            <option value="">Seleccionar ejecucion</option>
            {completedNormalizations.map((run) => (
              <option key={run.id} value={run.id}>
                {run.status} - {run.accepted_requirement_count} requisitos
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
        <button type="button" onClick={onCreate} disabled={!canCreate || submitting}>
          {submitting ? "Encolando..." : "Crear evaluacion financiera"}
        </button>
        <button
          type="button"
          className="button secondary"
          onClick={onForce}
          disabled={!canCreate || submitting}
        >
          Forzar nueva evaluacion
        </button>
      </div>
      {latest ? (
        <article className="run-summary">
          <strong>Ultima evaluacion: {latest.status}</strong>
          <p>
            Requisitos: {latest.requirement_count} · Evaluados: {latest.evaluated_count} · Cumple:{" "}
            {latest.complies_count} · No cumple: {latest.does_not_comply_count} · UNKNOWN:{" "}
            {latest.unknown_count} · Conflictos: {latest.conflicting_count}
          </p>
          <p>
            Snapshot: {latest.company_profile_snapshot_id} · Digest:{" "}
            {latest.input_digest.slice(0, 12)}...
          </p>
          {latest.error_message ? <p className="error">{latest.error_message}</p> : null}
          {latest.status === "FAILED" ? (
            <button type="button" onClick={() => onRetry(latest.id)}>
              Reintentar evaluacion
            </button>
          ) : null}
        </article>
      ) : (
        <p className="empty-state">No hay evaluaciones financieras creadas.</p>
      )}
      {(results?.items ?? []).length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Resultado</th>
                <th>Metrica</th>
                <th>Valor requerido</th>
                <th>Valor observado</th>
                <th>Explicacion</th>
                <th>Revision</th>
              </tr>
            </thead>
            <tbody>
              {(results?.items ?? []).map((result) => (
                <tr key={result.id}>
                  <td>{result.status}</td>
                  <td>{result.metric_type ?? "UNKNOWN"}</td>
                  <td>
                    {result.operator ?? "-"} {result.required_value ?? "-"}{" "}
                    {result.required_unit ?? ""}
                  </td>
                  <td>
                    {result.actual_value ?? "UNKNOWN"} {result.actual_unit ?? ""}
                  </td>
                  <td>{result.explanation_code}</td>
                  <td>
                    {result.review_status}
                    {result.requires_human_review ? " · requiere revision" : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}

function locationLabel(segment: ExtractedSegmentList["segments"][number]) {
  if (segment.page_number) return `pagina ${segment.page_number}`;
  if (segment.sheet_name)
    return `${segment.sheet_name} filas ${segment.row_start}-${segment.row_end}`;
  if (segment.line_start) return `lineas ${segment.line_start}-${segment.line_end}`;
  return `secuencia ${segment.sequence}`;
}

function expectedValue(requirement: NormalizedRequirement) {
  if (!requirement.expected_value) return "No informado";
  return [
    requirement.expected_value.value ?? "UNKNOWN",
    requirement.expected_value.unit,
    requirement.expected_value.raw_text ? `(${requirement.expected_value.raw_text})` : "",
  ]
    .filter(Boolean)
    .join(" ");
}

function formatDate(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("es-CO", { dateStyle: "medium" }).format(new Date(value))
    : "Sin fecha";
}

function formatBytes(value: number) {
  return `${Math.max(1, Math.round(value / 1024))} KB`;
}
