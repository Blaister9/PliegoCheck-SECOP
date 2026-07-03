"""Modelos relacionales de importacion manual."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
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
    DocumentExtractionStatus,
    DocumentProcessingJobStatus,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
    DocumentType,
    DocumentUploadStatus,
    ExtractedSegmentType,
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
