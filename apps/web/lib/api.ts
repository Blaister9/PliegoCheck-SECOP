import type {
  ApiError,
  CompanyCapability,
  CompanyCapabilityCreate,
  CompanyCertification,
  CompanyCertificationCreate,
  CompanyEvidenceDocumentMetadata,
  CompanyEvidenceLink,
  CompanyEvidenceLinkCreate,
  CompanyEvidenceLinkReview,
  CompanyEvidenceType,
  CompanyExperienceCreate,
  CompanyExperienceRecord,
  CompanyFinancialMetric,
  CompanyFinancialMetricCreate,
  CompanyFinancialPeriod,
  CompanyFinancialPeriodCreate,
  CompanyLegalRegistration,
  CompanyPerson,
  CompanyPersonCreate,
  CompanyProfileCompleteness,
  CompanyProfileCreate,
  CompanyProfileDetail,
  CompanyProfileList,
  CompanyProfileSnapshotCreate,
  CompanyProfileSnapshotDetail,
  CompanyProfileSnapshotSummary,
  CompanyProfileStatus,
  CompanyProfileUpdate,
  CompanyUnspscCode,
  CompanyUnspscCodeCreate,
  DecisionActionItem,
  DecisionActionStatus,
  DecisionQueueResponse,
  DecisionReadiness,
  DecisionRequest,
  DecisionReviewRequest,
  DecisionReviewResponse,
  DecisionRunDetail,
  DecisionRunList,
  DecisionReportPackageDetail,
  DecisionReportPackageList,
  DecisionReportPreview,
  DecisionReportQueueResponse,
  DecisionReportRequest,
  DocumentExtractionDetail,
  ExtractedSegmentList,
  ExtractedSegmentType,
  DocumentUploadResponse,
  ExtractionRetryResponse,
  FinancialEvaluationList,
  FinancialEvaluationQueueResponse,
  FinancialEvaluationRequest,
  FinancialEvaluationResultDetail,
  FinancialEvaluationResultList,
  FinancialEvaluationResultReviewRequest,
  FinancialEvaluationRunDetail,
  FinancialRequirementRule,
  FinancialRequirementRuleUpdate,
  NormalizationCreateRequest,
  NormalizationCreateResponse,
  NormalizationRetryResponse,
  NormalizationRunDetail,
  NormalizationRunList,
  ProcessInventory,
  ProcessCreate,
  ProcessDetail,
  ProcessList,
  ProcessStatus,
  RequirementDetail,
  RequirementList,
  SpecializedEvaluationDomain,
  SpecializedEvaluationList,
  SpecializedEvaluationQueueResponse,
  SpecializedEvaluationReadiness,
  SpecializedEvaluationRequest,
  SpecializedEvaluationResultDetail,
  SpecializedEvaluationResultList,
  SpecializedEvaluationResultReviewRequest,
  SpecializedEvaluationRunDetail,
} from "@pliegocheck/schemas";

const DEFAULT_TIMEOUT_MS = 10_000;

export class ApiClientError extends Error {
  readonly payload: ApiError | null;
  readonly status: number;

  constructor(message: string, status: number, payload: ApiError | null = null) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.payload = payload;
  }
}

function apiBaseUrl() {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  try {
    const response = await fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      signal: controller.signal,
      headers:
        init.body instanceof FormData
          ? init.headers
          : { "Content-Type": "application/json", ...init.headers },
    });
    if (!response.ok) {
      let payload: ApiError | null = null;
      try {
        payload = (await response.json()) as ApiError;
      } catch {
        payload = null;
      }
      throw new ApiClientError(
        payload?.message ?? "La API no pudo completar la solicitud.",
        response.status,
        payload,
      );
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiClientError("La API no respondio dentro del tiempo esperado.", 0);
    }
    throw new ApiClientError("No fue posible comunicarse con la API.", 0);
  } finally {
    clearTimeout(timeout);
  }
}

