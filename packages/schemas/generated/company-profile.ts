// Archivo generado automaticamente desde company-profile.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type CompanyCapabilityCategory =
  | "TECHNOLOGY"
  | "INFRASTRUCTURE"
  | "GEOGRAPHIC_COVERAGE"
  | "OPERATIONAL"
  | "SERVICE_CAPACITY"
  | "PLATFORM"
  | "SECURITY"
  | "QUALITY"
  | "OTHER";
export type CompanyCertificationType =
  | "ISO"
  | "QUALITY"
  | "SECURITY"
  | "CLOUD_PARTNER"
  | "MANUFACTURER_PARTNER"
  | "GOVERNMENT_REGISTRY"
  | "INDUSTRY"
  | "OTHER";
export type CompanyEvidenceType =
  | "RUT"
  | "CHAMBER_CERTIFICATE"
  | "RUP"
  | "FINANCIAL_STATEMENT"
  | "TAX_RETURN"
  | "EXPERIENCE_CERTIFICATE"
  | "CONTRACT"
  | "ACT_START"
  | "COMPLETION_CERTIFICATE"
  | "LIQUIDATION_RECORD"
  | "CV"
  | "DIPLOMA"
  | "PROFESSIONAL_LICENSE"
  | "PERSON_CERTIFICATION"
  | "COMPANY_CERTIFICATION"
  | "INSURANCE"
  | "UNSPSC_SUPPORT"
  | "OTHER";
export type CompanyEvidenceReviewStatus =
  "PENDING" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
export type CompanyEvidenceSubjectType =
  | "COMPANY_PROFILE"
  | "LEGAL_REGISTRATION"
  | "RUP_SNAPSHOT"
  | "UNSPSC_CODE"
  | "FINANCIAL_PERIOD"
  | "FINANCIAL_METRIC"
  | "EXPERIENCE_RECORD"
  | "PERSON"
  | "PERSON_EDUCATION"
  | "PERSON_EXPERIENCE"
  | "PERSON_CREDENTIAL"
  | "COMPANY_CERTIFICATION"
  | "COMPANY_CAPABILITY";
export type CompanyEvidenceValidationStatus =
  | "DOCUMENT_ONLY"
  | "VALID_SEGMENT"
  | "INVALID_SEGMENT"
  | "QUOTE_NOT_FOUND"
  | "LOCATION_MISMATCH"
  | "EXPIRED_EVIDENCE";
export type FinancialMetricType =
  | "CURRENT_ASSETS"
  | "CURRENT_LIABILITIES"
  | "TOTAL_ASSETS"
  | "TOTAL_LIABILITIES"
  | "EQUITY"
  | "REVENUE"
  | "OPERATING_PROFIT"
  | "NET_PROFIT"
  | "INTEREST_EXPENSE"
  | "WORKING_CAPITAL"
  | "LIQUIDITY_RATIO"
  | "DEBT_RATIO"
  | "INTEREST_COVERAGE"
  | "RETURN_ON_ASSETS"
  | "RETURN_ON_EQUITY"
  | "OTHER";
export type FinancialSourceType =
  "FINANCIAL_STATEMENT" | "RUP" | "TAX_RETURN" | "MANAGEMENT_CERTIFICATION" | "OTHER";
export type CompanyLegalRegistrationType =
  "RUT" | "CHAMBER_OF_COMMERCE" | "RUP" | "LEGAL_REPRESENTATION" | "TAX_REGISTRATION" | "OTHER";
export type PersonCredentialType =
  "PROFESSIONAL_LICENSE" | "CERTIFICATION" | "COURSE" | "LANGUAGE" | "SECURITY_CLEARANCE" | "OTHER";
export type CompanyProfileStatus = "DRAFT" | "INCOMPLETE" | "READY_FOR_REVIEW" | "ARCHIVED";
export type CompanyRecordStatus =
  "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
export type CompanySnapshotStatus = "DRAFT" | "PUBLISHED" | "SUPERSEDED";

/**
 * Contenedor para generar un unico JSON Schema con defs compartidos.
 */
