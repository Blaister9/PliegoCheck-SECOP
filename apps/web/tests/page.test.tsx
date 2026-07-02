import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
  REQUIREMENT_CATEGORY_VALUES,
} from "@pliegocheck/schemas";
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
    expect(screen.getByText("Inventario y extraccion documental - Microfase 3")).toBeDefined();
    expect(screen.getByRole("link", { name: "Procesos importados" })).toBeDefined();
    expect(screen.getByRole("link", { name: "Crear proceso" })).toBeDefined();
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
      "todavia no evalua requisitos",
    );
  });

  it("consume el paquete compartido de schemas", () => {
    render(<Home />);
    expect(NORMALIZED_REQUIREMENT_SCHEMA_VERSION).toBe("1.0.0");
    expect(REQUIREMENT_CATEGORY_VALUES.length).toBe(12);
    expect(
      screen.getAllByText(new RegExp(`v${NORMALIZED_REQUIREMENT_SCHEMA_VERSION}`)).length,
    ).toBeGreaterThan(0);
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
      .mockResolvedValueOnce(jsonResponse(processInventory()));

    render(<ProcessDetailClient processId="11111111-1111-1111-1111-111111111111" />);
    expect(await screen.findByText("Proceso de prueba")).toBeDefined();
    expect(
      screen.getByText(
        "La extraccion es deterministica y todavia no evalua requisitos ni produce una decision GO / NO GO.",
      ),
    ).toBeDefined();
    expect(screen.getByText("pliego.pdf")).toBeDefined();
    expect(screen.getByText("Estado: QUEUED")).toBeDefined();
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
      .mockResolvedValueOnce(jsonResponse(segmentList()));

    render(<ProcessDetailClient processId="11111111-1111-1111-1111-111111111111" />);
    expect(await screen.findByText("Estado: COMPLETED")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Ver segmentos" }));
    expect(await screen.findByText("Segmentos 1-1 de 1")).toBeDefined();
    expect(screen.getByText("Linea extraida <script>alert(1)</script>")).toBeDefined();
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
