"""Modelos relacionales de importacion manual."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pliegocheck_api.db import Base
from pliegocheck_schemas import (
    CompanyCapabilityCategory,
    CompanyCertificationType,
    CompanyEvidenceReviewStatus,
    CompanyEvidenceRole,
    CompanyEvidenceSubjectType,
    CompanyEvidenceType,
    CompanyEvidenceValidationStatus,
    CompanyLegalRegistrationType,
    CompanyProfileStatus,
    CompanyRecordStatus,
    CompanySnapshotStatus,
    DecisionActionPriority,
    DecisionActionStatus,
    DecisionActionType,
    DecisionFindingApplicability,
    DecisionFindingOutcome,
    DecisionFindingSourceType,
    DecisionJobStatus,
    DecisionOutcome,
    DecisionReportArtifactType,
    DecisionReportJobStatus,
    DecisionReportPackageStatus,
    DecisionReviewAction,
    DecisionRuleStatus,
    DecisionRunStatus,
    DocumentExtractionStatus,
    DocumentProcessingJobStatus,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
    DocumentType,
    DocumentUploadStatus,
    ExtractedSegmentType,
    FinancialCalculationStatus,
    FinancialEvaluationJobStatus,
    FinancialEvaluationResultStatus,
    FinancialEvaluationReviewStatus,
    FinancialEvaluationRunStatus,
    FinancialMetricType,
    FinancialOperator,
    FinancialPeriodPolicy,
    FinancialRuleMappingStatus,
    FinancialRuleSourceBasis,
    FinancialRuleType,
    NormalizationProvider,
    ProcessSource,
    ProcessStatus,
    RejectedCandidateReason,
    RequirementBasis,
    RequirementCategory,
    RequirementCriticality,
    RequirementEvidenceRole,
    RequirementEvidenceStatus,
    RequirementEvidenceValidationStatus,
    RequirementModality,
    RequirementNormalizationStatus,
    RequirementRelationType,
    RequirementReviewStatus,
    RequirementScope,
    RequirementSubsanability,
    SpecializedEvaluationDomain,
    SpecializedEvaluationJobStatus,
    SpecializedEvaluationResultStatus,
    SpecializedEvaluationReviewStatus,
    SpecializedEvaluationRunStatus,
    SpecializedEvidenceValidationStatus,
    SpecializedOperator,
    SpecializedRuleMappingStatus,
    SpecializedRuleSourceBasis,
    SpecializedRuleType,
)

PROCESS_STATUS_VALUES = ", ".join(f"'{status.value}'" for status in ProcessStatus)
PROCESS_SOURCE_VALUES = ", ".join(f"'{source.value}'" for source in ProcessSource)
DOCUMENT_TYPE_VALUES = ", ".join(f"'{document_type.value}'" for document_type in DocumentType)
DOCUMENT_UPLOAD_STATUS_VALUES = ", ".join(f"'{status.value}'" for status in DocumentUploadStatus)
DOCUMENT_PROCESSING_STATUS_VALUES = ", ".join(
    f"'{status.value}'" for status in DocumentProcessingStatus
)
DOCUMENT_PROCESSING_JOB_STATUS_VALUES = ", ".join(
    f"'{status.value}'" for status in DocumentProcessingJobStatus
)
DOCUMENT_PROCESSING_JOB_TYPE_VALUES = ", ".join(
    f"'{job_type.value}'" for job_type in DocumentProcessingJobType
)
DOCUMENT_EXTRACTION_STATUS_VALUES = ", ".join(
    f"'{status.value}'" for status in DocumentExtractionStatus
)
EXTRACTED_SEGMENT_TYPE_VALUES = ", ".join(
    f"'{segment_type.value}'" for segment_type in ExtractedSegmentType
)
NORMALIZATION_PROVIDER_VALUES = ", ".join(
    f"'{provider.value}'" for provider in NormalizationProvider
)
REQUIREMENT_NORMALIZATION_STATUS_VALUES = ", ".join(
    f"'{status.value}'" for status in RequirementNormalizationStatus
)
REQUIREMENT_CATEGORY_VALUES = ", ".join(f"'{category.value}'" for category in RequirementCategory)
REQUIREMENT_SCOPE_VALUES = ", ".join(f"'{scope.value}'" for scope in RequirementScope)
REQUIREMENT_MODALITY_VALUES = ", ".join(f"'{modality.value}'" for modality in RequirementModality)
REQUIREMENT_CRITICALITY_VALUES = ", ".join(
    f"'{criticality.value}'" for criticality in RequirementCriticality
)
REQUIREMENT_BASIS_VALUES = ", ".join(f"'{basis.value}'" for basis in RequirementBasis)
REQUIREMENT_SUBSANABILITY_VALUES = ", ".join(
    f"'{subsanability.value}'" for subsanability in RequirementSubsanability
)
REQUIREMENT_EVIDENCE_STATUS_VALUES = ", ".join(
    f"'{status.value}'" for status in RequirementEvidenceStatus
)
REQUIREMENT_REVIEW_STATUS_VALUES = ", ".join(
    f"'{status.value}'" for status in RequirementReviewStatus
)
REQUIREMENT_EVIDENCE_ROLE_VALUES = ", ".join(f"'{role.value}'" for role in RequirementEvidenceRole)
REQUIREMENT_EVIDENCE_VALIDATION_STATUS_VALUES = ", ".join(
    f"'{status.value}'" for status in RequirementEvidenceValidationStatus
)
REQUIREMENT_RELATION_TYPE_VALUES = ", ".join(
    f"'{relation.value}'" for relation in RequirementRelationType
)
REJECTED_CANDIDATE_REASON_VALUES = ", ".join(
    f"'{reason.value}'" for reason in RejectedCandidateReason
)
COMPANY_PROFILE_STATUS_VALUES = ", ".join(f"'{status.value}'" for status in CompanyProfileStatus)
COMPANY_RECORD_STATUS_VALUES = ", ".join(f"'{status.value}'" for status in CompanyRecordStatus)
COMPANY_LEGAL_REGISTRATION_TYPE_VALUES = ", ".join(
    f"'{item.value}'" for item in CompanyLegalRegistrationType
)
COMPANY_CAPABILITY_CATEGORY_VALUES = ", ".join(
    f"'{item.value}'" for item in CompanyCapabilityCategory
)
COMPANY_CERTIFICATION_TYPE_VALUES = ", ".join(
    f"'{item.value}'" for item in CompanyCertificationType
)
COMPANY_EVIDENCE_TYPE_VALUES = ", ".join(f"'{item.value}'" for item in CompanyEvidenceType)
COMPANY_EVIDENCE_REVIEW_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in CompanyEvidenceReviewStatus
)
COMPANY_EVIDENCE_SUBJECT_TYPE_VALUES = ", ".join(
    f"'{item.value}'" for item in CompanyEvidenceSubjectType
)
COMPANY_EVIDENCE_ROLE_VALUES = ", ".join(f"'{item.value}'" for item in CompanyEvidenceRole)
COMPANY_EVIDENCE_VALIDATION_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in CompanyEvidenceValidationStatus
)
COMPANY_SNAPSHOT_STATUS_VALUES = ", ".join(f"'{item.value}'" for item in CompanySnapshotStatus)
FINANCIAL_EVALUATION_JOB_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in FinancialEvaluationJobStatus
)
FINANCIAL_EVALUATION_RUN_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in FinancialEvaluationRunStatus
)
FINANCIAL_EVALUATION_RESULT_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in FinancialEvaluationResultStatus
)
FINANCIAL_EVALUATION_REVIEW_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in FinancialEvaluationReviewStatus
)
FINANCIAL_RULE_TYPE_VALUES = ", ".join(f"'{item.value}'" for item in FinancialRuleType)
FINANCIAL_RULE_MAPPING_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in FinancialRuleMappingStatus
)
FINANCIAL_OPERATOR_VALUES = ", ".join(f"'{item.value}'" for item in FinancialOperator)
FINANCIAL_PERIOD_POLICY_VALUES = ", ".join(f"'{item.value}'" for item in FinancialPeriodPolicy)
FINANCIAL_RULE_SOURCE_BASIS_VALUES = ", ".join(
    f"'{item.value}'" for item in FinancialRuleSourceBasis
)
FINANCIAL_CALCULATION_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in FinancialCalculationStatus
)
FINANCIAL_METRIC_TYPE_VALUES = ", ".join(f"'{item.value}'" for item in FinancialMetricType)
DECISION_OUTCOME_VALUES = ", ".join(f"'{item.value}'" for item in DecisionOutcome)
DECISION_JOB_STATUS_VALUES = ", ".join(f"'{item.value}'" for item in DecisionJobStatus)
DECISION_RUN_STATUS_VALUES = ", ".join(f"'{item.value}'" for item in DecisionRunStatus)
DECISION_FINDING_OUTCOME_VALUES = ", ".join(f"'{item.value}'" for item in DecisionFindingOutcome)
DECISION_FINDING_APPLICABILITY_VALUES = ", ".join(
    f"'{item.value}'" for item in DecisionFindingApplicability
)
DECISION_FINDING_SOURCE_TYPE_VALUES = ", ".join(
    f"'{item.value}'" for item in DecisionFindingSourceType
)
DECISION_RULE_STATUS_VALUES = ", ".join(f"'{item.value}'" for item in DecisionRuleStatus)
DECISION_REVIEW_ACTION_VALUES = ", ".join(f"'{item.value}'" for item in DecisionReviewAction)
DECISION_ACTION_TYPE_VALUES = ", ".join(f"'{item.value}'" for item in DecisionActionType)
DECISION_ACTION_PRIORITY_VALUES = ", ".join(f"'{item.value}'" for item in DecisionActionPriority)
DECISION_ACTION_STATUS_VALUES = ", ".join(f"'{item.value}'" for item in DecisionActionStatus)
DECISION_REPORT_JOB_STATUS_VALUES = ", ".join(f"'{item.value}'" for item in DecisionReportJobStatus)
DECISION_REPORT_PACKAGE_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in DecisionReportPackageStatus
)
DECISION_REPORT_ARTIFACT_TYPE_VALUES = ", ".join(
    f"'{item.value}'" for item in DecisionReportArtifactType
)
SPECIALIZED_DOMAIN_VALUES = ", ".join(f"'{item.value}'" for item in SpecializedEvaluationDomain)
SPECIALIZED_JOB_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in SpecializedEvaluationJobStatus
)
SPECIALIZED_RUN_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in SpecializedEvaluationRunStatus
)
SPECIALIZED_RESULT_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in SpecializedEvaluationResultStatus
)
SPECIALIZED_REVIEW_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in SpecializedEvaluationReviewStatus
)
SPECIALIZED_RULE_TYPE_VALUES = ", ".join(f"'{item.value}'" for item in SpecializedRuleType)
SPECIALIZED_RULE_MAPPING_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in SpecializedRuleMappingStatus
)
SPECIALIZED_OPERATOR_VALUES = ", ".join(f"'{item.value}'" for item in SpecializedOperator)
SPECIALIZED_RULE_SOURCE_BASIS_VALUES = ", ".join(
    f"'{item.value}'" for item in SpecializedRuleSourceBasis
)
SPECIALIZED_EVIDENCE_VALIDATION_STATUS_VALUES = ", ".join(
    f"'{item.value}'" for item in SpecializedEvidenceValidationStatus
)


class Process(Base):
    """Proceso de contratacion registrado manualmente."""

    __tablename__ = "processes"
    __table_args__ = (
        CheckConstraint(f"status IN ({PROCESS_STATUS_VALUES})", name="ck_processes_status"),
        CheckConstraint(f"source IN ({PROCESS_SOURCE_VALUES})", name="ck_processes_source"),
        CheckConstraint(
            "closing_at IS NULL OR published_at IS NULL OR closing_at >= published_at",
            name="ck_processes_closing_after_published",
        ),
        CheckConstraint("btrim(title) <> ''", name="ck_processes_title_not_blank"),
        CheckConstraint(
            "btrim(contracting_entity) <> ''",
            name="ck_processes_contracting_entity_not_blank",
        ),
        Index("ix_processes_created_at", "created_at"),
        Index("ix_processes_status", "status"),
        Index("ix_processes_is_system", "is_system"),
        Index("ix_processes_internal_reference", "internal_reference", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    internal_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    secop_reference: Mapped[str | None] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    contracting_entity: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(2083))
    selection_method: Mapped[str | None] = mapped_column(String(500))
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ProcessStatus.DRAFT.value,
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ProcessSource.MANUAL.value,
    )
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    documents: Mapped[list["ProcessDocument"]] = relationship(
        back_populates="process",
        cascade="all, delete-orphan",
        order_by="ProcessDocument.created_at",
    )
    company_profiles: Mapped[list["CompanyProfile"]] = relationship(
        back_populates="system_process",
        cascade="all, delete-orphan",
        order_by="CompanyProfile.created_at",
    )
    events: Mapped[list["ImportEvent"]] = relationship(
        back_populates="process",
        cascade="all, delete-orphan",
    )
    normalization_jobs: Mapped[list["RequirementNormalizationJob"]] = relationship(
        back_populates="process",
        cascade="all, delete-orphan",
        order_by="RequirementNormalizationJob.created_at",
    )
    normalization_runs: Mapped[list["RequirementNormalizationRun"]] = relationship(
        back_populates="process",
        cascade="all, delete-orphan",
        order_by="RequirementNormalizationRun.created_at",
    )
    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="process",
        cascade="all, delete-orphan",
        order_by="Requirement.created_at",
    )
    financial_evaluation_jobs: Mapped[list["FinancialEvaluationJob"]] = relationship(
        back_populates="process",
        cascade="all, delete-orphan",
        order_by="FinancialEvaluationJob.created_at",
    )
    financial_evaluation_runs: Mapped[list["FinancialEvaluationRun"]] = relationship(
        back_populates="process",
        cascade="all, delete-orphan",
        order_by="FinancialEvaluationRun.created_at",
    )


class ProcessDocument(Base):
    """Metadata de un documento original almacenado fuera de PostgreSQL."""

    __tablename__ = "process_documents"
    __table_args__ = (
        UniqueConstraint("process_id", "sha256", name="uq_process_documents_process_sha256"),
        CheckConstraint(f"document_type IN ({DOCUMENT_TYPE_VALUES})", name="ck_documents_type"),
        CheckConstraint(
            f"upload_status IN ({DOCUMENT_UPLOAD_STATUS_VALUES})",
            name="ck_documents_upload_status",
        ),
        CheckConstraint(
            f"processing_status IN ({DOCUMENT_PROCESSING_STATUS_VALUES})",
            name="ck_documents_processing_status",
        ),
        CheckConstraint("size_bytes > 0", name="ck_documents_size_positive"),
        CheckConstraint("sha256 ~ '^[a-f0-9]{64}$'", name="ck_documents_sha256"),
        Index("ix_process_documents_process_id", "process_id"),
        Index("ix_process_documents_processing_status", "processing_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(700), nullable=False, unique=True)
    declared_content_type: Mapped[str | None] = mapped_column(String(255))
    detected_content_type: Mapped[str | None] = mapped_column(String(255))
    extension: Mapped[str] = mapped_column(String(16), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=DocumentType.UNKNOWN.value,
    )
    upload_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DocumentUploadStatus.STORED.value,
    )
    processing_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DocumentProcessingStatus.NOT_QUEUED.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    process: Mapped[Process] = relationship(back_populates="documents")
    events: Mapped[list["ImportEvent"]] = relationship(back_populates="document")
    processing_jobs: Mapped[list["DocumentProcessingJob"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentProcessingJob.created_at",
    )
    extractions: Mapped[list["DocumentExtraction"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentExtraction.created_at",
    )
    company_evidence_document: Mapped["CompanyEvidenceDocument | None"] = relationship(
        back_populates="process_document",
        uselist=False,
    )


class DocumentProcessingJob(Base):
    """Trabajo de procesamiento documental respaldado por PostgreSQL."""

    __tablename__ = "document_processing_jobs"
    __table_args__ = (
        CheckConstraint(
            f"job_type IN ({DOCUMENT_PROCESSING_JOB_TYPE_VALUES})",
            name="ck_processing_jobs_type",
        ),
        CheckConstraint(
            f"status IN ({DOCUMENT_PROCESSING_JOB_STATUS_VALUES})",
            name="ck_processing_jobs_status",
        ),
        CheckConstraint("priority >= 0", name="ck_processing_jobs_priority_nonnegative"),
        CheckConstraint("attempt_count >= 0", name="ck_processing_jobs_attempt_nonnegative"),
        CheckConstraint("max_attempts > 0", name="ck_processing_jobs_max_attempts_positive"),
        Index(
            "ix_processing_jobs_claim",
            "status",
            "available_at",
            "priority",
            "created_at",
        ),
        Index("ix_processing_jobs_document_id", "document_id"),
        Index(
            "uq_processing_jobs_active_document_type",
            "document_id",
            "job_type",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'PROCESSING')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("process_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=DocumentProcessingJobType.EXTRACT_DOCUMENT.value,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DocumentProcessingJobStatus.PENDING.value,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(128))
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    last_error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped[ProcessDocument] = relationship(back_populates="processing_jobs")
    extractions: Mapped[list["DocumentExtraction"]] = relationship(back_populates="job")


class DocumentExtraction(Base):
    """Ejecucion versionada de extraccion deterministica."""

    __tablename__ = "document_extractions"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({DOCUMENT_EXTRACTION_STATUS_VALUES})",
            name="ck_document_extractions_status",
        ),
        CheckConstraint("source_sha256 ~ '^[a-f0-9]{64}$'", name="ck_extractions_sha256"),
        CheckConstraint("page_count IS NULL OR page_count >= 0", name="ck_extractions_page_count"),
        CheckConstraint(
            "sheet_count IS NULL OR sheet_count >= 0", name="ck_extractions_sheet_count"
        ),
        CheckConstraint("segment_count >= 0", name="ck_extractions_segment_count"),
        CheckConstraint("character_count >= 0", name="ck_extractions_character_count"),
        Index("ix_document_extractions_document_id", "document_id"),
        Index("ix_document_extractions_job_id", "job_id"),
        Index(
            "uq_document_extractions_active_version",
            "document_id",
            "source_sha256",
            "extractor_name",
            "extractor_version",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'PROCESSING')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("process_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("document_processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    extractor_name: Mapped[str] = mapped_column(String(128), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    detected_format: Mapped[str] = mapped_column(String(32), nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer)
    sheet_count: Mapped[int | None] = mapped_column(Integer)
    segment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    language_hint: Mapped[str | None] = mapped_column(String(32))
    warnings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped[ProcessDocument] = relationship(back_populates="extractions")
    job: Mapped[DocumentProcessingJob] = relationship(back_populates="extractions")
    segments: Mapped[list["ExtractedSegment"]] = relationship(
        back_populates="extraction",
        cascade="all, delete-orphan",
        order_by="ExtractedSegment.sequence",
    )


class ExtractedSegment(Base):
    """Segmento extraido con ubicacion reproducible de origen."""

    __tablename__ = "extracted_segments"
    __table_args__ = (
        UniqueConstraint("extraction_id", "sequence", name="uq_segments_extraction_sequence"),
        CheckConstraint(
            f"segment_type IN ({EXTRACTED_SEGMENT_TYPE_VALUES})",
            name="ck_segments_type",
        ),
        CheckConstraint("sequence > 0", name="ck_segments_sequence_positive"),
        CheckConstraint("btrim(text) <> ''", name="ck_segments_text_not_blank"),
        CheckConstraint("page_number IS NULL OR page_number > 0", name="ck_segments_page_positive"),
        CheckConstraint(
            "paragraph_index IS NULL OR paragraph_index > 0",
            name="ck_segments_paragraph_positive",
        ),
        CheckConstraint(
            "table_index IS NULL OR table_index > 0", name="ck_segments_table_positive"
        ),
        CheckConstraint(
            "row_start IS NULL OR row_start > 0", name="ck_segments_row_start_positive"
        ),
        CheckConstraint("row_end IS NULL OR row_end >= row_start", name="ck_segments_row_range"),
        CheckConstraint(
            "line_start IS NULL OR line_start > 0", name="ck_segments_line_start_positive"
        ),
        CheckConstraint(
            "line_end IS NULL OR line_end >= line_start", name="ck_segments_line_range"
        ),
        Index("ix_extracted_segments_extraction_id", "extraction_id"),
        Index("ix_extracted_segments_page_number", "page_number"),
        Index("ix_extracted_segments_sheet_name", "sheet_name"),
        Index("ix_extracted_segments_segment_type", "segment_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    extraction_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("document_extractions.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    segment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    paragraph_index: Mapped[int | None] = mapped_column(Integer)
    table_index: Mapped[int | None] = mapped_column(Integer)
    sheet_name: Mapped[str | None] = mapped_column(String(255))
    row_start: Mapped[int | None] = mapped_column(Integer)
    row_end: Mapped[int | None] = mapped_column(Integer)
    line_start: Mapped[int | None] = mapped_column(Integer)
    line_end: Mapped[int | None] = mapped_column(Integer)
    source_location: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    segment_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    extraction: Mapped[DocumentExtraction] = relationship(back_populates="segments")


class PromptVersion(Base):
    """Version inmutable de prompts de agentes."""

    __tablename__ = "prompt_versions"
    __table_args__ = (
        CheckConstraint("btrim(prompt_name) <> ''", name="ck_prompt_versions_name_not_blank"),
        CheckConstraint(
            "content_sha256 ~ '^[a-f0-9]{64}$'",
            name="ck_prompt_versions_content_sha256",
        ),
        Index("ix_prompt_versions_name_active", "prompt_name", "is_active"),
        Index(
            "ix_prompt_versions_identity",
            "prompt_name",
            "semantic_version",
            "content_sha256",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    prompt_name: Mapped[str] = mapped_column(String(128), nullable=False)
    semantic_version: Mapped[str] = mapped_column(String(32), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    system_content: Mapped[str] = mapped_column(Text, nullable=False)
    user_template_content: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="openai")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RequirementNormalizationJob(Base):
    """Trabajo PostgreSQL para normalizacion de requisitos a nivel de proceso."""

    __tablename__ = "requirement_normalization_jobs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({REQUIREMENT_NORMALIZATION_STATUS_VALUES})",
            name="ck_requirement_normalization_jobs_status",
        ),
        CheckConstraint(
            "priority >= 0",
            name="ck_requirement_normalization_jobs_priority_nonnegative",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_requirement_normalization_jobs_attempt_nonnegative",
        ),
        CheckConstraint(
            "max_attempts > 0",
            name="ck_requirement_normalization_jobs_max_attempts_positive",
        ),
        Index(
            "ix_requirement_normalization_jobs_claim",
            "status",
            "available_at",
            "priority",
            "created_at",
        ),
        Index("ix_requirement_normalization_jobs_process_id", "process_id"),
        Index("ix_requirement_normalization_jobs_run_id", "run_id"),
        Index(
            "uq_requirement_normalization_active_process",
            "process_id",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'PROCESSING')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=RequirementNormalizationStatus.PENDING.value,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(128))
    force: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    last_error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    process: Mapped[Process] = relationship(back_populates="normalization_jobs")


class RequirementNormalizationRun(Base):
    """Ejecucion auditable e inmutable de normalizacion."""

    __tablename__ = "requirement_normalization_runs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({REQUIREMENT_NORMALIZATION_STATUS_VALUES})",
            name="ck_requirement_normalization_runs_status",
        ),
        CheckConstraint(
            f"provider IN ({NORMALIZATION_PROVIDER_VALUES})",
            name="ck_requirement_normalization_runs_provider",
        ),
        CheckConstraint("segment_count >= 0", name="ck_requirement_normalization_runs_segments"),
        CheckConstraint("batch_count >= 0", name="ck_requirement_normalization_runs_batches"),
        CheckConstraint(
            "candidate_count >= 0", name="ck_requirement_normalization_runs_candidates"
        ),
        CheckConstraint(
            "accepted_requirement_count >= 0",
            name="ck_requirement_normalization_runs_accepted",
        ),
        CheckConstraint(
            "rejected_candidate_count >= 0",
            name="ck_requirement_normalization_runs_rejected",
        ),
        CheckConstraint("warning_count >= 0", name="ck_requirement_normalization_runs_warnings"),
        CheckConstraint("input_tokens >= 0", name="ck_requirement_normalization_runs_input_tokens"),
        CheckConstraint(
            "output_tokens >= 0",
            name="ck_requirement_normalization_runs_output_tokens",
        ),
        CheckConstraint(
            "reasoning_tokens >= 0",
            name="ck_requirement_normalization_runs_reasoning_tokens",
        ),
        CheckConstraint(
            "input_digest ~ '^[a-f0-9]{64}$'",
            name="ck_requirement_normalization_runs_input_digest",
        ),
        Index("ix_requirement_normalization_runs_process_id", "process_id"),
        Index("ix_requirement_normalization_runs_job_id", "job_id"),
        Index("ix_requirement_normalization_runs_created_at", "created_at"),
        Index("ix_requirement_normalization_runs_input_digest", "process_id", "input_digest"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=RequirementNormalizationStatus.PENDING.value,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    reasoning_effort: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompt_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    consolidation_prompt_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompt_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    input_manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    source_extraction_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    segment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    batch_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepted_requirement_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reasoning_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_response_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    process: Mapped[Process] = relationship(back_populates="normalization_runs")
    prompt_version: Mapped[PromptVersion] = relationship(foreign_keys=[prompt_version_id])
    consolidation_prompt_version: Mapped[PromptVersion] = relationship(
        foreign_keys=[consolidation_prompt_version_id]
    )
    batches: Mapped[list["RequirementNormalizationBatch"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="RequirementNormalizationBatch.batch_index",
    )
    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="Requirement.created_at",
    )
    rejected_candidates: Mapped[list["RejectedRequirementCandidate"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class RequirementNormalizationBatch(Base):
    """Lote reproducible de segmentos enviado al proveedor."""

    __tablename__ = "requirement_normalization_batches"
    __table_args__ = (
        UniqueConstraint("run_id", "batch_index", name="uq_requirement_batches_run_index"),
        CheckConstraint(
            f"status IN ({REQUIREMENT_NORMALIZATION_STATUS_VALUES})",
            name="ck_requirement_normalization_batches_status",
        ),
        CheckConstraint("batch_index >= 0", name="ck_requirement_batches_index_nonnegative"),
        CheckConstraint("candidate_count >= 0", name="ck_requirement_batches_candidates"),
        CheckConstraint("input_tokens >= 0", name="ck_requirement_batches_input_tokens"),
        CheckConstraint("output_tokens >= 0", name="ck_requirement_batches_output_tokens"),
        CheckConstraint("reasoning_tokens >= 0", name="ck_requirement_batches_reasoning_tokens"),
        CheckConstraint("input_digest ~ '^[a-f0-9]{64}$'", name="ck_requirement_batches_digest"),
        Index("ix_requirement_normalization_batches_run_id", "run_id"),
        Index("ix_requirement_normalization_batches_run_order", "run_id", "batch_index"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    batch_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=RequirementNormalizationStatus.PENDING.value,
    )
    segment_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_response_id: Mapped[str | None] = mapped_column(String(128))
    structured_output: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reasoning_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    run: Mapped[RequirementNormalizationRun] = relationship(back_populates="batches")


class Requirement(Base):
    """Requisito normalizado validado con evidencia real."""

    __tablename__ = "requirements"
    __table_args__ = (
        UniqueConstraint(
            "normalization_run_id",
            "stable_key",
            name="uq_requirements_run_stable_key",
        ),
        CheckConstraint(
            f"category IN ({REQUIREMENT_CATEGORY_VALUES})", name="ck_requirements_category"
        ),
        CheckConstraint(f"scope IN ({REQUIREMENT_SCOPE_VALUES})", name="ck_requirements_scope"),
        CheckConstraint(
            f"modality IN ({REQUIREMENT_MODALITY_VALUES})",
            name="ck_requirements_modality",
        ),
        CheckConstraint(
            f"criticality IN ({REQUIREMENT_CRITICALITY_VALUES})",
            name="ck_requirements_criticality",
        ),
        CheckConstraint(
            f"criticality_basis IN ({REQUIREMENT_BASIS_VALUES})",
            name="ck_requirements_criticality_basis",
        ),
        CheckConstraint(
            f"subsanability IN ({REQUIREMENT_SUBSANABILITY_VALUES})",
            name="ck_requirements_subsanability",
        ),
        CheckConstraint(
            f"subsanability_basis IN ({REQUIREMENT_BASIS_VALUES})",
            name="ck_requirements_subsanability_basis",
        ),
        CheckConstraint(
            f"evidence_status IN ({REQUIREMENT_EVIDENCE_STATUS_VALUES})",
            name="ck_requirements_evidence_status",
        ),
        CheckConstraint(
            f"review_status IN ({REQUIREMENT_REVIEW_STATUS_VALUES})",
            name="ck_requirements_review_status",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_requirements_confidence"),
        CheckConstraint("stable_key ~ '^[a-f0-9]{64}$'", name="ck_requirements_stable_key"),
        CheckConstraint("btrim(description) <> ''", name="ck_requirements_description_not_blank"),
        Index("ix_requirements_process_id", "process_id"),
        Index("ix_requirements_run_id", "normalization_run_id"),
        Index("ix_requirements_stable_key", "stable_key"),
        Index("ix_requirements_review_status", "review_status"),
        Index("ix_requirements_category", "category"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
    )
    normalization_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    stable_key: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    modality: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    condition_text: Mapped[str | None] = mapped_column(Text)
    expected_value: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    criticality: Mapped[str] = mapped_column(String(32), nullable=False)
    criticality_basis: Mapped[str] = mapped_column(String(32), nullable=False)
    subsanability: Mapped[str] = mapped_column(String(32), nullable=False)
    subsanability_basis: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    evidence_status: Mapped[str] = mapped_column(String(32), nullable=False)
    review_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=RequirementReviewStatus.PENDING.value,
    )
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    process: Mapped[Process] = relationship(back_populates="requirements")
    run: Mapped[RequirementNormalizationRun] = relationship(back_populates="requirements")
    evidence: Mapped[list["RequirementEvidence"]] = relationship(
        back_populates="requirement",
        cascade="all, delete-orphan",
        order_by="RequirementEvidence.created_at",
    )


class RequirementEvidence(Base):
    """Cita verificada de un segmento extraido."""

    __tablename__ = "requirement_evidence"
    __table_args__ = (
        CheckConstraint(
            f"evidence_role IN ({REQUIREMENT_EVIDENCE_ROLE_VALUES})",
            name="ck_requirement_evidence_role",
        ),
        CheckConstraint(
            f"validation_status IN ({REQUIREMENT_EVIDENCE_VALIDATION_STATUS_VALUES})",
            name="ck_requirement_evidence_validation_status",
        ),
        CheckConstraint("btrim(quoted_text) <> ''", name="ck_requirement_evidence_quote_not_blank"),
        CheckConstraint(
            "quote_start IS NULL OR quote_start >= 0",
            name="ck_requirement_evidence_quote_start",
        ),
        CheckConstraint(
            "quote_end IS NULL OR quote_start IS NULL OR quote_end >= quote_start",
            name="ck_requirement_evidence_quote_range",
        ),
        Index("ix_requirement_evidence_requirement_id", "requirement_id"),
        Index("ix_requirement_evidence_segment_id", "segment_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
    )
    extraction_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("document_extractions.id", ondelete="CASCADE"),
        nullable=False,
    )
    segment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("extracted_segments.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_role: Mapped[str] = mapped_column(String(32), nullable=False)
    quoted_text: Mapped[str] = mapped_column(Text, nullable=False)
    quote_start: Mapped[int | None] = mapped_column(Integer)
    quote_end: Mapped[int | None] = mapped_column(Integer)
    source_location: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    requirement: Mapped[Requirement] = relationship(back_populates="evidence")


class RequirementRelation(Base):
    """Relacion propuesta entre requisitos normalizados."""

    __tablename__ = "requirement_relations"
    __table_args__ = (
        UniqueConstraint(
            "normalization_run_id",
            "source_requirement_id",
            "target_requirement_id",
            "relation_type",
            name="uq_requirement_relations_unique",
        ),
        CheckConstraint(
            f"relation_type IN ({REQUIREMENT_RELATION_TYPE_VALUES})",
            name="ck_requirement_relations_type",
        ),
        CheckConstraint(
            "source_requirement_id <> target_requirement_id",
            name="ck_requirement_relations_not_self",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_requirement_relations_confidence",
        ),
        Index("ix_requirement_relations_process_id", "process_id"),
        Index("ix_requirement_relations_run_id", "normalization_run_id"),
        Index("ix_requirement_relations_source", "source_requirement_id"),
        Index("ix_requirement_relations_target", "target_requirement_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
    )
    normalization_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class RejectedRequirementCandidate(Base):
    """Candidato descartado con causa verificable."""

    __tablename__ = "rejected_requirement_candidates"
    __table_args__ = (
        CheckConstraint(
            f"rejection_reason IN ({REJECTED_CANDIDATE_REASON_VALUES})",
            name="ck_rejected_requirement_candidates_reason",
        ),
        Index("ix_rejected_candidates_run_id", "run_id"),
        Index("ix_rejected_candidates_batch_id", "batch_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    batch_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_batches.id", ondelete="SET NULL"),
    )
    candidate_id: Mapped[str | None] = mapped_column(String(128))
    rejection_reason: Mapped[str] = mapped_column(String(64), nullable=False)
    rejection_message: Mapped[str] = mapped_column(String(1000), nullable=False)
    raw_candidate: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    run: Mapped[RequirementNormalizationRun] = relationship(back_populates="rejected_candidates")


class CompanyProfile(Base):
    """Perfil mutable de una empresa local."""

    __tablename__ = "company_profiles"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({COMPANY_PROFILE_STATUS_VALUES})",
            name="ck_company_profiles_status",
        ),
        CheckConstraint("btrim(legal_name) <> ''", name="ck_company_profiles_legal_name"),
        Index("ix_company_profiles_internal_reference", "internal_reference", unique=True),
        Index("ix_company_profiles_tax_id", "tax_id"),
        Index("ix_company_profiles_status", "status"),
        UniqueConstraint("tax_id_type", "tax_id", name="uq_company_profiles_tax_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    system_process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    internal_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(500), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(500))
    tax_id: Mapped[str | None] = mapped_column(String(128))
    tax_id_type: Mapped[str | None] = mapped_column(String(64))
    company_type: Mapped[str | None] = mapped_column(String(128))
    legal_nature: Mapped[str | None] = mapped_column(String(128))
    incorporation_date: Mapped[datetime | None] = mapped_column(Date)
    country: Mapped[str | None] = mapped_column(String(64), default="CO")
    department: Mapped[str | None] = mapped_column(String(128))
    city: Mapped[str | None] = mapped_column(String(128))
    address: Mapped[str | None] = mapped_column(String(500))
    website: Mapped[str | None] = mapped_column(String(2083))
    primary_email: Mapped[str | None] = mapped_column(String(320))
    primary_phone: Mapped[str | None] = mapped_column(String(128))
    economic_activity_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=CompanyProfileStatus.DRAFT.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    system_process: Mapped[Process] = relationship(back_populates="company_profiles")
    legal_registrations: Mapped[list["CompanyLegalRegistration"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    rup_snapshots: Mapped[list["RupSnapshot"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    unspsc_codes: Mapped[list["CompanyUnspscCode"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    financial_periods: Mapped[list["CompanyFinancialPeriod"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    experience_records: Mapped[list["CompanyExperienceRecord"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    people: Mapped[list["CompanyPerson"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    certifications: Mapped[list["CompanyCertification"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    capabilities: Mapped[list["CompanyCapability"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    evidence_documents: Mapped[list["CompanyEvidenceDocument"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    evidence_links: Mapped[list["CompanyEvidenceLink"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["CompanyProfileSnapshot"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    audit_events: Mapped[list["CompanyAuditEvent"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class CompanyLegalRegistration(Base):
    __tablename__ = "company_legal_registrations"
    __table_args__ = (
        CheckConstraint(
            f"registration_type IN ({COMPANY_LEGAL_REGISTRATION_TYPE_VALUES})",
            name="ck_company_legal_registrations_type",
        ),
        CheckConstraint(
            f"status IN ({COMPANY_RECORD_STATUS_VALUES})",
            name="ck_company_legal_registrations_status",
        ),
        CheckConstraint(
            "expires_at IS NULL OR issued_at IS NULL OR expires_at >= issued_at",
            name="ck_company_legal_registrations_dates",
        ),
        Index("ix_company_legal_registrations_company_id", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    registration_type: Mapped[str] = mapped_column(String(64), nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(255))
    issuing_authority: Mapped[str | None] = mapped_column(String(500))
    issued_at: Mapped[datetime | None] = mapped_column(Date)
    expires_at: Mapped[datetime | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    declared_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    company: Mapped[CompanyProfile] = relationship(back_populates="legal_registrations")


class RupSnapshot(Base):
    __tablename__ = "rup_snapshots"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({COMPANY_RECORD_STATUS_VALUES})",
            name="ck_rup_snapshots_status",
        ),
        CheckConstraint(
            "valid_until IS NULL OR issued_at IS NULL OR valid_until >= issued_at",
            name="ck_rup_snapshots_dates",
        ),
        Index("ix_rup_snapshots_company_id", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    registration_number: Mapped[str | None] = mapped_column(String(255))
    issued_at: Mapped[datetime | None] = mapped_column(Date)
    valid_until: Mapped[datetime | None] = mapped_column(Date)
    renewal_year: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    financial_period_reference: Mapped[str | None] = mapped_column(String(255))
    organization_capacity: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    technical_capacity: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    financial_capacity: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    experience_capacity: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    raw_declared_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    company: Mapped[CompanyProfile] = relationship(back_populates="rup_snapshots")


class CompanyUnspscCode(Base):
    __tablename__ = "company_unspsc_codes"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({COMPANY_RECORD_STATUS_VALUES})",
            name="ck_company_unspsc_codes_status",
        ),
        CheckConstraint("btrim(code) <> ''", name="ck_company_unspsc_codes_code"),
        UniqueConstraint("company_id", "code", "valid_until", name="uq_company_unspsc_codes_code"),
        Index("ix_company_unspsc_codes_company_id", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str | None] = mapped_column(String(255))
    valid_from: Mapped[datetime | None] = mapped_column(Date)
    valid_until: Mapped[datetime | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    company: Mapped[CompanyProfile] = relationship(back_populates="unspsc_codes")


class CompanyFinancialPeriod(Base):
    __tablename__ = "company_financial_periods"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({COMPANY_RECORD_STATUS_VALUES})",
            name="ck_company_financial_periods_status",
        ),
        CheckConstraint("period_end >= period_start", name="ck_company_financial_periods_dates"),
        Index("ix_company_financial_periods_company_id", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    period_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    period_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    company: Mapped[CompanyProfile] = relationship(back_populates="financial_periods")
    metrics: Mapped[list["CompanyFinancialMetric"]] = relationship(
        back_populates="financial_period", cascade="all, delete-orphan"
    )


class CompanyFinancialMetric(Base):
    __tablename__ = "company_financial_metrics"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({COMPANY_RECORD_STATUS_VALUES})",
            name="ck_company_financial_metrics_status",
        ),
        Index("ix_company_financial_metrics_period_id", "financial_period_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    financial_period_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("company_financial_periods.id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_type: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(64))
    source_value: Mapped[str | None] = mapped_column(String(500))
    is_calculated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    formula: Mapped[str | None] = mapped_column(Text)
    formula_inputs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    calculation_version: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    financial_period: Mapped[CompanyFinancialPeriod] = relationship(back_populates="metrics")


class CompanyExperienceRecord(Base):
    __tablename__ = "company_experience_records"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({COMPANY_RECORD_STATUS_VALUES})",
            name="ck_company_experience_records_status",
        ),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_company_experience_records_dates",
        ),
        CheckConstraint(
            "company_participation_percentage IS NULL OR "
            "(company_participation_percentage >= 0 AND company_participation_percentage <= 100)",
            name="ck_company_experience_records_percentage",
        ),
        Index("ix_company_experience_records_company_id", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    contract_reference: Mapped[str | None] = mapped_column(String(255))
    contracting_party: Mapped[str] = mapped_column(String(500), nullable=False)
    contract_title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(128))
    sector: Mapped[str | None] = mapped_column(String(255))
    contract_type: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[datetime | None] = mapped_column(Date)
    end_date: Mapped[datetime | None] = mapped_column(Date)
    execution_status: Mapped[str] = mapped_column(String(64), nullable=False)
    total_contract_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    company_participation_percentage: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    company_attributable_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 2))
    attributable_value_formula: Mapped[str | None] = mapped_column(Text)
    consortium_name: Mapped[str | None] = mapped_column(String(500))
    consortium_members: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    unspsc_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    activities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    scope_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    company: Mapped[CompanyProfile] = relationship(back_populates="experience_records")


class CompanyPerson(Base):
    __tablename__ = "company_people"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({COMPANY_RECORD_STATUS_VALUES})",
            name="ck_company_people_status",
        ),
        Index("ix_company_people_company_id", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(500), nullable=False)
    identification_type: Mapped[str | None] = mapped_column(String(64))
    identification_number: Mapped[str | None] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(128))
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    availability_status: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    company: Mapped[CompanyProfile] = relationship(back_populates="people")
    education: Mapped[list["PersonEducation"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    experience: Mapped[list["PersonExperience"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    credentials: Mapped[list["PersonCredential"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )


class PersonEducation(Base):
    __tablename__ = "person_education"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_people.id", ondelete="CASCADE"), nullable=False
    )
    degree_type: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(500))
    graduation_date: Mapped[datetime | None] = mapped_column(Date)
    country: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    person: Mapped[CompanyPerson] = relationship(back_populates="education")


class PersonExperience(Base):
    __tablename__ = "person_experience"
    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_person_experience_dates",
        ),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_people.id", ondelete="CASCADE"), nullable=False
    )
    organization: Mapped[str] = mapped_column(String(500), nullable=False)
    role: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[datetime | None] = mapped_column(Date)
    end_date: Mapped[datetime | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    person: Mapped[CompanyPerson] = relationship(back_populates="experience")


class PersonCredential(Base):
    __tablename__ = "person_credentials"
    __table_args__ = (
        CheckConstraint(
            "expires_at IS NULL OR issued_at IS NULL OR expires_at >= issued_at",
            name="ck_person_credentials_dates",
        ),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_people.id", ondelete="CASCADE"), nullable=False
    )
    credential_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(500))
    credential_number: Mapped[str | None] = mapped_column(String(255))
    issued_at: Mapped[datetime | None] = mapped_column(Date)
    expires_at: Mapped[datetime | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    person: Mapped[CompanyPerson] = relationship(back_populates="credentials")


class CompanyCertification(Base):
    __tablename__ = "company_certifications"
    __table_args__ = (
        CheckConstraint(
            f"certification_type IN ({COMPANY_CERTIFICATION_TYPE_VALUES})",
            name="ck_company_certifications_type",
        ),
        CheckConstraint(
            f"status IN ({COMPANY_RECORD_STATUS_VALUES})",
            name="ck_company_certifications_status",
        ),
        CheckConstraint(
            "expires_at IS NULL OR issued_at IS NULL OR expires_at >= issued_at",
            name="ck_company_certifications_dates",
        ),
        Index("ix_company_certifications_company_id", "company_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    certification_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(500))
    certificate_number: Mapped[str | None] = mapped_column(String(255))
    scope: Mapped[str | None] = mapped_column(Text)
    issued_at: Mapped[datetime | None] = mapped_column(Date)
    expires_at: Mapped[datetime | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    company: Mapped[CompanyProfile] = relationship(back_populates="certifications")


class CompanyCapability(Base):
    __tablename__ = "company_capabilities"
    __table_args__ = (
        CheckConstraint(
            f"category IN ({COMPANY_CAPABILITY_CATEGORY_VALUES})",
            name="ck_company_capabilities_category",
        ),
        CheckConstraint(
            f"status IN ({COMPANY_RECORD_STATUS_VALUES})",
            name="ck_company_capabilities_status",
        ),
        Index("ix_company_capabilities_company_id", "company_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    value: Mapped[str | None] = mapped_column(String(500))
    unit: Mapped[str | None] = mapped_column(String(64))
    territorial_scope: Mapped[str | None] = mapped_column(String(500))
    valid_from: Mapped[datetime | None] = mapped_column(Date)
    valid_until: Mapped[datetime | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyRecordStatus.DECLARED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    company: Mapped[CompanyProfile] = relationship(back_populates="capabilities")


class CompanyEvidenceDocument(Base):
    __tablename__ = "company_evidence_documents"
    __table_args__ = (
        UniqueConstraint("company_id", "process_document_id", name="uq_company_evidence_document"),
        UniqueConstraint("company_id", "sha256", name="uq_company_evidence_sha256"),
        CheckConstraint(
            f"evidence_type IN ({COMPANY_EVIDENCE_TYPE_VALUES})",
            name="ck_company_evidence_documents_type",
        ),
        CheckConstraint(
            f"review_status IN ({COMPANY_EVIDENCE_REVIEW_STATUS_VALUES})",
            name="ck_company_evidence_documents_review_status",
        ),
        Index("ix_company_evidence_documents_company_id", "company_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    process_document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("process_documents.id", ondelete="CASCADE"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(500))
    issued_at: Mapped[datetime | None] = mapped_column(Date)
    expires_at: Mapped[datetime | None] = mapped_column(Date)
    review_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyEvidenceReviewStatus.PENDING.value
    )
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    company: Mapped[CompanyProfile] = relationship(back_populates="evidence_documents")
    process_document: Mapped[ProcessDocument] = relationship(
        back_populates="company_evidence_document"
    )


class CompanyEvidenceLink(Base):
    __tablename__ = "company_evidence_links"
    __table_args__ = (
        CheckConstraint(
            f"subject_type IN ({COMPANY_EVIDENCE_SUBJECT_TYPE_VALUES})",
            name="ck_company_evidence_links_subject_type",
        ),
        CheckConstraint(
            f"evidence_role IN ({COMPANY_EVIDENCE_ROLE_VALUES})",
            name="ck_company_evidence_links_role",
        ),
        CheckConstraint(
            f"validation_status IN ({COMPANY_EVIDENCE_VALIDATION_STATUS_VALUES})",
            name="ck_company_evidence_links_validation_status",
        ),
        CheckConstraint(
            f"review_status IN ({COMPANY_EVIDENCE_REVIEW_STATUS_VALUES})",
            name="ck_company_evidence_links_review_status",
        ),
        Index("ix_company_evidence_links_company_id", "company_id"),
        Index("ix_company_evidence_links_subject", "subject_type", "subject_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("company_evidence_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    extraction_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("document_extractions.id", ondelete="SET NULL")
    )
    segment_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("extracted_segments.id", ondelete="SET NULL")
    )
    evidence_role: Mapped[str] = mapped_column(String(32), nullable=False)
    quoted_text: Mapped[str | None] = mapped_column(Text)
    source_location: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    validation_status: Mapped[str] = mapped_column(String(64), nullable=False)
    review_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanyEvidenceReviewStatus.PENDING.value
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    company: Mapped[CompanyProfile] = relationship(back_populates="evidence_links")


class CompanyProfileSnapshot(Base):
    __tablename__ = "company_profile_snapshots"
    __table_args__ = (
        UniqueConstraint("company_id", "version", name="uq_company_profile_snapshots_version"),
        CheckConstraint(
            f"status IN ({COMPANY_SNAPSHOT_STATUS_VALUES})",
            name="ck_company_profile_snapshots_status",
        ),
        CheckConstraint("digest ~ '^[a-f0-9]{64}$'", name="ck_company_profile_snapshots_digest"),
        Index("ix_company_profile_snapshots_company_id", "company_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompanySnapshotStatus.DRAFT.value
    )
    digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    completeness_status: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    company: Mapped[CompanyProfile] = relationship(back_populates="snapshots")


class CompanyAuditEvent(Base):
    __tablename__ = "company_audit_events"
    __table_args__ = (Index("ix_company_audit_events_company_id", "company_id"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="local-user")
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    snapshot_version: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    company: Mapped[CompanyProfile] = relationship(back_populates="audit_events")


class FinancialFormulaVersion(Base):
    __tablename__ = "financial_formula_versions"
    __table_args__ = (
        UniqueConstraint(
            "formula_name", "semantic_version", name="uq_financial_formula_versions_name_version"
        ),
        CheckConstraint("btrim(formula_name) <> ''", name="ck_financial_formula_versions_name"),
        CheckConstraint(
            "btrim(semantic_version) <> ''", name="ck_financial_formula_versions_version"
        ),
        CheckConstraint("btrim(expression) <> ''", name="ck_financial_formula_versions_expression"),
        CheckConstraint(
            f"output_metric_type IN ({FINANCIAL_METRIC_TYPE_VALUES})",
            name="ck_financial_formula_versions_output_metric",
        ),
        Index("ix_financial_formula_versions_active", "formula_name", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    formula_name: Mapped[str] = mapped_column(String(128), nullable=False)
    semantic_version: Mapped[str] = mapped_column(String(32), nullable=False)
    expression: Mapped[str] = mapped_column(Text, nullable=False)
    required_metric_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    output_metric_type: Mapped[str] = mapped_column(String(64), nullable=False)
    output_unit: Mapped[str | None] = mapped_column(String(64))
    rounding_policy: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FinancialRequirementRule(Base):
    __tablename__ = "financial_requirement_rules"
    __table_args__ = (
        UniqueConstraint(
            "normalization_run_id",
            "requirement_id",
            "version",
            name="uq_financial_requirement_rules_version",
        ),
        CheckConstraint(
            f"rule_type IN ({FINANCIAL_RULE_TYPE_VALUES})",
            name="ck_financial_requirement_rules_type",
        ),
        CheckConstraint(
            f"metric_type IS NULL OR metric_type IN ({FINANCIAL_METRIC_TYPE_VALUES})",
            name="ck_financial_requirement_rules_metric",
        ),
        CheckConstraint(
            f"operator IS NULL OR operator IN ({FINANCIAL_OPERATOR_VALUES})",
            name="ck_financial_requirement_rules_operator",
        ),
        CheckConstraint(
            f"period_policy IN ({FINANCIAL_PERIOD_POLICY_VALUES})",
            name="ck_financial_requirement_rules_period_policy",
        ),
        CheckConstraint(
            f"source_basis IN ({FINANCIAL_RULE_SOURCE_BASIS_VALUES})",
            name="ck_financial_requirement_rules_source_basis",
        ),
        CheckConstraint(
            f"mapping_status IN ({FINANCIAL_RULE_MAPPING_STATUS_VALUES})",
            name="ck_financial_requirement_rules_mapping_status",
        ),
        CheckConstraint("version > 0", name="ck_financial_requirement_rules_version_positive"),
        Index("ix_financial_requirement_rules_requirement_id", "requirement_id"),
        Index("ix_financial_requirement_rules_run_id", "normalization_run_id"),
        Index(
            "ix_financial_requirement_rules_latest",
            "normalization_run_id",
            "requirement_id",
            "version",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    normalization_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_type: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_type: Mapped[str | None] = mapped_column(String(64))
    operator: Mapped[str | None] = mapped_column(String(64))
    required_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    required_min_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    required_max_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    unit: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str | None] = mapped_column(String(3))
    period_policy: Mapped[str] = mapped_column(String(64), nullable=False)
    period_year: Mapped[int | None] = mapped_column(Integer)
    condition_group: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    source_basis: Mapped[str] = mapped_column(String(64), nullable=False)
    mapping_status: Mapped[str] = mapped_column(String(64), nullable=False)
    mapping_warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    override_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FinancialEvaluationJob(Base):
    __tablename__ = "financial_evaluation_jobs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({FINANCIAL_EVALUATION_JOB_STATUS_VALUES})",
            name="ck_financial_evaluation_jobs_status",
        ),
        CheckConstraint("priority >= 0", name="ck_financial_evaluation_jobs_priority"),
        CheckConstraint("attempt_count >= 0", name="ck_financial_evaluation_jobs_attempts"),
        CheckConstraint("max_attempts > 0", name="ck_financial_evaluation_jobs_max_attempts"),
        Index(
            "ix_financial_evaluation_jobs_claim",
            "status",
            "available_at",
            "priority",
            "created_at",
        ),
        Index(
            "ix_financial_evaluation_jobs_inputs",
            "process_id",
            "normalization_run_id",
            "company_profile_snapshot_id",
        ),
        Index(
            "uq_financial_evaluation_jobs_active_inputs",
            "process_id",
            "normalization_run_id",
            "company_id",
            "company_profile_snapshot_id",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'PROCESSING')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    normalization_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    company_profile_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("company_profile_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=FinancialEvaluationJobStatus.PENDING.value
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(128))
    force: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    last_error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    process: Mapped[Process] = relationship(back_populates="financial_evaluation_jobs")


class FinancialEvaluationRun(Base):
    __tablename__ = "financial_evaluation_runs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({FINANCIAL_EVALUATION_RUN_STATUS_VALUES})",
            name="ck_financial_evaluation_runs_status",
        ),
        CheckConstraint("input_digest ~ '^[a-f0-9]{64}$'", name="ck_financial_runs_digest"),
        CheckConstraint("requirement_count >= 0", name="ck_financial_runs_requirement_count"),
        CheckConstraint("evaluated_count >= 0", name="ck_financial_runs_evaluated_count"),
        CheckConstraint("complies_count >= 0", name="ck_financial_runs_complies_count"),
        CheckConstraint(
            "does_not_comply_count >= 0", name="ck_financial_runs_does_not_comply_count"
        ),
        CheckConstraint("partial_count >= 0", name="ck_financial_runs_partial_count"),
        CheckConstraint("unknown_count >= 0", name="ck_financial_runs_unknown_count"),
        CheckConstraint("not_applicable_count >= 0", name="ck_financial_runs_not_applicable_count"),
        CheckConstraint("conflicting_count >= 0", name="ck_financial_runs_conflicting_count"),
        CheckConstraint("warning_count >= 0", name="ck_financial_runs_warning_count"),
        Index("ix_financial_runs_process_company", "process_id", "company_id", "created_at"),
        Index("ix_financial_runs_inputs", "process_id", "input_digest"),
        Index("ix_financial_runs_snapshot", "company_profile_snapshot_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_evaluation_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    normalization_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    company_profile_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("company_profile_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=FinancialEvaluationRunStatus.PENDING.value
    )
    input_manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), nullable=False)
    formula_versions: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    requirement_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evaluated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    complies_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    does_not_comply_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partial_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unknown_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    not_applicable_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflicting_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    process: Mapped[Process] = relationship(back_populates="financial_evaluation_runs")


class FinancialMetricCalculation(Base):
    __tablename__ = "financial_metric_calculations"
    __table_args__ = (
        CheckConstraint(
            f"metric_type IN ({FINANCIAL_METRIC_TYPE_VALUES})",
            name="ck_financial_metric_calculations_metric",
        ),
        CheckConstraint(
            f"status IN ({FINANCIAL_CALCULATION_STATUS_VALUES})",
            name="ck_financial_metric_calculations_status",
        ),
        Index("ix_financial_metric_calculations_run_id", "run_id"),
        Index("ix_financial_metric_calculations_period_id", "financial_period_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("financial_evaluation_runs.id", ondelete="CASCADE")
    )
    financial_period_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    metric_type: Mapped[str] = mapped_column(String(64), nullable=False)
    formula_name: Mapped[str] = mapped_column(String(128), nullable=False)
    formula_version: Mapped[str] = mapped_column(String(32), nullable=False)
    input_values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    raw_result: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    rounded_result: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    unit: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    warning_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FinancialEvaluationResult(Base):
    __tablename__ = "financial_evaluation_results"
    __table_args__ = (
        UniqueConstraint("run_id", "requirement_id", name="uq_financial_results_run_requirement"),
        CheckConstraint(
            f"status IN ({FINANCIAL_EVALUATION_RESULT_STATUS_VALUES})",
            name="ck_financial_evaluation_results_status",
        ),
        CheckConstraint(
            f"review_status IN ({FINANCIAL_EVALUATION_REVIEW_STATUS_VALUES})",
            name="ck_financial_evaluation_results_review_status",
        ),
        CheckConstraint(
            f"metric_type IS NULL OR metric_type IN ({FINANCIAL_METRIC_TYPE_VALUES})",
            name="ck_financial_evaluation_results_metric",
        ),
        CheckConstraint(
            f"operator IS NULL OR operator IN ({FINANCIAL_OPERATOR_VALUES})",
            name="ck_financial_evaluation_results_operator",
        ),
        Index("ix_financial_evaluation_results_run_id", "run_id"),
        Index("ix_financial_evaluation_results_requirement_id", "requirement_id"),
        Index("ix_financial_evaluation_results_status", "status"),
        Index("ix_financial_evaluation_results_period_id", "financial_period_id"),
        Index("ix_financial_evaluation_results_review", "review_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("financial_evaluation_runs.id", ondelete="CASCADE")
    )
    requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    financial_rule_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("financial_requirement_rules.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_type: Mapped[str | None] = mapped_column(String(64))
    operator: Mapped[str | None] = mapped_column(String(64))
    required_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    required_min_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    required_max_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    required_unit: Mapped[str | None] = mapped_column(String(64))
    actual_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    actual_unit: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str | None] = mapped_column(String(3))
    financial_period_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    calculation_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("financial_metric_calculations.id", ondelete="SET NULL")
    )
    explanation_code: Mapped[str] = mapped_column(String(64), nullable=False)
    explanation_parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    metric_inputs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    evidence_refs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=FinancialEvaluationReviewStatus.PENDING.value
    )
    reviewed_status: Mapped[str | None] = mapped_column(String(64))
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FinancialEvaluationResultReview(Base):
    __tablename__ = "financial_evaluation_result_reviews"
    __table_args__ = (
        CheckConstraint(
            f"review_status IN ({FINANCIAL_EVALUATION_REVIEW_STATUS_VALUES})",
            name="ck_financial_result_reviews_status",
        ),
        CheckConstraint(
            "override_status IS NULL OR override_status IN "
            f"({FINANCIAL_EVALUATION_RESULT_STATUS_VALUES})",
            name="ck_financial_result_reviews_override_status",
        ),
        Index("ix_financial_result_reviews_result_id", "result_id"),
        Index("ix_financial_result_reviews_reviewed_at", "reviewed_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_evaluation_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    override_status: Mapped[str | None] = mapped_column(String(64))
    override_reason: Mapped[str | None] = mapped_column(Text)
    original_status: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False, default="local-user")
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FinancialEvaluationEvent(Base):
    __tablename__ = "financial_evaluation_events"
    __table_args__ = (
        Index("ix_financial_evaluation_events_run_id", "run_id"),
        Index("ix_financial_evaluation_events_job_id", "job_id"),
        Index("ix_financial_evaluation_events_type", "event_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("financial_evaluation_jobs.id", ondelete="SET NULL")
    )
    run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("financial_evaluation_runs.id", ondelete="SET NULL")
    )
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SpecializedRequirementRule(Base):
    __tablename__ = "specialized_requirement_rules"
    __table_args__ = (
        CheckConstraint(
            f"domain IN ({SPECIALIZED_DOMAIN_VALUES})", name="ck_specialized_rules_domain"
        ),
        CheckConstraint(
            f"rule_type IN ({SPECIALIZED_RULE_TYPE_VALUES})",
            name="ck_specialized_rules_type",
        ),
        CheckConstraint(
            f"mapping_status IN ({SPECIALIZED_RULE_MAPPING_STATUS_VALUES})",
            name="ck_specialized_rules_mapping_status",
        ),
        CheckConstraint(
            f"source_basis IN ({SPECIALIZED_RULE_SOURCE_BASIS_VALUES})",
            name="ck_specialized_rules_source_basis",
        ),
        CheckConstraint(
            f"operator IS NULL OR operator IN ({SPECIALIZED_OPERATOR_VALUES})",
            name="ck_specialized_rules_operator",
        ),
        CheckConstraint("version > 0", name="ck_specialized_rules_version"),
        Index("ix_specialized_rules_requirement", "requirement_id", "domain"),
        Index("ix_specialized_rules_normalization", "normalization_run_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    normalization_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(128))
    operator: Mapped[str | None] = mapped_column(String(64))
    expected_value: Mapped[str | None] = mapped_column(Text)
    expected_min_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    expected_max_value: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    unit: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str | None] = mapped_column(String(3))
    period_policy: Mapped[str | None] = mapped_column(String(64))
    condition_group: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    source_basis: Mapped[str] = mapped_column(String(64), nullable=False)
    mapping_status: Mapped[str] = mapped_column(String(32), nullable=False)
    mapping_warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual_override_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SpecializedEvaluationJob(Base):
    __tablename__ = "specialized_evaluation_jobs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({SPECIALIZED_JOB_STATUS_VALUES})", name="ck_specialized_jobs_status"
        ),
        CheckConstraint(
            f"domain IN ({SPECIALIZED_DOMAIN_VALUES})", name="ck_specialized_jobs_domain"
        ),
        CheckConstraint("priority >= 0", name="ck_specialized_jobs_priority"),
        CheckConstraint("attempt_count >= 0", name="ck_specialized_jobs_attempts"),
        CheckConstraint("max_attempts > 0", name="ck_specialized_jobs_max_attempts"),
        Index("ix_specialized_jobs_claim", "status", "available_at", "priority", "created_at"),
        Index("ix_specialized_jobs_process", "process_id"),
        Index("ix_specialized_jobs_company", "company_id"),
        Index("ix_specialized_jobs_domain", "domain"),
        Index(
            "uq_specialized_jobs_active_inputs",
            "process_id",
            "normalization_run_id",
            "company_id",
            "company_profile_snapshot_id",
            "domain",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'PROCESSING')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    normalization_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    company_profile_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("company_profile_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    run_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SpecializedEvaluationJobStatus.PENDING.value
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(128))
    force: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    last_error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SpecializedEvaluationRun(Base):
    __tablename__ = "specialized_evaluation_runs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({SPECIALIZED_RUN_STATUS_VALUES})", name="ck_specialized_runs_status"
        ),
        CheckConstraint(
            f"domain IN ({SPECIALIZED_DOMAIN_VALUES})", name="ck_specialized_runs_domain"
        ),
        CheckConstraint("input_digest ~ '^[a-f0-9]{64}$'", name="ck_specialized_runs_digest"),
        CheckConstraint("requirement_count >= 0", name="ck_specialized_runs_requirement_count"),
        CheckConstraint("evaluated_count >= 0", name="ck_specialized_runs_evaluated_count"),
        CheckConstraint("complies_count >= 0", name="ck_specialized_runs_complies_count"),
        CheckConstraint(
            "does_not_comply_count >= 0", name="ck_specialized_runs_does_not_comply_count"
        ),
        CheckConstraint("partial_count >= 0", name="ck_specialized_runs_partial_count"),
        CheckConstraint("unknown_count >= 0", name="ck_specialized_runs_unknown_count"),
        CheckConstraint(
            "not_applicable_count >= 0", name="ck_specialized_runs_not_applicable_count"
        ),
        CheckConstraint("conflicting_count >= 0", name="ck_specialized_runs_conflicting_count"),
        CheckConstraint("warning_count >= 0", name="ck_specialized_runs_warning_count"),
        Index("ix_specialized_runs_process_company", "process_id", "company_id", "created_at"),
        Index("ix_specialized_runs_inputs", "process_id", "input_digest"),
        Index("ix_specialized_runs_snapshot", "company_profile_snapshot_id"),
        Index("ix_specialized_runs_domain", "domain"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("specialized_evaluation_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    normalization_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    company_profile_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("company_profile_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SpecializedEvaluationRunStatus.PENDING.value
    )
    input_manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(64), nullable=False)
    requirement_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evaluated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    complies_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    does_not_comply_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partial_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unknown_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    not_applicable_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflicting_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SpecializedEvaluationResult(Base):
    __tablename__ = "specialized_evaluation_results"
    __table_args__ = (
        UniqueConstraint("run_id", "requirement_id", name="uq_specialized_results_run_requirement"),
        CheckConstraint(
            f"domain IN ({SPECIALIZED_DOMAIN_VALUES})", name="ck_specialized_results_domain"
        ),
        CheckConstraint(
            f"status IN ({SPECIALIZED_RESULT_STATUS_VALUES})",
            name="ck_specialized_results_status",
        ),
        CheckConstraint(
            f"review_status IN ({SPECIALIZED_REVIEW_STATUS_VALUES})",
            name="ck_specialized_results_review_status",
        ),
        CheckConstraint(
            f"rule_type IN ({SPECIALIZED_RULE_TYPE_VALUES})",
            name="ck_specialized_results_rule_type",
        ),
        CheckConstraint(
            f"operator IS NULL OR operator IN ({SPECIALIZED_OPERATOR_VALUES})",
            name="ck_specialized_results_operator",
        ),
        Index("ix_specialized_results_run_id", "run_id"),
        Index("ix_specialized_results_requirement_id", "requirement_id"),
        Index("ix_specialized_results_status", "status"),
        Index("ix_specialized_results_domain", "domain"),
        Index("ix_specialized_results_review", "review_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("specialized_evaluation_runs.id", ondelete="CASCADE")
    )
    requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    specialized_rule_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("specialized_requirement_rules.id", ondelete="SET NULL")
    )
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(128))
    operator: Mapped[str | None] = mapped_column(String(64))
    expected_value: Mapped[str | None] = mapped_column(Text)
    actual_value: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(64))
    source_record_type: Mapped[str | None] = mapped_column(String(64))
    source_record_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    explanation_code: Mapped[str] = mapped_column(String(64), nullable=False)
    explanation_parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    evidence_refs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SpecializedEvaluationReviewStatus.PENDING.value
    )
    reviewed_status: Mapped[str | None] = mapped_column(String(64))
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SpecializedEvaluationEvidence(Base):
    __tablename__ = "specialized_evaluation_evidence"
    __table_args__ = (
        CheckConstraint(
            f"validation_status IN ({SPECIALIZED_EVIDENCE_VALIDATION_STATUS_VALUES})",
            name="ck_specialized_evidence_validation",
        ),
        Index("ix_specialized_evidence_result", "result_id"),
        Index("ix_specialized_evidence_document", "company_evidence_document_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("specialized_evaluation_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    company_evidence_link_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    company_evidence_document_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    requirement_evidence_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    extracted_segment_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    quoted_text: Mapped[str | None] = mapped_column(Text)
    source_location: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SpecializedEvaluationReview(Base):
    __tablename__ = "specialized_evaluation_reviews"
    __table_args__ = (
        CheckConstraint(
            "action IN ('CONFIRM', 'OVERRIDE', 'REJECT')",
            name="ck_specialized_reviews_action",
        ),
        CheckConstraint(
            f"original_status IN ({SPECIALIZED_RESULT_STATUS_VALUES})",
            name="ck_specialized_reviews_original_status",
        ),
        CheckConstraint(
            f"reviewed_status IS NULL OR reviewed_status IN ({SPECIALIZED_RESULT_STATUS_VALUES})",
            name="ck_specialized_reviews_reviewed_status",
        ),
        Index("ix_specialized_reviews_result_id", "result_id"),
        Index("ix_specialized_reviews_reviewed_at", "reviewed_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("specialized_evaluation_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    original_status: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewed_status: Mapped[str | None] = mapped_column(String(64))
    reason: Mapped[str | None] = mapped_column(Text)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False, default="local-user")
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SpecializedEvaluationEvent(Base):
    __tablename__ = "specialized_evaluation_events"
    __table_args__ = (
        Index("ix_specialized_events_run_id", "run_id"),
        Index("ix_specialized_events_job_id", "job_id"),
        Index("ix_specialized_events_type", "event_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("specialized_evaluation_jobs.id", ondelete="SET NULL")
    )
    run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("specialized_evaluation_runs.id", ondelete="SET NULL")
    )
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="SET NULL")
    )
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ImportEvent(Base):
    """Evento basico de importacion sin contenido documental."""

    __tablename__ = "import_events"
    __table_args__ = (
        Index("ix_import_events_process_id", "process_id"),
        Index("ix_import_events_document_id", "document_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("process_documents.id", ondelete="SET NULL"),
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    process: Mapped[Process] = relationship(back_populates="events")
    document: Mapped[ProcessDocument | None] = relationship(back_populates="events")


class DecisionPolicyVersion(Base):
    """Snapshot inmutable de una version de la politica de decision."""

    __tablename__ = "decision_policy_versions"
    __table_args__ = (
        UniqueConstraint(
            "policy_name", "semantic_version", name="uq_decision_policy_versions_name_version"
        ),
        CheckConstraint(
            "content_sha256 ~ '^[a-f0-9]{64}$'", name="ck_decision_policy_versions_hash"
        ),
        CheckConstraint("btrim(policy_name) <> ''", name="ck_decision_policy_versions_name"),
        Index("ix_decision_policy_versions_active", "policy_name", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    policy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    semantic_version: Mapped[str] = mapped_column(String(32), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    policy_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class DecisionJob(Base):
    """Trabajo de decision en la cola PostgreSQL."""

    __tablename__ = "decision_jobs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({DECISION_JOB_STATUS_VALUES})", name="ck_decision_jobs_status"
        ),
        CheckConstraint("priority >= 0", name="ck_decision_jobs_priority"),
        CheckConstraint("attempt_count >= 0", name="ck_decision_jobs_attempts"),
        CheckConstraint("max_attempts > 0", name="ck_decision_jobs_max_attempts"),
        Index("ix_decision_jobs_claim", "status", "available_at", "priority", "created_at"),
        Index("ix_decision_jobs_process", "process_id"),
        Index("ix_decision_jobs_company", "company_id"),
        Index(
            "uq_decision_jobs_active_inputs",
            "process_id",
            "normalization_run_id",
            "company_id",
            "company_profile_snapshot_id",
            "financial_evaluation_run_id",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'PROCESSING')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    normalization_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    company_profile_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("company_profile_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    financial_evaluation_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DecisionJobStatus.PENDING.value
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(128))
    force: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    last_error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DecisionRun(Base):
    """Ejecucion inmutable del motor de decision con snapshot de inputs."""

    __tablename__ = "decision_runs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({DECISION_RUN_STATUS_VALUES})", name="ck_decision_runs_status"
        ),
        CheckConstraint(
            f"engine_outcome IS NULL OR engine_outcome IN ({DECISION_OUTCOME_VALUES})",
            name="ck_decision_runs_engine_outcome",
        ),
        CheckConstraint(
            f"reviewed_outcome IS NULL OR reviewed_outcome IN ({DECISION_OUTCOME_VALUES})",
            name="ck_decision_runs_reviewed_outcome",
        ),
        CheckConstraint(
            f"effective_outcome IS NULL OR effective_outcome IN ({DECISION_OUTCOME_VALUES})",
            name="ck_decision_runs_effective_outcome",
        ),
        CheckConstraint("input_digest ~ '^[a-f0-9]{64}$'", name="ck_decision_runs_digest"),
        CheckConstraint("requirement_count >= 0", name="ck_decision_runs_requirement_count"),
        CheckConstraint("finding_count >= 0", name="ck_decision_runs_finding_count"),
        CheckConstraint("action_count >= 0", name="ck_decision_runs_action_count"),
        CheckConstraint("warning_count >= 0", name="ck_decision_runs_warning_count"),
        Index("ix_decision_runs_process_company", "process_id", "company_id", "created_at"),
        Index("ix_decision_runs_inputs", "process_id", "input_digest"),
        Index("ix_decision_runs_snapshot", "company_profile_snapshot_id"),
        Index("ix_decision_runs_outcome", "effective_outcome"),
        Index("ix_decision_runs_policy", "policy_version_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_jobs.id", ondelete="CASCADE"), nullable=False
    )
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    normalization_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_normalization_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False
    )
    company_profile_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("company_profile_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    financial_evaluation_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    policy_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("decision_policy_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DecisionRunStatus.PENDING.value
    )
    engine_outcome: Mapped[str | None] = mapped_column(String(32))
    reviewed_outcome: Mapped[str | None] = mapped_column(String(32))
    effective_outcome: Mapped[str | None] = mapped_column(String(32))
    reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    input_manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    coverage_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    requirement_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    finding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    action_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    policy_version: Mapped[DecisionPolicyVersion] = relationship()


class DecisionInputFindingSnapshot(Base):
    """Hallazgo canonico persistido como parte del snapshot del run."""

    __tablename__ = "decision_input_findings"
    __table_args__ = (
        UniqueConstraint(
            "decision_run_id", "source_finding_key", name="uq_decision_findings_run_key"
        ),
        CheckConstraint(
            f"outcome IN ({DECISION_FINDING_OUTCOME_VALUES})",
            name="ck_decision_findings_outcome",
        ),
        CheckConstraint(
            f"applicability IN ({DECISION_FINDING_APPLICABILITY_VALUES})",
            name="ck_decision_findings_applicability",
        ),
        CheckConstraint(
            f"source_type IN ({DECISION_FINDING_SOURCE_TYPE_VALUES})",
            name="ck_decision_findings_source_type",
        ),
        Index("ix_decision_findings_run", "decision_run_id"),
        Index("ix_decision_findings_requirement", "requirement_id"),
        Index("ix_decision_findings_outcome", "outcome"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    decision_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False
    )
    source_finding_key: Mapped[str] = mapped_column(String(128), nullable=False)
    requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    modality: Mapped[str] = mapped_column(String(64), nullable=False)
    criticality: Mapped[str] = mapped_column(String(32), nullable=False)
    criticality_basis: Mapped[str] = mapped_column(String(32), nullable=False)
    subsanability: Mapped[str] = mapped_column(String(32), nullable=False)
    subsanability_basis: Mapped[str] = mapped_column(String(32), nullable=False)
    evaluation_domain: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_run_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    source_result_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    applicability: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_quality: Mapped[str | None] = mapped_column(String(64))
    review_status: Mapped[str | None] = mapped_column(String(32))
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_blocking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_remediable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    partner_solvable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    submission_blocker: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    condition_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    warning_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence_references: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DecisionRuleEvaluationRecord(Base):
    """Evaluacion trazable de una regla dentro de un run."""

    __tablename__ = "decision_rule_evaluations"
    __table_args__ = (
        UniqueConstraint("decision_run_id", "rule_code", name="uq_decision_rules_run_code"),
        CheckConstraint(
            f"status IN ({DECISION_RULE_STATUS_VALUES})", name="ck_decision_rules_status"
        ),
        CheckConstraint(
            f"suggested_outcome IS NULL OR suggested_outcome IN ({DECISION_OUTCOME_VALUES})",
            name="ck_decision_rules_suggested_outcome",
        ),
        Index("ix_decision_rules_run", "decision_run_id"),
        Index("ix_decision_rules_code", "rule_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    decision_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False
    )
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    suggested_outcome: Mapped[str | None] = mapped_column(String(32))
    fact_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    requirement_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    finding_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    reason_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DecisionActionItemRecord(Base):
    """Accion requerida generada deterministicamente por el motor."""

    __tablename__ = "decision_action_items"
    __table_args__ = (
        CheckConstraint(
            f"action_type IN ({DECISION_ACTION_TYPE_VALUES})", name="ck_decision_actions_type"
        ),
        CheckConstraint(
            f"priority IN ({DECISION_ACTION_PRIORITY_VALUES})", name="ck_decision_actions_priority"
        ),
        CheckConstraint(
            f"status IN ({DECISION_ACTION_STATUS_VALUES})", name="ck_decision_actions_status"
        ),
        Index("ix_decision_actions_run", "decision_run_id"),
        Index("ix_decision_actions_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    decision_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    title_code: Mapped[str] = mapped_column(String(128), nullable=False)
    description_code: Mapped[str] = mapped_column(String(128), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    requirement_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    finding_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DecisionActionStatus.OPEN.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DecisionReview(Base):
    """Revision u override manual auditado de un run de decision."""

    __tablename__ = "decision_reviews"
    __table_args__ = (
        CheckConstraint(
            f"action IN ({DECISION_REVIEW_ACTION_VALUES})", name="ck_decision_reviews_action"
        ),
        CheckConstraint(
            f"original_outcome IN ({DECISION_OUTCOME_VALUES})",
            name="ck_decision_reviews_original_outcome",
        ),
        CheckConstraint(
            f"reviewed_outcome IS NULL OR reviewed_outcome IN ({DECISION_OUTCOME_VALUES})",
            name="ck_decision_reviews_reviewed_outcome",
        ),
        Index("ix_decision_reviews_run", "decision_run_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    decision_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    original_outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    reviewed_outcome: Mapped[str | None] = mapped_column(String(32))
    reason: Mapped[str | None] = mapped_column(Text)
    reviewer_reference: Mapped[str] = mapped_column(
        String(128), nullable=False, default="local-user"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DecisionEvent(Base):
    """Evento de auditoria del ciclo de decision, sin contenido sensible."""

    __tablename__ = "decision_events"
    __table_args__ = (
        Index("ix_decision_events_run", "run_id"),
        Index("ix_decision_events_job", "job_id"),
        Index("ix_decision_events_type", "event_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_jobs.id", ondelete="SET NULL")
    )
    run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id", ondelete="SET NULL")
    )
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("company_profiles.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DecisionReportJob(Base):
    """Trabajo asincrono de generacion de paquete de decision."""

    __tablename__ = "decision_report_jobs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({DECISION_REPORT_JOB_STATUS_VALUES})",
            name="ck_decision_report_jobs_status",
        ),
        CheckConstraint("priority >= 0", name="ck_decision_report_jobs_priority"),
        CheckConstraint("attempt_count >= 0", name="ck_decision_report_jobs_attempts"),
        CheckConstraint("max_attempts > 0", name="ck_decision_report_jobs_max_attempts"),
        Index("ix_decision_report_jobs_claim", "status", "available_at", "priority", "created_at"),
        Index("ix_decision_report_jobs_process", "process_id"),
        Index("ix_decision_report_jobs_decision_run", "decision_run_id"),
        Index(
            "uq_decision_report_jobs_active_run",
            "decision_run_id",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'PROCESSING')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    decision_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False
    )
    package_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DecisionReportJobStatus.PENDING.value
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(128))
    force: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    last_error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DecisionReportPackage(Base):
    """Snapshot inmutable de un paquete auditable de decision."""

    __tablename__ = "decision_report_packages"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({DECISION_REPORT_PACKAGE_STATUS_VALUES})",
            name="ck_decision_report_packages_status",
        ),
        CheckConstraint(
            "input_digest ~ '^[a-f0-9]{64}$'", name="ck_decision_report_packages_input_digest"
        ),
        CheckConstraint(
            "package_digest IS NULL OR package_digest ~ '^[a-f0-9]{64}$'",
            name="ck_decision_report_packages_package_digest",
        ),
        CheckConstraint("artifact_count >= 0", name="ck_decision_report_packages_artifact_count"),
        CheckConstraint("warning_count >= 0", name="ck_decision_report_packages_warning_count"),
        Index("ix_decision_report_packages_process", "process_id"),
        Index("ix_decision_report_packages_decision_run", "decision_run_id"),
        Index("ix_decision_report_packages_status", "status"),
        Index("ix_decision_report_packages_created_at", "created_at"),
        Index("ix_decision_report_packages_idempotency", "decision_run_id", "input_digest"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    decision_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_report_jobs.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DecisionReportPackageStatus.DRAFT.value
    )
    package_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    template_version: Mapped[str] = mapped_column(String(32), nullable=False)
    input_manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    package_digest: Mapped[str | None] = mapped_column(String(64))
    artifact_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False, default="local-worker")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(1000))


class DecisionReportArtifact(Base):
    """Metadata de un artefacto generado y almacenado fuera de PostgreSQL."""

    __tablename__ = "decision_report_artifacts"
    __table_args__ = (
        CheckConstraint(
            f"artifact_type IN ({DECISION_REPORT_ARTIFACT_TYPE_VALUES})",
            name="ck_decision_report_artifacts_type",
        ),
        CheckConstraint("size_bytes >= 0", name="ck_decision_report_artifacts_size"),
        CheckConstraint("sha256 ~ '^[a-f0-9]{64}$'", name="ck_decision_report_artifacts_sha"),
        CheckConstraint(
            "source_digest ~ '^[a-f0-9]{64}$'", name="ck_decision_report_artifacts_source_digest"
        ),
        Index("ix_decision_report_artifacts_package", "package_id"),
        UniqueConstraint(
            "package_id", "filename", name="uq_decision_report_artifacts_package_filename"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    package_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("decision_report_packages.id", ondelete="CASCADE"),
        nullable=False,
    )
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(700), nullable=False, unique=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    template_version: Mapped[str] = mapped_column(String(32), nullable=False)
    source_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DecisionReportSection(Base):
    """Resumen estructurado de secciones visibles en web."""

    __tablename__ = "decision_report_sections"
    __table_args__ = (
        Index("ix_decision_report_sections_package", "package_id", "sequence"),
        UniqueConstraint("package_id", "section_code", name="uq_decision_report_sections_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    package_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("decision_report_packages.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    summary_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    warning_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DecisionReportEvent(Base):
    """Evento sanitizado del ciclo de reporte."""

    __tablename__ = "decision_report_events"
    __table_args__ = (
        Index("ix_decision_report_events_job", "job_id"),
        Index("ix_decision_report_events_package", "package_id"),
        Index("ix_decision_report_events_type", "event_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_report_jobs.id", ondelete="SET NULL")
    )
    package_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_report_packages.id", ondelete="SET NULL")
    )
    process_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False
    )
    decision_run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
