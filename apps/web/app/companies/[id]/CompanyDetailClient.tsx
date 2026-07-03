"use client";

import { FormEvent, useEffect, useState } from "react";
import type { ReactNode } from "react";
import type {
  CompanyEvidenceDocumentMetadata,
  CompanyEvidenceType,
  CompanyProfileCompleteness,
  CompanyProfileDetail,
  CompanyProfileSnapshotSummary,
} from "@pliegocheck/schemas";
import { COMPANY_EVIDENCE_TYPE_VALUES } from "@pliegocheck/schemas";
import {
  ApiClientError,
  archiveCompany,
  createCapability,
  createCertification,
  createExperience,
  createFinancialMetric,
  createFinancialPeriod,
  createLegalRegistration,
  createPerson,
  createRup,
  createSnapshot,
  createUnspsc,
  getCompany,
  getCompleteness,
  listEvidenceDocuments,
  listSnapshots,
  publishSnapshot,
  updateCompany,
  uploadCompanyEvidence,
} from "../../../lib/api";

export function CompanyDetailClient({ companyId }: { companyId: string }) {
  const [company, setCompany] = useState<CompanyProfileDetail | null>(null);
  const [evidence, setEvidence] = useState<CompanyEvidenceDocumentMetadata[]>([]);
  const [completeness, setCompleteness] = useState<CompanyProfileCompleteness | null>(null);
  const [snapshots, setSnapshots] = useState<CompanyProfileSnapshotSummary[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [evidenceType, setEvidenceType] = useState<CompanyEvidenceType>("OTHER");

  async function load() {
    setError(null);
    try {
      const [nextCompany, nextEvidence, nextCompleteness, nextSnapshots] = await Promise.all([
        getCompany(companyId),
        listEvidenceDocuments(companyId),
        getCompleteness(companyId),
        listSnapshots(companyId),
      ]);
      setCompany(nextCompany);
      setEvidence(nextEvidence);
      setCompleteness(nextCompleteness);
      setSnapshots(nextSnapshots);
    } catch (loadError) {
      setError(loadError instanceof ApiClientError ? loadError.message : "Error consultando API.");
    }
  }

  useEffect(() => {
    void load();
  }, [companyId]);

  async function submitIdentity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      await updateCompany(companyId, {
        legal_name: required(form, "legal_name"),
        trade_name: optional(form, "trade_name"),
        tax_id: optional(form, "tax_id"),
        tax_id_type: optional(form, "tax_id_type"),
        primary_email: optional(form, "primary_email"),
        primary_phone: optional(form, "primary_phone"),
      });
    }, "Empresa actualizada.");
  }

  async function submitLegal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      await createLegalRegistration(companyId, {
        registration_type: required(form, "registration_type"),
        registration_number: optional(form, "registration_number"),
        issuing_authority: optional(form, "issuing_authority"),
        issued_at: optional(form, "issued_at"),
        expires_at: optional(form, "expires_at"),
      });
    }, "Registro juridico creado.");
  }

  async function submitRup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      await createRup(companyId, {
        registration_number: optional(form, "registration_number"),
        issued_at: optional(form, "issued_at"),
        valid_until: optional(form, "valid_until"),
        renewal_year: numberOrNull(form, "renewal_year"),
        financial_capacity: optional(form, "financial_capacity"),
      });
    }, "RUP registrado.");
  }

  async function submitFinancial(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      const period = await createFinancialPeriod(companyId, {
        period_start: required(form, "period_start"),
        period_end: required(form, "period_end"),
        currency: required(form, "currency"),
        source_type: required(form, "source_type") as "FINANCIAL_STATEMENT",
        status: "DECLARED",
      });
      await createFinancialMetric(companyId, period.id, {
        metric_type: required(form, "metric_type") as "LIQUIDITY_RATIO",
        value: required(form, "value"),
        unit: optional(form, "unit"),
        source_value: optional(form, "source_value"),
        is_calculated: false,
        formula: null,
        formula_inputs: {},
        calculation_version: null,
        status: "DECLARED",
      });
    }, "Periodo y metrica financiera creados.");
  }

  async function submitExperience(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      await createExperience(companyId, {
        contracting_party: required(form, "contracting_party"),
        contract_title: required(form, "contract_title"),
        execution_status: "COMPLETED",
        total_contract_value: optional(form, "total_contract_value"),
        company_participation_percentage: optional(form, "company_participation_percentage"),
        currency: required(form, "currency"),
        consortium_name: optional(form, "consortium_name"),
        consortium_members: csv(form, "consortium_members"),
        unspsc_codes: csv(form, "unspsc_codes"),
        activities: [],
        scope_tags: [],
      });
    }, "Experiencia creada.");
  }

  async function submitPerson(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      await createPerson(companyId, {
        full_name: required(form, "full_name"),
        identification_type: optional(form, "identification_type"),
        identification_number: optional(form, "identification_number"),
        email: optional(form, "email"),
        phone: optional(form, "phone"),
        relationship_type: required(form, "relationship_type") as "EMPLOYEE",
        availability_status: required(form, "availability_status") as "AVAILABLE",
        status: "DECLARED",
      });
    }, "Persona creada.");
  }

  async function submitCertification(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      await createCertification(companyId, {
        certification_type: required(form, "certification_type") as "ISO",
        name: required(form, "name"),
        issuer: optional(form, "issuer"),
        issued_at: optional(form, "issued_at"),
        expires_at: optional(form, "expires_at"),
        status: "DECLARED",
      });
    }, "Certificacion creada.");
  }

  async function submitCapability(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      await createCapability(companyId, {
        category: required(form, "category") as "GEOGRAPHIC_COVERAGE",
        name: required(form, "name"),
        value: optional(form, "value"),
        unit: optional(form, "unit"),
        status: "DECLARED",
      });
    }, "Capacidad creada.");
  }

  async function submitEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await action(async () => {
      const result = await uploadCompanyEvidence(companyId, files, evidenceType);
      setFiles([]);
      setMessage(`Almacenados: ${result.stored_count}. Rechazados: ${result.rejected_count}.`);
    }, "Evidencia cargada.");
  }

  async function createSnapshotAction() {
    await action(async () => {
      await createSnapshot(companyId, {
        notes: "Snapshot creado desde UI",
        allow_incomplete: true,
      });
    }, "Snapshot creado.");
  }

  async function publishSnapshotAction(snapshotId: string) {
    await action(async () => {
      await publishSnapshot(companyId, snapshotId);
    }, "Snapshot publicado.");
  }

  async function archiveAction() {
    await action(async () => {
      await archiveCompany(companyId);
    }, "Empresa archivada.");
  }

  async function action(fn: () => Promise<void>, success: string) {
    setError(null);
    setMessage(null);
    try {
      await fn();
      setMessage(success);
      await load();
    } catch (actionError) {
      setError(
        actionError instanceof ApiClientError
          ? (actionError.payload?.message ?? actionError.message)
          : "No fue posible completar la accion.",
      );
    }
  }

  if (!company) {
    return (
      <main className="container">
        <p>Cargando empresa...</p>
        {error ? (
          <p role="alert" className="error">
            {error}
          </p>
        ) : null}
      </main>
    );
  }

  return (
    <main className="container wide">
      <header className="page-header">
        <div>
          <h1>{company.legal_name}</h1>
          <p className="lead">
            {company.internal_reference} - Estado {company.status} - NIT{" "}
            {company.tax_id_masked ?? "sin NIT"}
          </p>
        </div>
        <button type="button" className="button secondary" onClick={() => void archiveAction()}>
          Archivar
        </button>
      </header>

      <aside className="notice" role="note">
        La completitud del perfil no determina si la empresa cumple un proceso de contratacion.
      </aside>
      <aside className="notice" role="note">
        Las evaluaciones futuras utilizaran una version especifica del perfil, no los datos
        editables actuales.
      </aside>
      {message ? <p className="success">{message}</p> : null}
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : null}

      <nav className="tabs" aria-label="Secciones de empresa">
        {[
          "Identidad",
          "Legal",
          "Finanzas",
          "Experiencia",
          "Personal",
          "Certificaciones",
          "Capacidades",
          "Evidencias",
          "Completitud",
          "Snapshots",
        ].map((item) => (
          <a href={`#${item.toLowerCase()}`} key={item}>
            {item}
          </a>
        ))}
      </nav>

      <section id="identidad">
        <h2>Identidad</h2>
        <form className="form-grid compact" onSubmit={submitIdentity}>
          <label>
            Razon social
            <input name="legal_name" defaultValue={company.legal_name} required />
          </label>
          <label>
            Nombre comercial
            <input name="trade_name" defaultValue={company.trade_name ?? ""} />
          </label>
          <label>
            NIT
            <input name="tax_id" defaultValue={company.tax_id ?? ""} />
          </label>
          <label>
            Tipo ID
            <input name="tax_id_type" defaultValue={company.tax_id_type ?? "NIT"} />
          </label>
          <label>
            Correo
            <input name="primary_email" defaultValue={company.primary_email ?? ""} />
          </label>
          <label>
            Telefono
            <input name="primary_phone" defaultValue={company.primary_phone ?? ""} />
          </label>
          <button type="submit">Guardar identidad</button>
        </form>
      </section>

      <section id="legal" className="two-column">
        <Panel title="Registros juridicos" onSubmit={submitLegal}>
          <select name="registration_type" defaultValue="RUT">
            <option>RUT</option>
            <option>CHAMBER_OF_COMMERCE</option>
            <option>RUP</option>
          </select>
          <input name="registration_number" placeholder="Numero" />
          <input name="issuing_authority" placeholder="Autoridad" />
          <input name="issued_at" type="date" />
          <input name="expires_at" type="date" />
        </Panel>
        <Panel title="RUP y UNSPSC" onSubmit={submitRup}>
          <input name="registration_number" placeholder="Numero RUP" />
          <input name="issued_at" type="date" />
          <input name="valid_until" type="date" />
          <input name="renewal_year" placeholder="Ano renovacion" inputMode="numeric" />
          <input name="financial_capacity" placeholder="Capacidad financiera" />
        </Panel>
        <form
          className="inline-form"
          onSubmit={async (event) => {
            event.preventDefault();
            const form = new FormData(event.currentTarget);
            await action(async () => {
              await createUnspsc(companyId, {
                code: required(form, "code"),
                description: optional(form, "description"),
                source: "MANUAL",
                status: "DECLARED",
              });
            }, "Codigo UNSPSC creado.");
          }}
        >
          <input name="code" placeholder="UNSPSC" required />
          <input name="description" placeholder="Descripcion opcional" />
          <button type="submit">Agregar UNSPSC</button>
        </form>
      </section>

      <section id="finanzas">
        <Panel title="Finanzas" onSubmit={submitFinancial}>
          <input name="period_start" type="date" required />
          <input name="period_end" type="date" required />
          <input name="currency" defaultValue="COP" />
          <select name="source_type" defaultValue="FINANCIAL_STATEMENT">
            <option>FINANCIAL_STATEMENT</option>
            <option>RUP</option>
            <option>TAX_RETURN</option>
          </select>
          <select name="metric_type" defaultValue="LIQUIDITY_RATIO">
            <option>LIQUIDITY_RATIO</option>
            <option>WORKING_CAPITAL</option>
            <option>DEBT_RATIO</option>
          </select>
          <input name="value" placeholder="Valor" required />
          <input name="unit" placeholder="Unidad" />
          <input name="source_value" placeholder="Valor fuente" />
        </Panel>
      </section>

      <section id="experiencia">
        <Panel title="Experiencia contractual" onSubmit={submitExperience}>
          <input name="contracting_party" placeholder="Contratante" required />
          <input name="contract_title" placeholder="Objeto / titulo" required />
          <input name="total_contract_value" placeholder="Valor total" />
          <input name="company_participation_percentage" placeholder="% participacion" />
          <input name="currency" defaultValue="COP" />
          <input name="consortium_name" placeholder="Consorcio / UT" />
          <input name="consortium_members" placeholder="Integrantes separados por coma" />
          <input name="unspsc_codes" placeholder="UNSPSC separados por coma" />
        </Panel>
      </section>

      <section id="personal">
        <Panel title="Personal" onSubmit={submitPerson}>
          <input name="full_name" placeholder="Nombre completo" required />
          <input name="identification_type" placeholder="Tipo ID" />
          <input name="identification_number" placeholder="Identificacion (se enmascara)" />
          <input name="email" placeholder="Correo" />
          <input name="phone" placeholder="Telefono" />
          <select name="relationship_type" defaultValue="EMPLOYEE">
            <option>EMPLOYEE</option>
            <option>CONTRACTOR</option>
            <option>ALLY</option>
          </select>
          <select name="availability_status" defaultValue="AVAILABLE">
            <option>AVAILABLE</option>
            <option>PARTIAL</option>
            <option>UNKNOWN</option>
          </select>
        </Panel>
      </section>

      <section id="certificaciones" className="two-column">
        <Panel title="Certificaciones" onSubmit={submitCertification}>
          <select name="certification_type" defaultValue="ISO">
            <option>ISO</option>
            <option>QUALITY</option>
            <option>SECURITY</option>
            <option>OTHER</option>
          </select>
          <input name="name" placeholder="Nombre" required />
          <input name="issuer" placeholder="Emisor" />
          <input name="issued_at" type="date" />
          <input name="expires_at" type="date" />
        </Panel>
        <Panel title="Capacidades" onSubmit={submitCapability}>
          <select name="category" defaultValue="GEOGRAPHIC_COVERAGE">
            <option>GEOGRAPHIC_COVERAGE</option>
            <option>TECHNOLOGY</option>
            <option>OPERATIONAL</option>
            <option>OTHER</option>
          </select>
          <input name="name" placeholder="Nombre" required />
          <input name="value" placeholder="Valor declarado" />
          <input name="unit" placeholder="Unidad" />
        </Panel>
      </section>

      <section id="evidencias">
        <h2>Evidencias</h2>
        <form className="toolbar" onSubmit={submitEvidence}>
          <label>
            Tipo
            <select
              value={evidenceType}
              onChange={(event) => setEvidenceType(event.target.value as CompanyEvidenceType)}
            >
              {COMPANY_EVIDENCE_TYPE_VALUES.map((value) => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </label>
          <label>
            Documentos
            <input
              type="file"
              multiple
              onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
            />
          </label>
          <button type="submit" disabled={!files.length}>
            Cargar evidencias
          </button>
        </form>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Titulo</th>
                <th>Tipo</th>
                <th>Hash</th>
                <th>Revision</th>
                <th>Extraccion</th>
              </tr>
            </thead>
            <tbody>
              {evidence.map((item) => (
                <tr key={item.id}>
                  <td>{item.title}</td>
                  <td>{item.evidence_type}</td>
                  <td>
                    <code>{item.sha256.slice(0, 12)}</code>
                  </td>
                  <td>{item.review_status}</td>
                  <td>{item.processing_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section id="completitud">
        <h2>Completitud</h2>
        {completeness ? (
          <>
            <p>
              Estado general: {completeness.ready_for_review ? "READY_FOR_REVIEW" : "INCOMPLETE"} -
              Cobertura {Math.round(Number(completeness.evidence_coverage) * 100)}%
            </p>
            <p>
              Registros sin soporte: {completeness.unsupported_record_count}. Evidencias vencidas:{" "}
              {completeness.expired_evidence_count}. Conflictos:{" "}
              {completeness.conflicting_evidence_count}.
            </p>
            <ul>
              {completeness.missing_items.map((item, index) => (
                <li key={`${item.category}-${index}`}>
                  {item.category}: {item.message}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>

      <section id="snapshots">
        <h2>Snapshots</h2>
        <button type="button" onClick={() => void createSnapshotAction()}>
          Crear snapshot
        </button>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Version</th>
                <th>Estado</th>
                <th>Digest</th>
                <th>Accion</th>
              </tr>
            </thead>
            <tbody>
              {snapshots.map((snapshot) => (
                <tr key={snapshot.id}>
                  <td>{snapshot.version}</td>
                  <td>{snapshot.status}</td>
                  <td>
                    <code>{snapshot.digest.slice(0, 16)}</code>
                  </td>
                  <td>
                    {snapshot.status === "DRAFT" ? (
                      <button type="button" onClick={() => void publishSnapshotAction(snapshot.id)}>
                        Publicar
                      </button>
                    ) : (
                      "Inmutable"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

function Panel({
  title,
  onSubmit,
  children,
}: {
  title: string;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  children: ReactNode;
}) {
  return (
    <form className="form-grid compact" onSubmit={onSubmit}>
      <h2 className="full">{title}</h2>
      {children}
      <button type="submit">Guardar</button>
    </form>
  );
}

function required(form: FormData, name: string) {
  return String(form.get(name) ?? "").trim();
}

function optional(form: FormData, name: string) {
  const value = required(form, name);
  return value === "" ? null : value;
}

function numberOrNull(form: FormData, name: string) {
  const value = optional(form, name);
  return value === null ? null : Number(value);
}

function csv(form: FormData, name: string) {
  return required(form, name)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
