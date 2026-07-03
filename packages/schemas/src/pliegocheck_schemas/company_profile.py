"""Contratos de perfiles de empresa, evidencias y snapshots (Microfase 5)."""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator,
)

COMPANY_PROFILE_SCHEMA_VERSION = "1.0.0"

NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
EmailText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=320)]


class CompanyProfileStatus(StrEnum):
    DRAFT = "DRAFT"
    INCOMPLETE = "INCOMPLETE"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    ARCHIVED = "ARCHIVED"


class CompanyRecordStatus(StrEnum):
    DECLARED = "DECLARED"
    SUPPORTED = "SUPPORTED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class CompanyLegalRegistrationType(StrEnum):
    RUT = "RUT"
    CHAMBER_OF_COMMERCE = "CHAMBER_OF_COMMERCE"
    RUP = "RUP"
    LEGAL_REPRESENTATION = "LEGAL_REPRESENTATION"
    TAX_REGISTRATION = "TAX_REGISTRATION"
    OTHER = "OTHER"


class FinancialSourceType(StrEnum):
    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"
    RUP = "RUP"
    TAX_RETURN = "TAX_RETURN"
    MANAGEMENT_CERTIFICATION = "MANAGEMENT_CERTIFICATION"
    OTHER = "OTHER"


class FinancialMetricType(StrEnum):
    CURRENT_ASSETS = "CURRENT_ASSETS"
    CURRENT_LIABILITIES = "CURRENT_LIABILITIES"
    TOTAL_ASSETS = "TOTAL_ASSETS"
    TOTAL_LIABILITIES = "TOTAL_LIABILITIES"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    OPERATING_PROFIT = "OPERATING_PROFIT"
    NET_PROFIT = "NET_PROFIT"
    WORKING_CAPITAL = "WORKING_CAPITAL"
    LIQUIDITY_RATIO = "LIQUIDITY_RATIO"
    DEBT_RATIO = "DEBT_RATIO"
    INTEREST_COVERAGE = "INTEREST_COVERAGE"
    RETURN_ON_ASSETS = "RETURN_ON_ASSETS"
    RETURN_ON_EQUITY = "RETURN_ON_EQUITY"
    OTHER = "OTHER"


class ExperienceExecutionStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    SUSPENDED = "SUSPENDED"
    UNKNOWN = "UNKNOWN"


class PersonRelationshipType(StrEnum):
    EMPLOYEE = "EMPLOYEE"
    CONTRACTOR = "CONTRACTOR"
    PARTNER = "PARTNER"
    ALLY = "ALLY"
    POTENTIAL = "POTENTIAL"
    OTHER = "OTHER"


class PersonAvailabilityStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class PersonCredentialType(StrEnum):
    PROFESSIONAL_LICENSE = "PROFESSIONAL_LICENSE"
    CERTIFICATION = "CERTIFICATION"
    COURSE = "COURSE"
    LANGUAGE = "LANGUAGE"
    SECURITY_CLEARANCE = "SECURITY_CLEARANCE"
    OTHER = "OTHER"


class CompanyCertificationType(StrEnum):
    ISO = "ISO"
    QUALITY = "QUALITY"
    SECURITY = "SECURITY"
    CLOUD_PARTNER = "CLOUD_PARTNER"
    MANUFACTURER_PARTNER = "MANUFACTURER_PARTNER"
    GOVERNMENT_REGISTRY = "GOVERNMENT_REGISTRY"
    INDUSTRY = "INDUSTRY"
    OTHER = "OTHER"


class CompanyCapabilityCategory(StrEnum):
    TECHNOLOGY = "TECHNOLOGY"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    GEOGRAPHIC_COVERAGE = "GEOGRAPHIC_COVERAGE"
    OPERATIONAL = "OPERATIONAL"
    SERVICE_CAPACITY = "SERVICE_CAPACITY"
    PLATFORM = "PLATFORM"
    SECURITY = "SECURITY"
    QUALITY = "QUALITY"
    OTHER = "OTHER"


