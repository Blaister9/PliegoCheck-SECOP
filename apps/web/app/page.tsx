import {
  COMPANY_PROFILE_SCHEMA_VERSION,
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
    description: "Requiere consorcio, union temporal o aliado para complementar capacidad.",
  },
  {
    code: "NO_GO",
    description: "Existe incumplimiento relevante o inviabilidad.",
  },
  {
    code: "NO_CARGAR",
    description:
      "Existe una causal insubsanable o un riesgo critico que impide presentar la oferta.",
  },
  {
    code: "PENDIENTE_INFORMACION",
    description: "No hay evidencia suficiente para tomar una decision responsable.",
  },
] as const;

const ARCHITECTURE = [
  {
    name: "apps/web",
    detail: "Interfaz de usuario (Next.js + TypeScript).",
  },
  {
    name: "apps/api",
    detail: "API, inventario documental y motor deterministico de decision (FastAPI + Python).",
  },
  {
    name: "apps/worker",
    detail: "Extraccion deterministica de documentos y trabajos de procesamiento (Python).",
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
        <p className="status-badge">Perfil de empresa y evidencias - Microfase 5</p>
        <p className="lead">
          Plataforma multiagente de analisis <strong>GO / NO GO</strong> para procesos de
          contratacion publica publicados en SECOP II (Colombia). En esta fase permite crear
          procesos manualmente, adjuntar documentos originales, normalizar requisitos con evidencia
          trazable y construir perfiles de empresa con soportes y snapshots inmutables.
        </p>
        <nav className="actions" aria-label="Acciones principales">
          <Link className="button" href="/processes">
            Procesos importados
          </Link>
          <Link className="button secondary" href="/processes/new">
            Crear proceso
          </Link>
          <Link className="button secondary" href="/companies">
            Empresas
          </Link>
          <Link className="button secondary" href="/companies/new">
            Crear empresa
          </Link>
          <Link className="button secondary" href="/opportunities">
            Oportunidades SECOP
          </Link>
          <Link className="button secondary" href="/monitors">
            Monitores
          </Link>
          <Link className="button secondary" href="/alerts">
            Alertas
          </Link>
        </nav>
      </header>

      <aside className="notice" role="note" aria-label="Estado del proyecto">
        <strong>Aviso:</strong> la completitud del perfil de empresa no evalua cumplimiento contra
        procesos y no emite decisiones GO / NO GO.
      </aside>

      <section aria-labelledby="arquitectura">
        <h2 id="arquitectura">Arquitectura general</h2>
        <ul className="architecture">
          {ARCHITECTURE.map((component) => (
            <li key={component.name}>
              <code>{component.name}</code> - {component.detail}
            </li>
          ))}
        </ul>
        <p>
          La decision final la produce un motor deterministico con reglas versionadas, separado de
          los agentes de IA (ver{" "}
          <a href={`${DOCS_BASE}/docs/decision-engine.md`}>docs/decision-engine.md</a>).
        </p>
      </section>

      <section aria-labelledby="estados">
        <h2 id="estados">Estados posibles de decision</h2>
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
          categorias de requisitos. Este dato proviene del paquete compartido{" "}
          <code>@pliegocheck/schemas</code>, generado desde el modelo canonico. Perfiles de empresa
          usan <code>CompanyProfile</code> v{COMPANY_PROFILE_SCHEMA_VERSION}.
        </p>
      </section>

      <section aria-labelledby="documentacion">
        <h2 id="documentacion">Documentacion</h2>
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
          El resultado de PliegoCheck es apoyo para la decision de participar en un proceso; no
          reemplaza la revision juridica, financiera ni contractual profesional.
        </p>
      </footer>
    </main>
  );
}
