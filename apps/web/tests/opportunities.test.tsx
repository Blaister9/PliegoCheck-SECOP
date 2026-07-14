import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import OpportunitiesPage from "../app/opportunities/page";

describe("bandeja de oportunidades", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn()));
  afterEach(() => vi.unstubAllGlobals());

  it("selecciona empresa y snapshot, descubre, ordena y abre detalle", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(response(companies()))
      .mockResolvedValueOnce(response(snapshots()))
      .mockResolvedValueOnce(response({ ...inbox(), items: [], total: 0 }))
      .mockResolvedValueOnce(response({ ...inbox(), items: [], total: 0 }))
      .mockResolvedValueOnce(response(discovery()))
      .mockResolvedValueOnce(response(inbox()));
    render(<OpportunitiesPage />);
    fireEvent.change(await screen.findByLabelText("Empresa"), { target: { value: "company-1" } });
    fireEvent.change(await screen.findByLabelText("Snapshot publicado"), {
      target: { value: "snapshot-1" },
    });
    await screen.findByText("No se encontraron oportunidades con estos filtros.");
    fireEvent.change(screen.getByLabelText("Orden"), { target: { value: "compatibility" } });
    fireEvent.click(screen.getByRole("button", { name: "Descubrir oportunidades" }));
    expect(await screen.findByText("Interventoria fixture")).toBeDefined();
    expect(screen.getByText(/Compatibilidad:/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Ver detalle" }));
    expect(screen.getByRole("region", { name: "Detalle de oportunidad" })).toBeDefined();
    expect(screen.getByText(/Coincidencia fuerte/)).toBeDefined();
  });

  it("muestra carga y estado vacio", async () => {
    let resolveDiscovery!: (value: Response) => void;
    vi.mocked(fetch)
      .mockResolvedValueOnce(response(companies()))
      .mockResolvedValueOnce(response(snapshots()))
      .mockResolvedValueOnce(response({ ...inbox(), items: [], total: 0 }))
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveDiscovery = resolve;
          }),
      )
      .mockResolvedValueOnce(response({ ...inbox(), items: [], total: 0 }));
    render(<OpportunitiesPage />);
    fireEvent.change(await screen.findByLabelText("Empresa"), { target: { value: "company-1" } });
    fireEvent.change(await screen.findByLabelText("Snapshot publicado"), {
      target: { value: "snapshot-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Descubrir oportunidades" }));
    expect(screen.getByRole("button", { name: "Consultando…" })).toBeDefined();
    resolveDiscovery(response(discovery()));
    expect(
      await screen.findByText("No se encontraron oportunidades con estos filtros."),
    ).toBeDefined();
  });

  it("muestra error de API", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(response(companies()))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ message: "Fallo controlado" }), {
          status: 500,
          headers: { "Content-Type": "application/json" },
        }),
      );
    render(<OpportunitiesPage />);
    fireEvent.change(await screen.findByLabelText("Empresa"), { target: { value: "company-1" } });
    expect(await screen.findByRole("alert")).toBeDefined();
  });

  it("incluye aviso obligatorio y lenguaje de revisión", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(response(companies()));
    render(<OpportunitiesPage />);
    expect(screen.getByRole("note").textContent).toContain("compatibilidad preliminar");
    expect(screen.getByRole("note").textContent).toContain("revisión humana");
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  });
});

function response(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
function companies() {
  return {
    items: [
      {
        id: "company-1",
        legal_name: "Empresa fixture",
        trade_name: null,
        internal_reference: "CP-1",
        tax_id_masked: null,
        tax_id_type: null,
        status: "ACTIVE",
        completeness_status: "COMPLETE",
        evidence_coverage: 100,
        pending_evidence_count: 0,
        updated_at: "2026-07-13T12:00:00Z",
      },
    ],
    total: 1,
    limit: 100,
    offset: 0,
  };
}
function snapshots() {
  return [
    {
      id: "snapshot-1",
      company_id: "company-1",
      version: 1,
      status: "PUBLISHED",
      digest: "a".repeat(64),
      completeness_status: "COMPLETE",
      created_at: "2026-07-13T12:00:00Z",
      published_at: "2026-07-13T12:00:00Z",
    },
  ];
}
function discovery() {
  return {
    reused: false,
    run: {
      id: "run-1",
      company_profile_id: "company-1",
      company_snapshot_id: "snapshot-1",
      policy_version: "1.0.0",
      policy_hash: "b".repeat(64),
      status: "COMPLETED",
      effective_at: "2026-07-13T12:00:00Z",
      input_digest: "c".repeat(64),
      candidate_count: 1,
      assessed_count: 1,
      warning_count: 0,
      created_at: "2026-07-13T12:00:00Z",
    },
  };
}
function inbox() {
  return {
    items: [
      {
        id: "opp-1",
        candidate_id: "candidate-1",
        company_snapshot_id: "snapshot-1",
        policy_version: "1.0.0",
        policy_hash: "b".repeat(64),
        analysis_level: "METADATA_SCREENING",
        outcome: "REVISAR_PRIMERO",
        compatibility_score: 82,
        urgency_score: 50,
        information_completeness: 90,
        days_remaining: 10,
        urgency_status: "NORMAL",
        requires_human_review: true,
        input_digest: "d".repeat(64),
        summary: "Revisión prioritaria explicable.",
        warnings: [],
        missing_information: {},
        partner_reasons: [],
        effective_at: "2026-07-13T12:00:00Z",
        created_at: "2026-07-13T12:00:00Z",
        latest_review_action: null,
        candidate: {
          id: "candidate-1",
          discovery_run_id: "run-1",
          external_search_result_id: "source-1",
          process_id: null,
          source_system: "SECOP_II",
          source_process_id: "fixture",
          source_reference: "fixture",
          title: "Interventoria fixture",
          entity_name: "Entidad fixture",
          modality: "Licitacion",
          source_status: "Publicado",
          publication_date: "2026-07-12T12:00:00Z",
          closing_date: "2026-07-23T12:00:00Z",
          estimated_value: 100000000,
          currency: "COP",
          department: "Cundinamarca",
          municipality: "Bogota",
          document_status: "DOCUMENT_LINKS_AVAILABLE",
          created_at: "2026-07-13T12:00:00Z",
        },
        components: [
          {
            component: "RELEVANCE",
            status: "STRONG_MATCH",
            score: 100,
            weight: 0.22,
            weighted_score: 22,
            reason_code: "TEXT_STRONG_MATCH",
            explanation: "Coincidencia fuerte por objeto contractual.",
            explanation_parameters: {},
            evidence_refs: [],
            warnings: [],
            evidence: [],
          },
        ],
      },
    ],
    total: 1,
    limit: 20,
    offset: 0,
    disclaimer: "compatibilidad preliminar",
  };
}
