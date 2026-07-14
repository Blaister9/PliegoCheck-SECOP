import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ExternalDocumentSyncPanel } from "../app/processes/[id]/ExternalDocumentSyncPanel";

describe("panel de documentos externos SECOP", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn()));
  afterEach(() => vi.unstubAllGlobals());

  it("muestra inventario, estados y avisos de control", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        response({
          process_id: "11111111-1111-1111-1111-111111111111",
          available: true,
          enabled: true,
          source_system: "SECOP_II",
          external_process_link_id: "22222222-2222-2222-2222-222222222222",
          active_sync_run_id: null,
          last_sync_at: null,
          reason: null,
        }),
      )
      .mockResolvedValueOnce(
        response({ process_id: "11111111-1111-1111-1111-111111111111", items: [], total: 0 }),
      )
      .mockResolvedValueOnce(
        response({
          process_id: "11111111-1111-1111-1111-111111111111",
          total: 1,
          items: [
            {
              id: "33333333-3333-3333-3333-333333333333",
              process_id: "11111111-1111-1111-1111-111111111111",
              source_system: "SECOP_II",
              source_document_id: "DOC-1",
              source_document_reference: null,
              title: "Adenda 1.pdf",
              document_type: "pdf",
              document_category: "adenda",
              source_url: "https://files.example.gov.co/a.pdf",
              source_public_url: "https://www.datos.gov.co/resource/dmgg-8hin",
              published_at: null,
              updated_at_source: null,
              reported_size_bytes: 100,
              reported_content_type: null,
              discovery_status: "DISCOVERED",
              download_status: "NOT_REQUESTED",
              addendum_status: "POTENTIAL_ADDENDUM",
              requires_human_review: true,
              current_version_id: null,
              version_count: 0,
              first_seen_at: "2026-07-13T12:00:00Z",
              last_seen_at: "2026-07-13T12:00:00Z",
            },
          ],
        }),
      );
    render(<ExternalDocumentSyncPanel processId="11111111-1111-1111-1111-111111111111" />);
    expect(screen.getByText(/fuentes publicas externas/)).toBeDefined();
    expect(screen.getByText(/no presenta ofertas/)).toBeDefined();
    expect(screen.getByText(/requiere revision humana/)).toBeDefined();
    expect(await screen.findByText("Adenda 1.pdf")).toBeDefined();
    expect(screen.getByText(/POTENTIAL_ADDENDUM/)).toBeDefined();
    expect(
      (screen.getByRole("button", { name: "Extraer documento" }) as HTMLButtonElement).disabled,
    ).toBe(true);
  });
});

function response(payload: object): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
