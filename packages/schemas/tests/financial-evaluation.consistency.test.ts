import { describe, expect, it } from "vitest";
import schema from "../generated/financial-evaluation.schema.json";
import {
  FINANCIAL_EVALUATION_RESULT_STATUS_VALUES,
  FINANCIAL_EVALUATION_REVIEW_STATUS_VALUES,
  FINANCIAL_EVALUATION_SCHEMA_VERSION,
  FINANCIAL_OPERATOR_VALUES,
  FINANCIAL_RULE_MAPPING_STATUS_VALUES,
} from "../index";
import type { FinancialEvaluationRequest, FinancialEvaluationResultReviewRequest } from "../index";

type SchemaDefs = Record<string, { enum?: string[]; required?: string[] }>;
const defs = (schema as { $defs: SchemaDefs }).$defs;

describe("financial evaluation generated contracts", () => {
  it("exports runtime enums and stable schema version", () => {
    expect(FINANCIAL_EVALUATION_SCHEMA_VERSION).toBe("1.0.0");
    expect([...FINANCIAL_EVALUATION_RESULT_STATUS_VALUES]).toEqual(
      defs.FinancialEvaluationResultStatus.enum,
    );
    expect([...FINANCIAL_EVALUATION_REVIEW_STATUS_VALUES]).toContain("OVERRIDDEN");
    expect([...FINANCIAL_RULE_MAPPING_STATUS_VALUES]).toContain("AMBIGUOUS");
    expect([...FINANCIAL_OPERATOR_VALUES]).toContain("GREATER_THAN_OR_EQUAL");
  });

  it("types queue and review payloads without GO/NO_GO decisions", () => {
    const request: FinancialEvaluationRequest = {
      normalization_run_id: "00000000-0000-0000-0000-000000000001",
      company_id: "00000000-0000-0000-0000-000000000002",
      company_profile_snapshot_id: "00000000-0000-0000-0000-000000000003",
      force: false,
    };
    const review: FinancialEvaluationResultReviewRequest = {
      review_status: "CONFIRMED",
      override_result: null,
      override_reason: null,
      review_notes: null,
    };
    expect(JSON.stringify({ request, review })).not.toContain("GO");
  });
});
