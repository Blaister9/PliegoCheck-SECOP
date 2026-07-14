"use client";

import { useEffect, useState } from "react";
import type { ExternalProcurementProcessLinkList } from "@pliegocheck/schemas";
import { ApiClientError, listProcessExternalLinks } from "../../../lib/api";

export function ExternalLinksPanel({ processId }: { processId: string }) {
  const [data, setData] = useState<ExternalProcurementProcessLinkList | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    listProcessExternalLinks(processId)
      .then(setData)
      .catch((loadError) =>
        setError(
          loadError instanceof ApiClientError
            ? loadError.message
            : "No fue posible cargar la trazabilidad externa.",
        ),
      );
  }, [processId]);
  if (error)
    return (
      <p role="alert" className="error">
        {error}
      </p>
    );
  if (!data || !Array.isArray(data.items) || data.items.length === 0) return null;
  return (
    <section>
      <h2>Fuente externa</h2>
      {data.items.map((link) => (
        <article className="external-link" key={link.id}>
          <p>
            <strong>{link.source_system}</strong> ·{" "}
            {link.source_process_reference ?? link.source_process_id}
          </p>
          <p>Documentos: {link.documents_status}</p>
          {link.source_url ? (
            <a href={link.source_url} target="_blank" rel="noreferrer">
              Abrir registro oficial
            </a>
          ) : (
            <span>Enlace no disponible</span>
          )}
        </article>
      ))}
    </section>
  );
}
