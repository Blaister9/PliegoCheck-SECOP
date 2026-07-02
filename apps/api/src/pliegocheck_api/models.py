"""Modelos relacionales de importacion manual."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
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
    ProcessSource,
    ProcessStatus,
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
