// Verifica que los artefactos generados del piloto permanezcan consistentes.
import { describe, expect, it } from "vitest";
import schema from "../generated/pilot.schema.json";
import validSummary from "../examples/pilot-run-summary.valid.json";
import { PILOT_STEP_NAME_VALUES, PILOT_STEP_STATE_VALUES } from "../index";
import type { PilotRunSummary } from "../index";

type SchemaDefs = Record<string, { enum?: string[]; required?: string[] }>;
const defs = (schema as { $defs: SchemaDefs }).$defs;

describe("consistencia de contratos de piloto", () => {
  it("los enums TypeScript coinciden con el JSON Schema", () => {
    expect([...PILOT_STEP_NAME_VALUES]).toEqual(defs.PilotStepName.enum);
    expect([...PILOT_STEP_STATE_VALUES]).toEqual(defs.PilotStepState.enum);
  });

  it("el ejemplo valido satisface el tipo generado", () => {
    const summary: PilotRunSummary = validSummary as PilotRunSummary;
    expect(summary.decision_outcome).toBe("PENDIENTE_INFORMACION");
    expect(summary.synthetic_data_only).toBe(true);
    expect(defs.PilotRunSummary.required).toContain("duration_seconds");
  });
});
