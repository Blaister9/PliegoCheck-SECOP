# mypy: ignore-errors
"""Endpoints de perfiles de empresa, evidencias y snapshots."""

import json
import logging
from collections.abc import Iterator
from datetime import UTC, date, datetime
from hashlib import sha256
from http import HTTPStatus
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated, Any
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from pliegocheck_api.config import Settings, get_settings
from pliegocheck_api.db import get_session
from pliegocheck_api.errors import DomainError
from pliegocheck_api.file_validation import (
    FileValidationError,
    detect_content_type,
    validate_declared_content_type,
    validate_original_filename,
)
from pliegocheck_api.models import (
    CompanyAuditEvent,
    CompanyCapability,
    CompanyCertification,
    CompanyEvidenceDocument,
    CompanyEvidenceLink,
    CompanyExperienceRecord,
    CompanyFinancialMetric,
    CompanyFinancialPeriod,
    CompanyLegalRegistration,
    CompanyPerson,
    CompanyProfile,
    CompanyProfileSnapshot,
    CompanyUnspscCode,
    DocumentExtraction,
    DocumentProcessingJob,
    ExtractedSegment,
    PersonCredential,
    PersonEducation,
    PersonExperience,
    Process,
    ProcessDocument,
    RupSnapshot,
)
from pliegocheck_api.storage import DocumentStorage, LocalDocumentStorage, StorageError
from pliegocheck_schemas import (
    ApiError,
    CompanyCapabilityCreate,
    CompanyCapabilityUpdate,
    CompanyCertificationCreate,
    CompanyCertificationUpdate,
    CompanyErrorCode,
    CompanyEvidenceDocumentMetadata,
    CompanyEvidenceLinkCreate,
    CompanyEvidenceLinkReview,
    CompanyEvidenceReviewStatus,
    CompanyEvidenceRole,
    CompanyEvidenceSubjectType,
    CompanyEvidenceType,
    CompanyEvidenceUploadResponse,
    CompanyEvidenceUploadResult,
    CompanyEvidenceValidationStatus,
    CompanyExperienceCreate,
    CompanyExperienceUpdate,
    CompanyFinancialMetricCreate,
    CompanyFinancialPeriodCreate,
    CompanyFinancialPeriodUpdate,
    CompanyPersonCreate,
    CompanyPersonUpdate,
    CompanyProfileCompleteness,
    CompanyProfileCreate,
    CompanyProfileDetail,
    CompanyProfileList,
    CompanyProfileMissingItem,
    CompanyProfileSnapshotCreate,
    CompanyProfileSnapshotDetail,
    CompanyProfileSnapshotSummary,
    CompanyProfileStatus,
    CompanyProfileSummary,
    CompanyProfileUpdate,
    CompanyRecordStatus,
    CompanySnapshotStatus,
    CompanyUnspscCodeCreate,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
    DocumentType,
    DocumentUploadStatus,
    LegalRegistrationCreate,
    LegalRegistrationUpdate,
    PersonCredentialCreate,
    PersonEducationCreate,
    PersonExperienceCreate,
    ProcessSource,
    ProcessStatus,
    RupSnapshotCreate,
    RupSnapshotUpdate,
    UploadErrorCode,
)
from pliegocheck_schemas import (
    CompanyCapability as CompanyCapabilityContract,
)
from pliegocheck_schemas import (
    CompanyCertification as CompanyCertificationContract,
)
from pliegocheck_schemas import (
    CompanyEvidenceLink as CompanyEvidenceLinkContract,
)
from pliegocheck_schemas import (
    CompanyExperienceRecord as CompanyExperienceContract,
)
from pliegocheck_schemas import (
    CompanyFinancialMetric as CompanyFinancialMetricContract,
)
from pliegocheck_schemas import (
    CompanyFinancialPeriod as CompanyFinancialPeriodContract,
)
from pliegocheck_schemas import (
    CompanyLegalRegistration as CompanyLegalRegistrationContract,
)
from pliegocheck_schemas import (
    CompanyPerson as CompanyPersonContract,
)
from pliegocheck_schemas import (
    CompanyUnspscCode as CompanyUnspscCodeContract,
)
from pliegocheck_schemas import (
    PersonCredential as PersonCredentialContract,
)
from pliegocheck_schemas import (
    PersonEducation as PersonEducationContract,
)
from pliegocheck_schemas import (
    PersonExperience as PersonExperienceContract,
)
from pliegocheck_schemas import (
    RupSnapshot as RupSnapshotContract,
)

router = APIRouter(prefix="/companies", tags=["companies"])
logger = logging.getLogger(__name__)
CHUNK_SIZE = 1024 * 1024
MAX_LIST_LIMIT = 100

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
FilesParam = Annotated[list[UploadFile], File()]
LimitParam = Annotated[int, Query(ge=1, le=MAX_LIST_LIMIT)]
OffsetParam = Annotated[int, Query(ge=0)]


def get_storage(settings: SettingsDep) -> DocumentStorage:
    return LocalDocumentStorage(settings.storage_path)


StorageDep = Annotated[DocumentStorage, Depends(get_storage)]


def _normalize_tax_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = "".join(char for char in value.strip().upper() if char.isalnum())
    return normalized or None


