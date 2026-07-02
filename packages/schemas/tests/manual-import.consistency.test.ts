// Verifica que los artefactos generados de importacion manual conserven
// campos de dominio que podrian confundirse con metadatos JSON Schema.
import { describe, expect, it } from "vitest";
import schema from "../generated/manual-import.schema.json";
import validExample from "../examples/process-create.valid.json";
import {
  DOCUMENT_TYPE_VALUES,
  DOCUMENT_UPLOAD_STATUS_VALUES,
  PROCESS_SOURCE_VALUES,
  PROCESS_STATUS_VALUES,
  UPLOAD_ERROR_CODE_VALUES,
} from "../index";
import type { ProcessCreate } from "../index";

type SchemaDefs = Record<string, { enum?: string[]; properties?: Record<string, unknown> }>;
const defs = (schema as { $defs: SchemaDefs }).$defs;

describe("consistencia de contratos de importacion manual", () => {
  it("los enums TypeScript coinciden con el JSON Schema", () => {
    expect([...PROCESS_SOURCE_VALUES]).toEqual(defs.ProcessSource.enum);
    expect([...PROCESS_STATUS_VALUES]).toEqual(defs.ProcessStatus.enum);
    expect([...DOCUMENT_TYPE_VALUES]).toEqual(defs.DocumentType.enum);
    expect([...DOCUMENT_UPLOAD_STATUS_VALUES]).toEqual(defs.DocumentUploadStatus.enum);
    expect([...UPLOAD_ERROR_CODE_VALUES]).toEqual(defs.UploadErrorCode.enum);
  });

  it("conserva title como campo de dominio en ProcessCreate", () => {
    expect(defs.ProcessCreate.properties).toHaveProperty("title");
  });

  it("el ejemplo valido satisface el tipo TypeScript generado", () => {
    const process: ProcessCreate = validExample as ProcessCreate;
    expect(process.title).toBe("Servicio de vigilancia judicial");
    expect(process.contracting_entity).toBe("Entidad de ejemplo");
  });
});
