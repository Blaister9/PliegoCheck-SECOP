"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import type { DocumentUploadResponse, ProcessDetail } from "@pliegocheck/schemas";
import { ApiClientError, downloadUrl, getProcess, uploadDocuments } from "../../../lib/api";

export function ProcessDetailClient({ processId }: { processId: string }) {
  const [process, setProcess] = useState<ProcessDetail | null>(null);
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setProcess(await getProcess(processId));
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
        Los documentos todavía no han sido extraídos ni analizados.
      </aside>

      <section>
        <h2>Inventario documental</h2>
        {process.documents.length === 0 ? <p>No hay documentos cargados.</p> : null}
        {process.documents.map((document) => (
          <article className="document-row" key={document.id}>
            <div>
              <strong>{document.original_filename}</strong>
              <p>
                {document.document_type} · {formatBytes(document.size_bytes)} · {document.extension}
              </p>
              <p title={document.sha256}>SHA-256: {document.sha256.slice(0, 12)}...</p>
            </div>
            <a className="button secondary" href={downloadUrl(process.id, document.id)}>
              Descargar
            </a>
          </article>
        ))}
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

function formatDate(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("es-CO", { dateStyle: "medium" }).format(new Date(value))
    : "Sin fecha";
}

function formatBytes(value: number) {
  return `${Math.round(value / 1024)} KB`;
}
