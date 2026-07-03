import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  COMPANY_PROFILE_SCHEMA_VERSION,
  NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
  REQUIREMENT_CATEGORY_VALUES,
} from "@pliegocheck/schemas";
import { CompanyDetailClient } from "../app/companies/[id]/CompanyDetailClient";
import CompaniesPage from "../app/companies/page";
import NewCompanyPage from "../app/companies/new/page";
import Home from "../app/page";
import { ProcessDetailClient } from "../app/processes/[id]/ProcessDetailClient";
import ProcessesPage from "../app/processes/page";
import NewProcessPage from "../app/processes/new/page";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

beforeEach(() => {
  pushMock.mockReset();
  vi.stubGlobal("fetch", vi.fn());
});

describe("pagina principal", () => {
  it("muestra el nombre del producto y el estado de la fase", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { level: 1, name: "PliegoCheck-SECOP" })).toBeDefined();
    expect(screen.getByText("Perfil de empresa y evidencias - Microfase 5")).toBeDefined();
    expect(screen.getByRole("link", { name: "Procesos importados" })).toBeDefined();
    expect(screen.getByRole("link", { name: "Crear proceso" })).toBeDefined();
    expect(screen.getByRole("link", { name: "Empresas" })).toBeDefined();
    expect(screen.getByRole("link", { name: "Crear empresa" })).toBeDefined();
  });

  it("expone los seis estados de decision", () => {
    render(<Home />);
    for (const code of [
      "GO",
      "GO_CONDICIONADO",
      "BUSCAR_ALIADO",
      "NO_GO",
      "NO_CARGAR",
      "PENDIENTE_INFORMACION",
    ]) {
      expect(screen.getAllByText(code).length).toBeGreaterThan(0);
    }
  });

  it("muestra el aviso de que no existe analisis de requisitos", () => {
    render(<Home />);
    expect(screen.getByRole("note", { name: "Estado del proyecto" }).textContent).toContain(
      "la completitud del perfil de empresa no evalua cumplimiento",
    );
  });

  it("consume el paquete compartido de schemas", () => {
    render(<Home />);
    expect(NORMALIZED_REQUIREMENT_SCHEMA_VERSION).toBe("2.0.0");
    expect(COMPANY_PROFILE_SCHEMA_VERSION).toBe("1.0.0");
    expect(REQUIREMENT_CATEGORY_VALUES.length).toBe(12);
    expect(
      screen.getAllByText(new RegExp(`v${NORMALIZED_REQUIREMENT_SCHEMA_VERSION}`)).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(new RegExp(`v${COMPANY_PROFILE_SCHEMA_VERSION}`)).length,
    ).toBeGreaterThan(0);
  });
});

