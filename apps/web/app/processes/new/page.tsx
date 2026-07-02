"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiClientError, createProcess } from "../../../lib/api";

export default function NewProcessPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      const process = await createProcess({
        title: String(form.get("title") ?? ""),
        contracting_entity: String(form.get("contracting_entity") ?? ""),
        secop_reference: optional(form.get("secop_reference")),
        description: optional(form.get("description")),
        source_url: optional(form.get("source_url")),
        selection_method: optional(form.get("selection_method")),
        estimated_value: optional(form.get("estimated_value")),
        currency: String(form.get("currency") ?? "COP") || "COP",
        published_at: optional(form.get("published_at")),
        closing_at: optional(form.get("closing_at")),
      });
      router.push(`/processes/${process.id}`);
    } catch (submitError) {
      setError(
        submitError instanceof ApiClientError
          ? (submitError.payload?.message ?? submitError.message)
          : "No fue posible crear el proceso.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="container">
      <h1>Crear proceso</h1>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Titulo *
          <input name="title" required minLength={1} />
        </label>
        <label>
          Entidad contratante *
          <input name="contracting_entity" required minLength={1} />
        </label>
        <label>
          Referencia SECOP
          <input name="secop_reference" />
        </label>
        <label>
          URL fuente
          <input name="source_url" type="url" />
        </label>
        <label>
          Modalidad
          <input name="selection_method" />
        </label>
        <label>
          Valor estimado
          <input name="estimated_value" inputMode="decimal" />
        </label>
        <label>
          Moneda
          <input name="currency" defaultValue="COP" maxLength={3} />
        </label>
        <label>
          Publicado
          <input name="published_at" type="datetime-local" />
        </label>
        <label>
          Cierre
          <input name="closing_at" type="datetime-local" />
        </label>
        <label className="full">
          Descripcion
          <textarea name="description" rows={4} />
        </label>
        {error ? (
          <p role="alert" className="error">
            {error}
          </p>
        ) : null}
        <button type="submit" disabled={submitting}>
          {submitting ? "Creando..." : "Crear proceso"}
        </button>
      </form>
    </main>
  );
}

function optional(value: FormDataEntryValue | null) {
  const text = String(value ?? "").trim();
  if (text === "") return null;
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(text)) {
    return `${text}:00-05:00`;
  }
  return text;
}