class CompanyEvidenceType(StrEnum):
    RUT = "RUT"
    CHAMBER_CERTIFICATE = "CHAMBER_CERTIFICATE"
    RUP = "RUP"
    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"
    TAX_RETURN = "TAX_RETURN"
    EXPERIENCE_CERTIFICATE = "EXPERIENCE_CERTIFICATE"
    CONTRACT = "CONTRACT"
    ACT_START = "ACT_START"
    COMPLETION_CERTIFICATE = "COMPLETION_CERTIFICATE"
    LIQUIDATION_RECORD = "LIQUIDATION_RECORD"
    CV = "CV"
    DIPLOMA = "DIPLOMA"
    PROFESSIONAL_LICENSE = "PROFESSIONAL_LICENSE"
    PERSON_CERTIFICATION = "PERSON_CERTIFICATION"
    COMPANY_CERTIFICATION = "COMPANY_CERTIFICATION"
    INSURANCE = "INSURANCE"
    UNSPSC_SUPPORT = "UNSPSC_SUPPORT"
    OTHER = "OTHER"


class CompanyEvidenceReviewStatus(StrEnum):
    PENDING = "PENDING"
    SUPPORTED = "SUPPORTED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class CompanyEvidenceSubjectType(StrEnum):
    COMPANY_PROFILE = "COMPANY_PROFILE"
    LEGAL_REGISTRATION = "LEGAL_REGISTRATION"
    RUP_SNAPSHOT = "RUP_SNAPSHOT"
    UNSPSC_CODE = "UNSPSC_CODE"
    FINANCIAL_PERIOD = "FINANCIAL_PERIOD"
    FINANCIAL_METRIC = "FINANCIAL_METRIC"
    EXPERIENCE_RECORD = "EXPERIENCE_RECORD"
    PERSON = "PERSON"
    PERSON_EDUCATION = "PERSON_EDUCATION"
    PERSON_EXPERIENCE = "PERSON_EXPERIENCE"
    PERSON_CREDENTIAL = "PERSON_CREDENTIAL"
    COMPANY_CERTIFICATION = "COMPANY_CERTIFICATION"
    COMPANY_CAPABILITY = "COMPANY_CAPABILITY"


class CompanyEvidenceRole(StrEnum):
    PRIMARY = "PRIMARY"
    SUPPORTING = "SUPPORTING"
    CONFLICTING = "CONFLICTING"


class CompanyEvidenceValidationStatus(StrEnum):
    DOCUMENT_ONLY = "DOCUMENT_ONLY"
    VALID_SEGMENT = "VALID_SEGMENT"
    INVALID_SEGMENT = "INVALID_SEGMENT"
    QUOTE_NOT_FOUND = "QUOTE_NOT_FOUND"
    LOCATION_MISMATCH = "LOCATION_MISMATCH"
    EXPIRED_EVIDENCE = "EXPIRED_EVIDENCE"


class CompanySnapshotStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"


class CompanyErrorCode(StrEnum):
    COMPANY_NOT_FOUND = "COMPANY_NOT_FOUND"
    COMPANY_ARCHIVED = "COMPANY_ARCHIVED"
    DUPLICATE_TAX_ID = "DUPLICATE_TAX_ID"
    INVALID_COMPANY_DATA = "INVALID_COMPANY_DATA"
    LEGAL_REGISTRATION_NOT_FOUND = "LEGAL_REGISTRATION_NOT_FOUND"
    RUP_SNAPSHOT_NOT_FOUND = "RUP_SNAPSHOT_NOT_FOUND"
    FINANCIAL_PERIOD_NOT_FOUND = "FINANCIAL_PERIOD_NOT_FOUND"
    FINANCIAL_METRIC_NOT_FOUND = "FINANCIAL_METRIC_NOT_FOUND"
    EXPERIENCE_RECORD_NOT_FOUND = "EXPERIENCE_RECORD_NOT_FOUND"
    PERSON_NOT_FOUND = "PERSON_NOT_FOUND"
    CERTIFICATION_NOT_FOUND = "CERTIFICATION_NOT_FOUND"
    CAPABILITY_NOT_FOUND = "CAPABILITY_NOT_FOUND"
    EVIDENCE_DOCUMENT_NOT_FOUND = "EVIDENCE_DOCUMENT_NOT_FOUND"
    EVIDENCE_LINK_NOT_FOUND = "EVIDENCE_LINK_NOT_FOUND"
    EVIDENCE_SUBJECT_NOT_FOUND = "EVIDENCE_SUBJECT_NOT_FOUND"
    EVIDENCE_SUBJECT_COMPANY_MISMATCH = "EVIDENCE_SUBJECT_COMPANY_MISMATCH"
    EVIDENCE_DOCUMENT_COMPANY_MISMATCH = "EVIDENCE_DOCUMENT_COMPANY_MISMATCH"
    EVIDENCE_QUOTE_NOT_FOUND = "EVIDENCE_QUOTE_NOT_FOUND"
    EVIDENCE_EXPIRED = "EVIDENCE_EXPIRED"
    PROFILE_INCOMPLETE = "PROFILE_INCOMPLETE"
    SNAPSHOT_NOT_FOUND = "SNAPSHOT_NOT_FOUND"
    SNAPSHOT_ALREADY_PUBLISHED = "SNAPSHOT_ALREADY_PUBLISHED"
    SNAPSHOT_IMMUTABLE = "SNAPSHOT_IMMUTABLE"
    SNAPSHOT_DIGEST_MISMATCH = "SNAPSHOT_DIGEST_MISMATCH"
    DATABASE_ERROR = "DATABASE_ERROR"


class CompanyProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legal_name: ShortText
    trade_name: ShortText | None = None
    tax_id: ShortText | None = None
    tax_id_type: ShortText | None = None
    company_type: ShortText | None = None
    legal_nature: ShortText | None = None
    incorporation_date: date | None = None
    country: ShortText | None = "CO"
    department: ShortText | None = None
    city: ShortText | None = None
    address: ShortText | None = None
    website: HttpUrl | None = None
    primary_email: EmailText | None = None
    primary_phone: ShortText | None = None
    economic_activity_codes: list[str] = Field(default_factory=list)


class CompanyProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legal_name: ShortText | None = None
    trade_name: ShortText | None = None
    tax_id: ShortText | None = None
    tax_id_type: ShortText | None = None
    company_type: ShortText | None = None
    legal_nature: ShortText | None = None
    incorporation_date: date | None = None
    country: ShortText | None = None
    department: ShortText | None = None
    city: ShortText | None = None
    address: ShortText | None = None
    website: HttpUrl | None = None
    primary_email: EmailText | None = None
    primary_phone: ShortText | None = None
    economic_activity_codes: list[str] | None = None
    status: CompanyProfileStatus | None = None


class CompanyProfileSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    internal_reference: str
    legal_name: str
    trade_name: str | None
    tax_id_masked: str | None
    tax_id_type: str | None
    status: CompanyProfileStatus
    completeness_status: str
    evidence_coverage: Decimal = Field(ge=0, le=1)
    pending_evidence_count: int = Field(ge=0)
    updated_at: AwareDatetime


class CompanyProfileList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CompanyProfileSummary]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class CompanyProfileDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    internal_reference: str
    legal_name: str
    trade_name: str | None
    tax_id: str | None
    tax_id_masked: str | None
    tax_id_type: str | None
    company_type: str | None
    legal_nature: str | None
    incorporation_date: date | None
    country: str | None
    department: str | None
    city: str | None
    address: str | None
    website: str | None
    primary_email: str | None
    primary_phone: str | None
    economic_activity_codes: list[str]
    status: CompanyProfileStatus
    created_at: AwareDatetime
    updated_at: AwareDatetime
    archived_at: AwareDatetime | None
    legal_registrations: list["CompanyLegalRegistration"] = Field(default_factory=list)
    rup_snapshots: list["RupSnapshot"] = Field(default_factory=list)
    unspsc_codes: list["CompanyUnspscCode"] = Field(default_factory=list)
    financial_periods: list["CompanyFinancialPeriod"] = Field(default_factory=list)
    experience_records: list["CompanyExperienceRecord"] = Field(default_factory=list)
    people: list["CompanyPerson"] = Field(default_factory=list)
    certifications: list["CompanyCertification"] = Field(default_factory=list)
    capabilities: list["CompanyCapability"] = Field(default_factory=list)
    evidence_documents: list["CompanyEvidenceDocumentMetadata"] = Field(default_factory=list)
    evidence_links: list["CompanyEvidenceLink"] = Field(default_factory=list)


