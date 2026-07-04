"""Genera los artefactos derivados de los contratos canonicos Pydantic.

Produce, de forma deterministica (sin fechas, rutas locales ni contenido variable):

- ``generated/<contrato>.schema.json``: JSON Schema de cada contrato.
- ``generated/<contrato>.enums.ts``: constantes TypeScript de los vocabularios
  cerrados, para consumo en runtime desde el frontend.

Los tipos TypeScript de las interfaces se generan aparte desde los JSON Schema
(``scripts/generate-ts.mjs``). Este script falla con codigo distinto de cero
si la generacion no puede completarse.
"""

import json
import sys
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from pliegocheck_schemas.company_profile import (
    COMPANY_PROFILE_SCHEMA_VERSION,
    CompanyCapabilityCategory,
    CompanyCertificationType,
    CompanyErrorCode,
    CompanyEvidenceReviewStatus,
    CompanyEvidenceRole,
    CompanyEvidenceSubjectType,
    CompanyEvidenceType,
    CompanyEvidenceValidationStatus,
    CompanyLegalRegistrationType,
    CompanyProfileContracts,
    CompanyProfileStatus,
    CompanyRecordStatus,
    CompanySnapshotStatus,
    ExperienceExecutionStatus,
    FinancialMetricType,
    FinancialSourceType,
    PersonAvailabilityStatus,
    PersonCredentialType,
    PersonRelationshipType,
)
from pliegocheck_schemas.decision import (
    DECISION_SCHEMA_VERSION,
    DecisionActionPriority,
    DecisionActionStatus,
    DecisionActionType,
    DecisionContracts,
    DecisionCoverageStatus,
    DecisionErrorCode,
    DecisionEvaluationDomain,
    DecisionFindingApplicability,
    DecisionFindingOutcome,
    DecisionFindingSourceType,
    DecisionJobStatus,
    DecisionOutcome,
    DecisionReasonCode,
    DecisionReviewAction,
    DecisionRuleStatus,
    DecisionRunStatus,
)
from pliegocheck_schemas.decision_report import (
    DECISION_REPORT_SCHEMA_VERSION,
    DecisionReportArtifactType,
    DecisionReportContracts,
    DecisionReportErrorCode,
    DecisionReportJobStatus,
    DecisionReportPackageStatus,
)
from pliegocheck_schemas.document_extraction import (
    DOCUMENT_EXTRACTION_SCHEMA_VERSION,
    DocumentExtractionContracts,
    DocumentExtractionStatus,
    DocumentProcessingJobStatus,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
    ExtractedSegmentType,
    ExtractionErrorCode,
)
from pliegocheck_schemas.financial_evaluation import (
    FINANCIAL_EVALUATION_SCHEMA_VERSION,
    FinancialCalculationStatus,
    FinancialCompositeOperator,
    FinancialErrorCode,
    FinancialEvaluationContracts,
    FinancialEvaluationJobStatus,
    FinancialEvaluationResultStatus,
    FinancialEvaluationReviewStatus,
    FinancialEvaluationRunStatus,
    FinancialExplanationCode,
    FinancialMetricUsability,
    FinancialOperator,
    FinancialPeriodPolicy,
    FinancialRuleMappingStatus,
    FinancialRuleSourceBasis,
    FinancialRuleType,
)
from pliegocheck_schemas.manual_import import (
    MANUAL_IMPORT_SCHEMA_VERSION,
    DocumentType,
    DocumentUploadStatus,
    ManualImportContracts,
    ProcessSource,
    ProcessStatus,
    UploadErrorCode,
)
from pliegocheck_schemas.normalized_requirement import (
    NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
    NormalizationErrorCode,
    NormalizationProvider,
    NormalizedRequirement,
    RejectedCandidateReason,
    RequirementBasis,
    RequirementCategory,
    RequirementCriticality,
    RequirementEvidenceRole,
    RequirementEvidenceStatus,
    RequirementEvidenceValidationStatus,
    RequirementModality,
    RequirementNormalizationContracts,
    RequirementNormalizationStatus,
    RequirementRelationType,
    RequirementReviewStatus,
    RequirementScope,
    RequirementSubsanability,
)
from pliegocheck_schemas.specialized_evaluation import (
    SPECIALIZED_EVALUATION_SCHEMA_VERSION,
    SpecializedDataUsability,
    SpecializedErrorCode,
    SpecializedEvaluationContracts,
    SpecializedEvaluationDomain,
    SpecializedEvaluationJobStatus,
    SpecializedEvaluationResultStatus,
    SpecializedEvaluationReviewStatus,
    SpecializedEvaluationRunStatus,
    SpecializedEvidenceValidationStatus,
    SpecializedExplanationCode,
    SpecializedOperator,
    SpecializedRuleMappingStatus,
    SpecializedRuleSourceBasis,
    SpecializedRuleType,
)

