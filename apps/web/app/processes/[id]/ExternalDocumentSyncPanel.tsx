"use client";

import { useEffect, useState } from "react";
import type {
  ExternalProcessDocumentList,
  ExternalProcessDocumentVersion,
  ExternalProcessSyncReadiness,
  ExternalProcessSyncRunDetail,
  ExternalProcessSyncRunList,
} from "@pliegocheck/schemas";
import {
  ApiClientError,
  extractExternalDocument,
  getExternalSyncReadiness,
  getExternalSyncRun,
  listExternalDocuments,
  listExternalDocumentVersions,
  listExternalSyncRuns,
  queueExternalDocumentDownload,
  queueExternalSync,
} from "../../../lib/api";

export function ExternalDocumentSyncPanel({ processId }: { processId: string }) {
  const [readiness, setReadiness] = useState<ExternalProcessSyncReadiness | null>(null);
  const [runs, setRuns] = useState<ExternalProcessSyncRunList | null>(null);
  const [latest, setLatest] = useState<ExternalProcessSyncRunDetail | null>(null);
  const [documents, setDocuments] = useState<ExternalProcessDocumentList | null>(null);
  const [versions, setVersions] = useState<ExternalProcessDocumentVersion[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    const [ready, runList, documentList] = await Promise.all([
      getExternalSyncReadiness(processId),
      listExternalSyncRuns(processId),
      listExternalDocuments(processId),
    ]);
    setReadiness(ready);
    setRuns(runList);
    setDocuments(documentList);
    setLatest(runList.items[0] ? await getExternalSyncRun(processId, runList.items[0].id) : null);
    setMessage(null);
  }

  useEffect(() => {
    void load().catch(handleError);
  }, [processId]);

  function handleError(error: unknown) {
    setMessage(
      error instanceof ApiClientError && error.status === 403
        ? "Tu rol no tiene permiso para esta operacion."
        : error instanceof Error
          ? error.message
          : "No fue posible consultar documentos externos.",
    );
  }

  async function action(operation: () => Promise<unknown>, success: string) {
    setBusy(true);
    setMessage(null);
    try {
      await operation();
      await load();
      setMessage(success);
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="external-documents-title">
      <div className="section-heading">
        <h2 id="external-documents-title">Sincronizacion SECOP y documentos publicos</h2>
        <button
          type="button"
          disabled={busy || !readiness?.available}
          onClick={() => void action(() => queueExternalSync(processId), "Sincronizacion en cola.")}
        >
          Actualizar desde SECOP
        </button>
      </div>
      <aside className="notice" role="note">
        <p>
          Los documentos provienen de fuentes publicas externas. Su disponibilidad, contenido y
          actualizacion dependen del sistema de origen.
        </p>
        <p>La sincronizacion no reemplaza la verificacion manual del expediente oficial.</p>
        <p>
          Una posible adenda requiere revision humana antes de volver a evaluar el proceso. La
          descarga y la extraccion son acciones separadas y explicitas.
        </p>
        <p>PliegoCheck no presenta ofertas ni realiza tramites en SECOP.</p>
      </aside>
      {message ? <p role="status">{message}</p> : null}
      <p>
        Fuente: {readiness?.source_system ?? "no disponible"}. Ultimo sync:{" "}
        {readiness?.last_sync_at ?? "sin ejecuciones"}. Estado:{" "}
        {runs?.items[0]?.status ?? "sin ejecuciones"}. Actualizacion externa:{" "}
        {runs?.items[0]?.source_updated_at ?? "no informada"}.
      </p>
      {(runs?.items[0]?.warnings ?? []).map((warning, index) => (
        <p className="warning" key={index}>
          {String(warning.message ?? warning.code ?? "Advertencia externa")}
        </p>
      ))}
      {runs?.items[0]?.error_message ? (
        <p className="error">{runs.items[0].error_message}</p>
      ) : null}
      {latest?.events?.length ? (
        <div>
          <h3>Cambios detectados</h3>
          <ul>
            {latest.events.map((event) => (
              <li key={event.id}>
                {event.event_type}: {event.new_value ?? event.old_value ?? "cambio registrado"}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Documento</th>
              <th>Fuente</th>
              <th>Descarga</th>
              <th>Adenda</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {(documents?.items ?? []).map((document) => (
              <tr key={document.id}>
                <td>
                  {document.title}
                  <br />
                  <a href={document.source_public_url ?? "#"} target="_blank" rel="noreferrer">
                    Ver fuente oficial
                  </a>
                </td>
                <td>{document.discovery_status}</td>
                <td>
                  {document.download_status} — {document.version_count} version(es)
                </td>
                <td>
                  {document.addendum_status}
                  {document.requires_human_review ? " — revisar" : ""}
                </td>
                <td>
                  <button
                    type="button"
                    disabled={busy || document.download_status === "UNSUPPORTED"}
                    onClick={() =>
                      void action(
                        () => queueExternalDocumentDownload(processId, document.id),
                        "Descarga en cola; no se inicio extraccion.",
                      )
                    }
                  >
                    Descargar documento
                  </button>{" "}
                  <button
                    type="button"
                    disabled={busy || !document.current_version_id}
                    onClick={() =>
                      void action(
                        () => extractExternalDocument(processId, document.id),
                        "Extraccion en cola.",
                      )
                    }
                  >
                    Extraer documento
                  </button>{" "}
                  <button
                    type="button"
                    disabled={busy || document.version_count === 0}
                    onClick={() =>
                      void listExternalDocumentVersions(processId, document.id)
                        .then(setVersions)
                        .catch(handleError)
                    }
                  >
                    Ver versiones
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {documents?.total === 0 ? <p>Aun no hay documentos descubiertos.</p> : null}
      {versions.length ? (
        <div>
          <h3>Versiones</h3>
          <ul>
            {versions.map((version) => (
              <li key={version.id}>
                v{version.version_number} — SHA-256 {version.sha256} —{" "}
                {version.detected_content_type}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
