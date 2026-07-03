"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import type { CompanyProfileList, CompanyProfileStatus } from "@pliegocheck/schemas";
import { COMPANY_PROFILE_STATUS_VALUES } from "@pliegocheck/schemas";
import { ApiClientError, listCompanies } from "../../lib/api";

export default function CompaniesPage() {
  const [data, setData] = useState<CompanyProfileList | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<CompanyProfileStatus | "">("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(nextSearch = search, nextStatus = status) {
    setLoading(true);
    setError(null);
    try {
      setData(await listCompanies({ search: nextSearch, status: nextStatus }));
    } catch (loadError) {
      setError(loadError instanceof ApiClientError ? loadError.message : "Error consultando API.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load("", "");
  }, []);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void load(search, status);
  }

  return (
    <main className="container wide">
      <header className="page-header">
        <div>
          <h1>Empresas</h1>
          <p className="lead">
            Perfiles corporativos locales con evidencias y snapshots auditables.
          </p>
        </div>
        <Link className="button" href="/companies/new">
          Crear empresa
        </Link>
      </header>

      <form className="toolbar" onSubmit={submit}>
        <label>
          Buscar
          <input value={search} onChange={(event) => setSearch(event.target.value)} />
        </label>
        <label>
          Estado
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value as CompanyProfileStatus | "")}
          >
            <option value="">Todos</option>
            {COMPANY_PROFILE_STATUS_VALUES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">Filtrar</button>
      </form>

      {loading ? <p>Cargando empresas...</p> : null}
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : null}
      {!loading && data?.items.length === 0 ? (
        <section className="empty-state">
          <h2>No hay empresas registradas</h2>
          <p>Crea una empresa ficticia o real de trabajo local para adjuntar soportes.</p>
        </section>
      ) : null}
      {data && data.items.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Referencia</th>
                <th>Razon social</th>
                <th>NIT</th>
                <th>Estado</th>
                <th>Completitud</th>
                <th>Evidencias pendientes</th>
                <th>Actualizada</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((company) => (
                <tr key={company.id}>
                  <td>
                    <Link href={`/companies/${company.id}`}>{company.internal_reference}</Link>
                  </td>
                  <td>{company.legal_name}</td>
                  <td>{company.tax_id_masked ?? "Sin NIT"}</td>
                  <td>{company.status}</td>
                  <td>
                    {company.completeness_status} (
                    {Math.round(Number(company.evidence_coverage) * 100)}%)
                  </td>
                  <td>{company.pending_evidence_count}</td>
                  <td>{formatDate(company.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </main>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-CO", { dateStyle: "medium" }).format(new Date(value));
}