GENERATED_DIR = Path(__file__).resolve().parent.parent / "generated"

TS_HEADER = (
    "// Archivo generado automaticamente por packages/schemas/scripts/generate.py.\n"
    "// No editar a mano: la definicion canonica son los modelos Pydantic de\n"
    "// packages/schemas/src/pliegocheck_schemas/.\n"
)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


def strip_property_titles(node: object) -> None:
    """Elimina ``title`` recursivamente.

    Los nombres de los tipos TypeScript provienen de las claves de ``$defs``;
    los ``title`` por propiedad solo generan aliases ruidosos y colisiones.
    """
    if isinstance(node, dict):
        node.pop("title", None)
        for key, value in node.items():
            if key == "properties" and isinstance(value, dict):
                for property_schema in value.values():
                    strip_property_titles(property_schema)
                continue
            strip_property_titles(value)
    elif isinstance(node, list):
        for item in node:
            strip_property_titles(item)


def generate_json_schema(model: type[BaseModel], filename: str) -> None:
    schema = model.model_json_schema()
    strip_property_titles(schema)
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    content = json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    write_text(GENERATED_DIR / filename, content)


def ts_const_block(const_name: str, type_name: str, enum_cls: type[StrEnum]) -> str:
    values = ", ".join(f'"{member.value}"' for member in enum_cls)
    return (
        f"export const {const_name} = [{values}] as const;\n"
        f"export type {type_name} = (typeof {const_name})[number];\n"
    )


def generate_requirement_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        "export const NORMALIZED_REQUIREMENT_SCHEMA_VERSION = "
        f'"{NORMALIZED_REQUIREMENT_SCHEMA_VERSION}";\n',
        ts_const_block(
            "REQUIREMENT_CATEGORY_VALUES", "RequirementCategoryValue", RequirementCategory
        ),
        ts_const_block("REQUIREMENT_SCOPE_VALUES", "RequirementScopeValue", RequirementScope),
        ts_const_block(
            "REQUIREMENT_MODALITY_VALUES", "RequirementModalityValue", RequirementModality
        ),
        ts_const_block(
            "REQUIREMENT_CRITICALITY_VALUES", "RequirementCriticalityValue", RequirementCriticality
        ),
        ts_const_block("REQUIREMENT_BASIS_VALUES", "RequirementBasisValue", RequirementBasis),
        ts_const_block(
            "REQUIREMENT_SUBSANABILITY_VALUES",
            "RequirementSubsanabilityValue",
            RequirementSubsanability,
        ),
        ts_const_block(
            "REQUIREMENT_EVIDENCE_STATUS_VALUES",
            "RequirementEvidenceStatusValue",
            RequirementEvidenceStatus,
        ),
        ts_const_block(
            "REQUIREMENT_REVIEW_STATUS_VALUES",
            "RequirementReviewStatusValue",
            RequirementReviewStatus,
        ),
        ts_const_block(
            "REQUIREMENT_EVIDENCE_ROLE_VALUES",
            "RequirementEvidenceRoleValue",
            RequirementEvidenceRole,
        ),
        ts_const_block(
            "REQUIREMENT_EVIDENCE_VALIDATION_STATUS_VALUES",
            "RequirementEvidenceValidationStatusValue",
            RequirementEvidenceValidationStatus,
        ),
        ts_const_block(
            "REQUIREMENT_RELATION_TYPE_VALUES",
            "RequirementRelationTypeValue",
            RequirementRelationType,
        ),
        ts_const_block(
            "NORMALIZATION_PROVIDER_VALUES",
            "NormalizationProviderValue",
            NormalizationProvider,
        ),
        ts_const_block(
            "REQUIREMENT_NORMALIZATION_STATUS_VALUES",
            "RequirementNormalizationStatusValue",
            RequirementNormalizationStatus,
        ),
        ts_const_block(
            "REJECTED_CANDIDATE_REASON_VALUES",
            "RejectedCandidateReasonValue",
            RejectedCandidateReason,
        ),
        ts_const_block(
            "NORMALIZATION_ERROR_CODE_VALUES",
            "NormalizationErrorCodeValue",
            NormalizationErrorCode,
        ),
    ]
    write_text(GENERATED_DIR / "normalized-requirement.enums.ts", "\n".join(blocks))


