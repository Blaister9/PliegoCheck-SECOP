import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import NotificationDeliveriesPage from "../app/notification-deliveries/page";
import NotificationOperationsPage from "../app/operations/notifications/page";
import NotificationSettingsPage from "../app/settings/notifications/page";

const response = (body: unknown) =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

describe("entrega de notificaciones", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn()));
  afterEach(() => vi.unstubAllGlobals());
  it("muestra preferencias, avisos y destino vacío", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(response({ items: [], total: 0 }))
      .mockResolvedValueOnce(response({ items: [], total: 0 }));
    render(<NotificationSettingsPage />);
    expect(await screen.findByText("No hay destinos configurados.")).toBeDefined();
    expect(screen.getAllByRole("note")[0].textContent).toContain("deshabilitada por defecto");
  });
  it("muestra historial vacío y conserva alerta interna", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(response({ items: [], total: 0, limit: 50, offset: 0 }));
    render(<NotificationDeliveriesPage />);
    expect(await screen.findByText("No hay entregas registradas.")).toBeDefined();
    expect(screen.getByRole("note").textContent).toContain("alerta interna");
  });
  it("muestra readiness operativo", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        response({
          external_delivery_enabled: false,
          dry_run: true,
          email_enabled: false,
          webhook_enabled: false,
          pending_count: 0,
          processing_count: 0,
          retryable_count: 0,
          permanent_failure_count: 0,
          delivered_last_24h: 0,
          suppressed_last_24h: 0,
          reasons: [],
        }),
      )
      .mockResolvedValueOnce(
        response({ by_status: {}, by_channel: {}, generated_at: "2026-07-14T00:00:00Z" }),
      );
    render(<NotificationOperationsPage />);
    expect(await screen.findByText(/Entrega externa deshabilitada/)).toBeDefined();
  });
  it("crea un destino y refresca el formulario tras la respuesta asíncrona", async () => {
    const destination = {
      id: "11111111-1111-4111-8111-111111111111",
      owner_actor_id: null,
      channel: "EMAIL_SMTP",
      name: "Mailpit sintético",
      status: "ACTIVE",
      masked_destination: "p***@example.test",
      verified_at: null,
      last_tested_at: null,
      last_test_status: null,
      created_at: "2026-07-14T00:00:00Z",
      updated_at: "2026-07-14T00:00:00Z",
      configuration: {},
      secret_configured: false,
    };
    vi.mocked(fetch)
      .mockResolvedValueOnce(response({ items: [], total: 0 }))
      .mockResolvedValueOnce(response({ items: [], total: 0 }))
      .mockResolvedValueOnce(response(destination))
      .mockResolvedValueOnce(response({ items: [destination], total: 1 }))
      .mockResolvedValueOnce(response({ items: [], total: 0 }));
    render(<NotificationSettingsPage />);
    await screen.findByText("No hay destinos configurados.");
    fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: destination.name } });
    fireEvent.change(screen.getByLabelText("Correo o URL"), {
      target: { value: "pilot@example.test" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Crear destino" }));
    expect(await screen.findAllByText(destination.name)).toHaveLength(2);
    await waitFor(() => expect(screen.getByLabelText("Nombre")).toHaveProperty("value", ""));
  });
});
