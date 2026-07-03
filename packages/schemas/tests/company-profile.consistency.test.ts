import { describe, expect, it } from "vitest";
import type {
  CompanyProfileCreate,
  CompanyProfileSnapshotCreate,
} from "../generated/company-profile";
import {
  COMPANY_EVIDENCE_TYPE_VALUES,
  COMPANY_PROFILE_SCHEMA_VERSION,
  COMPANY_PROFILE_STATUS_VALUES,
} from "../generated/company-profile.enums";

describe("company profile generated contracts", () => {
  it("exports runtime enums and stable schema version", () => {
    expect(COMPANY_PROFILE_SCHEMA_VERSION).toBe("1.0.0");
    expect(COMPANY_PROFILE_STATUS_VALUES).toContain("DRAFT");
    expect(COMPANY_EVIDENCE_TYPE_VALUES).toContain("RUP");
  });

  it("types create and snapshot payloads", () => {
    const profile: CompanyProfileCreate = {
      legal_name: "Empresa Sintetica SAS",
      trade_name: null,
      tax_id: "900123456",
      tax_id_type: "NIT",
      company_type: null,
      legal_nature: null,
      incorporation_date: null,
      country: "CO",
      department: null,
      city: null,
      address: null,
      website: null,
      primary_email: null,
      primary_phone: null,
      economic_activity_codes: [],
    };
    const snapshot: CompanyProfileSnapshotCreate = { notes: null, allow_incomplete: false };
    expect(profile.legal_name).toContain("Sintetica");
    expect(snapshot.allow_incomplete).toBe(false);
  });
});
