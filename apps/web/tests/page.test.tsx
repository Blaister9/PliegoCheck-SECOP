// Valida que la pagina principal exponga los estados de decision y consuma
// el paquete compartido de contratos.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
  REQUIREMENT_CATEGORY_VALUES,
} from "@pliegocheck/schemas";
import Home from "../app/page";

describe("pagina principal", () => {
  it("muestra el nombre del producto y el estado de la fase", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { level: 1, name: "PliegoCheck-SECOP" })).toBeDefined();
    expect(screen.getByText("Fundación técnica — Microfase 1")).toBeDefined();
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

  it("muestra el aviso de que no existe analisis funcional", () => {
    render(<Home />);
    expect(screen.getByRole("note", { name: "Estado del proyecto" }).textContent).toContain(
      "Todavía no existe análisis funcional de procesos",
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