export interface CompanyProfile {
  capability: CompanyCapability;
  capability_create: CompanyCapabilityCreate;
  capability_update: CompanyCapabilityUpdate;
  certification: CompanyCertification;
  certification_create: CompanyCertificationCreate;
  certification_update: CompanyCertificationUpdate;
  company_profile_create: CompanyProfileCreate;
  company_profile_detail: CompanyProfileDetail;
  company_profile_list: CompanyProfileList;
  company_profile_summary: CompanyProfileSummary;
  company_profile_update: CompanyProfileUpdate;
  completeness: CompanyProfileCompleteness;
  evidence_document: CompanyEvidenceDocumentMetadata;
  evidence_link: CompanyEvidenceLink;
  evidence_link_create: CompanyEvidenceLinkCreate;
  evidence_link_review: CompanyEvidenceLinkReview;
  evidence_upload_response: CompanyEvidenceUploadResponse;
  experience_create: CompanyExperienceCreate;
  experience_record: CompanyExperienceRecord;
  experience_update: CompanyExperienceUpdate;
  financial_metric: CompanyFinancialMetric;
  financial_metric_create: CompanyFinancialMetricCreate;
  financial_period: CompanyFinancialPeriod;
  financial_period_create: CompanyFinancialPeriodCreate;
  financial_period_update: CompanyFinancialPeriodUpdate;
  legal_registration: CompanyLegalRegistration;
  legal_registration_create: LegalRegistrationCreate;
  missing_item: CompanyProfileMissingItem;
  person: CompanyPerson;
  person_create: CompanyPersonCreate;
  person_credential: PersonCredential;
  person_credential_create: PersonCredentialCreate;
  person_education: PersonEducation;
  person_education_create: PersonEducationCreate;
  person_experience: PersonExperience;
  person_experience_create: PersonExperienceCreate;
  person_update: CompanyPersonUpdate;
  rup_snapshot: RupSnapshot;
  rup_snapshot_create: RupSnapshotCreate;
  snapshot_create: CompanyProfileSnapshotCreate;
  snapshot_detail: CompanyProfileSnapshotDetail;
  snapshot_summary: CompanyProfileSnapshotSummary;
  unspsc_code: CompanyUnspscCode;
  unspsc_code_create: CompanyUnspscCodeCreate;
}
export interface CompanyCapability {
  category: CompanyCapabilityCategory;
  company_id: string;
  created_at: string;
  description?: string | null;
  id: string;
  name: string;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  territorial_scope?: string | null;
  unit?: string | null;
  updated_at: string;
  valid_from?: string | null;
  valid_until?: string | null;
  value?: number | string | null;
}
export interface CompanyCapabilityCreate {
  category: CompanyCapabilityCategory;
  description?: string | null;
  name: string;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  territorial_scope?: string | null;
  unit?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
  value?: number | string | null;
}
export interface CompanyCapabilityUpdate {
  category?: CompanyCapabilityCategory | null;
  description?: string | null;
  name?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  territorial_scope?: string | null;
  unit?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
  value?: number | string | null;
}
export interface CompanyCertification {
  certificate_number?: string | null;
  certification_type: CompanyCertificationType;
  company_id: string;
  created_at: string;
  expires_at?: string | null;
  id: string;
  issued_at?: string | null;
  issuer?: string | null;
  name: string;
  scope?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  updated_at: string;
}
export interface CompanyCertificationCreate {
  certificate_number?: string | null;
  certification_type: CompanyCertificationType;
  expires_at?: string | null;
  issued_at?: string | null;
  issuer?: string | null;
  name: string;
  scope?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
}
export interface CompanyCertificationUpdate {
  certificate_number?: string | null;
  certification_type?: CompanyCertificationType | null;
  expires_at?: string | null;
  issued_at?: string | null;
  issuer?: string | null;
  name?: string | null;
  scope?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
}
export interface CompanyProfileCreate {
  address?: string | null;
  city?: string | null;
  company_type?: string | null;
  country?: string | null;
  department?: string | null;
  economic_activity_codes?: string[];
  incorporation_date?: string | null;
  legal_name: string;
  legal_nature?: string | null;
  primary_email?: string | null;
  primary_phone?: string | null;
  tax_id?: string | null;
  tax_id_type?: string | null;
  trade_name?: string | null;
  website?: string | null;
}
export interface CompanyProfileDetail {
  address: string | null;
  archived_at: string | null;
  capabilities?: CompanyCapability[];
  certifications?: CompanyCertification[];
  city: string | null;
  company_type: string | null;
  country: string | null;
  created_at: string;
  department: string | null;
  economic_activity_codes: string[];
  evidence_documents?: CompanyEvidenceDocumentMetadata[];
  evidence_links?: CompanyEvidenceLink[];
  experience_records?: CompanyExperienceRecord[];
  financial_periods?: CompanyFinancialPeriod[];
  id: string;
  incorporation_date: string | null;
  internal_reference: string;
  legal_name: string;
  legal_nature: string | null;
  legal_registrations?: CompanyLegalRegistration[];
  people?: CompanyPerson[];
  primary_email: string | null;
  primary_phone: string | null;
  rup_snapshots?: RupSnapshot[];
  status: CompanyProfileStatus;
  tax_id: string | null;
  tax_id_masked: string | null;
  tax_id_type: string | null;
  trade_name: string | null;
  unspsc_codes?: CompanyUnspscCode[];
  updated_at: string;
  website: string | null;
}
export interface CompanyEvidenceDocumentMetadata {
  company_id: string;
  created_at: string;
  evidence_type: CompanyEvidenceType;
  expires_at: string | null;
  extension: string;
  id: string;
  issued_at: string | null;
  issuer: string | null;
  notes: string | null;
  original_filename: string;
  process_document_id: string;
  processing_status: string;
  review_status: CompanyEvidenceReviewStatus;
  sha256: string;
  size_bytes: number;
  title: string;
  updated_at: string;
}
export interface CompanyEvidenceLink {
  company_id: string;
  created_at: string;
  document_id: string;
  evidence_role?: "PRIMARY" | "SUPPORTING" | "CONFLICTING";
  extraction_id?: string | null;
  id: string;
  notes?: string | null;
  quoted_text?: string | null;
  review_status?: "PENDING" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  segment_id?: string | null;
  source_location?: {
    [k: string]: unknown;
  };
  subject_id: string;
  subject_type: CompanyEvidenceSubjectType;
  updated_at: string;
  validation_status: CompanyEvidenceValidationStatus;
}
export interface CompanyExperienceRecord {
  activities?: string[];
  attributable_value_formula?: string | null;
  company_attributable_value?: number | string | null;
  company_id: string;
  company_participation_percentage?: number | string | null;
  consortium_members?: string[];
  consortium_name?: string | null;
  contract_reference?: string | null;
  contract_title: string;
  contract_type?: string | null;
  contracting_party: string;
  country?: string | null;
  created_at: string;
  currency?: string;
  description?: string | null;
  end_date?: string | null;
  execution_status?:
    "PLANNED" | "IN_PROGRESS" | "COMPLETED" | "TERMINATED" | "SUSPENDED" | "UNKNOWN";
  id: string;
  scope_tags?: string[];
  sector?: string | null;
  start_date?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  total_contract_value?: number | string | null;
  unspsc_codes?: string[];
  updated_at: string;
}
export interface CompanyFinancialPeriod {
  company_id: string;
  created_at: string;
  currency?: string;
  id: string;
  metrics?: CompanyFinancialMetric[];
  period_end: string;
  period_start: string;
  source_type: FinancialSourceType;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  updated_at: string;
}
export interface CompanyFinancialMetric {
  calculation_version?: string | null;
  created_at: string;
  financial_period_id: string;
  formula?: string | null;
  formula_inputs?: {
    [k: string]: unknown;
  };
  id: string;
  is_calculated?: boolean;
  metric_type: FinancialMetricType;
  source_value?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  unit?: string | null;
  updated_at: string;
  value: number | string;
}
export interface CompanyLegalRegistration {
  company_id: string;
  created_at: string;
  declared_data?: {
    [k: string]: unknown;
  };
  expires_at?: string | null;
  id: string;
  issued_at?: string | null;
  issuing_authority?: string | null;
  notes?: string | null;
  registration_number?: string | null;
  registration_type: CompanyLegalRegistrationType;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  updated_at: string;
}
export interface CompanyPerson {
  availability_status?: "AVAILABLE" | "PARTIAL" | "UNAVAILABLE" | "UNKNOWN";
  company_id: string;
  created_at: string;
  credentials?: PersonCredential[];
  education?: PersonEducation[];
  email?: string | null;
  experience?: PersonExperience[];
  full_name: string;
  id: string;
  identification_masked: string | null;
  identification_number?: string | null;
  identification_type?: string | null;
  phone?: string | null;
  relationship_type?: "EMPLOYEE" | "CONTRACTOR" | "PARTNER" | "ALLY" | "POTENTIAL" | "OTHER";
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  updated_at: string;
}
export interface PersonCredential {
  created_at: string;
  credential_number?: string | null;
  credential_type: PersonCredentialType;
  expires_at?: string | null;
  id: string;
  issued_at?: string | null;
  issuer?: string | null;
  name: string;
  person_id: string;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  updated_at: string;
}
export interface PersonEducation {
  country?: string | null;
  created_at: string;
  degree_type?: string | null;
  graduation_date?: string | null;
  id: string;
  institution?: string | null;
  person_id: string;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  title: string;
  updated_at: string;
}
export interface PersonExperience {
  created_at: string;
  description?: string | null;
  end_date?: string | null;
  id: string;
  organization: string;
  person_id: string;
  role: string;
  start_date?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  updated_at: string;
}
export interface RupSnapshot {
  company_id: string;
  created_at: string;
  experience_capacity?: number | string | null;
  financial_capacity?: number | string | null;
  financial_period_reference?: string | null;
  id: string;
  issued_at?: string | null;
  organization_capacity?: number | string | null;
  raw_declared_data?: {
    [k: string]: unknown;
  };
  registration_number?: string | null;
  renewal_year?: number | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  technical_capacity?: number | string | null;
  updated_at: string;
  valid_until?: string | null;
}
export interface CompanyUnspscCode {
  code: string;
  company_id: string;
  created_at: string;
  description?: string | null;
  id: string;
  source?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  updated_at: string;
  valid_from?: string | null;
  valid_until?: string | null;
}
export interface CompanyProfileList {
  items: CompanyProfileSummary[];
  limit: number;
  offset: number;
  total: number;
}
export interface CompanyProfileSummary {
  completeness_status: string;
  evidence_coverage: number | string;
  id: string;
  internal_reference: string;
  legal_name: string;
  pending_evidence_count: number;
  status: CompanyProfileStatus;
  tax_id_masked: string | null;
  tax_id_type: string | null;
  trade_name: string | null;
  updated_at: string;
}
export interface CompanyProfileUpdate {
  address?: string | null;
  city?: string | null;
  company_type?: string | null;
  country?: string | null;
  department?: string | null;
  economic_activity_codes?: string[] | null;
  incorporation_date?: string | null;
  legal_name?: string | null;
  legal_nature?: string | null;
  primary_email?: string | null;
  primary_phone?: string | null;
  status?: CompanyProfileStatus | null;
  tax_id?: string | null;
  tax_id_type?: string | null;
  trade_name?: string | null;
  website?: string | null;
}
export interface CompanyProfileCompleteness {
  certifications_complete: boolean;
  company_id: string;
  conflicting_evidence_count: number;
  evidence_coverage: number | string;
  experience_complete: boolean;
  expired_evidence_count: number;
  financial_complete: boolean;
  generated_at: string;
  identity_complete: boolean;
  legal_registration_complete: boolean;
  missing_items: CompanyProfileMissingItem[];
  personnel_complete: boolean;
  ready_for_review: boolean;
  rup_complete: boolean;
  unsupported_record_count: number;
}
export interface CompanyProfileMissingItem {
  category: string;
  message: string;
  severity?: "INFO" | "WARNING" | "BLOCKING";
  subject_id?: string | null;
  subject_type?: CompanyEvidenceSubjectType | null;
}
export interface CompanyEvidenceLinkCreate {
  document_id: string;
  evidence_role?: "PRIMARY" | "SUPPORTING" | "CONFLICTING";
  extraction_id?: string | null;
  notes?: string | null;
  quoted_text?: string | null;
  review_status?: "PENDING" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  segment_id?: string | null;
  source_location?: {
    [k: string]: unknown;
  };
  subject_id: string;
  subject_type: CompanyEvidenceSubjectType;
}
export interface CompanyEvidenceLinkReview {
  notes?: string | null;
  review_status: CompanyEvidenceReviewStatus;
}
export interface CompanyEvidenceUploadResponse {
  company_id: string;
  rejected_count: number;
  results: CompanyEvidenceUploadResult[];
  stored_count: number;
}
export interface CompanyEvidenceUploadResult {
  document?: CompanyEvidenceDocumentMetadata | null;
  error?: {
    [k: string]: unknown;
  } | null;
  original_filename: string;
  upload_status: "STORED" | "REJECTED";
}
export interface CompanyExperienceCreate {
  activities?: string[];
  attributable_value_formula?: string | null;
  company_attributable_value?: number | string | null;
  company_participation_percentage?: number | string | null;
  consortium_members?: string[];
  consortium_name?: string | null;
  contract_reference?: string | null;
  contract_title: string;
  contract_type?: string | null;
  contracting_party: string;
  country?: string | null;
  currency?: string;
  description?: string | null;
  end_date?: string | null;
  execution_status?:
    "PLANNED" | "IN_PROGRESS" | "COMPLETED" | "TERMINATED" | "SUSPENDED" | "UNKNOWN";
  scope_tags?: string[];
  sector?: string | null;
  start_date?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  total_contract_value?: number | string | null;
  unspsc_codes?: string[];
}
export interface CompanyExperienceUpdate {
  activities?: string[];
  attributable_value_formula?: string | null;
  company_attributable_value?: number | string | null;
  company_participation_percentage?: number | string | null;
  consortium_members?: string[];
  consortium_name?: string | null;
  contract_reference?: string | null;
  contract_title?: string | null;
  contract_type?: string | null;
  contracting_party?: string | null;
  country?: string | null;
  currency?: string;
  description?: string | null;
  end_date?: string | null;
  execution_status?:
    "PLANNED" | "IN_PROGRESS" | "COMPLETED" | "TERMINATED" | "SUSPENDED" | "UNKNOWN";
  scope_tags?: string[];
  sector?: string | null;
  start_date?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  total_contract_value?: number | string | null;
  unspsc_codes?: string[];
}
export interface CompanyFinancialMetricCreate {
  calculation_version?: string | null;
  formula?: string | null;
  formula_inputs?: {
    [k: string]: unknown;
  };
  is_calculated?: boolean;
  metric_type: FinancialMetricType;
  source_value?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  unit?: string | null;
  value: number | string;
}
export interface CompanyFinancialPeriodCreate {
  currency?: string;
  period_end: string;
  period_start: string;
  source_type: FinancialSourceType;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
}
export interface CompanyFinancialPeriodUpdate {
  currency?: string | null;
  period_end?: string | null;
  period_start?: string | null;
  source_type?: FinancialSourceType | null;
  status?: CompanyRecordStatus | null;
}
export interface LegalRegistrationCreate {
  declared_data?: {
    [k: string]: unknown;
  };
  expires_at?: string | null;
  issued_at?: string | null;
  issuing_authority?: string | null;
  notes?: string | null;
  registration_number?: string | null;
  registration_type: CompanyLegalRegistrationType;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
}
export interface CompanyPersonCreate {
  availability_status?: "AVAILABLE" | "PARTIAL" | "UNAVAILABLE" | "UNKNOWN";
  email?: string | null;
  full_name: string;
  identification_number?: string | null;
  identification_type?: string | null;
  phone?: string | null;
  relationship_type?: "EMPLOYEE" | "CONTRACTOR" | "PARTNER" | "ALLY" | "POTENTIAL" | "OTHER";
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
}
export interface PersonCredentialCreate {
  credential_number?: string | null;
  credential_type: PersonCredentialType;
  expires_at?: string | null;
  issued_at?: string | null;
  issuer?: string | null;
  name: string;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
}
export interface PersonEducationCreate {
  country?: string | null;
  degree_type?: string | null;
  graduation_date?: string | null;
  institution?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  title: string;
}
export interface PersonExperienceCreate {
  description?: string | null;
  end_date?: string | null;
  organization: string;
  role: string;
  start_date?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
}
export interface CompanyPersonUpdate {
  availability_status?: "AVAILABLE" | "PARTIAL" | "UNAVAILABLE" | "UNKNOWN";
  email?: string | null;
  full_name?: string | null;
  identification_number?: string | null;
  identification_type?: string | null;
  phone?: string | null;
  relationship_type?: "EMPLOYEE" | "CONTRACTOR" | "PARTNER" | "ALLY" | "POTENTIAL" | "OTHER";
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
}
export interface RupSnapshotCreate {
  experience_capacity?: number | string | null;
  financial_capacity?: number | string | null;
  financial_period_reference?: string | null;
  issued_at?: string | null;
  organization_capacity?: number | string | null;
  raw_declared_data?: {
    [k: string]: unknown;
  };
  registration_number?: string | null;
  renewal_year?: number | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  technical_capacity?: number | string | null;
  valid_until?: string | null;
}
export interface CompanyProfileSnapshotCreate {
  allow_incomplete?: boolean;
  notes?: string | null;
}
export interface CompanyProfileSnapshotDetail {
  company_id: string;
  completeness_status: string;
  created_at: string;
  digest: string;
  id: string;
  notes: string | null;
  payload: {
    [k: string]: unknown;
  };
  published_at: string | null;
  status: CompanySnapshotStatus;
  version: number;
}
export interface CompanyProfileSnapshotSummary {
  company_id: string;
  completeness_status: string;
  created_at: string;
  digest: string;
  id: string;
  published_at: string | null;
  status: CompanySnapshotStatus;
  version: number;
}
export interface CompanyUnspscCodeCreate {
  code: string;
  description?: string | null;
  source?: string | null;
  status?: "DECLARED" | "SUPPORTED" | "VERIFIED" | "REJECTED" | "EXPIRED" | "NEEDS_REVIEW";
  valid_from?: string | null;
  valid_until?: string | null;
}