def generate_manual_import_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        f'export const MANUAL_IMPORT_SCHEMA_VERSION = "{MANUAL_IMPORT_SCHEMA_VERSION}";\n',
        ts_const_block("PROCESS_SOURCE_VALUES", "ProcessSourceValue", ProcessSource),
        ts_const_block("PROCESS_STATUS_VALUES", "ProcessStatusValue", ProcessStatus),
        ts_const_block("DOCUMENT_TYPE_VALUES", "DocumentTypeValue", DocumentType),
        ts_const_block(
            "DOCUMENT_UPLOAD_STATUS_VALUES", "DocumentUploadStatusValue", DocumentUploadStatus
        ),
        ts_const_block("UPLOAD_ERROR_CODE_VALUES", "UploadErrorCodeValue", UploadErrorCode),
    ]
    write_text(GENERATED_DIR / "manual-import.enums.ts", "\n".join(blocks))


def generate_document_extraction_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        "export const DOCUMENT_EXTRACTION_SCHEMA_VERSION = "
        f'"{DOCUMENT_EXTRACTION_SCHEMA_VERSION}";\n',
        ts_const_block(
            "DOCUMENT_PROCESSING_STATUS_VALUES",
            "DocumentProcessingStatusValue",
            DocumentProcessingStatus,
        ),
        ts_const_block(
            "DOCUMENT_PROCESSING_JOB_STATUS_VALUES",
            "DocumentProcessingJobStatusValue",
            DocumentProcessingJobStatus,
        ),
        ts_const_block(
            "DOCUMENT_PROCESSING_JOB_TYPE_VALUES",
            "DocumentProcessingJobTypeValue",
            DocumentProcessingJobType,
        ),
        ts_const_block(
            "DOCUMENT_EXTRACTION_STATUS_VALUES",
            "DocumentExtractionStatusValue",
            DocumentExtractionStatus,
        ),
        ts_const_block(
            "EXTRACTED_SEGMENT_TYPE_VALUES",
            "ExtractedSegmentTypeValue",
            ExtractedSegmentType,
        ),
        ts_const_block(
            "EXTRACTION_ERROR_CODE_VALUES",
            "ExtractionErrorCodeValue",
            ExtractionErrorCode,
        ),
    ]
    write_text(GENERATED_DIR / "document-extraction.enums.ts", "\n".join(blocks))


