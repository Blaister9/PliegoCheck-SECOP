// Verifica que los artefactos generados de decision permanezcan consistentes.
import { describe, expect, it } from "vitest";
import schema from "../generated/decision.schema.json";
import validRequest from "../examples/decision-request.valid.json";
import {
  DECISION_OUTCOME_VALUES,
  DECISION_REASON_CODE_VALUES,
  DECISION_RULE_STATUS_VALUES,
  DECISION_ACTION_STATUS_VALUES,
} from "../index";
import type { DecisionRequest } from "../index";

type SchemaDefs = Record<string, { enum?: string[]; required?: string[] }>;
const defs = (schema as { $defs: SchemaDefs }).$defs;

describe("consistencia de contratos de decision", () => {
  it("los enums TypeScript coinciden con el JSON Schema", () => {
    expect([...DECISION_OUTCOME_VALUES]).toEqual(defs.DecisionOutcome.enum);
    expect([...DECISION_RULE_STATUS_VALUES]).toEqual(defs.DecisionRuleStatus.enum);
    expect([...DECISION_ACTION_STATUS_VALUES]).toEqual(defs.DecisionActionStatus.enum);
    expect([...DECISION_REASON_CODE_VALUES]).toEqual(defs.DecisionReasonCode.enum);
  });

  it("la precedencia cubre los seis resultados", () => {
    expect(DECISION_OUTCOME_VALUES.length).toBe(6);
    expect(DECISION_OUTCOME_VALUES).toContain("NO_CARGAR");
    expect(DECISION_OUTCOME_VALUES).toContain("PENDIENTE_INFORMACION");
  });

  it("el ejemplo valido satisface el tipo generado", () => {
    const request: DecisionRequest = validRequest as DecisionRequest;
    expect(request.force).toBe(false);
    expect(defs.DecisionRequest.required).toContain("normalization_run_id");
    expect(defs.DecisionRequest.required).toContain("financial_evaluation_run_id");
  });
});
