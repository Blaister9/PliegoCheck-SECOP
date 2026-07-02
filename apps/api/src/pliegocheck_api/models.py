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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pliegocheck_api.db import Base
from pliegocheck_schemas import DocumentType, DocumentUploadStatus, ProcessSource, ProcessStatus

PROCESS_STATUS_VALUES = ", ".join(f"'{status.value}'" for status in ProcessStatus)
PROCESS_SOURCE_VALUES = ", ".join(f"'{source.value}'" for source in ProcessSource)
DOCUMENT_TYPE_VALUES = ", ".join(f"'{document_type.value}'" for document_type in DocumentType)
DOCUMENT_UPLOAD_STATUS_VALUES = ", ".join(f"'{status.value}'" for status in DocumentUploadStatus)


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
        CheckConstraint("size_bytes > 0", name="ck_documents_size_positive"),
        CheckConstraint("sha256 ~ '^[a-f0-9]{64}$'", name="ck_documents_sha256"),
        Index("ix_process_documents_process_id", "process_id"),
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    process: Mapped[Process] = relationship(back_populates="documents")
    events: Mapped[list["ImportEvent"]] = relationship(back_populates="document")


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