describe("empresas", () => {
  it("muestra estado vacio real", async () => {
    mockJson({ items: [], total: 0, limit: 20, offset: 0 });
    render(<CompaniesPage />);
    expect(await screen.findByText("No hay empresas registradas")).toBeDefined();
  });

  it("muestra empresas devueltas por la API con identificador enmascarado", async () => {
    mockJson({
      items: [
        {
          id: "10101010-1010-1010-1010-101010101010",
          internal_reference: "CP-20260702-ABC12345",
          legal_name: "Empresa Demo SAS",
          trade_name: null,
          tax_id_masked: "*****1234",
          tax_id_type: "NIT",
          status: "DRAFT",
          completeness_status: "INCOMPLETE",
          evidence_coverage: 0.25,
          pending_evidence_count: 2,
          updated_at: "2026-07-02T00:00:00Z",
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    });
    render(<CompaniesPage />);
    expect(await screen.findByText("Empresa Demo SAS")).toBeDefined();
    expect(screen.getByText("*****1234")).toBeDefined();
  });
});

describe("crear empresa", () => {
  it("envia formulario y redirige al detalle tras confirmacion API", async () => {
    mockJson({ id: "10101010-1010-1010-1010-101010101010" });
    render(<NewCompanyPage />);
    fireEvent.change(screen.getByLabelText("Razon social *"), {
      target: { value: "Empresa Demo SAS" },
    });
    fireEvent.change(screen.getByLabelText("NIT / identificacion"), {
      target: { value: "900123456-7" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Crear empresa" }));
    await waitFor(() =>
      expect(pushMock).toHaveBeenCalledWith("/companies/10101010-1010-1010-1010-101010101010"),
    );
  });
});

describe("detalle de empresa", () => {
  it("muestra advertencias, evidencia y snapshots sin exponer IDs completos", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse(companyDetail()))
      .mockResolvedValueOnce(jsonResponse([companyEvidence()]))
      .mockResolvedValueOnce(jsonResponse(companyCompleteness()))
      .mockResolvedValueOnce(jsonResponse([companySnapshot()]));

    render(<CompanyDetailClient companyId="10101010-1010-1010-1010-101010101010" />);
    expect(await screen.findByText("Empresa Demo SAS")).toBeDefined();
    expect(screen.getByText(/La completitud del perfil no determina/)).toBeDefined();
    expect(
      screen.getByText(/Las evaluaciones futuras utilizaran una version especifica/),
    ).toBeDefined();
    expect(screen.getByText(/NIT \*\*\*\*\*1234/)).toBeDefined();
    expect(screen.getByText("rut-demo.pdf")).toBeDefined();
    expect(screen.getByText("Estado general: READY_FOR_REVIEW - Cobertura 100%")).toBeDefined();
    expect(screen.getByText("Inmutable")).toBeDefined();
  });
});

describe("procesos importados", () => {
  it("muestra estado vacio real", async () => {
    mockJson({ items: [], total: 0, limit: 20, offset: 0 });
    render(<ProcessesPage />);
    expect(await screen.findByText("No hay procesos importados")).toBeDefined();
  });

  it("muestra procesos devueltos por la API", async () => {
    mockJson({
      items: [
        {
          id: "11111111-1111-1111-1111-111111111111",
          internal_reference: "MAN-20260702-ABC12345",
          secop_reference: "CO1",
          title: "Servicio de vigilancia",
          contracting_entity: "Entidad",
          status: "DRAFT",
          closing_at: null,
          document_count: 0,
          created_at: "2026-07-02T00:00:00Z",
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    });
    render(<ProcessesPage />);
    expect(await screen.findByText("Servicio de vigilancia")).toBeDefined();
    expect(screen.getByText("MAN-20260702-ABC12345")).toBeDefined();
  });

  it("muestra errores de API", async () => {
    mockError("API caida");
    render(<ProcessesPage />);
    expect((await screen.findByRole("alert")).textContent).toContain("API caida");
  });
});

describe("crear proceso", () => {
  it("envia formulario y redirige al detalle tras confirmacion API", async () => {
    mockJson({ id: "22222222-2222-2222-2222-222222222222" });
    render(<NewProcessPage />);
    fireEvent.change(screen.getByLabelText("Titulo *"), { target: { value: "Proceso" } });
    fireEvent.change(screen.getByLabelText("Entidad contratante *"), {
      target: { value: "Entidad" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Crear proceso" }));
    await waitFor(() =>
      expect(pushMock).toHaveBeenCalledWith("/processes/22222222-2222-2222-2222-222222222222"),
    );
  });

  it("muestra error estructurado del servidor", async () => {
    mockError("Datos invalidos", 422);
    render(<NewProcessPage />);
    fireEvent.change(screen.getByLabelText("Titulo *"), { target: { value: "Proceso" } });
    fireEvent.change(screen.getByLabelText("Entidad contratante *"), {
      target: { value: "Entidad" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Crear proceso" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Datos invalidos");
  });
});

describe("detalle de proceso", () => {
  it("muestra inventario, aviso y resultados de carga", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse(processDetail()))
      .mockResolvedValueOnce(jsonResponse(processInventory()))
      .mockResolvedValueOnce(jsonResponse(normalizationList()))
      .mockResolvedValueOnce(jsonResponse(requirementList()))
      .mockResolvedValueOnce(
        jsonResponse(
          {
            process_id: "11111111-1111-1111-1111-111111111111",
            stored_count: 1,
            rejected_count: 1,
            results: [
              { original_filename: "pliego.pdf", upload_status: "STORED", document: null },
              {
                original_filename: "pliego.exe",
                upload_status: "REJECTED",
                error: { code: "FILE_TYPE_NOT_ALLOWED", message: "Formato no permitido" },
              },
            ],
          },
          207,
        ),
      )
      .mockResolvedValueOnce(jsonResponse(processDetail()))
      .mockResolvedValueOnce(jsonResponse(processInventory()))
      .mockResolvedValueOnce(jsonResponse(normalizationList()))
      .mockResolvedValueOnce(jsonResponse(requirementList()));

    render(<ProcessDetailClient processId="11111111-1111-1111-1111-111111111111" />);
    expect(await screen.findByText("Proceso de prueba")).toBeDefined();
    expect(
      screen.getByText(
        "La extraccion es deterministica y todavia no evalua requisitos ni produce una decision GO / NO GO.",
      ),
    ).toBeDefined();
    expect(screen.getByText("pliego.pdf")).toBeDefined();
    expect(screen.getByText("Estado: QUEUED")).toBeDefined();
    expect(screen.getByText("Requisitos normalizados")).toBeDefined();
    const file = new File(["contenido"], "nuevo.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText("Documentos"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Cargar" }));
    expect(await screen.findByText("Almacenados: 1. Rechazados: 1.")).toBeDefined();
    expect(screen.getByText("pliego.exe: REJECTED (FILE_TYPE_NOT_ALLOWED)")).toBeDefined();
  });

  it("muestra preview de segmentos como texto plano", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse(processDetail()))
      .mockResolvedValueOnce(jsonResponse(processInventory("COMPLETED")))
      .mockResolvedValueOnce(jsonResponse(normalizationList()))
      .mockResolvedValueOnce(jsonResponse(requirementList()))
      .mockResolvedValueOnce(jsonResponse(segmentList()));

    render(<ProcessDetailClient processId="11111111-1111-1111-1111-111111111111" />);
    expect(await screen.findByText("Estado: COMPLETED")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Ver segmentos" }));
    expect(await screen.findByText("Segmentos 1-1 de 1")).toBeDefined();
    expect(screen.getByText("Linea extraida <script>alert(1)</script>")).toBeDefined();
  });

  it("muestra runs y detalle de evidencia de requisitos", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse(processDetail()))
      .mockResolvedValueOnce(jsonResponse(processInventory("COMPLETED")))
      .mockResolvedValueOnce(jsonResponse(normalizationList("COMPLETED")))
      .mockResolvedValueOnce(jsonResponse(requirementList()))
      .mockResolvedValueOnce(jsonResponse(requirementDetail()));

    render(<ProcessDetailClient processId="11111111-1111-1111-1111-111111111111" />);
    expect(await screen.findByText("Ultima ejecucion: COMPLETED")).toBeDefined();
    expect(
      screen.getByText("El proponente debe acreditar indice de liquidez minimo de 1.2."),
    ).toBeDefined();
    fireEvent.click(
      screen.getByRole("button", {
        name: "El proponente debe acreditar indice de liquidez minimo de 1.2.",
      }),
    );
    expect(await screen.findByText("Detalle del requisito")).toBeDefined();
    expect(screen.getByText("indice de liquidez minimo de 1.2")).toBeDefined();
  });
});

function processDetail() {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    internal_reference: "MAN-20260702-ABC12345",
    secop_reference: null,
    title: "Proceso de prueba",
    contracting_entity: "Entidad",
    description: null,
    source_url: null,
    selection_method: null,
    estimated_value: null,
    currency: "COP",
    published_at: null,
    closing_at: null,
    status: "READY_FOR_INVENTORY",
    source: "MANUAL",
    document_count: 1,
    documents: [
      {
        id: "33333333-3333-3333-3333-333333333333",
        original_filename: "pliego.pdf",
        document_type: "UNKNOWN",
        extension: ".pdf",
        size_bytes: 1024,
        sha256: "a".repeat(64),
        declared_content_type: "application/pdf",
        detected_content_type: "application/pdf",
        upload_status: "STORED",
        processing_status: "QUEUED",
        created_at: "2026-07-02T00:00:00Z",
      },
    ],
    created_at: "2026-07-02T00:00:00Z",
    updated_at: "2026-07-02T00:00:00Z",
  };
}

function processInventory(status = "QUEUED") {
  return {
    process_id: "11111111-1111-1111-1111-111111111111",
    total: 1,
    documents: [
      {
        document_id: "33333333-3333-3333-3333-333333333333",
        original_filename: "pliego.pdf",
        document_type: "UNKNOWN",
        extension: ".pdf",
        size_bytes: 1024,
        sha256: "a".repeat(64),
        declared_content_type: "application/pdf",
        detected_content_type: "application/pdf",
        upload_status: "STORED",
        processing_status: status,
        detected_format: status === "QUEUED" ? null : "pdf",
        page_count: status === "QUEUED" ? null : 1,
        sheet_count: null,
        has_text: status === "COMPLETED",
        is_encrypted: false,
        needs_ocr: false,
        contains_macros: false,
        segment_count: status === "QUEUED" ? 0 : 1,
        character_count: status === "QUEUED" ? 0 : 42,
        warnings: [],
        latest_extraction: null,
        created_at: "2026-07-02T00:00:00Z",
      },
    ],
  };
}

function segmentList() {
  return {
    extraction_id: "44444444-4444-4444-4444-444444444444",
    total: 1,
    limit: 20,
    offset: 0,
    segments: [
      {
        id: "55555555-5555-5555-5555-555555555555",
        extraction_id: "44444444-4444-4444-4444-444444444444",
        sequence: 1,
        segment_type: "TEXT_LINES",
        text: "Linea extraida <script>alert(1)</script>",
        page_number: null,
        paragraph_index: null,
        table_index: null,
        sheet_name: null,
        row_start: null,
        row_end: null,
        line_start: 1,
        line_end: 1,
        source_location: { line_start: 1, line_end: 1 },
        metadata: {},
        created_at: "2026-07-02T00:00:00Z",
      },
    ],
  };
}

function normalizationList(status = "PENDING") {
  return {
    process_id: "11111111-1111-1111-1111-111111111111",
    total: 1,
    limit: 20,
    offset: 0,
    items: [
      {
        id: "66666666-6666-6666-6666-666666666666",
        job_id: "77777777-7777-7777-7777-777777777777",
        process_id: "11111111-1111-1111-1111-111111111111",
        status,
        provider: "fake",
        model: "gpt-5.5-pro",
        reasoning_effort: "high",
        prompt_version_id: "88888888-8888-8888-8888-888888888888",
        consolidation_prompt_version_id: "99999999-9999-9999-9999-999999999999",
        input_digest: "a".repeat(64),
        source_extraction_ids: ["44444444-4444-4444-4444-444444444444"],
        segment_count: 1,
        batch_count: 1,
        candidate_count: 1,
        accepted_requirement_count: status === "COMPLETED" ? 1 : 0,
        rejected_candidate_count: 0,
        warning_count: 0,
        input_tokens: 10,
        output_tokens: 20,
        reasoning_tokens: 0,
        provider_response_ids: [],
        started_at: null,
        finished_at: null,
        error_code: null,
        error_message: null,
        created_at: "2026-07-02T00:00:00Z",
        updated_at: "2026-07-02T00:00:00Z",
      },
    ],
  };
}

function requirementList() {
  return {
    process_id: "11111111-1111-1111-1111-111111111111",
    total: 1,
    limit: 50,
    offset: 0,
    items: [requirementBase()],
  };
}

function requirementDetail() {
  return {
    ...requirementBase(),
    evidence: [
      {
        id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        requirement_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        extraction_id: "44444444-4444-4444-4444-444444444444",
        segment_id: "55555555-5555-5555-5555-555555555555",
        evidence_role: "PRIMARY",
        quoted_text: "indice de liquidez minimo de 1.2",
        quote_start: null,
        quote_end: null,
        source_location: {
          page_number: 1,
          paragraph_index: null,
          table_index: null,
          sheet_name: null,
          row_start: null,
          row_end: null,
          line_start: null,
          line_end: null,
          section: null,
        },
        validation_status: "VALID",
        created_at: "2026-07-02T00:00:00Z",
      },
    ],
    relations: [],
    run: normalizationList("COMPLETED").items[0],
    prompt_version: {
      id: "88888888-8888-8888-8888-888888888888",
      prompt_name: "requirement-normalization",
      semantic_version: "1.0.0",
      content_sha256: "b".repeat(64),
      provider: "openai",
      is_active: true,
      created_at: "2026-07-02T00:00:00Z",
    },
    documents: [],
  };
}

function requirementBase() {
  return {
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    process_id: "11111111-1111-1111-1111-111111111111",
    normalization_run_id: "66666666-6666-6666-6666-666666666666",
    stable_key: "c".repeat(64),
    category: "FINANCIAL",
    scope: "HABILITATING",
    modality: "MANDATORY",
    description: "El proponente debe acreditar indice de liquidez minimo de 1.2.",
    condition_text: null,
    expected_value: { value: 1.2, unit: null, raw_text: "1.2" },
    criticality: "UNKNOWN",
    criticality_basis: "UNKNOWN",
    subsanability: "UNKNOWN",
    subsanability_basis: "UNKNOWN",
    confidence: 0.86,
    evidence_status: "VALIDATED",
    review_status: "PENDING",
    requires_human_review: true,
    is_active: true,
    created_at: "2026-07-02T00:00:00Z",
    updated_at: "2026-07-02T00:00:00Z",
  };
}

function companyDetail() {
  return {
    id: "10101010-1010-1010-1010-101010101010",
    internal_reference: "CP-20260702-ABC12345",
    legal_name: "Empresa Demo SAS",
    trade_name: null,
    tax_id: "9001234567",
    tax_id_masked: "*****1234",
    tax_id_type: "NIT",
    company_type: "SAS",
    legal_nature: "Privada",
    incorporation_date: "2020-01-01",
    country: "CO",
    department: "Bogota",
    city: "Bogota",
    address: null,
    website: null,
    primary_email: "contacto@example.com",
    primary_phone: null,
    economic_activity_codes: ["6201"],
    status: "DRAFT",
    created_at: "2026-07-02T00:00:00Z",
    updated_at: "2026-07-02T00:00:00Z",
    archived_at: null,
    legal_registrations: [],
    rup_snapshots: [],
    unspsc_codes: [],
    financial_periods: [],
    experience_records: [],
    people: [],
    certifications: [],
    capabilities: [],
    evidence_documents: [companyEvidence()],
    evidence_links: [],
  };
}

function companyEvidence() {
  return {
    id: "20202020-2020-2020-2020-202020202020",
    company_id: "10101010-1010-1010-1010-101010101010",
    process_document_id: "30303030-3030-3030-3030-303030303030",
    evidence_type: "RUT",
    title: "rut-demo.pdf",
    original_filename: "rut-demo.pdf",
    sha256: "a".repeat(64),
    size_bytes: 1024,
    declared_content_type: "application/pdf",
    detected_content_type: "application/pdf",
    storage_uri: null,
    issued_at: null,
    expires_at: null,
    source_authority: "DIAN",
    review_status: "VERIFIED",
    processing_status: "COMPLETED",
    latest_extraction_id: "40404040-4040-4040-4040-404040404040",
    created_at: "2026-07-02T00:00:00Z",
    updated_at: "2026-07-02T00:00:00Z",
  };
}

function companyCompleteness() {
  return {
    company_id: "10101010-1010-1010-1010-101010101010",
    identity_complete: true,
    legal_registration_complete: true,
    rup_complete: true,
    financial_complete: true,
    experience_complete: true,
    personnel_complete: true,
    certifications_complete: true,
    evidence_coverage: 1,
    expired_evidence_count: 0,
    unsupported_record_count: 0,
    conflicting_evidence_count: 0,
    missing_items: [],
    ready_for_review: true,
    generated_at: "2026-07-02T00:00:00Z",
  };
}

function companySnapshot() {
  return {
    id: "50505050-5050-5050-5050-505050505050",
    company_id: "10101010-1010-1010-1010-101010101010",
    version: 1,
    status: "PUBLISHED",
    digest: "b".repeat(64),
    completeness_status: "READY_FOR_REVIEW",
    created_at: "2026-07-02T00:00:00Z",
    published_at: "2026-07-02T00:00:00Z",
  };
}

function mockJson(payload: unknown) {
  vi.mocked(fetch).mockResolvedValue(jsonResponse(payload));
}

function mockError(message: string, status = 500) {
  vi.mocked(fetch).mockResolvedValue(
    jsonResponse({ code: "DATABASE_ERROR", message, details: {} }, status, false),
  );
}

function jsonResponse(payload: unknown, status = 200, ok = status < 400) {
  return {
    ok,
    status,
    json: async () => payload,
  } as Response;
}
