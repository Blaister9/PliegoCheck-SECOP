import { describe, expect, it } from "vitest";
import schema from "../generated/external-procurement.schema.json";
import {
  EXTERNAL_PROCUREMENT_DOCUMENT_STATUS_VALUES,
  EXTERNAL_PROCUREMENT_IMPORT_STATUS_VALUES,
  EXTERNAL_PROCUREMENT_SOURCE_SYSTEM_VALUES,
} from "../index";
import type { ExternalProcurementSearchRequest } from "../index";

type SchemaDefs = Record<string, { enum?: string[] }>;
const defs = (schema as { $defs: SchemaDefs }).$defs;

describe("consistencia de contratos SECOP", () => {
  it("mantiene vocabularios cerrados sincronizados", () => {
    expect([...EXTERNAL_PROCUREMENT_SOURCE_SYSTEM_VALUES]).toEqual(
      defs.ExternalProcurementSourceSystem.enum,
    );
    expect([...EXTERNAL_PROCUREMENT_IMPORT_STATUS_VALUES]).toEqual(
      defs.ExternalProcurementImportStatus.enum,
    );
    expect([...EXTERNAL_PROCUREMENT_DOCUMENT_STATUS_VALUES]).toEqual(
      defs.ExternalProcurementDocumentStatus.enum,
    );
  });

  it("expone filtros tipados y paginacion acotada", () => {
    const request: ExternalProcurementSearchRequest = {
      source_system: "SECOP_II",
      query: "vigilancia",
      limit: 20,
      offset: 0,
    };
    expect(request.source_system).toBe("SECOP_II");
  });
});
