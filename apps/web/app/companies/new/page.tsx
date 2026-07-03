"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiClientError, createCompany } from "../../../lib/api";

export default function NewCompanyPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      const company = await createCompany({
        legal_name: String(form.get("legal_name") ?? ""),
        trade_name: optional(form.get("trade_name")),
        tax_id: optional(form.get("tax_id")),
        tax_id_type: optional(form.get("tax_id_type")),
        company_type: optional(form.get("company_type")),
        legal_nature: optional(form.get("legal_nature")),
        incorporation_date: optional(form.get("incorporation_date")),
        country: optional(form.get("country")) ?? "CO",
        department: optional(form.get("department")),
        city: optional(form.get("city")),
        address: optional(form.get("address")),
        website: optional(form.get("website")),
        primary_email: optional(form.get("primary_email")),
        primary_phone: optional(form.get("primary_phone")),
        economic_activity_codes: csv(form.get("economic_activity_codes")),
      });
      router.push(`/companies/${company.id}`);
    } catch (submitError) {
      setError(
        submitError instanceof ApiClientError
          ? (submitError.payload?.message ?? submitError.message)
          : "No fue posible crear la empresa.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="container">
      <h1>Crear empresa</h1>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Razon social *
          <input name="legal_name" required minLength={1} />
        </label>
        <label>
          Nombre comercial
          <input name="trade_name" />
        </label>
        <label>
          NIT / identificacion
          <input name="tax_id" />
        </label>
        <label>
          Tipo de identificacion
          <input name="tax_id_type" defaultValue="NIT" />
        </label>
        <label>
          Tipo de empresa
          <input name="company_type" />
        </label>
        <label>
          Naturaleza juridica
          <input name="legal_nature" />
        </label>
        <label>
          Fecha de constitucion
          <input name="incorporation_date" type="date" />
        </label>
        <label>
          Pais
          <input name="country" defaultValue="CO" />
        </label>
        <label>
          Departamento
          <input name="department" />
        </label>
        <label>
          Ciudad
          <input name="city" />
        </label>
        <label>
          Sitio web
          <input name="website" type="url" />
        </label>
        <label>
          Correo principal
          <input name="primary_email" type="email" />
        </label>
        <label className="full">
          Direccion
          <input name="address" />
        </label>
        <label className="full">
          Codigos de actividad economica
          <input name="economic_activity_codes" placeholder="6201, 7110" />
        </label>
        {error ? (
          <p role="alert" className="error">
            {error}
          </p>
        ) : null}
        <button type="submit" disabled={submitting}>
          {submitting ? "Creando..." : "Crear empresa"}
        </button>
      </form>
    </main>
  );
}

function optional(value: FormDataEntryValue | null) {
  const text = String(value ?? "").trim();
  return text === "" ? null : text;
}

function csv(value: FormDataEntryValue | null) {
  return String(value ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
