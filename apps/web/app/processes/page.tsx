"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import type { ProcessList, ProcessStatus } from "@pliegocheck/schemas";
import { PROCESS_STATUS_VALUES } from "@pliegocheck/schemas";
import { ApiClientError, listProcesses } from "../../lib/api";

export default function ProcessesPage() {
  const [data, setData] = useState<ProcessList | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ProcessStatus | "">("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadProcesses(nextSearch = search, nextStatus = status) {
    setLoading(true);
    setError(null);
    try {
      setData(await listProcesses({ search: nextSearch, status: nextStatus }));
    } catch (loadError) {
      setError(loadError instanceof ApiClientError ? loadError.message : "Error consultando API.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProcesses("", "");
  }, []);

  function submitFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadProcesses(search, status);
  }

  return (
    <main className="container wide">
      <header className="page-header">
        <div>
          <h1>Procesos importados</h1>
          <p className="lead">Procesos creados manualmente y su inventario documental inicial.</p>
        </div>
        <Link className="button" href="/processes/new">
          Crear proceso
        </Link>
      </header>

      <form className="toolbar" onSubmit={submitFilters}>
        <label>
          Buscar
          <input value={search} onChange={(event) => setSearch(event.target.value)} />
        </label>
        <label>
          Estado
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value as ProcessStatus | "")}
          >
            <option value="">Todos</option>
            {PROCESS_STATUS_VALUES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">Filtrar</button>
      </form>

      {loading ? <p>Cargando procesos...</p> : null}
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : null}
      {!loading && data?.items.length === 0 ? (
        <section className="empty-state">
          <h2>No hay procesos importados</h2>
          <p>Crea el primer proceso manual para adjuntar sus documentos originales.</p>
        </section>
      ) : null}
      {data && data.items.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Referencia interna</th>
                <th>SECOP</th>
                <th>Titulo</th>
                <th>Entidad</th>
                <th>Estado</th>
                <th>Cierre</th>
                <th>Documentos</th>
                <th>Creado</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((process) => (
                <tr key={process.id}>
                  <td>
                    <Link href={`/processes/${process.id}`}>{process.internal_reference}</Link>
                  </td>
                  <td>{process.secop_reference ?? "Sin referencia"}</td>
                  <td>{process.title}</td>
                  <td>{process.contracting_entity}</td>
                  <td>{process.status}</td>
                  <td>{formatDate(process.closing_at)}</td>
                  <td>{process.document_count}</td>
                  <td>{formatDate(process.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </main>
  );
}

function formatDate(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("es-CO", { dateStyle: "medium" }).format(new Date(value))
    : "Sin fecha";
}