def generate_company_profile_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        f'export const COMPANY_PROFILE_SCHEMA_VERSION = "{COMPANY_PROFILE_SCHEMA_VERSION}";\n',
        ts_const_block(
            "COMPANY_PROFILE_STATUS_VALUES", "CompanyProfileStatusValue", CompanyProfileStatus
        ),
        ts_const_block(
            "COMPANY_RECORD_STATUS_VALUES", "CompanyRecordStatusValue", CompanyRecordStatus
        ),
        ts_const_block(
            "COMPANY_LEGAL_REGISTRATION_TYPE_VALUES",
            "CompanyLegalRegistrationTypeValue",
            CompanyLegalRegistrationType,
        ),
        ts_const_block(
            "FINANCIAL_SOURCE_TYPE_VALUES", "FinancialSourceTypeValue", FinancialSourceType
        ),
        ts_const_block(
            "FINANCIAL_METRIC_TYPE_VALUES", "FinancialMetricTypeValue", FinancialMetricType
        ),
        ts_const_block(
            "EXPERIENCE_EXECUTION_STATUS_VALUES",
            "ExperienceExecutionStatusValue",
            ExperienceExecutionStatus,
        ),
        ts_const_block(
            "PERSON_RELATIONSHIP_TYPE_VALUES",
            "PersonRelationshipTypeValue",
            PersonRelationshipType,
        ),
        ts_const_block(
            "PERSON_AVAILABILITY_STATUS_VALUES",
            "PersonAvailabilityStatusValue",
            PersonAvailabilityStatus,
        ),
        ts_const_block(
            "PERSON_CREDENTIAL_TYPE_VALUES", "PersonCredentialTypeValue", PersonCredentialType
        ),
        ts_const_block(
            "COMPANY_CERTIFICATION_TYPE_VALUES",
            "CompanyCertificationTypeValue",
            CompanyCertificationType,
        ),
        ts_const_block(
            "COMPANY_CAPABILITY_CATEGORY_VALUES",
            "CompanyCapabilityCategoryValue",
            CompanyCapabilityCategory,
        ),
        ts_const_block(
            "COMPANY_EVIDENCE_TYPE_VALUES", "CompanyEvidenceTypeValue", CompanyEvidenceType
        ),
        ts_const_block(
            "COMPANY_EVIDENCE_REVIEW_STATUS_VALUES",
            "CompanyEvidenceReviewStatusValue",
            CompanyEvidenceReviewStatus,
        ),
        ts_const_block(
            "COMPANY_EVIDENCE_SUBJECT_TYPE_VALUES",
            "CompanyEvidenceSubjectTypeValue",
            CompanyEvidenceSubjectType,
        ),
        ts_const_block(
            "COMPANY_EVIDENCE_ROLE_VALUES", "CompanyEvidenceRoleValue", CompanyEvidenceRole
        ),
        ts_const_block(
            "COMPANY_EVIDENCE_VALIDATION_STATUS_VALUES",
            "CompanyEvidenceValidationStatusValue",
            CompanyEvidenceValidationStatus,
        ),
        ts_const_block(
            "COMPANY_SNAPSHOT_STATUS_VALUES", "CompanySnapshotStatusValue", CompanySnapshotStatus
        ),
        ts_const_block("COMPANY_ERROR_CODE_VALUES", "CompanyErrorCodeValue", CompanyErrorCode),
    ]
    write_text(GENERATED_DIR / "company-profile.enums.ts", "\n".join(blocks))


def generate_financial_evaluation_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        "export const FINANCIAL_EVALUATION_SCHEMA_VERSION = "
        f'"{FINANCIAL_EVALUATION_SCHEMA_VERSION}";\n',
        ts_const_block(
            "FINANCIAL_EVALUATION_JOB_STATUS_VALUES",
            "FinancialEvaluationJobStatusValue",
            FinancialEvaluationJobStatus,
        ),
        ts_const_block(
            "FINANCIAL_EVALUATION_RUN_STATUS_VALUES",
            "FinancialEvaluationRunStatusValue",
            FinancialEvaluationRunStatus,
        ),
        ts_const_block(
            "FINANCIAL_EVALUATION_RESULT_STATUS_VALUES",
            "FinancialEvaluationResultStatusValue",
            FinancialEvaluationResultStatus,
        ),
        ts_const_block(
            "FINANCIAL_EVALUATION_REVIEW_STATUS_VALUES",
            "FinancialEvaluationReviewStatusValue",
            FinancialEvaluationReviewStatus,
        ),
        ts_const_block("FINANCIAL_RULE_TYPE_VALUES", "FinancialRuleTypeValue", FinancialRuleType),
        ts_const_block(
            "FINANCIAL_RULE_MAPPING_STATUS_VALUES",
            "FinancialRuleMappingStatusValue",
            FinancialRuleMappingStatus,
        ),
        ts_const_block("FINANCIAL_OPERATOR_VALUES", "FinancialOperatorValue", FinancialOperator),
        ts_const_block(
            "FINANCIAL_PERIOD_POLICY_VALUES",
            "FinancialPeriodPolicyValue",
            FinancialPeriodPolicy,
        ),
        ts_const_block(
            "FINANCIAL_METRIC_USABILITY_VALUES",
            "FinancialMetricUsabilityValue",
            FinancialMetricUsability,
        ),
        ts_const_block(
            "FINANCIAL_CALCULATION_STATUS_VALUES",
            "FinancialCalculationStatusValue",
            FinancialCalculationStatus,
        ),
        ts_const_block(
            "FINANCIAL_COMPOSITE_OPERATOR_VALUES",
            "FinancialCompositeOperatorValue",
            FinancialCompositeOperator,
        ),
        ts_const_block(
            "FINANCIAL_RULE_SOURCE_BASIS_VALUES",
            "FinancialRuleSourceBasisValue",
            FinancialRuleSourceBasis,
        ),
        ts_const_block(
            "FINANCIAL_EXPLANATION_CODE_VALUES",
            "FinancialExplanationCodeValue",
            FinancialExplanationCode,
        ),
        ts_const_block(
            "FINANCIAL_ERROR_CODE_VALUES",
            "FinancialErrorCodeValue",
            FinancialErrorCode,
        ),
    ]
    write_text(GENERATED_DIR / "financial-evaluation.enums.ts", "\n".join(blocks))


