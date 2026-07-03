// Verifica que los artefactos generados de normalizacion permanezcan sincronizados.
import { describe, expect, it } from "vitest";
import schema from "../generated/requirement-normalization.schema.json";
import validExample from "../examples/normalized-requirement.valid.json";
import {
  NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
  REQUIREMENT_CATEGORY_VALUES,
  REQUIREMENT_CRITICALITY_VALUES,
  REQUIREMENT_EVIDENCE_STATUS_VALUES,
  REQUIREMENT_MODALITY_VALUES,
  REQUIREMENT_NORMALIZATION_STATUS_VALUES,
  REQUIREMENT_SCOPE_VALUES,
  REQUIREMENT_SUBSANABILITY_VALUES,
} from "../index";
import type { NormalizedRequirement, RequirementNormalizationAgentOutput } from "../index";

type SchemaDefs = Record<string, { enum?: string[]; required?: string[] }>;
const defs = (schema as { $defs: SchemaDefs }).$defs;

describe("consistencia de normalizacion de requisitos", () => {
  it("los enums TypeScript coinciden con el JSON Schema", () => {
    expect([...REQUIREMENT_CATEGORY_VALUES]).toEqual(defs.RequirementCategory.enum);
    expect([...REQUIREMENT_SCOPE_VALUES]).toEqual(defs.RequirementScope.enum);
    expect([...REQUIREMENT_MODALITY_VALUES]).toEqual(defs.RequirementModality.enum);
    expect([...REQUIREMENT_CRITICALITY_VALUES]).toEqual(defs.RequirementCriticality.enum);
    expect([...REQUIREMENT_SUBSANABILITY_VALUES]).toEqual(defs.RequirementSubsanability.enum);
    expect([...REQUIREMENT_EVIDENCE_STATUS_VALUES]).toEqual(defs.RequirementEvidenceStatus.enum);
    expect([...REQUIREMENT_NORMALIZATION_STATUS_VALUES]).toEqual(
      defs.RequirementNormalizationStatus.enum,
    );
  });

  it("el contrato de agente no permite campos adicionales", () => {
    const agentSchema = defs.RequirementNormalizationAgentOutput as {
      additionalProperties?: boolean;
      required?: string[];
    };
    expect(agentSchema.additionalProperties).toBe(false);
    expect(agentSchema.required).toContain("candidates");
  });

  it("el ejemplo valido satisface el tipo TypeScript generado", () => {
    const requirement: NormalizedRequirement = validExample as NormalizedRequirement;
    expect(NORMALIZED_REQUIREMENT_SCHEMA_VERSION).toBe("2.0.0");
    expect(requirement.review_status).toBe("PENDING");
    expect(REQUIREMENT_CATEGORY_VALUES).toContain(requirement.category);
  });

  it("la salida del agente no incluye decision de cumplimiento", () => {
    const output: RequirementNormalizationAgentOutput = {
      schema_version: "2.0.0",
      agent: "RequirementNormalizationAgent",
      prompt_version: "1.0.0",
      process_id: "22222222-2222-2222-2222-222222222222",
      batch_index: 0,
      candidates: [],
      warnings: [],
    };
    expect(JSON.stringify(output)).not.toContain("GO");
  });
});
