import {
  NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
  REQUIREMENT_CATEGORY_VALUES,
} from "@pliegocheck/schemas";
import Link from "next/link";

const DOCS_BASE = "https://github.com/Blaister9/PliegoCheck-SECOP/blob/main";

const DECISION_STATES = [
  {
    code: "GO",
    description: "No se detectan bloqueos con la evidencia disponible.",
  },
  {
    code: "GO_CONDICIONADO",
    description: "Puede participar si completa acciones o soportes pendientes.",
  },
  {
    code: "BUSCAR_ALIADO",
    description: "Requiere consorcio, unión temporal o aliado para complementar capacidad.",
  },
  {
    code: "NO_GO",
    description: "Existe incumplimiento relevante o inviabilidad.",
  },
  {
    code: "NO_CARGAR",
    description:
      "Existe una causal insubsanable o un riesgo crítico que impide presentar la oferta.",
  },
  {
    code: "PENDIENTE_INFORMACION",
    description: "No hay evidencia suficiente para tomar una decisión responsable.",
  },
] as const;

const ARCHITECTURE = [
  {
    name: "apps/web",
    detail: "Interfaz de usuario (Next.js + TypeScript).",
  },
  {
    name: "apps/api",
    detail: "API y motor determinístico de decisión (FastAPI + Python).",
  },
  {
    name: "apps/worker",
    detail: "Procesamiento asíncrono de documentos y agentes (Python, aún sin cola real).",
  },
  {
    name: "packages/schemas",
    detail: "Contratos compartidos y versionados entre frontend, API y worker.",
  },
] as const;

export default function Home() {
  return (
    <main className="container">
      <header>
        <h1>PliegoCheck-SECOP</h1>
        <p className="status-badge">Importación manual — Microfase 2</p>
        <p className="lead">
          Plataforma multiagente de análisis <strong>GO / NO GO</strong> para procesos de
          contratación pública publicados en SECOP II (Colombia). En esta fase permite crear
          procesos manualmente y adjuntar documentos originales para inventario inicial.
        </p>
        <nav className="actions" aria-label="Acciones principales">
          <Link className="button" href="/processes">
            Procesos importados
          </Link>
          <Link className="button secondary" href="/processes/new">
            Crear proceso
          </Link>
        </nav>
      </header>

      <aside className="notice" role="note" aria-label="Estado del proyecto">
        <strong>Aviso:</strong> los documentos todavía no se extraen ni analizan. No se consultan
        datos de SECOP II y no se emiten decisiones GO / NO GO.
      </aside>

      <section aria-labelledby="arquitectura">
        <h2 id="arquitectura">Arquitectura general</h2>
        <ul className="architecture">
          {ARCHITECTURE.map((component) => (
            <li key={component.name}>
              <code>{component.name}</code> — {component.detail}
            </li>
          ))}
        </ul>
        <p>
          La decisión final la produce un motor determinístico con reglas versionadas, separado de
          los agentes de IA (ver{" "}
          <a href={`${DOCS_BASE}/docs/decision-engine.md`}>docs/decision-engine.md</a>).
        </p>
      </section>

      <section aria-labelledby="estados">
        <h2 id="estados">Estados posibles de decisión</h2>
        <dl className="decision-states">
          {DECISION_STATES.map((state) => (
            <div key={state.code} className="decision-state">
              <dt>
                <code>{state.code}</code>
              </dt>
              <dd>{state.description}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="contratos">
        <h2 id="contratos">Contratos compartidos</h2>
        <p>
          Primer contrato versionado: <code>NormalizedRequirement</code> v
          {NORMALIZED_REQUIREMENT_SCHEMA_VERSION}, con {REQUIREMENT_CATEGORY_VALUES.length}{" "}
          categorías de requisitos. Este dato proviene del paquete compartido{" "}
          <code>@pliegocheck/schemas</code>, generado desde el modelo canónico.
        </p>
      </section>

      <section aria-labelledby="documentacion">
        <h2 id="documentacion">Documentación</h2>
        <ul>
          <li>
            <a href={`${DOCS_BASE}/README.md`}>README del proyecto</a>
          </li>
          <li>
            <a href={`${DOCS_BASE}/docs/ADR-001-stack-and-architecture.md`}>
              Arquitectura y stack (ADR-001)
            </a>
          </li>
          <li>
            <a href={`${DOCS_BASE}/docs/roadmap.md`}>Roadmap por microfases</a>
          </li>
        </ul>
      </section>

      <footer>
        <p>
          El resultado de PliegoCheck es apoyo para la decisión de participar en un proceso; no
          reemplaza la revisión jurídica, financiera ni contractual profesional.
        </p>
      </footer>
    </main>
  );
}