def generate_decision_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        f'export const DECISION_SCHEMA_VERSION = "{DECISION_SCHEMA_VERSION}";\n',
        ts_const_block("DECISION_OUTCOME_VALUES", "DecisionOutcomeValue", DecisionOutcome),
        ts_const_block("DECISION_JOB_STATUS_VALUES", "DecisionJobStatusValue", DecisionJobStatus),
        ts_const_block("DECISION_RUN_STATUS_VALUES", "DecisionRunStatusValue", DecisionRunStatus),
        ts_const_block(
            "DECISION_FINDING_OUTCOME_VALUES",
            "DecisionFindingOutcomeValue",
            DecisionFindingOutcome,
        ),
        ts_const_block(
            "DECISION_EVALUATION_DOMAIN_VALUES",
            "DecisionEvaluationDomainValue",
            DecisionEvaluationDomain,
        ),
        ts_const_block(
            "DECISION_FINDING_APPLICABILITY_VALUES",
            "DecisionFindingApplicabilityValue",
            DecisionFindingApplicability,
        ),
        ts_const_block(
            "DECISION_FINDING_SOURCE_TYPE_VALUES",
            "DecisionFindingSourceTypeValue",
            DecisionFindingSourceType,
        ),
        ts_const_block(
            "DECISION_COVERAGE_STATUS_VALUES",
            "DecisionCoverageStatusValue",
            DecisionCoverageStatus,
        ),
        ts_const_block(
            "DECISION_RULE_STATUS_VALUES", "DecisionRuleStatusValue", DecisionRuleStatus
        ),
        ts_const_block(
            "DECISION_REVIEW_ACTION_VALUES", "DecisionReviewActionValue", DecisionReviewAction
        ),
        ts_const_block(
            "DECISION_ACTION_TYPE_VALUES", "DecisionActionTypeValue", DecisionActionType
        ),
        ts_const_block(
            "DECISION_ACTION_PRIORITY_VALUES",
            "DecisionActionPriorityValue",
            DecisionActionPriority,
        ),
        ts_const_block(
            "DECISION_ACTION_STATUS_VALUES",
            "DecisionActionStatusValue",
            DecisionActionStatus,
        ),
        ts_const_block(
            "DECISION_REASON_CODE_VALUES", "DecisionReasonCodeValue", DecisionReasonCode
        ),
        ts_const_block("DECISION_ERROR_CODE_VALUES", "DecisionErrorCodeValue", DecisionErrorCode),
    ]
    write_text(GENERATED_DIR / "decision.enums.ts", "\n".join(blocks))


def generate_decision_report_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        f'export const DECISION_REPORT_SCHEMA_VERSION = "{DECISION_REPORT_SCHEMA_VERSION}";\n',
        ts_const_block(
            "DECISION_REPORT_JOB_STATUS_VALUES",
            "DecisionReportJobStatusValue",
            DecisionReportJobStatus,
        ),
        ts_const_block(
            "DECISION_REPORT_PACKAGE_STATUS_VALUES",
            "DecisionReportPackageStatusValue",
            DecisionReportPackageStatus,
        ),
        ts_const_block(
            "DECISION_REPORT_ARTIFACT_TYPE_VALUES",
            "DecisionReportArtifactTypeValue",
            DecisionReportArtifactType,
        ),
        ts_const_block(
            "DECISION_REPORT_ERROR_CODE_VALUES",
            "DecisionReportErrorCodeValue",
            DecisionReportErrorCode,
        ),
    ]
    write_text(GENERATED_DIR / "decision-report.enums.ts", "\n".join(blocks))


