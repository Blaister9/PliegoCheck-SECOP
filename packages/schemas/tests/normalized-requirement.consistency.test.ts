// Verifica que los artefactos generados (JSON Schema, constantes TypeScript)
// permanezcan consistentes entre si y con los ejemplos versionados.
import { describe, expect, it } from "vitest";
import schema from "../generated/normalized-requirement.schema.json";
import validExample from "../examples/normalized-requirement.valid.json";
import {
  NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
  REQUIREMENT_CATEGORY_VALUES,
  REQUIREMENT_CRITICALITY_VALUES,
  REQUIREMENT_STATUS_VALUES,
  REQUIREMENT_SUBSANABILITY_VALUES,
} from "../index";
import type { NormalizedRequirement } from "../index";

type SchemaDefs = Record<string, { enum?: string[] }>;
const defs = (schema as { $defs: SchemaDefs }).$defs;

describe("consistencia de artefactos generados", () => {
  it("los enums TypeScript coinciden con el JSON Schema", () => {
    expect([...REQUIREMENT_CATEGORY_VALUES]).toEqual(defs.RequirementCategory.enum);
    expect([...REQUIREMENT_STATUS_VALUES]).toEqual(defs.RequirementStatus.enum);
    expect([...REQUIREMENT_CRITICALITY_VALUES]).toEqual(defs.RequirementCriticality.enum);
    expect([...REQUIREMENT_SUBSANABILITY_VALUES]).toEqual(defs.RequirementSubsanability.enum);
  });

  it("el JSON Schema declara obligatorios todos los campos de primer nivel", () => {
    const required = (schema as { required: string[] }).required;
    expect(required).toContain("schema_version");
    expect(required).toContain("requirement_id");
    expect(required).toContain("status");
    expect(required).toContain("confidence");
    expect(required).toContain("requires_human_review");
  });

  it("el ejemplo valido satisface el tipo TypeScript generado", () => {
    // Asignacion tipada: si el tipo generado divergiera del ejemplo, tsc fallaria.
    const requirement: NormalizedRequirement = validExample as NormalizedRequirement;
    expect(requirement.schema_version).toBe(NORMALIZED_REQUIREMENT_SCHEMA_VERSION);
    expect(requirement.requirement_id).toBe("REQ-001");
    expect(REQUIREMENT_STATUS_VALUES).toContain(requirement.status);
  });
});