def _mask_identifier(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 4:
        return "*" * len(value)
    return f"{'*' * (len(value) - 4)}{value[-4:]}"


def _validate_incorporation_date(value: date | None) -> None:
    if value is not None and value > date.today():
        raise DomainError(
            CompanyErrorCode.INVALID_COMPANY_DATA,
            "La fecha de constitucion no puede estar en el futuro.",
            status_code=HTTPStatus.BAD_REQUEST,
        )


def _company_or_404(session: Session, company_id: UUID) -> CompanyProfile:
    company = session.scalar(
        select(CompanyProfile)
        .where(CompanyProfile.id == company_id)
        .options(
            selectinload(CompanyProfile.legal_registrations),
            selectinload(CompanyProfile.rup_snapshots),
            selectinload(CompanyProfile.unspsc_codes),
            selectinload(CompanyProfile.financial_periods).selectinload(
                CompanyFinancialPeriod.metrics
            ),
            selectinload(CompanyProfile.experience_records),
            selectinload(CompanyProfile.people).selectinload(CompanyPerson.education),
            selectinload(CompanyProfile.people).selectinload(CompanyPerson.experience),
            selectinload(CompanyProfile.people).selectinload(CompanyPerson.credentials),
            selectinload(CompanyProfile.certifications),
            selectinload(CompanyProfile.capabilities),
            selectinload(CompanyProfile.evidence_documents).selectinload(
                CompanyEvidenceDocument.process_document
            ),
            selectinload(CompanyProfile.evidence_links),
            selectinload(CompanyProfile.snapshots),
        )
    )
    if company is None:
        raise DomainError(
            CompanyErrorCode.COMPANY_NOT_FOUND,
            "La empresa no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return company


def _ensure_not_archived(company: CompanyProfile) -> None:
    if company.status == CompanyProfileStatus.ARCHIVED.value:
        raise DomainError(
            CompanyErrorCode.COMPANY_ARCHIVED,
            "La empresa esta archivada.",
            status_code=HTTPStatus.CONFLICT,
        )


def _add_audit(
    session: Session,
    *,
    company_id: UUID,
    event_type: str,
    entity_type: str,
    entity_id: UUID | None,
    summary: str,
    details: dict[str, Any] | None = None,
    snapshot_version: int | None = None,
) -> None:
    session.add(
        CompanyAuditEvent(
            id=uuid4(),
            company_id=company_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor="local-user",
            summary=summary,
            details=details or {},
            snapshot_version=snapshot_version,
        )
    )


def _company_summary(session: Session, company: CompanyProfile) -> CompanyProfileSummary:
    completeness = calculate_completeness(session, company)
    return CompanyProfileSummary(
        id=company.id,
        internal_reference=company.internal_reference,
        legal_name=company.legal_name,
        trade_name=company.trade_name,
        tax_id_masked=_mask_identifier(company.tax_id),
        tax_id_type=company.tax_id_type,
        status=CompanyProfileStatus(company.status),
        completeness_status="READY_FOR_REVIEW" if completeness.ready_for_review else "INCOMPLETE",
        evidence_coverage=completeness.evidence_coverage,
        pending_evidence_count=sum(
            1
            for document in company.evidence_documents
            if document.review_status == CompanyEvidenceReviewStatus.PENDING.value
        ),
        updated_at=company.updated_at,
    )


def _company_detail(company: CompanyProfile) -> CompanyProfileDetail:
    return CompanyProfileDetail(
        id=company.id,
        internal_reference=company.internal_reference,
        legal_name=company.legal_name,
        trade_name=company.trade_name,
        tax_id=company.tax_id,
        tax_id_masked=_mask_identifier(company.tax_id),
        tax_id_type=company.tax_id_type,
        company_type=company.company_type,
        legal_nature=company.legal_nature,
        incorporation_date=company.incorporation_date,
        country=company.country,
        department=company.department,
        city=company.city,
        address=company.address,
        website=company.website,
        primary_email=company.primary_email,
        primary_phone=company.primary_phone,
        economic_activity_codes=company.economic_activity_codes,
        status=CompanyProfileStatus(company.status),
        created_at=company.created_at,
        updated_at=company.updated_at,
        archived_at=company.archived_at,
        legal_registrations=[
            _legal_registration_contract(row) for row in company.legal_registrations
        ],
        rup_snapshots=[_rup_contract(row) for row in company.rup_snapshots],
        unspsc_codes=[_unspsc_contract(row) for row in company.unspsc_codes],
        financial_periods=[_financial_period_contract(row) for row in company.financial_periods],
        experience_records=[_experience_contract(row) for row in company.experience_records],
        people=[_person_contract(row) for row in company.people],
        certifications=[_certification_contract(row) for row in company.certifications],
        capabilities=[_capability_contract(row) for row in company.capabilities],
        evidence_documents=[_evidence_document_contract(row) for row in company.evidence_documents],
        evidence_links=[_evidence_link_contract(row) for row in company.evidence_links],
    )


def _legal_registration_contract(row: CompanyLegalRegistration) -> CompanyLegalRegistrationContract:
    return CompanyLegalRegistrationContract(
        id=row.id,
        company_id=row.company_id,
        registration_type=row.registration_type,
        registration_number=row.registration_number,
        issuing_authority=row.issuing_authority,
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        status=row.status,
        declared_data=row.declared_data,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _rup_contract(row: RupSnapshot) -> RupSnapshotContract:
    return RupSnapshotContract(
        id=row.id,
        company_id=row.company_id,
        registration_number=row.registration_number,
        issued_at=row.issued_at,
        valid_until=row.valid_until,
        renewal_year=row.renewal_year,
        status=row.status,
        financial_period_reference=row.financial_period_reference,
        organization_capacity=row.organization_capacity,
        technical_capacity=row.technical_capacity,
        financial_capacity=row.financial_capacity,
        experience_capacity=row.experience_capacity,
        raw_declared_data=row.raw_declared_data,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _unspsc_contract(row: CompanyUnspscCode) -> CompanyUnspscCodeContract:
    return CompanyUnspscCodeContract(
        id=row.id,
        company_id=row.company_id,
        code=row.code,
        description=row.description,
        source=row.source,
        valid_from=row.valid_from,
        valid_until=row.valid_until,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _metric_contract(row: CompanyFinancialMetric) -> CompanyFinancialMetricContract:
    return CompanyFinancialMetricContract(
        id=row.id,
        financial_period_id=row.financial_period_id,
        metric_type=row.metric_type,
        value=row.value,
        unit=row.unit,
        source_value=row.source_value,
        is_calculated=row.is_calculated,
        formula=row.formula,
        formula_inputs=row.formula_inputs,
        calculation_version=row.calculation_version,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _financial_period_contract(row: CompanyFinancialPeriod) -> CompanyFinancialPeriodContract:
    return CompanyFinancialPeriodContract(
        id=row.id,
        company_id=row.company_id,
        period_start=row.period_start,
        period_end=row.period_end,
        currency=row.currency,
        source_type=row.source_type,
        status=row.status,
        metrics=[_metric_contract(metric) for metric in row.metrics],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _experience_contract(row: CompanyExperienceRecord) -> CompanyExperienceContract:
    return CompanyExperienceContract(
        id=row.id,
        company_id=row.company_id,
        contract_reference=row.contract_reference,
        contracting_party=row.contracting_party,
        contract_title=row.contract_title,
        description=row.description,
        country=row.country,
        sector=row.sector,
        contract_type=row.contract_type,
        start_date=row.start_date,
        end_date=row.end_date,
        execution_status=row.execution_status,
        total_contract_value=row.total_contract_value,
        currency=row.currency,
        company_participation_percentage=row.company_participation_percentage,
        company_attributable_value=row.company_attributable_value,
        attributable_value_formula=row.attributable_value_formula,
        consortium_name=row.consortium_name,
        consortium_members=row.consortium_members,
        unspsc_codes=row.unspsc_codes,
        activities=row.activities,
        scope_tags=row.scope_tags,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _education_contract(row: PersonEducation) -> PersonEducationContract:
    return PersonEducationContract(
        id=row.id,
        person_id=row.person_id,
        degree_type=row.degree_type,
        title=row.title,
        institution=row.institution,
        graduation_date=row.graduation_date,
        country=row.country,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _person_experience_contract(row: PersonExperience) -> PersonExperienceContract:
    return PersonExperienceContract(
        id=row.id,
        person_id=row.person_id,
        organization=row.organization,
        role=row.role,
        description=row.description,
        start_date=row.start_date,
        end_date=row.end_date,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _credential_contract(row: PersonCredential) -> PersonCredentialContract:
    return PersonCredentialContract(
        id=row.id,
        person_id=row.person_id,
        credential_type=row.credential_type,
        name=row.name,
        issuer=row.issuer,
        credential_number=row.credential_number,
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _person_contract(row: CompanyPerson) -> CompanyPersonContract:
    return CompanyPersonContract(
        id=row.id,
        company_id=row.company_id,
        full_name=row.full_name,
        identification_type=row.identification_type,
        identification_number=row.identification_number,
        identification_masked=_mask_identifier(row.identification_number),
        email=row.email,
        phone=row.phone,
        relationship_type=row.relationship_type,
        availability_status=row.availability_status,
        status=row.status,
        education=[_education_contract(item) for item in row.education],
        experience=[_person_experience_contract(item) for item in row.experience],
        credentials=[_credential_contract(item) for item in row.credentials],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _certification_contract(row: CompanyCertification) -> CompanyCertificationContract:
    return CompanyCertificationContract(
        id=row.id,
        company_id=row.company_id,
        certification_type=row.certification_type,
        name=row.name,
        issuer=row.issuer,
        certificate_number=row.certificate_number,
        scope=row.scope,
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _capability_contract(row: CompanyCapability) -> CompanyCapabilityContract:
    return CompanyCapabilityContract(
        id=row.id,
        company_id=row.company_id,
        category=row.category,
        name=row.name,
        description=row.description,
        value=row.value,
        unit=row.unit,
        territorial_scope=row.territorial_scope,
        valid_from=row.valid_from,
        valid_until=row.valid_until,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _evidence_document_contract(row: CompanyEvidenceDocument) -> CompanyEvidenceDocumentMetadata:
    document = row.process_document
    return CompanyEvidenceDocumentMetadata(
        id=row.id,
        company_id=row.company_id,
        process_document_id=row.process_document_id,
        evidence_type=row.evidence_type,
        title=row.title,
        original_filename=document.original_filename,
        extension=document.extension,
        size_bytes=document.size_bytes,
        sha256=row.sha256,
        issuer=row.issuer,
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        review_status=row.review_status,
        processing_status=document.processing_status,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _evidence_link_contract(row: CompanyEvidenceLink) -> CompanyEvidenceLinkContract:
    return CompanyEvidenceLinkContract(
        id=row.id,
        company_id=row.company_id,
        document_id=row.document_id,
        subject_type=row.subject_type,
        subject_id=row.subject_id,
        extraction_id=row.extraction_id,
        segment_id=row.segment_id,
        evidence_role=row.evidence_role,
        quoted_text=row.quoted_text,
        source_location=row.source_location,
        validation_status=row.validation_status,
        review_status=row.review_status,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _snapshot_summary(row: CompanyProfileSnapshot) -> CompanyProfileSnapshotSummary:
    return CompanyProfileSnapshotSummary(
        id=row.id,
        company_id=row.company_id,
        version=row.version,
        status=row.status,
        digest=row.digest,
        completeness_status=row.completeness_status,
        created_at=row.created_at,
        published_at=row.published_at,
    )


def _snapshot_detail(row: CompanyProfileSnapshot) -> CompanyProfileSnapshotDetail:
    return CompanyProfileSnapshotDetail(
        **_snapshot_summary(row).model_dump(),
        payload=row.payload,
        notes=row.notes,
    )


@router.post("", response_model=CompanyProfileDetail, status_code=HTTPStatus.CREATED)
def create_company(payload: CompanyProfileCreate, session: SessionDep) -> CompanyProfileDetail:
    now = datetime.now(UTC)
    company_id = uuid4()
    normalized_tax_id = _normalize_tax_id(payload.tax_id)
    _validate_incorporation_date(payload.incorporation_date)
    system_process = Process(
        id=uuid4(),
        internal_reference=f"CPDOC-{now:%Y%m%d}-{company_id.hex[:8].upper()}",
        title=f"Documentos de evidencia de {payload.legal_name}",
        contracting_entity=payload.legal_name,
        currency="COP",
        status=ProcessStatus.DRAFT.value,
        source=ProcessSource.MANUAL.value,
        is_system=True,
    )
    company = CompanyProfile(
        id=company_id,
        system_process=system_process,
        internal_reference=f"CP-{now:%Y%m%d}-{company_id.hex[:8].upper()}",
        legal_name=payload.legal_name,
        trade_name=payload.trade_name,
        tax_id=normalized_tax_id,
        tax_id_type=payload.tax_id_type,
        company_type=payload.company_type,
        legal_nature=payload.legal_nature,
        incorporation_date=payload.incorporation_date,
        country=payload.country,
        department=payload.department,
        city=payload.city,
        address=payload.address,
        website=str(payload.website) if payload.website is not None else None,
        primary_email=payload.primary_email,
        primary_phone=payload.primary_phone,
        economic_activity_codes=payload.economic_activity_codes,
        status=CompanyProfileStatus.DRAFT.value,
    )
    session.add(company)
    _add_audit(
        session,
        company_id=company.id,
        event_type="COMPANY_CREATED",
        entity_type="COMPANY_PROFILE",
        entity_id=company.id,
        summary="Empresa creada.",
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DomainError(
            CompanyErrorCode.DUPLICATE_TAX_ID,
            "Ya existe una empresa con ese identificador tributario.",
            status_code=HTTPStatus.CONFLICT,
        ) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise DomainError(
            CompanyErrorCode.DATABASE_ERROR,
            "No fue posible crear la empresa.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        ) from exc
    return _company_detail(_company_or_404(session, company.id))


@router.get("", response_model=CompanyProfileList)
def list_companies(
    session: SessionDep,
    limit: LimitParam = 20,
    offset: OffsetParam = 0,
    status: Annotated[CompanyProfileStatus | None, Query()] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
) -> CompanyProfileList:
    filters = []
    if status is not None:
        filters.append(CompanyProfile.status == status.value)
    if search is not None:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                CompanyProfile.legal_name.ilike(pattern),
                CompanyProfile.trade_name.ilike(pattern),
                CompanyProfile.internal_reference.ilike(pattern),
                CompanyProfile.tax_id.ilike(pattern),
            )
        )
    count_query = select(func.count()).select_from(CompanyProfile)
    items_query = (
        select(CompanyProfile)
        .options(selectinload(CompanyProfile.evidence_documents))
        .order_by(CompanyProfile.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if filters:
        count_query = count_query.where(*filters)
        items_query = items_query.where(*filters)
    total = session.scalar(count_query) or 0
    companies = session.scalars(items_query).all()
    return CompanyProfileList(
        items=[_company_summary(session, company) for company in companies],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{company_id}", response_model=CompanyProfileDetail)
def get_company(company_id: UUID, session: SessionDep) -> CompanyProfileDetail:
    return _company_detail(_company_or_404(session, company_id))


@router.patch("/{company_id}", response_model=CompanyProfileDetail)
def update_company(
    company_id: UUID, payload: CompanyProfileUpdate, session: SessionDep
) -> CompanyProfileDetail:
    company = _company_or_404(session, company_id)
    _ensure_not_archived(company)
    values = payload.model_dump(exclude_unset=True)
    if "tax_id" in values:
        values["tax_id"] = _normalize_tax_id(values["tax_id"])
    if "incorporation_date" in values:
        _validate_incorporation_date(values["incorporation_date"])
    if "website" in values and values["website"] is not None:
        values["website"] = str(values["website"])
    for key, value in values.items():
        setattr(company, key, value.value if hasattr(value, "value") else value)
    _add_audit(
        session,
        company_id=company.id,
        event_type="COMPANY_UPDATED",
        entity_type="COMPANY_PROFILE",
        entity_id=company.id,
        summary="Empresa actualizada.",
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DomainError(
            CompanyErrorCode.DUPLICATE_TAX_ID,
            "Ya existe una empresa con ese identificador tributario.",
            status_code=HTTPStatus.CONFLICT,
        ) from exc
    return _company_detail(_company_or_404(session, company_id))


@router.post("/{company_id}/archive", response_model=CompanyProfileDetail)
def archive_company(company_id: UUID, session: SessionDep) -> CompanyProfileDetail:
    company = _company_or_404(session, company_id)
    company.status = CompanyProfileStatus.ARCHIVED.value
    company.archived_at = datetime.now(UTC)
    _add_audit(
        session,
        company_id=company.id,
        event_type="COMPANY_ARCHIVED",
        entity_type="COMPANY_PROFILE",
        entity_id=company.id,
        summary="Empresa archivada.",
    )
    session.commit()
    return _company_detail(_company_or_404(session, company_id))


@router.post("/{company_id}/legal-registrations", response_model=CompanyLegalRegistrationContract)
def create_legal_registration(
    company_id: UUID, payload: LegalRegistrationCreate, session: SessionDep
) -> CompanyLegalRegistrationContract:
    company = _company_or_404(session, company_id)
    _ensure_not_archived(company)
    row = CompanyLegalRegistration(company_id=company.id, **_dump(payload))
    session.add(row)
    _add_audit(
        session,
        company_id=company.id,
        event_type="LEGAL_REGISTRATION_CREATED",
        entity_type="LEGAL_REGISTRATION",
        entity_id=row.id,
        summary="Registro legal creado.",
    )
    session.commit()
    session.refresh(row)
    return _legal_registration_contract(row)


@router.get(
    "/{company_id}/legal-registrations", response_model=list[CompanyLegalRegistrationContract]
)
def list_legal_registrations(
    company_id: UUID, session: SessionDep
) -> list[CompanyLegalRegistrationContract]:
    company = _company_or_404(session, company_id)
    return [_legal_registration_contract(row) for row in company.legal_registrations]


@router.patch(
    "/{company_id}/legal-registrations/{registration_id}",
    response_model=CompanyLegalRegistrationContract,
)
def update_legal_registration(
    company_id: UUID,
    registration_id: UUID,
    payload: LegalRegistrationUpdate,
    session: SessionDep,
) -> CompanyLegalRegistrationContract:
    row = _company_row_or_404(
        session,
        CompanyLegalRegistration,
        company_id,
        registration_id,
        CompanyErrorCode.LEGAL_REGISTRATION_NOT_FOUND,
    )
    _patch(row, payload)
    session.commit()
    session.refresh(row)
    return _legal_registration_contract(row)


@router.post("/{company_id}/rup", response_model=RupSnapshotContract)
def create_rup(
    company_id: UUID, payload: RupSnapshotCreate, session: SessionDep
) -> RupSnapshotContract:
    _company_or_404(session, company_id)
    row = RupSnapshot(company_id=company_id, **_dump(payload))
    session.add(row)
    _add_audit(
        session,
        company_id=company_id,
        event_type="RUP_CREATED",
        entity_type="RUP_SNAPSHOT",
        entity_id=row.id,
        summary="Snapshot RUP creado.",
    )
    session.commit()
    session.refresh(row)
    return _rup_contract(row)


@router.get("/{company_id}/rup", response_model=list[RupSnapshotContract])
def list_rup(company_id: UUID, session: SessionDep) -> list[RupSnapshotContract]:
    company = _company_or_404(session, company_id)
    return [_rup_contract(row) for row in company.rup_snapshots]


@router.patch("/{company_id}/rup/{rup_id}", response_model=RupSnapshotContract)
def update_rup(
    company_id: UUID, rup_id: UUID, payload: RupSnapshotUpdate, session: SessionDep
) -> RupSnapshotContract:
    row = _company_row_or_404(
        session, RupSnapshot, company_id, rup_id, CompanyErrorCode.RUP_SNAPSHOT_NOT_FOUND
    )
    _patch(row, payload)
    session.commit()
    session.refresh(row)
    return _rup_contract(row)


@router.post("/{company_id}/unspsc", response_model=CompanyUnspscCodeContract)
def create_unspsc(
    company_id: UUID, payload: CompanyUnspscCodeCreate, session: SessionDep
) -> CompanyUnspscCodeContract:
    _company_or_404(session, company_id)
    row = CompanyUnspscCode(company_id=company_id, **_dump(payload))
    session.add(row)
    session.commit()
    session.refresh(row)
    return _unspsc_contract(row)


@router.get("/{company_id}/unspsc", response_model=list[CompanyUnspscCodeContract])
def list_unspsc(company_id: UUID, session: SessionDep) -> list[CompanyUnspscCodeContract]:
    company = _company_or_404(session, company_id)
    return [_unspsc_contract(row) for row in company.unspsc_codes]


@router.post("/{company_id}/financial-periods", response_model=CompanyFinancialPeriodContract)
def create_financial_period(
    company_id: UUID, payload: CompanyFinancialPeriodCreate, session: SessionDep
) -> CompanyFinancialPeriodContract:
    _company_or_404(session, company_id)
    row = CompanyFinancialPeriod(company_id=company_id, **_dump(payload))
    session.add(row)
    _add_audit(
        session,
        company_id=company_id,
        event_type="FINANCIAL_PERIOD_CREATED",
        entity_type="FINANCIAL_PERIOD",
        entity_id=row.id,
        summary="Periodo financiero creado.",
    )
    session.commit()
    return _financial_period_contract(
        _company_row_or_404(
            session,
            CompanyFinancialPeriod,
            company_id,
            row.id,
            CompanyErrorCode.FINANCIAL_PERIOD_NOT_FOUND,
        )
    )


@router.get("/{company_id}/financial-periods", response_model=list[CompanyFinancialPeriodContract])
def list_financial_periods(
    company_id: UUID, session: SessionDep
) -> list[CompanyFinancialPeriodContract]:
    company = _company_or_404(session, company_id)
    return [_financial_period_contract(row) for row in company.financial_periods]


@router.get(
    "/{company_id}/financial-periods/{period_id}",
    response_model=CompanyFinancialPeriodContract,
)
def get_financial_period(
    company_id: UUID, period_id: UUID, session: SessionDep
) -> CompanyFinancialPeriodContract:
    row = _company_row_or_404(
        session,
        CompanyFinancialPeriod,
        company_id,
        period_id,
        CompanyErrorCode.FINANCIAL_PERIOD_NOT_FOUND,
    )
    return _financial_period_contract(row)


@router.patch(
    "/{company_id}/financial-periods/{period_id}",
    response_model=CompanyFinancialPeriodContract,
)
def update_financial_period(
    company_id: UUID,
    period_id: UUID,
    payload: CompanyFinancialPeriodUpdate,
    session: SessionDep,
) -> CompanyFinancialPeriodContract:
    row = _company_row_or_404(
        session,
        CompanyFinancialPeriod,
        company_id,
        period_id,
        CompanyErrorCode.FINANCIAL_PERIOD_NOT_FOUND,
    )
    _patch(row, payload)
    session.commit()
    return _financial_period_contract(row)


@router.post(
    "/{company_id}/financial-periods/{period_id}/metrics",
    response_model=CompanyFinancialMetricContract,
)
def create_financial_metric(
    company_id: UUID,
    period_id: UUID,
    payload: CompanyFinancialMetricCreate,
    session: SessionDep,
) -> CompanyFinancialMetricContract:
    _company_row_or_404(
        session,
        CompanyFinancialPeriod,
        company_id,
        period_id,
        CompanyErrorCode.FINANCIAL_PERIOD_NOT_FOUND,
    )
    row = CompanyFinancialMetric(financial_period_id=period_id, **_dump(payload))
    session.add(row)
    _add_audit(
        session,
        company_id=company_id,
        event_type="FINANCIAL_METRIC_CREATED",
        entity_type="FINANCIAL_METRIC",
        entity_id=row.id,
        summary="Metrica financiera creada.",
    )
    session.commit()
    session.refresh(row)
    return _metric_contract(row)


@router.post("/{company_id}/experience", response_model=CompanyExperienceContract)
def create_experience(
    company_id: UUID, payload: CompanyExperienceCreate, session: SessionDep
) -> CompanyExperienceContract:
    _company_or_404(session, company_id)
    data = _dump(payload)
    if (
        data.get("company_attributable_value") is None
        and data.get("total_contract_value") is not None
        and data.get("company_participation_percentage") is not None
    ):
        data["company_attributable_value"] = (
            data["total_contract_value"] * data["company_participation_percentage"] / 100
        )
        data["attributable_value_formula"] = (
            "total_contract_value * company_participation_percentage / 100"
        )
    row = CompanyExperienceRecord(company_id=company_id, **data)
    session.add(row)
    _add_audit(
        session,
        company_id=company_id,
        event_type="EXPERIENCE_CREATED",
        entity_type="EXPERIENCE_RECORD",
        entity_id=row.id,
        summary="Experiencia creada.",
    )
    session.commit()
    session.refresh(row)
    return _experience_contract(row)


@router.get("/{company_id}/experience", response_model=list[CompanyExperienceContract])
def list_experience(company_id: UUID, session: SessionDep) -> list[CompanyExperienceContract]:
    company = _company_or_404(session, company_id)
    return [_experience_contract(row) for row in company.experience_records]


@router.get("/{company_id}/experience/{experience_id}", response_model=CompanyExperienceContract)
def get_experience(
    company_id: UUID, experience_id: UUID, session: SessionDep
) -> CompanyExperienceContract:
    row = _company_row_or_404(
        session,
        CompanyExperienceRecord,
        company_id,
        experience_id,
        CompanyErrorCode.EXPERIENCE_RECORD_NOT_FOUND,
    )
    return _experience_contract(row)


@router.patch("/{company_id}/experience/{experience_id}", response_model=CompanyExperienceContract)
def update_experience(
    company_id: UUID,
    experience_id: UUID,
    payload: CompanyExperienceUpdate,
    session: SessionDep,
) -> CompanyExperienceContract:
    row = _company_row_or_404(
        session,
        CompanyExperienceRecord,
        company_id,
        experience_id,
        CompanyErrorCode.EXPERIENCE_RECORD_NOT_FOUND,
    )
    _patch(row, payload)
    session.commit()
    return _experience_contract(row)


@router.post("/{company_id}/people", response_model=CompanyPersonContract)
def create_person(
    company_id: UUID, payload: CompanyPersonCreate, session: SessionDep
) -> CompanyPersonContract:
    _company_or_404(session, company_id)
    row = CompanyPerson(company_id=company_id, **_dump(payload))
    session.add(row)
    _add_audit(
        session,
        company_id=company_id,
        event_type="PERSON_CREATED",
        entity_type="PERSON",
        entity_id=row.id,
        summary="Persona creada.",
    )
    session.commit()
    return _person_contract(_person_or_404(session, company_id, row.id))


@router.get("/{company_id}/people", response_model=list[CompanyPersonContract])
def list_people(company_id: UUID, session: SessionDep) -> list[CompanyPersonContract]:
    company = _company_or_404(session, company_id)
    return [_person_contract(row) for row in company.people]


@router.get("/{company_id}/people/{person_id}", response_model=CompanyPersonContract)
def get_person(company_id: UUID, person_id: UUID, session: SessionDep) -> CompanyPersonContract:
    return _person_contract(_person_or_404(session, company_id, person_id))


@router.patch("/{company_id}/people/{person_id}", response_model=CompanyPersonContract)
def update_person(
    company_id: UUID, person_id: UUID, payload: CompanyPersonUpdate, session: SessionDep
) -> CompanyPersonContract:
    row = _person_or_404(session, company_id, person_id)
    _patch(row, payload)
    session.commit()
    return _person_contract(_person_or_404(session, company_id, person_id))


@router.post("/{company_id}/people/{person_id}/education", response_model=PersonEducationContract)
def create_person_education(
    company_id: UUID,
    person_id: UUID,
    payload: PersonEducationCreate,
    session: SessionDep,
) -> PersonEducationContract:
    _person_or_404(session, company_id, person_id)
    row = PersonEducation(person_id=person_id, **_dump(payload))
    session.add(row)
    session.commit()
    session.refresh(row)
    return _education_contract(row)


@router.post("/{company_id}/people/{person_id}/experience", response_model=PersonExperienceContract)
def create_person_experience(
    company_id: UUID,
    person_id: UUID,
    payload: PersonExperienceCreate,
    session: SessionDep,
) -> PersonExperienceContract:
    _person_or_404(session, company_id, person_id)
    row = PersonExperience(person_id=person_id, **_dump(payload))
    session.add(row)
    session.commit()
    session.refresh(row)
    return _person_experience_contract(row)


@router.post(
    "/{company_id}/people/{person_id}/credentials", response_model=PersonCredentialContract
)
def create_person_credential(
    company_id: UUID,
    person_id: UUID,
    payload: PersonCredentialCreate,
    session: SessionDep,
) -> PersonCredentialContract:
    _person_or_404(session, company_id, person_id)
    row = PersonCredential(person_id=person_id, **_dump(payload))
    session.add(row)
    session.commit()
    session.refresh(row)
    return _credential_contract(row)


@router.post("/{company_id}/certifications", response_model=CompanyCertificationContract)
def create_certification(
    company_id: UUID, payload: CompanyCertificationCreate, session: SessionDep
) -> CompanyCertificationContract:
    _company_or_404(session, company_id)
    row = CompanyCertification(company_id=company_id, **_dump(payload))
    session.add(row)
    _add_audit(
        session,
        company_id=company_id,
        event_type="CERTIFICATION_CREATED",
        entity_type="COMPANY_CERTIFICATION",
        entity_id=row.id,
        summary="Certificacion creada.",
    )
    session.commit()
    session.refresh(row)
    return _certification_contract(row)


@router.get("/{company_id}/certifications", response_model=list[CompanyCertificationContract])
def list_certifications(
    company_id: UUID, session: SessionDep
) -> list[CompanyCertificationContract]:
    company = _company_or_404(session, company_id)
    return [_certification_contract(row) for row in company.certifications]


@router.patch(
    "/{company_id}/certifications/{certification_id}",
    response_model=CompanyCertificationContract,
)
def update_certification(
    company_id: UUID,
    certification_id: UUID,
    payload: CompanyCertificationUpdate,
    session: SessionDep,
) -> CompanyCertificationContract:
    row = _company_row_or_404(
        session,
        CompanyCertification,
        company_id,
        certification_id,
        CompanyErrorCode.CERTIFICATION_NOT_FOUND,
    )
    _patch(row, payload)
    session.commit()
    return _certification_contract(row)


@router.post("/{company_id}/capabilities", response_model=CompanyCapabilityContract)
def create_capability(
    company_id: UUID, payload: CompanyCapabilityCreate, session: SessionDep
) -> CompanyCapabilityContract:
    _company_or_404(session, company_id)
    data = _dump(payload)
    if data.get("value") is not None:
        data["value"] = str(data["value"])
    row = CompanyCapability(company_id=company_id, **data)
    session.add(row)
    _add_audit(
        session,
        company_id=company_id,
        event_type="CAPABILITY_CREATED",
        entity_type="COMPANY_CAPABILITY",
        entity_id=row.id,
        summary="Capacidad creada.",
    )
    session.commit()
    session.refresh(row)
    return _capability_contract(row)


@router.get("/{company_id}/capabilities", response_model=list[CompanyCapabilityContract])
def list_capabilities(company_id: UUID, session: SessionDep) -> list[CompanyCapabilityContract]:
    company = _company_or_404(session, company_id)
    return [_capability_contract(row) for row in company.capabilities]


@router.patch(
    "/{company_id}/capabilities/{capability_id}", response_model=CompanyCapabilityContract
)
def update_capability(
    company_id: UUID,
    capability_id: UUID,
    payload: CompanyCapabilityUpdate,
    session: SessionDep,
) -> CompanyCapabilityContract:
    row = _company_row_or_404(
        session, CompanyCapability, company_id, capability_id, CompanyErrorCode.CAPABILITY_NOT_FOUND
    )
    _patch(row, payload)
    session.commit()
    return _capability_contract(row)


@router.post("/{company_id}/evidence-documents", response_model=CompanyEvidenceUploadResponse)
def upload_evidence_documents(
    company_id: UUID,
    response: Response,
    session: SessionDep,
    storage: StorageDep,
    settings: SettingsDep,
    files: FilesParam,
    evidence_type: Annotated[CompanyEvidenceType, Query()] = CompanyEvidenceType.OTHER,
    title: Annotated[str | None, Query(max_length=500)] = None,
) -> CompanyEvidenceUploadResponse:
    company = _company_or_404(session, company_id)
    _ensure_not_archived(company)
    results = [
        _store_company_evidence(
            company=company,
            upload=upload,
            session=session,
            storage=storage,
            max_file_size=settings.max_file_size_bytes,
            evidence_type=evidence_type,
            title=title,
        )
        for upload in files
    ]
    stored_count = sum(1 for item in results if item.upload_status == "STORED")
    rejected_count = len(results) - stored_count
    response.status_code = (
        HTTPStatus.CREATED
        if stored_count and not rejected_count
        else HTTPStatus.MULTI_STATUS
        if stored_count
        else HTTPStatus.BAD_REQUEST
    )
    return CompanyEvidenceUploadResponse(
        company_id=company_id,
        results=results,
        stored_count=stored_count,
        rejected_count=rejected_count,
    )


@router.get(
    "/{company_id}/evidence-documents", response_model=list[CompanyEvidenceDocumentMetadata]
)
def list_evidence_documents(
    company_id: UUID, session: SessionDep
) -> list[CompanyEvidenceDocumentMetadata]:
    company = _company_or_404(session, company_id)
    return [_evidence_document_contract(row) for row in company.evidence_documents]


@router.get(
    "/{company_id}/evidence-documents/{document_id}",
    response_model=CompanyEvidenceDocumentMetadata,
)
def get_evidence_document(
    company_id: UUID, document_id: UUID, session: SessionDep
) -> CompanyEvidenceDocumentMetadata:
    return _evidence_document_contract(_evidence_document_or_404(session, company_id, document_id))


@router.get("/{company_id}/evidence-documents/{document_id}/download")
def download_evidence_document(
    company_id: UUID,
    document_id: UUID,
    session: SessionDep,
    storage: StorageDep,
) -> StreamingResponse:
    evidence = _evidence_document_or_404(session, company_id, document_id)
    document = evidence.process_document
    if not storage.exists(document.storage_key):
        raise DomainError(
            CompanyErrorCode.EVIDENCE_DOCUMENT_NOT_FOUND,
            "El archivo original no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return StreamingResponse(
        _stream_storage(storage, document.storage_key),
        media_type=document.detected_content_type or "application/octet-stream",
        headers={"Content-Disposition": _content_disposition(document.original_filename)},
    )


@router.post("/{company_id}/evidence-links", response_model=CompanyEvidenceLinkContract)
def create_evidence_link(
    company_id: UUID, payload: CompanyEvidenceLinkCreate, session: SessionDep
) -> CompanyEvidenceLinkContract:
    _company_or_404(session, company_id)
    document = _evidence_document_or_404(session, company_id, payload.document_id)
    _validate_subject_belongs_to_company(
        session, company_id, payload.subject_type, payload.subject_id
    )
    validation_status = _validate_evidence_reference(session, document, payload)
    row = CompanyEvidenceLink(
        id=uuid4(),
        company_id=company_id,
        document_id=payload.document_id,
        subject_type=payload.subject_type.value,
        subject_id=payload.subject_id,
        extraction_id=payload.extraction_id,
        segment_id=payload.segment_id,
        evidence_role=payload.evidence_role.value,
        quoted_text=payload.quoted_text,
        source_location=payload.source_location,
        validation_status=validation_status.value,
        review_status=payload.review_status.value,
        notes=payload.notes,
    )
    session.add(row)
    _add_audit(
        session,
        company_id=company_id,
        event_type="EVIDENCE_LINK_CREATED",
        entity_type=payload.subject_type.value,
        entity_id=payload.subject_id,
        summary="Vinculo de evidencia creado.",
        details={"validation_status": validation_status.value},
    )
    _mark_subject_supported(
        session, company_id, payload.subject_type, payload.subject_id, validation_status
    )
    session.commit()
    session.refresh(row)
    return _evidence_link_contract(row)


@router.get("/{company_id}/evidence-links", response_model=list[CompanyEvidenceLinkContract])
def list_evidence_links(company_id: UUID, session: SessionDep) -> list[CompanyEvidenceLinkContract]:
    company = _company_or_404(session, company_id)
    return [_evidence_link_contract(row) for row in company.evidence_links]


@router.patch(
    "/{company_id}/evidence-links/{link_id}/review", response_model=CompanyEvidenceLinkContract
)
def review_evidence_link(
    company_id: UUID,
    link_id: UUID,
    payload: CompanyEvidenceLinkReview,
    session: SessionDep,
) -> CompanyEvidenceLinkContract:
    row = session.scalar(
        select(CompanyEvidenceLink).where(
            CompanyEvidenceLink.company_id == company_id,
            CompanyEvidenceLink.id == link_id,
        )
    )
    if row is None:
        raise DomainError(
            CompanyErrorCode.EVIDENCE_LINK_NOT_FOUND,
            "El vinculo de evidencia no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    row.review_status = payload.review_status.value
    row.notes = payload.notes
    session.commit()
    session.refresh(row)
    return _evidence_link_contract(row)


@router.get("/{company_id}/completeness", response_model=CompanyProfileCompleteness)
def get_completeness(company_id: UUID, session: SessionDep) -> CompanyProfileCompleteness:
    company = _company_or_404(session, company_id)
    return calculate_completeness(session, company)


@router.post("/{company_id}/snapshots", response_model=CompanyProfileSnapshotDetail)
def create_snapshot(
    company_id: UUID, payload: CompanyProfileSnapshotCreate, session: SessionDep
) -> CompanyProfileSnapshotDetail:
    company = _company_or_404(session, company_id)
    completeness = calculate_completeness(session, company)
    if not completeness.ready_for_review and not payload.allow_incomplete:
        raise DomainError(
            CompanyErrorCode.PROFILE_INCOMPLETE,
            "El perfil tiene faltantes y no puede publicarse como listo.",
            status_code=HTTPStatus.CONFLICT,
        )
    snapshot_payload = _snapshot_payload(company, completeness)
    digest = _stable_digest(snapshot_payload)
    next_version = (
        session.scalar(
            select(func.max(CompanyProfileSnapshot.version)).where(
                CompanyProfileSnapshot.company_id == company_id
            )
        )
        or 0
    ) + 1
    row = CompanyProfileSnapshot(
        id=uuid4(),
        company_id=company_id,
        version=next_version,
        status=CompanySnapshotStatus.DRAFT.value,
        digest=digest,
        payload=snapshot_payload,
        completeness_status="READY_FOR_REVIEW" if completeness.ready_for_review else "INCOMPLETE",
        notes=payload.notes,
    )
    session.add(row)
    _add_audit(
        session,
        company_id=company_id,
        event_type="SNAPSHOT_CREATED",
        entity_type="COMPANY_PROFILE_SNAPSHOT",
        entity_id=row.id,
        summary="Snapshot de perfil creado.",
        snapshot_version=next_version,
    )
    session.commit()
    session.refresh(row)
    return _snapshot_detail(row)


@router.get("/{company_id}/snapshots", response_model=list[CompanyProfileSnapshotSummary])
def list_snapshots(company_id: UUID, session: SessionDep) -> list[CompanyProfileSnapshotSummary]:
    company = _company_or_404(session, company_id)
    return [
        _snapshot_summary(row) for row in sorted(company.snapshots, key=lambda item: item.version)
    ]


@router.get("/{company_id}/snapshots/{snapshot_id}", response_model=CompanyProfileSnapshotDetail)
def get_snapshot(
    company_id: UUID, snapshot_id: UUID, session: SessionDep
) -> CompanyProfileSnapshotDetail:
    return _snapshot_detail(_snapshot_or_404(session, company_id, snapshot_id))


@router.post(
    "/{company_id}/snapshots/{snapshot_id}/publish", response_model=CompanyProfileSnapshotDetail
)
def publish_snapshot(
    company_id: UUID, snapshot_id: UUID, session: SessionDep
) -> CompanyProfileSnapshotDetail:
    row = _snapshot_or_404(session, company_id, snapshot_id)
    if row.status == CompanySnapshotStatus.PUBLISHED.value:
        raise DomainError(
            CompanyErrorCode.SNAPSHOT_ALREADY_PUBLISHED,
            "El snapshot ya fue publicado.",
            status_code=HTTPStatus.CONFLICT,
        )
    current_digest = _stable_digest(row.payload)
    if current_digest != row.digest:
        raise DomainError(
            CompanyErrorCode.SNAPSHOT_DIGEST_MISMATCH,
            "El digest del snapshot no coincide.",
            status_code=HTTPStatus.CONFLICT,
        )
    for existing in session.scalars(
        select(CompanyProfileSnapshot).where(
            CompanyProfileSnapshot.company_id == company_id,
            CompanyProfileSnapshot.status == CompanySnapshotStatus.PUBLISHED.value,
        )
    ):
        existing.status = CompanySnapshotStatus.SUPERSEDED.value
    row.status = CompanySnapshotStatus.PUBLISHED.value
    row.published_at = datetime.now(UTC)
    _add_audit(
        session,
        company_id=company_id,
        event_type="SNAPSHOT_PUBLISHED",
        entity_type="COMPANY_PROFILE_SNAPSHOT",
        entity_id=row.id,
        summary="Snapshot de perfil publicado.",
        snapshot_version=row.version,
    )
    session.commit()
    session.refresh(row)
    return _snapshot_detail(row)


def calculate_completeness(session: Session, company: CompanyProfile) -> CompanyProfileCompleteness:
    now = datetime.now(UTC)
    links = list(company.evidence_links)
    supported_subjects = {
        (link.subject_type, str(link.subject_id))
        for link in links
        if link.review_status != CompanyEvidenceReviewStatus.REJECTED.value
    }
    records: list[tuple[str, str, UUID, str]] = []
    records.extend(
        ("LEGAL_REGISTRATION", "legal", item.id, item.status)
        for item in company.legal_registrations
    )
    records.extend(("RUP_SNAPSHOT", "rup", item.id, item.status) for item in company.rup_snapshots)
    records.extend(("UNSPSC_CODE", "unspsc", item.id, item.status) for item in company.unspsc_codes)
    records.extend(
        ("FINANCIAL_PERIOD", "financial", item.id, item.status)
        for item in company.financial_periods
    )
    for period in company.financial_periods:
        records.extend(
            ("FINANCIAL_METRIC", "financial", item.id, item.status) for item in period.metrics
        )
    records.extend(
        ("EXPERIENCE_RECORD", "experience", item.id, item.status)
        for item in company.experience_records
    )
    records.extend(("PERSON", "personnel", item.id, item.status) for item in company.people)
    for person in company.people:
        records.extend(
            ("PERSON_CREDENTIAL", "personnel", item.id, item.status) for item in person.credentials
        )
    records.extend(
        ("COMPANY_CERTIFICATION", "certifications", item.id, item.status)
        for item in company.certifications
    )
    records.extend(
        ("COMPANY_CAPABILITY", "capabilities", item.id, item.status)
        for item in company.capabilities
    )
    supported_count = sum(
        1
        for subject_type, _, subject_id, _ in records
        if (subject_type, str(subject_id)) in supported_subjects
    )
    unsupported_record_count = sum(
        1
        for subject_type, _, subject_id, status in records
        if status == CompanyRecordStatus.DECLARED.value
        and (subject_type, str(subject_id)) not in supported_subjects
    )
    expired_evidence_count = sum(
        1
        for doc in company.evidence_documents
        if doc.review_status == CompanyEvidenceReviewStatus.EXPIRED.value
        or (doc.expires_at is not None and doc.expires_at < date.today())
    )
    conflicting_evidence_count = sum(
        1 for link in links if link.evidence_role == CompanyEvidenceRole.CONFLICTING.value
    )
    missing: list[CompanyProfileMissingItem] = []
    identity_complete = bool(company.legal_name and company.tax_id)
    if not identity_complete:
        missing.append(
            CompanyProfileMissingItem(
                category="identity",
                subject_type=CompanyEvidenceSubjectType.COMPANY_PROFILE,
                subject_id=company.id,
                message="Falta NIT o datos basicos de identidad.",
                severity="WARNING",
            )
        )
    checks = {
        "legal_registration_complete": bool(company.legal_registrations),
        "rup_complete": bool(company.rup_snapshots),
        "financial_complete": bool(
            company.financial_periods and any(p.metrics for p in company.financial_periods)
        ),
        "experience_complete": bool(company.experience_records),
        "personnel_complete": bool(company.people),
        "certifications_complete": bool(company.certifications),
    }
    for name, ok in checks.items():
        if not ok:
            missing.append(
                CompanyProfileMissingItem(
                    category=name.removesuffix("_complete"),
                    message=f"No hay registros para {name.removesuffix('_complete')}.",
                    severity="WARNING",
                )
            )
    for subject_type, category, subject_id, status in records:
        if (subject_type, str(subject_id)) not in supported_subjects:
            missing.append(
                CompanyProfileMissingItem(
                    category=category,
                    subject_type=CompanyEvidenceSubjectType(subject_type),
                    subject_id=subject_id,
                    message="Registro sin evidencia vinculada.",
                    severity="WARNING"
                    if status != CompanyRecordStatus.REJECTED.value
                    else "BLOCKING",
                )
            )
    coverage = 1 if not records else supported_count / len(records)
    ready_for_review = (
        identity_complete
        and all(checks.values())
        and unsupported_record_count == 0
        and expired_evidence_count == 0
        and conflicting_evidence_count == 0
    )
    return CompanyProfileCompleteness(
        company_id=company.id,
        identity_complete=identity_complete,
        legal_registration_complete=checks["legal_registration_complete"],
        rup_complete=checks["rup_complete"],
        financial_complete=checks["financial_complete"],
        experience_complete=checks["experience_complete"],
        personnel_complete=checks["personnel_complete"],
        certifications_complete=checks["certifications_complete"],
        evidence_coverage=coverage,
        expired_evidence_count=expired_evidence_count,
        unsupported_record_count=unsupported_record_count,
        conflicting_evidence_count=conflicting_evidence_count,
        missing_items=missing,
        ready_for_review=ready_for_review,
        generated_at=now,
    )


def _snapshot_payload(
    company: CompanyProfile, completeness: CompanyProfileCompleteness
) -> dict[str, Any]:
    return {
        "company": _company_detail(company).model_dump(mode="json"),
        "legal_registrations": [
            _legal_registration_contract(item).model_dump(mode="json")
            for item in company.legal_registrations
        ],
        "rup_snapshots": [
            _rup_contract(item).model_dump(mode="json") for item in company.rup_snapshots
        ],
        "unspsc_codes": [
            _unspsc_contract(item).model_dump(mode="json") for item in company.unspsc_codes
        ],
        "financial_periods": [
            _financial_period_contract(item).model_dump(mode="json")
            for item in company.financial_periods
        ],
        "experience_records": [
            _experience_contract(item).model_dump(mode="json")
            for item in company.experience_records
        ],
        "people": [_person_contract(item).model_dump(mode="json") for item in company.people],
        "certifications": [
            _certification_contract(item).model_dump(mode="json") for item in company.certifications
        ],
        "capabilities": [
            _capability_contract(item).model_dump(mode="json") for item in company.capabilities
        ],
        "evidence_documents": [
            _evidence_document_contract(item).model_dump(mode="json")
            for item in company.evidence_documents
        ],
        "evidence_links": [
            _evidence_link_contract(item).model_dump(mode="json") for item in company.evidence_links
        ],
        "completeness": completeness.model_dump(mode="json"),
    }


def _stable_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _dump(payload: Any) -> dict[str, Any]:
    data = payload.model_dump(exclude_unset=True)
    for key, value in list(data.items()):
        if hasattr(value, "value"):
            data[key] = value.value
        if isinstance(value, list):
            data[key] = [item.value if hasattr(item, "value") else item for item in value]
    return data


def _patch(row: Any, payload: Any) -> None:
    for key, value in _dump(payload).items():
        setattr(row, key, value)


def _company_row_or_404(
    session: Session, model: Any, company_id: UUID, row_id: UUID, code: CompanyErrorCode
) -> Any:
    row = session.scalar(select(model).where(model.company_id == company_id, model.id == row_id))
    if row is None:
        raise DomainError(code, "El registro no existe.", status_code=HTTPStatus.NOT_FOUND)
    return row


def _person_or_404(session: Session, company_id: UUID, person_id: UUID) -> CompanyPerson:
    row = _company_row_or_404(
        session, CompanyPerson, company_id, person_id, CompanyErrorCode.PERSON_NOT_FOUND
    )
    return row


def _evidence_document_or_404(
    session: Session, company_id: UUID, document_id: UUID
) -> CompanyEvidenceDocument:
    row = session.scalar(
        select(CompanyEvidenceDocument)
        .where(
            CompanyEvidenceDocument.company_id == company_id,
            CompanyEvidenceDocument.id == document_id,
        )
        .options(selectinload(CompanyEvidenceDocument.process_document))
    )
    if row is None:
        raise DomainError(
            CompanyErrorCode.EVIDENCE_DOCUMENT_NOT_FOUND,
            "El documento de evidencia no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return row


def _snapshot_or_404(
    session: Session, company_id: UUID, snapshot_id: UUID
) -> CompanyProfileSnapshot:
    row = session.scalar(
        select(CompanyProfileSnapshot).where(
            CompanyProfileSnapshot.company_id == company_id,
            CompanyProfileSnapshot.id == snapshot_id,
        )
    )
    if row is None:
        raise DomainError(
            CompanyErrorCode.SNAPSHOT_NOT_FOUND,
            "El snapshot no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return row


def _validate_subject_belongs_to_company(
    session: Session,
    company_id: UUID,
    subject_type: CompanyEvidenceSubjectType,
    subject_id: UUID,
) -> None:
    if subject_type == CompanyEvidenceSubjectType.COMPANY_PROFILE:
        if subject_id != company_id:
            raise DomainError(
                CompanyErrorCode.EVIDENCE_SUBJECT_COMPANY_MISMATCH,
                "El dato no pertenece a la empresa.",
                status_code=HTTPStatus.BAD_REQUEST,
            )
        return
    model_map = {
        CompanyEvidenceSubjectType.LEGAL_REGISTRATION: CompanyLegalRegistration,
        CompanyEvidenceSubjectType.RUP_SNAPSHOT: RupSnapshot,
        CompanyEvidenceSubjectType.UNSPSC_CODE: CompanyUnspscCode,
        CompanyEvidenceSubjectType.FINANCIAL_PERIOD: CompanyFinancialPeriod,
        CompanyEvidenceSubjectType.EXPERIENCE_RECORD: CompanyExperienceRecord,
        CompanyEvidenceSubjectType.PERSON: CompanyPerson,
        CompanyEvidenceSubjectType.COMPANY_CERTIFICATION: CompanyCertification,
        CompanyEvidenceSubjectType.COMPANY_CAPABILITY: CompanyCapability,
    }
    if subject_type == CompanyEvidenceSubjectType.FINANCIAL_METRIC:
        row = session.scalar(
            select(CompanyFinancialMetric)
            .join(CompanyFinancialPeriod)
            .where(
                CompanyFinancialPeriod.company_id == company_id,
                CompanyFinancialMetric.id == subject_id,
            )
        )
    elif subject_type in {
        CompanyEvidenceSubjectType.PERSON_EDUCATION,
        CompanyEvidenceSubjectType.PERSON_EXPERIENCE,
        CompanyEvidenceSubjectType.PERSON_CREDENTIAL,
    }:
        person_model = {
            CompanyEvidenceSubjectType.PERSON_EDUCATION: PersonEducation,
            CompanyEvidenceSubjectType.PERSON_EXPERIENCE: PersonExperience,
            CompanyEvidenceSubjectType.PERSON_CREDENTIAL: PersonCredential,
        }[subject_type]
        row = session.scalar(
            select(person_model)
            .join(CompanyPerson)
            .where(CompanyPerson.company_id == company_id, person_model.id == subject_id)
        )
    else:
        model = model_map.get(subject_type)
        row = (
            None
            if model is None
            else session.scalar(
                select(model).where(model.company_id == company_id, model.id == subject_id)
            )
        )
    if row is None:
        raise DomainError(
            CompanyErrorCode.EVIDENCE_SUBJECT_NOT_FOUND,
            "El dato a soportar no existe para esta empresa.",
            status_code=HTTPStatus.NOT_FOUND,
        )


def _validate_evidence_reference(
    session: Session,
    document: CompanyEvidenceDocument,
    payload: CompanyEvidenceLinkCreate,
) -> CompanyEvidenceValidationStatus:
    if payload.segment_id is None:
        return _expired_or(CompanyEvidenceValidationStatus.DOCUMENT_ONLY, document)
    segment = session.get(ExtractedSegment, payload.segment_id)
    if segment is None:
        return CompanyEvidenceValidationStatus.INVALID_SEGMENT
    extraction = session.get(DocumentExtraction, segment.extraction_id)
    if extraction is None or extraction.document_id != document.process_document_id:
        return CompanyEvidenceValidationStatus.INVALID_SEGMENT
    if payload.extraction_id is not None and payload.extraction_id != extraction.id:
        return CompanyEvidenceValidationStatus.INVALID_SEGMENT
    if payload.quoted_text and payload.quoted_text not in segment.text:
        return CompanyEvidenceValidationStatus.QUOTE_NOT_FOUND
    return _expired_or(CompanyEvidenceValidationStatus.VALID_SEGMENT, document)


def _expired_or(
    status: CompanyEvidenceValidationStatus,
    document: CompanyEvidenceDocument,
) -> CompanyEvidenceValidationStatus:
    if document.expires_at is not None and document.expires_at < date.today():
        return CompanyEvidenceValidationStatus.EXPIRED_EVIDENCE
    return status


def _mark_subject_supported(
    session: Session,
    company_id: UUID,
    subject_type: CompanyEvidenceSubjectType,
    subject_id: UUID,
    validation_status: CompanyEvidenceValidationStatus,
) -> None:
    if validation_status in {
        CompanyEvidenceValidationStatus.INVALID_SEGMENT,
        CompanyEvidenceValidationStatus.QUOTE_NOT_FOUND,
        CompanyEvidenceValidationStatus.LOCATION_MISMATCH,
    }:
        return
    if subject_type == CompanyEvidenceSubjectType.COMPANY_PROFILE:
        return
    model_map = {
        CompanyEvidenceSubjectType.LEGAL_REGISTRATION: CompanyLegalRegistration,
        CompanyEvidenceSubjectType.RUP_SNAPSHOT: RupSnapshot,
        CompanyEvidenceSubjectType.UNSPSC_CODE: CompanyUnspscCode,
        CompanyEvidenceSubjectType.FINANCIAL_PERIOD: CompanyFinancialPeriod,
        CompanyEvidenceSubjectType.EXPERIENCE_RECORD: CompanyExperienceRecord,
        CompanyEvidenceSubjectType.PERSON: CompanyPerson,
        CompanyEvidenceSubjectType.COMPANY_CERTIFICATION: CompanyCertification,
        CompanyEvidenceSubjectType.COMPANY_CAPABILITY: CompanyCapability,
    }
    model = model_map.get(subject_type)
    if model is not None:
        row = session.scalar(
            select(model).where(model.company_id == company_id, model.id == subject_id)
        )
        if row is not None and row.status == CompanyRecordStatus.DECLARED.value:
            row.status = CompanyRecordStatus.SUPPORTED.value


def _store_company_evidence(
    *,
    company: CompanyProfile,
    upload: UploadFile,
    session: Session,
    storage: DocumentStorage,
    max_file_size: int,
    evidence_type: CompanyEvidenceType,
    title: str | None,
) -> CompanyEvidenceUploadResult:
    original_filename = upload.filename or "archivo-sin-nombre"
    temp_path: Path | None = None
    storage_key: str | None = None
    try:
        original_filename, extension = validate_original_filename(upload.filename)
        validate_declared_content_type(extension, upload.content_type)
        temp_path, digest, size_bytes = _write_temp_and_hash(upload, max_file_size)
        if size_bytes == 0:
            raise FileValidationError(UploadErrorCode.FILE_EMPTY, "El archivo esta vacio.")
        detected_content_type = detect_content_type(temp_path, extension)
        if session.scalar(
            select(CompanyEvidenceDocument.id).where(
                CompanyEvidenceDocument.company_id == company.id,
                CompanyEvidenceDocument.sha256 == digest,
            )
        ):
            return _evidence_rejected(
                original_filename, "DUPLICATE_DOCUMENT", "El documento ya fue cargado."
            )
        process_document_id = uuid4()
        stored_filename = f"{process_document_id.hex}{extension}"
        storage_key = f"companies/{company.id}/{process_document_id}/{stored_filename}"
        storage.save(temp_path, storage_key)
        temp_path = None
        process_document = ProcessDocument(
            id=process_document_id,
            process_id=company.system_process_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_key=storage_key,
            declared_content_type=upload.content_type,
            detected_content_type=detected_content_type,
            extension=extension,
            size_bytes=size_bytes,
            sha256=digest,
            document_type=DocumentType.SUPPORTING_DOCUMENT.value,
            upload_status=DocumentUploadStatus.STORED.value,
            processing_status=DocumentProcessingStatus.QUEUED.value,
        )
        session.add(process_document)
        session.add(
            DocumentProcessingJob(
                id=uuid4(),
                document_id=process_document_id,
                job_type=DocumentProcessingJobType.EXTRACT_DOCUMENT.value,
                max_attempts=get_settings().worker_max_attempts,
                available_at=datetime.now(UTC),
            )
        )
        evidence = CompanyEvidenceDocument(
            id=uuid4(),
            company_id=company.id,
            process_document_id=process_document_id,
            evidence_type=evidence_type.value,
            title=title or original_filename,
            review_status=CompanyEvidenceReviewStatus.PENDING.value,
            sha256=digest,
        )
        session.add(evidence)
        _add_audit(
            session,
            company_id=company.id,
            event_type="EVIDENCE_DOCUMENT_UPLOADED",
            entity_type="EVIDENCE_DOCUMENT",
            entity_id=evidence.id,
            summary="Documento de evidencia cargado.",
            details={"evidence_type": evidence.evidence_type, "sha256": digest},
        )
        session.commit()
        session.refresh(evidence)
        return CompanyEvidenceUploadResult(
            original_filename=original_filename,
            upload_status="STORED",
            document=_evidence_document_contract(
                _evidence_document_or_404(session, company.id, evidence.id)
            ),
            error=None,
        )
    except FileValidationError as exc:
        session.rollback()
        return _evidence_rejected(original_filename, exc.code.value, exc.message)
    except (IntegrityError, StorageError):
        session.rollback()
        if storage_key is not None:
            try:
                storage.delete(storage_key)
            except StorageError:
                logger.exception("company_evidence_compensation_failed")
        return _evidence_rejected(
            original_filename, "STORAGE_ERROR", "No fue posible almacenar la evidencia."
        )
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _evidence_rejected(
    original_filename: str, code: str, message: str
) -> CompanyEvidenceUploadResult:
    return CompanyEvidenceUploadResult(
        original_filename=original_filename,
        upload_status="REJECTED",
        document=None,
        error=ApiError(
            code=UploadErrorCode.DOCUMENT_NOT_FOUND, message=message, details={"code": code}
        ).model_dump(mode="json"),
    )


def _write_temp_and_hash(upload: UploadFile, max_file_size: int) -> tuple[Path, str, int]:
    hasher = sha256()
    size = 0
    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(
            delete=False, prefix="pliegocheck-company-upload-", suffix=".tmp"
        ) as temp:
            temp_path = Path(temp.name)
            while chunk := upload.file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > max_file_size:
                    raise FileValidationError(
                        UploadErrorCode.FILE_TOO_LARGE,
                        "El archivo supera el tamano maximo permitido.",
                    )
                hasher.update(chunk)
                temp.write(chunk)
    except Exception:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
        raise
    assert temp_path is not None
    return temp_path, hasher.hexdigest(), size


def _stream_storage(storage: DocumentStorage, storage_key: str) -> Iterator[bytes]:
    with storage.open(storage_key) as fh:
        while chunk := fh.read(CHUNK_SIZE):
            yield chunk


def _content_disposition(filename: str) -> str:
    fallback = "".join(char if char.isalnum() or char in "._-" else "_" for char in filename)
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename)}"