def generate_specialized_evaluation_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        "export const SPECIALIZED_EVALUATION_SCHEMA_VERSION = "
        f'"{SPECIALIZED_EVALUATION_SCHEMA_VERSION}";\n',
        ts_const_block(
            "SPECIALIZED_EVALUATION_DOMAIN_VALUES",
            "SpecializedEvaluationDomainValue",
            SpecializedEvaluationDomain,
        ),
        ts_const_block(
            "SPECIALIZED_EVALUATION_JOB_STATUS_VALUES",
            "SpecializedEvaluationJobStatusValue",
            SpecializedEvaluationJobStatus,
        ),
        ts_const_block(
            "SPECIALIZED_EVALUATION_RUN_STATUS_VALUES",
            "SpecializedEvaluationRunStatusValue",
            SpecializedEvaluationRunStatus,
        ),
        ts_const_block(
            "SPECIALIZED_EVALUATION_RESULT_STATUS_VALUES",
            "SpecializedEvaluationResultStatusValue",
            SpecializedEvaluationResultStatus,
        ),
        ts_const_block(
            "SPECIALIZED_EVALUATION_REVIEW_STATUS_VALUES",
            "SpecializedEvaluationReviewStatusValue",
            SpecializedEvaluationReviewStatus,
        ),
        ts_const_block(
            "SPECIALIZED_RULE_TYPE_VALUES", "SpecializedRuleTypeValue", SpecializedRuleType
        ),
        ts_const_block(
            "SPECIALIZED_RULE_MAPPING_STATUS_VALUES",
            "SpecializedRuleMappingStatusValue",
            SpecializedRuleMappingStatus,
        ),
        ts_const_block(
            "SPECIALIZED_OPERATOR_VALUES", "SpecializedOperatorValue", SpecializedOperator
        ),
        ts_const_block(
            "SPECIALIZED_EVIDENCE_VALIDATION_STATUS_VALUES",
            "SpecializedEvidenceValidationStatusValue",
            SpecializedEvidenceValidationStatus,
        ),
        ts_const_block(
            "SPECIALIZED_DATA_USABILITY_VALUES",
            "SpecializedDataUsabilityValue",
            SpecializedDataUsability,
        ),
        ts_const_block(
            "SPECIALIZED_RULE_SOURCE_BASIS_VALUES",
            "SpecializedRuleSourceBasisValue",
            SpecializedRuleSourceBasis,
        ),
        ts_const_block(
            "SPECIALIZED_EXPLANATION_CODE_VALUES",
            "SpecializedExplanationCodeValue",
            SpecializedExplanationCode,
        ),
        ts_const_block(
            "SPECIALIZED_ERROR_CODE_VALUES", "SpecializedErrorCodeValue", SpecializedErrorCode
        ),
    ]
    write_text(GENERATED_DIR / "specialized-evaluation.enums.ts", "\n".join(blocks))


def main() -> int:
    try:
        generate_json_schema(CompanyProfileContracts, "company-profile.schema.json")
        generate_json_schema(FinancialEvaluationContracts, "financial-evaluation.schema.json")
        generate_json_schema(NormalizedRequirement, "normalized-requirement.schema.json")
        generate_json_schema(
            RequirementNormalizationContracts,
            "requirement-normalization.schema.json",
        )
        generate_json_schema(ManualImportContracts, "manual-import.schema.json")
        generate_json_schema(DocumentExtractionContracts, "document-extraction.schema.json")
        generate_json_schema(DecisionContracts, "decision.schema.json")
        generate_json_schema(DecisionReportContracts, "decision-report.schema.json")
        generate_json_schema(SpecializedEvaluationContracts, "specialized-evaluation.schema.json")
        generate_decision_enums_ts()
        generate_decision_report_enums_ts()
        generate_specialized_evaluation_enums_ts()
        generate_requirement_enums_ts()
        generate_company_profile_enums_ts()
        generate_financial_evaluation_enums_ts()
        generate_manual_import_enums_ts()
        generate_document_extraction_enums_ts()
    except Exception as exc:  # el fallo debe ser visible y con codigo distinto de cero
        print(f"ERROR generando contratos: {exc}", file=sys.stderr)
        return 1
    print("Contratos generados en packages/schemas/generated/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
