import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SecopImportPage from "../app/processes/import/page";

describe("busqueda e importacion SECOP", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn()));
  afterEach(() => vi.unstubAllGlobals());

  it("muestra formulario, fuentes y avisos obligatorios", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(response(sources()));
    render(<SecopImportPage />);
    expect(screen.getByText(/fuentes públicas externas/)).toBeDefined();
    expect(screen.getByText(/sujetos a cambios/)).toBeDefined();
    expect(screen.getByText(/no ejecuta evaluación automática/)).toBeDefined();
    expect(
      screen.getByText(/no presenta ofertas ni realiza trámites transaccionales/),
    ).toBeDefined();
    expect(await screen.findByRole("option", { name: /SECOP II/ })).toBeDefined();
    expect(screen.getByLabelText("Palabra clave")).toBeDefined();
    expect(screen.getByLabelText("Entidad")).toBeDefined();
    expect(screen.getByLabelText("Publicado desde")).toBeDefined();
  });

  it("renderiza resultados normalizados sin payload crudo", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(response(sources()))
      .mockResolvedValueOnce(response(searchResponse()));
    render(<SecopImportPage />);
    await screen.findByRole("option", { name: /SECOP II/ });
    fireEvent.change(screen.getByLabelText("Palabra clave"), {
      target: { value: "vigilancia" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    expect(await screen.findByText("Servicio de vigilancia fixture")).toBeDefined();
    expect(screen.getByText("ENTIDAD PUBLICA FIXTURE")).toBeDefined();
    expect(screen.getByRole("link", { name: "Abrir fuente oficial" })).toBeDefined();
    expect(screen.queryByText("raw_payload")).toBeNull();
  });

  it("importa y permite navegar al proceso interno", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(response(sources()))
      .mockResolvedValueOnce(response(searchResponse()))
      .mockResolvedValueOnce(
        response({
          id: "44444444-4444-4444-4444-444444444444",
          source_result_id: "22222222-2222-2222-2222-222222222222",
          process_id: "33333333-3333-3333-3333-333333333333",
          status: "IMPORTED",
          deduplication_key: "a".repeat(64),
          imported_at: "2026-07-13T12:00:00Z",
          created_at: "2026-07-13T12:00:00Z",
          message: "Importado",
        }),
      );
    render(<SecopImportPage />);
    await screen.findByRole("option", { name: /SECOP II/ });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    fireEvent.click(await screen.findByRole("button", { name: "Importar proceso" }));
    const link = await screen.findByRole("link", { name: "Ver proceso interno" });
    expect(link.getAttribute("href")).toBe("/processes/33333333-3333-3333-3333-333333333333");
  });

  it("muestra el estado vacio", async () => {
    const empty = searchResponse();
    empty.items = [];
    empty.search.result_count = 0;
    vi.mocked(fetch)
      .mockResolvedValueOnce(response(sources()))
      .mockResolvedValueOnce(response(empty));
    render(<SecopImportPage />);
    await screen.findByRole("option", { name: /SECOP II/ });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    expect(await screen.findByText("No se encontraron procesos.")).toBeDefined();
    await waitFor(() => expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2));
  });

  it("mantiene siguiente cuando la fuente entrego una pagina completa", async () => {
    const page = searchResponse();
    page.search.source_row_count = 20;
    vi.mocked(fetch)
      .mockResolvedValueOnce(response(sources()))
      .mockResolvedValueOnce(response(page));
    render(<SecopImportPage />);
    await screen.findByRole("option", { name: /SECOP II/ });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    const next = await screen.findByRole("button", { name: "Siguiente" });
    expect((next as HTMLButtonElement).disabled).toBe(false);
  });
});

function sources() {
  return [
    {
      id: "11111111-1111-1111-1111-111111111111",
      source_system: "SECOP_II",
      provider: "datos_abiertos",
      name: "SECOP II - Procesos de Contratacion",
      base_url: "https://www.datos.gov.co",
      dataset_id: "p6dx-8zbt",
      human_url: "https://www.datos.gov.co/d/p6dx-8zbt",
      api_url: "https://www.datos.gov.co/resource/p6dx-8zbt.json",
      status: "AVAILABLE",
      enabled: true,
      last_checked_at: null,
      metadata: {},
      created_at: "2026-07-13T12:00:00Z",
      updated_at: "2026-07-13T12:00:00Z",
    },
  ];
}

function searchResponse() {
  return {
    search: {
      id: "55555555-5555-5555-5555-555555555555",
      source_id: "11111111-1111-1111-1111-111111111111",
      source_system: "SECOP_II",
      query: null,
      filters: {},
      status: "COMPLETED",
      result_count: 1,
      source_row_count: 1,
      page_count: 1,
      limit: 20,
      offset: 0,
      unsupported_filters: [],
      warnings: [],
      started_at: "2026-07-13T12:00:00Z",
      finished_at: "2026-07-13T12:00:01Z",
      error_code: null,
      error_message: null,
      created_at: "2026-07-13T12:00:00Z",
    },
    items: [
      {
        id: "22222222-2222-2222-2222-222222222222",
        search_id: "55555555-5555-5555-5555-555555555555",
        source_id: "11111111-1111-1111-1111-111111111111",
        source_system: "SECOP_II",
        source_dataset: "p6dx-8zbt",
        source_process_id: "CO1.REQ.FIXTURE",
        source_process_reference: "LP-FIXTURE",
        title: "Servicio de vigilancia fixture",
        entity_name: "ENTIDAD PUBLICA FIXTURE",
        modality: "Licitacion publica",
        status: "Publicado",
        estimated_value: "1000000.00",
        currency: "COP",
        publication_date: "2026-07-01T00:00:00-05:00",
        closing_date: null,
        department: "Bogota D.C.",
        municipality: "Bogota",
        source_url: "https://community.secop.gov.co/Public/Tendering/fixture",
        documents_status: "DOCUMENT_LINKS_AVAILABLE",
        raw_payload_hash: "a".repeat(64),
        field_statuses: {},
        warnings: [],
        import_status: "PENDING",
        process_id: null,
        created_at: "2026-07-13T12:00:00Z",
      },
    ],
  };
}

function response(payload: unknown, status = 200) {
  return { ok: status < 400, status, json: async () => payload } as Response;
}
