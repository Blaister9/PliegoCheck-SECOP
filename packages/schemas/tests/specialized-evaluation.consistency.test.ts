import {
  SPECIALIZED_EVALUATION_DOMAIN_VALUES,
  SPECIALIZED_EVALUATION_RESULT_STATUS_VALUES,
} from "../generated/specialized-evaluation.enums";
import { describe, expect, it } from "vitest";

describe("specialized evaluation generated contracts", () => {
  it("exports deterministic domains", () => {
    expect(SPECIALIZED_EVALUATION_DOMAIN_VALUES).toContain("LEGAL");
    expect(SPECIALIZED_EVALUATION_DOMAIN_VALUES).toContain("EXPERIENCE");
    expect(SPECIALIZED_EVALUATION_DOMAIN_VALUES).toContain("TECHNICAL");
  });

  it("keeps uncertainty explicit", () => {
    expect(SPECIALIZED_EVALUATION_RESULT_STATUS_VALUES).toContain("UNKNOWN");
    expect(SPECIALIZED_EVALUATION_RESULT_STATUS_VALUES).toContain("CONFLICTING_EVIDENCE");
  });
});
