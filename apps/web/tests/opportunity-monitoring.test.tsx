import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import AlertsPage from "../app/alerts/page";
import MonitorsPage from "../app/monitors/page";

const response = (body: unknown) =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

describe("monitores y alertas", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn()));
  afterEach(() => vi.unstubAllGlobals());
  it("muestra formulario, estado vacío y advertencia SECOP", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(response({ items: [], total: 0, limit: 20, offset: 0 }))
      .mockResolvedValueOnce(response({ items: [], total: 0, limit: 100, offset: 0 }));
    render(<MonitorsPage />);
    expect(await screen.findByText("No hay monitores configurados.")).toBeDefined();
    expect(screen.getByRole("note").textContent).toContain("disponibilidad de SECOP");
    expect(screen.getByRole("button", { name: "Crear monitor" })).toBeDefined();
  });
  it("lista alerta y permite marcarla leída", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        response({
          items: [
            {
              id: "a",
              monitor_id: "m",
              monitor_run_id: "r",
              opportunity_id: null,
              assessment_id: null,
              alert_type: "MONITOR_RECOVERED",
              severity: "INFO",
              status: "UNREAD",
              title: "Monitor recuperado",
              summary: "Consulta completada",
              reason_code: "MONITOR_RECOVERED",
              occurred_at: "2026-07-14T00:00:00Z",
              first_seen_at: "2026-07-14T00:00:00Z",
              last_seen_at: "2026-07-14T00:00:00Z",
              read_at: null,
              archived_at: null,
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
          disclaimer: "x",
        }),
      )
      .mockResolvedValueOnce(response({ updated_ids: ["a"], status: "READ" }))
      .mockResolvedValueOnce(
        response({ items: [], total: 0, limit: 20, offset: 0, disclaimer: "x" }),
      );
    render(<AlertsPage />);
    expect(await screen.findByText("Monitor recuperado")).toBeDefined();
    expect(screen.getByRole("note").textContent).toContain("No constituyen una recomendación");
    fireEvent.click(screen.getByRole("button", { name: "Marcar leída" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
  });
});