export function listProcesses(params: {
  limit?: number;
  offset?: number;
  status?: ProcessStatus | "";
  search?: string;
}) {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  if (params.status) query.set("status", params.status);
  if (params.search?.trim()) query.set("search", params.search.trim());
  return request<ProcessList>(`/processes?${query.toString()}`);
}

export function createProcess(payload: ProcessCreate) {
  return request<ProcessDetail>("/processes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getProcess(processId: string) {
  return request<ProcessDetail>(`/processes/${processId}`);
}

export function getInventory(processId: string) {
  return request<ProcessInventory>(`/processes/${processId}/inventory`);
}

export function enqueueProcessExtractions(processId: string) {
  return request<ExtractionRetryResponse[]>(`/processes/${processId}/extractions`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function enqueueDocumentExtraction(processId: string, documentId: string, force = false) {
  return request<ExtractionRetryResponse>(
    `/processes/${processId}/documents/${documentId}/extractions`,
    {
      method: "POST",
      body: JSON.stringify({ force }),
    },
  );
}

export function getDocumentExtraction(processId: string, documentId: string) {
  return request<DocumentExtractionDetail>(
    `/processes/${processId}/documents/${documentId}/extraction`,
  );
}

export function getExtractionSegments(
  processId: string,
  documentId: string,
  params: {
    limit?: number;
    offset?: number;
    page_number?: string;
    sheet_name?: string;
    segment_type?: ExtractedSegmentType | "";
  } = {},
) {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  if (params.page_number?.trim()) query.set("page_number", params.page_number.trim());
  if (params.sheet_name?.trim()) query.set("sheet_name", params.sheet_name.trim());
  if (params.segment_type) query.set("segment_type", params.segment_type);
  return request<ExtractedSegmentList>(
    `/processes/${processId}/documents/${documentId}/extraction/segments?${query.toString()}`,
  );
}

export function createRequirementNormalization(
  processId: string,
  payload: NormalizationCreateRequest = { force: false, document_ids: null },
) {
  return request<NormalizationCreateResponse>(
    `/processes/${processId}/requirements/normalizations`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function listRequirementNormalizations(processId: string) {
  return request<NormalizationRunList>(
    `/processes/${processId}/requirements/normalizations?limit=20&offset=0`,
  );
}

export function getRequirementNormalization(processId: string, runId: string) {
  return request<NormalizationRunDetail>(
    `/processes/${processId}/requirements/normalizations/${runId}`,
  );
}

export function retryRequirementNormalization(processId: string, runId: string) {
  return request<NormalizationRetryResponse>(
    `/processes/${processId}/requirements/normalizations/${runId}/retry`,
    {
      method: "POST",
      body: JSON.stringify({}),
    },
  );
}

export function listRequirements(processId: string, normalizationRunId?: string) {
  const query = new URLSearchParams({ limit: "50", offset: "0" });
  if (normalizationRunId) query.set("normalization_run_id", normalizationRunId);
  return request<RequirementList>(`/processes/${processId}/requirements?${query.toString()}`);
}

export function getRequirement(processId: string, requirementId: string) {
  return request<RequirementDetail>(`/processes/${processId}/requirements/${requirementId}`);
}

export function createFinancialEvaluation(processId: string, payload: FinancialEvaluationRequest) {
  return request<FinancialEvaluationQueueResponse>(
    `/processes/${processId}/financial-evaluations`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function listFinancialEvaluations(processId: string) {
  return request<FinancialEvaluationList>(
    `/processes/${processId}/financial-evaluations?limit=20&offset=0`,
  );
}

export function getFinancialEvaluation(processId: string, runId: string) {
  return request<FinancialEvaluationRunDetail>(
    `/processes/${processId}/financial-evaluations/${runId}`,
  );
}

export function retryFinancialEvaluation(processId: string, runId: string) {
  return request<FinancialEvaluationQueueResponse>(
    `/processes/${processId}/financial-evaluations/${runId}/retry`,
    { method: "POST", body: JSON.stringify({ force: true }) },
  );
}

export function listFinancialEvaluationResults(processId: string, runId: string) {
  return request<FinancialEvaluationResultList>(
    `/processes/${processId}/financial-evaluations/${runId}/results?limit=100&offset=0`,
  );
}

export function getFinancialEvaluationResult(processId: string, runId: string, resultId: string) {
  return request<FinancialEvaluationResultDetail>(
    `/processes/${processId}/financial-evaluations/${runId}/results/${resultId}`,
  );
}

export function reviewFinancialEvaluationResult(
  processId: string,
  runId: string,
  resultId: string,
  payload: FinancialEvaluationResultReviewRequest,
) {
  return request<FinancialEvaluationResultDetail>(
    `/processes/${processId}/financial-evaluations/${runId}/results/${resultId}/review`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function getFinancialRule(processId: string, requirementId: string) {
  return request<FinancialRequirementRule>(
    `/processes/${processId}/financial-requirements/${requirementId}/rule`,
  );
}

export function updateFinancialRule(
  processId: string,
  requirementId: string,
  payload: FinancialRequirementRuleUpdate,
) {
  return request<FinancialRequirementRule>(
    `/processes/${processId}/financial-requirements/${requirementId}/rule`,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function getSpecializedEvaluationReadiness(
  processId: string,
  params: {
    normalization_run_id: string;
    company_profile_snapshot_id: string;
    domain: SpecializedEvaluationDomain;
  },
) {
  const query = new URLSearchParams(params);
  return request<SpecializedEvaluationReadiness>(
    `/processes/${processId}/specialized-evaluations/readiness?${query.toString()}`,
  );
}

export function createSpecializedEvaluation(
  processId: string,
  payload: SpecializedEvaluationRequest,
) {
  return request<SpecializedEvaluationQueueResponse>(
    `/processes/${processId}/specialized-evaluations`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function listSpecializedEvaluations(
  processId: string,
  params: { domain?: SpecializedEvaluationDomain | ""; limit?: number; offset?: number } = {},
) {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  if (params.domain) query.set("domain", params.domain);
  return request<SpecializedEvaluationList>(
    `/processes/${processId}/specialized-evaluations?${query.toString()}`,
  );
}

export function getSpecializedEvaluation(processId: string, runId: string) {
  return request<SpecializedEvaluationRunDetail>(
    `/processes/${processId}/specialized-evaluations/${runId}`,
  );
}

export function retrySpecializedEvaluation(processId: string, runId: string) {
  return request<SpecializedEvaluationQueueResponse>(
    `/processes/${processId}/specialized-evaluations/${runId}/retry`,
    { method: "POST", body: JSON.stringify({ force: true }) },
  );
}

export function listSpecializedEvaluationResults(processId: string, runId: string) {
  return request<SpecializedEvaluationResultList>(
    `/processes/${processId}/specialized-evaluations/${runId}/results?limit=100&offset=0`,
  );
}

export function getSpecializedEvaluationResult(processId: string, runId: string, resultId: string) {
  return request<SpecializedEvaluationResultDetail>(
    `/processes/${processId}/specialized-evaluations/${runId}/results/${resultId}`,
  );
}

export function reviewSpecializedEvaluationResult(
  processId: string,
  runId: string,
  resultId: string,
  payload: SpecializedEvaluationResultReviewRequest,
) {
  return request<SpecializedEvaluationResultDetail>(
    `/processes/${processId}/specialized-evaluations/${runId}/results/${resultId}/review`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function getDecisionReadiness(
  processId: string,
  params: {
    normalization_run_id: string;
    company_profile_snapshot_id: string;
    financial_evaluation_run_id: string;
  },
) {
  const query = new URLSearchParams(params);
  return request<DecisionReadiness>(
    `/processes/${processId}/decision-readiness?${query.toString()}`,
  );
}

export function createDecision(processId: string, payload: DecisionRequest) {
  return request<DecisionQueueResponse>(`/processes/${processId}/decisions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listDecisions(processId: string, params: { limit?: number; offset?: number } = {}) {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  return request<DecisionRunList>(`/processes/${processId}/decisions?${query.toString()}`);
}

export function getDecision(processId: string, decisionRunId: string) {
  return request<DecisionRunDetail>(`/processes/${processId}/decisions/${decisionRunId}`);
}

export function retryDecision(processId: string, decisionRunId: string) {
  return request<DecisionQueueResponse>(
    `/processes/${processId}/decisions/${decisionRunId}/retry`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export function reviewDecision(
  processId: string,
  decisionRunId: string,
  payload: DecisionReviewRequest,
) {
  return request<DecisionReviewResponse>(
    `/processes/${processId}/decisions/${decisionRunId}/review`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function updateDecisionAction(
  processId: string,
  decisionRunId: string,
  actionId: string,
  status: DecisionActionStatus,
) {
  return request<DecisionActionItem>(
    `/processes/${processId}/decisions/${decisionRunId}/actions/${actionId}`,
    { method: "PATCH", body: JSON.stringify({ status }) },
  );
}

export function createDecisionReport(processId: string, payload: DecisionReportRequest) {
  return request<DecisionReportQueueResponse>(`/processes/${processId}/decision-reports`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listDecisionReports(
  processId: string,
  params: { decision_run_id?: string; limit?: number; offset?: number } = {},
) {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  if (params.decision_run_id) query.set("decision_run_id", params.decision_run_id);
  return request<DecisionReportPackageList>(
    `/processes/${processId}/decision-reports?${query.toString()}`,
  );
}

export function getDecisionReport(processId: string, packageId: string) {
  return request<DecisionReportPackageDetail>(
    `/processes/${processId}/decision-reports/${packageId}`,
  );
}

export function getDecisionReportPreview(processId: string, packageId: string) {
  return request<DecisionReportPreview>(
    `/processes/${processId}/decision-reports/${packageId}/preview`,
  );
}

export function retryDecisionReport(processId: string, packageId: string) {
  return request<DecisionReportQueueResponse>(
    `/processes/${processId}/decision-reports/${packageId}/retry`,
    { method: "POST", body: JSON.stringify({ force: true }) },
  );
}

export function decisionReportArtifactDownloadUrl(
  processId: string,
  packageId: string,
  artifactId: string,
) {
  return `${apiBaseUrl()}/processes/${processId}/decision-reports/${packageId}/artifacts/${artifactId}/download`;
}

export function decisionReportZipDownloadUrl(processId: string, packageId: string) {
  return `${apiBaseUrl()}/processes/${processId}/decision-reports/${packageId}/download`;
}

export function listCompanies(params: {
  limit?: number;
  offset?: number;
  status?: CompanyProfileStatus | "";
  search?: string;
}) {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  if (params.status) query.set("status", params.status);
  if (params.search?.trim()) query.set("search", params.search.trim());
  return request<CompanyProfileList>(`/companies?${query.toString()}`);
}

export function createCompany(payload: CompanyProfileCreate) {
  return request<CompanyProfileDetail>("/companies", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCompany(companyId: string) {
  return request<CompanyProfileDetail>(`/companies/${companyId}`);
}

export function updateCompany(companyId: string, payload: CompanyProfileUpdate) {
  return request<CompanyProfileDetail>(`/companies/${companyId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function archiveCompany(companyId: string) {
  return request<CompanyProfileDetail>(`/companies/${companyId}/archive`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function createLegalRegistration(companyId: string, payload: unknown) {
  return request<CompanyLegalRegistration>(`/companies/${companyId}/legal-registrations`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createRup(companyId: string, payload: unknown) {
  return request(`/companies/${companyId}/rup`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createUnspsc(companyId: string, payload: CompanyUnspscCodeCreate) {
  return request<CompanyUnspscCode>(`/companies/${companyId}/unspsc`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createFinancialPeriod(companyId: string, payload: CompanyFinancialPeriodCreate) {
  return request<CompanyFinancialPeriod>(`/companies/${companyId}/financial-periods`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createFinancialMetric(
  companyId: string,
  periodId: string,
  payload: CompanyFinancialMetricCreate,
) {
  return request<CompanyFinancialMetric>(
    `/companies/${companyId}/financial-periods/${periodId}/metrics`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function createExperience(companyId: string, payload: CompanyExperienceCreate) {
  return request<CompanyExperienceRecord>(`/companies/${companyId}/experience`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createPerson(companyId: string, payload: CompanyPersonCreate) {
  return request<CompanyPerson>(`/companies/${companyId}/people`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createCertification(companyId: string, payload: CompanyCertificationCreate) {
  return request<CompanyCertification>(`/companies/${companyId}/certifications`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createCapability(companyId: string, payload: CompanyCapabilityCreate) {
  return request<CompanyCapability>(`/companies/${companyId}/capabilities`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCompleteness(companyId: string) {
  return request<CompanyProfileCompleteness>(`/companies/${companyId}/completeness`);
}

export function listEvidenceDocuments(companyId: string) {
  return request<CompanyEvidenceDocumentMetadata[]>(`/companies/${companyId}/evidence-documents`);
}

export function createEvidenceLink(companyId: string, payload: CompanyEvidenceLinkCreate) {
  return request<CompanyEvidenceLink>(`/companies/${companyId}/evidence-links`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function reviewEvidenceLink(
  companyId: string,
  linkId: string,
  payload: CompanyEvidenceLinkReview,
) {
  return request<CompanyEvidenceLink>(`/companies/${companyId}/evidence-links/${linkId}/review`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listSnapshots(companyId: string) {
  return request<CompanyProfileSnapshotSummary[]>(`/companies/${companyId}/snapshots`);
}

export function createSnapshot(companyId: string, payload: CompanyProfileSnapshotCreate) {
  return request<CompanyProfileSnapshotDetail>(`/companies/${companyId}/snapshots`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function publishSnapshot(companyId: string, snapshotId: string) {
  return request<CompanyProfileSnapshotDetail>(
    `/companies/${companyId}/snapshots/${snapshotId}/publish`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export async function uploadDocuments(processId: string, files: File[]) {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  const response = await fetch(`${apiBaseUrl()}/processes/${processId}/documents`, {
    method: "POST",
    body: form,
  });
  if (![201, 207, 400].includes(response.status)) {
    let payload: ApiError | null = null;
    try {
      payload = (await response.json()) as ApiError;
    } catch {
      payload = null;
    }
    throw new ApiClientError(
      payload?.message ?? "No fue posible cargar los documentos.",
      response.status,
      payload,
    );
  }
  return (await response.json()) as DocumentUploadResponse;
}

export async function uploadCompanyEvidence(
  companyId: string,
  files: File[],
  evidenceType: CompanyEvidenceType = "OTHER",
  title?: string,
) {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  const query = new URLSearchParams({ evidence_type: evidenceType });
  if (title?.trim()) query.set("title", title.trim());
  const response = await fetch(
    `${apiBaseUrl()}/companies/${companyId}/evidence-documents?${query.toString()}`,
    { method: "POST", body: form },
  );
  if (![201, 207, 400].includes(response.status)) {
    let payload: ApiError | null = null;
    try {
      payload = (await response.json()) as ApiError;
    } catch {
      payload = null;
    }
    throw new ApiClientError(
      payload?.message ?? "No fue posible cargar las evidencias.",
      response.status,
      payload,
    );
  }
  return (await response.json()) as {
    stored_count: number;
    rejected_count: number;
    results: Array<{ original_filename: string; upload_status: string }>;
  };
}

export function downloadUrl(processId: string, documentId: string) {
  return `${apiBaseUrl()}/processes/${processId}/documents/${documentId}/download`;
}

export function companyEvidenceDownloadUrl(companyId: string, documentId: string) {
  return `${apiBaseUrl()}/companies/${companyId}/evidence-documents/${documentId}/download`;
}