class DateRangeMixin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_dates(self) -> "DateRangeMixin":
        start = getattr(self, "start_date", None) or getattr(self, "period_start", None)
        end = getattr(self, "end_date", None) or getattr(self, "period_end", None)
        issued_at = getattr(self, "issued_at", None)
        expires_at = getattr(self, "expires_at", None) or getattr(self, "valid_until", None)
        if start is not None and end is not None and end < start:
            raise ValueError("La fecha final no puede ser anterior a la inicial")
        if issued_at is not None and expires_at is not None and expires_at < issued_at:
            raise ValueError("La fecha de expiracion no puede ser anterior a la emision")
        return self


class LegalRegistrationCreate(DateRangeMixin):
    registration_type: CompanyLegalRegistrationType
    registration_number: ShortText | None = None
    issuing_authority: ShortText | None = None
    issued_at: date | None = None
    expires_at: date | None = None
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED
    declared_data: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=2000)


class LegalRegistrationUpdate(LegalRegistrationCreate):
    registration_type: CompanyLegalRegistrationType | None = None  # type: ignore[assignment]


class CompanyLegalRegistration(LegalRegistrationCreate):
    id: UUID
    company_id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class RupSnapshotCreate(DateRangeMixin):
    registration_number: ShortText | None = None
    issued_at: date | None = None
    valid_until: date | None = None
    renewal_year: int | None = Field(default=None, ge=1900, le=2200)
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED
    financial_period_reference: ShortText | None = None
    organization_capacity: Decimal | None = None
    technical_capacity: Decimal | None = None
    financial_capacity: Decimal | None = None
    experience_capacity: Decimal | None = None
    raw_declared_data: dict[str, Any] = Field(default_factory=dict)


class RupSnapshotUpdate(RupSnapshotCreate):
    pass


class RupSnapshot(RupSnapshotCreate):
    id: UUID
    company_id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyUnspscCodeCreate(DateRangeMixin):
    code: ShortText
    description: ShortText | None = None
    source: ShortText | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED


class CompanyUnspscCode(CompanyUnspscCodeCreate):
    id: UUID
    company_id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyFinancialPeriodCreate(DateRangeMixin):
    period_start: date
    period_end: date
    currency: CurrencyCode = "COP"
    source_type: FinancialSourceType
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED


class CompanyFinancialPeriodUpdate(DateRangeMixin):
    period_start: date | None = None
    period_end: date | None = None
    currency: CurrencyCode | None = None
    source_type: FinancialSourceType | None = None
    status: CompanyRecordStatus | None = None


class CompanyFinancialMetricCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_type: FinancialMetricType
    value: Decimal
    unit: ShortText | None = None
    source_value: ShortText | None = None
    is_calculated: bool = False
    formula: str | None = Field(default=None, max_length=1000)
    formula_inputs: dict[str, Any] = Field(default_factory=dict)
    calculation_version: str | None = Field(default=None, max_length=64)
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED


class CompanyFinancialMetric(CompanyFinancialMetricCreate):
    id: UUID
    financial_period_id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyFinancialPeriod(CompanyFinancialPeriodCreate):
    id: UUID
    company_id: UUID
    metrics: list[CompanyFinancialMetric] = Field(default_factory=list)
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyExperienceCreate(DateRangeMixin):
    contract_reference: ShortText | None = None
    contracting_party: ShortText
    contract_title: ShortText
    description: str | None = Field(default=None, max_length=5000)
    country: ShortText | None = None
    sector: ShortText | None = None
    contract_type: ShortText | None = None
    start_date: date | None = None
    end_date: date | None = None
    execution_status: ExperienceExecutionStatus = ExperienceExecutionStatus.UNKNOWN
    total_contract_value: Decimal | None = Field(default=None, ge=0)
    currency: CurrencyCode = "COP"
    company_participation_percentage: Decimal | None = Field(default=None, ge=0, le=100)
    company_attributable_value: Decimal | None = Field(default=None, ge=0)
    attributable_value_formula: str | None = Field(default=None, max_length=1000)
    consortium_name: ShortText | None = None
    consortium_members: list[str] = Field(default_factory=list)
    unspsc_codes: list[str] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)
    scope_tags: list[str] = Field(default_factory=list)
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED


class CompanyExperienceUpdate(CompanyExperienceCreate):
    contracting_party: ShortText | None = None  # type: ignore[assignment]
    contract_title: ShortText | None = None  # type: ignore[assignment]


class CompanyExperienceRecord(CompanyExperienceCreate):
    id: UUID
    company_id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyPersonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: ShortText
    identification_type: ShortText | None = None
    identification_number: ShortText | None = None
    email: EmailText | None = None
    phone: ShortText | None = None
    relationship_type: PersonRelationshipType = PersonRelationshipType.OTHER
    availability_status: PersonAvailabilityStatus = PersonAvailabilityStatus.UNKNOWN
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED


class CompanyPersonUpdate(CompanyPersonCreate):
    full_name: ShortText | None = None  # type: ignore[assignment]


class PersonEducationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degree_type: ShortText | None = None
    title: ShortText
    institution: ShortText | None = None
    graduation_date: date | None = None
    country: ShortText | None = None
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED


class PersonExperienceCreate(DateRangeMixin):
    organization: ShortText
    role: ShortText
    description: str | None = Field(default=None, max_length=5000)
    start_date: date | None = None
    end_date: date | None = None
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED


class PersonCredentialCreate(DateRangeMixin):
    credential_type: PersonCredentialType
    name: ShortText
    issuer: ShortText | None = None
    credential_number: ShortText | None = None
    issued_at: date | None = None
    expires_at: date | None = None
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED


class PersonEducation(PersonEducationCreate):
    id: UUID
    person_id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class PersonExperience(PersonExperienceCreate):
    id: UUID
    person_id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class PersonCredential(PersonCredentialCreate):
    id: UUID
    person_id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyPerson(CompanyPersonCreate):
    id: UUID
    company_id: UUID
    identification_masked: str | None
    education: list[PersonEducation] = Field(default_factory=list)
    experience: list[PersonExperience] = Field(default_factory=list)
    credentials: list[PersonCredential] = Field(default_factory=list)
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyCertificationCreate(DateRangeMixin):
    certification_type: CompanyCertificationType
    name: ShortText
    issuer: ShortText | None = None
    certificate_number: ShortText | None = None
    scope: str | None = Field(default=None, max_length=2000)
    issued_at: date | None = None
    expires_at: date | None = None
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED


class CompanyCertificationUpdate(CompanyCertificationCreate):
    certification_type: CompanyCertificationType | None = None  # type: ignore[assignment]
    name: ShortText | None = None  # type: ignore[assignment]


class CompanyCertification(CompanyCertificationCreate):
    id: UUID
    company_id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyCapabilityCreate(DateRangeMixin):
    category: CompanyCapabilityCategory
    name: ShortText
    description: str | None = Field(default=None, max_length=5000)
    value: Decimal | str | None = None
    unit: ShortText | None = None
    territorial_scope: ShortText | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    status: CompanyRecordStatus = CompanyRecordStatus.DECLARED


class CompanyCapabilityUpdate(CompanyCapabilityCreate):
    category: CompanyCapabilityCategory | None = None  # type: ignore[assignment]
    name: ShortText | None = None  # type: ignore[assignment]


class CompanyCapability(CompanyCapabilityCreate):
    id: UUID
    company_id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyEvidenceDocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    company_id: UUID
    process_document_id: UUID
    evidence_type: CompanyEvidenceType
    title: str
    original_filename: str
    extension: str
    size_bytes: int = Field(gt=0)
    sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    issuer: str | None
    issued_at: date | None
    expires_at: date | None
    review_status: CompanyEvidenceReviewStatus
    processing_status: str
    notes: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyEvidenceUploadResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_filename: str
    upload_status: Literal["STORED", "REJECTED"]
    document: CompanyEvidenceDocumentMetadata | None = None
    error: dict[str, Any] | None = None


class CompanyEvidenceUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    results: list[CompanyEvidenceUploadResult]
    stored_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)


class CompanyEvidenceLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    subject_type: CompanyEvidenceSubjectType
    subject_id: UUID
    extraction_id: UUID | None = None
    segment_id: UUID | None = None
    evidence_role: CompanyEvidenceRole = CompanyEvidenceRole.PRIMARY
    quoted_text: str | None = Field(default=None, max_length=5000)
    source_location: dict[str, Any] = Field(default_factory=dict)
    review_status: CompanyEvidenceReviewStatus = CompanyEvidenceReviewStatus.PENDING
    notes: str | None = Field(default=None, max_length=2000)


class CompanyEvidenceLinkReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_status: CompanyEvidenceReviewStatus
    notes: str | None = Field(default=None, max_length=2000)


class CompanyEvidenceLink(CompanyEvidenceLinkCreate):
    id: UUID
    company_id: UUID
    validation_status: CompanyEvidenceValidationStatus
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CompanyProfileMissingItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    subject_type: CompanyEvidenceSubjectType | None = None
    subject_id: UUID | None = None
    message: str
    severity: Literal["INFO", "WARNING", "BLOCKING"] = "WARNING"


class CompanyProfileCompleteness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    identity_complete: bool
    legal_registration_complete: bool
    rup_complete: bool
    financial_complete: bool
    experience_complete: bool
    personnel_complete: bool
    certifications_complete: bool
    evidence_coverage: Decimal = Field(ge=0, le=1)
    expired_evidence_count: int = Field(ge=0)
    unsupported_record_count: int = Field(ge=0)
    conflicting_evidence_count: int = Field(ge=0)
    missing_items: list[CompanyProfileMissingItem]
    ready_for_review: bool
    generated_at: AwareDatetime


class CompanyProfileSnapshotCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: str | None = Field(default=None, max_length=2000)
    allow_incomplete: bool = False


class CompanyProfileSnapshotSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    company_id: UUID
    version: int = Field(gt=0)
    status: CompanySnapshotStatus
    digest: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    completeness_status: str
    created_at: AwareDatetime
    published_at: AwareDatetime | None


class CompanyProfileSnapshotDetail(CompanyProfileSnapshotSummary):
    payload: dict[str, Any]
    notes: str | None


class CompanyProfileContracts(BaseModel):
    """Contenedor para generar un unico JSON Schema con defs compartidos."""

    model_config = ConfigDict(extra="forbid")

    company_profile_create: CompanyProfileCreate
    company_profile_update: CompanyProfileUpdate
    company_profile_summary: CompanyProfileSummary
    company_profile_detail: CompanyProfileDetail
    company_profile_list: CompanyProfileList
    legal_registration_create: LegalRegistrationCreate
    legal_registration: CompanyLegalRegistration
    rup_snapshot_create: RupSnapshotCreate
    rup_snapshot: RupSnapshot
    unspsc_code_create: CompanyUnspscCodeCreate
    unspsc_code: CompanyUnspscCode
    financial_period_create: CompanyFinancialPeriodCreate
    financial_period_update: CompanyFinancialPeriodUpdate
    financial_period: CompanyFinancialPeriod
    financial_metric_create: CompanyFinancialMetricCreate
    financial_metric: CompanyFinancialMetric
    experience_create: CompanyExperienceCreate
    experience_update: CompanyExperienceUpdate
    experience_record: CompanyExperienceRecord
    person_create: CompanyPersonCreate
    person_update: CompanyPersonUpdate
    person: CompanyPerson
    person_education_create: PersonEducationCreate
    person_education: PersonEducation
    person_experience_create: PersonExperienceCreate
    person_experience: PersonExperience
    person_credential_create: PersonCredentialCreate
    person_credential: PersonCredential
    certification_create: CompanyCertificationCreate
    certification_update: CompanyCertificationUpdate
    certification: CompanyCertification
    capability_create: CompanyCapabilityCreate
    capability_update: CompanyCapabilityUpdate
    capability: CompanyCapability
    evidence_document: CompanyEvidenceDocumentMetadata
    evidence_upload_response: CompanyEvidenceUploadResponse
    evidence_link_create: CompanyEvidenceLinkCreate
    evidence_link_review: CompanyEvidenceLinkReview
    evidence_link: CompanyEvidenceLink
    completeness: CompanyProfileCompleteness
    missing_item: CompanyProfileMissingItem
    snapshot_summary: CompanyProfileSnapshotSummary
    snapshot_detail: CompanyProfileSnapshotDetail
    snapshot_create: CompanyProfileSnapshotCreate
