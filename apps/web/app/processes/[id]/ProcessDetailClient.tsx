"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import type {
  DocumentUploadResponse,
  ExtractedSegmentList,
  ExtractedSegmentType,
  ProcessDetail,
  ProcessInventory,
} from "@pliegocheck/schemas";
import { EXTRACTED_SEGMENT_TYPE_VALUES } from "@pliegocheck/schemas";
import {
  ApiClientError,
  downloadUrl,
  enqueueDocumentExtraction,
  enqueueProcessExtractions,
  getExtractionSegments,
  getInventory,
  getProcess,
  uploadDocuments,
} from "../../../lib/api";

export function ProcessDetailClient({ processId }: { processId: string }) {
  const [process, setProcess] = useState<ProcessDetail | null>(null);
  const [inventory, setInventory] = useState<ProcessInventory | null>(null);
  const [segments, setSegments] = useState<ExtractedSegmentList | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  const [segmentType, setSegmentType] = useState<ExtractedSegmentType | "">("");
  const [pageNumber, setPageNumber] = useState("");
  const [sheetName, setSheetName] = useState("");
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [processPayload, inventoryPayload] = await Promise.all([
        getProcess(processId),
        getInventory(processId),
      ]);
      setProcess(processPayload);
      setInventory(inventoryPayload);
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
          <strong>Moneda:</strong> {process.currency}
        </p>
        <p>
          <strong>Valor estimado:</strong> {process.estimated_value ?? "No informado"}
        </p>
        <p>
          <strong>Cierre:</strong> {formatDate(process.closing_at)}
        </p>
      </section>

      <aside className="notice" role="note">
        La extraccion es deterministica y todavia no evalua requisitos ni produce una decision GO /
        NO GO.
      </aside>

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

function locationLabel(segment: ExtractedSegmentList["segments"][number]) {
  if (segment.page_number) return `pagina ${segment.page_number}`;
  if (segment.sheet_name)
    return `${segment.sheet_name} filas ${segment.row_start}-${segment.row_end}`;
  if (segment.line_start) return `lineas ${segment.line_start}-${segment.line_end}`;
  return `secuencia ${segment.sequence}`;
}

function formatDate(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("es-CO", { dateStyle: "medium" }).format(new Date(value))
    : "Sin fecha";
}

function formatBytes(value: number) {
  return `${Math.max(1, Math.round(value / 1024))} KB`;
}
