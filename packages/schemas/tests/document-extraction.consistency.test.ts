import { describe, expect, it } from "vitest";
import schema from "../generated/document-extraction.schema.json";
import validExample from "../examples/extraction-request.valid.json";
import {
  DOCUMENT_EXTRACTION_STATUS_VALUES,
  DOCUMENT_PROCESSING_JOB_STATUS_VALUES,
  DOCUMENT_PROCESSING_STATUS_VALUES,
  EXTRACTED_SEGMENT_TYPE_VALUES,
  EXTRACTION_ERROR_CODE_VALUES,
} from "../index";
import type { ExtractionRequest } from "../index";

type SchemaDefs = Record<string, { enum?: string[]; properties?: Record<string, unknown> }>;
const defs = (schema as { $defs: SchemaDefs }).$defs;

describe("consistencia de contratos de extraccion documental", () => {
  it("los enums TypeScript coinciden con el JSON Schema", () => {
    expect([...DOCUMENT_PROCESSING_STATUS_VALUES]).toEqual(defs.DocumentProcessingStatus.enum);
    expect([...DOCUMENT_PROCESSING_JOB_STATUS_VALUES]).toEqual(
      defs.DocumentProcessingJobStatus.enum,
    );
    expect([...DOCUMENT_EXTRACTION_STATUS_VALUES]).toEqual(defs.DocumentExtractionStatus.enum);
    expect([...EXTRACTED_SEGMENT_TYPE_VALUES]).toEqual(defs.ExtractedSegmentType.enum);
    expect([...EXTRACTION_ERROR_CODE_VALUES]).toEqual(defs.ExtractionErrorCode.enum);
  });

  it("el ejemplo valido satisface el tipo TypeScript generado", () => {
    const request: ExtractionRequest = validExample as ExtractionRequest;
    expect(request.force).toBe(true);
  });
});
