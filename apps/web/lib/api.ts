import type {
  ApiError,
  AuthCurrentUser,
  AuthLoginRequest,
  AuthLoginResponse,
  AuthUserCreateRequest,
  AuthUserList,
  OperationalAuditEventList,
  SystemConfigSummary,
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
  ExternalProcurementImportResponse,
  ExternalProcurementProcessLinkList,
  ExternalProcurementSearchRequest,
  ExternalProcurementSearchResponse,
  ExternalProcurementSourceSummary,
  ExternalDocumentDownloadResponse,
  ExternalDocumentExtractResponse,
  ExternalProcessDocumentList,
  ExternalProcessDocumentVersion,
  ExternalProcessSyncQueueResponse,
  ExternalProcessSyncReadiness,
  ExternalProcessSyncRunDetail,
  ExternalProcessSyncRunList,
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
  OpportunityAssessmentDetail,
  OpportunityDeepAnalysisResponse,
  OpportunityDiscoveryRequest,
  OpportunityDiscoveryResponse,
  OpportunityDiscoveryRunDetail,
  OpportunityInboxFilters,
  OpportunityInboxResponse,
  OpportunityReviewRequest,
  OpportunityReviewResponse,
  OpportunityAlertActionRequest,
  OpportunityAlertActionResponse,
  OpportunityAlertList,
  OpportunityAlertUnreadCount,
  OpportunityMonitorCreateRequest,
  OpportunityMonitorDetail,
  OpportunityMonitorList,
  OpportunityMonitorManualRunResponse,
  NotificationDeliveryDetail,
  NotificationDeliveryList,
  NotificationDestinationCreateRequest,
  NotificationDestinationDetail,
  NotificationDestinationList,
  NotificationReadiness,
  NotificationRetentionResponse,
  NotificationStatistics,
  NotificationSubscriptionCreateRequest,
  NotificationSubscriptionDetail,
  NotificationSubscriptionList,
  NotificationTestResponse,
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

async function request<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs = DEFAULT_TIMEOUT_MS,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      signal: controller.signal,
      credentials: "include",
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

export function login(payload: AuthLoginRequest) {
  return request<AuthLoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logout() {
  return request<{ status: string }>("/auth/logout", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function getCurrentUser() {
  return request<AuthCurrentUser>("/auth/me");
}

export function listAdminUsers() {
  return request<AuthUserList>("/admin/users?limit=50&offset=0");
}

export function createAdminUser(payload: AuthUserCreateRequest) {
  return request<AuthUserList>("/admin/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listAuditEvents() {
  return request<OperationalAuditEventList>("/admin/audit-events?limit=50&offset=0");
}

export function getSystemConfig() {
  return request<SystemConfigSummary>("/admin/system-config");
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

export function listExternalProcurementSources() {
  return request<ExternalProcurementSourceSummary[]>("/external-procurement/sources");
}

export function searchExternalProcurement(payload: ExternalProcurementSearchRequest) {
  return request<ExternalProcurementSearchResponse>(
    "/external-procurement/searches",
    { method: "POST", body: JSON.stringify(payload) },
    35_000,
  );
}

export function importExternalProcurementResult(resultId: string, sourceProcessId: string) {
  return request<ExternalProcurementImportResponse>(
    `/external-procurement/results/${resultId}/import`,
    {
      method: "POST",
      body: JSON.stringify({ expected_source_process_id: sourceProcessId }),
    },
  );
}

export function listProcessExternalLinks(processId: string) {
  return request<ExternalProcurementProcessLinkList>(`/processes/${processId}/external-links`);
}

export function getExternalSyncReadiness(processId: string) {
  return request<ExternalProcessSyncReadiness>(`/processes/${processId}/external-sync/readiness`);
}

export function queueExternalSync(processId: string) {
  return request<ExternalProcessSyncQueueResponse>(`/processes/${processId}/external-sync`, {
    method: "POST",
    body: JSON.stringify({ discover_documents: true }),
  });
}

export function listExternalSyncRuns(processId: string) {
  return request<ExternalProcessSyncRunList>(`/processes/${processId}/external-sync-runs`);
}

export function getExternalSyncRun(processId: string, runId: string) {
  return request<ExternalProcessSyncRunDetail>(
    `/processes/${processId}/external-sync-runs/${runId}`,
  );
}

export function listExternalDocuments(processId: string) {
  return request<ExternalProcessDocumentList>(`/processes/${processId}/external-documents`);
}

export function queueExternalDocumentDownload(processId: string, documentId: string) {
  return request<ExternalDocumentDownloadResponse>(
    `/processes/${processId}/external-documents/${documentId}/download`,
    { method: "POST", body: JSON.stringify({ confirm_public_download: true }) },
  );
}

export function extractExternalDocument(processId: string, documentId: string) {
  return request<ExternalDocumentExtractResponse>(
    `/processes/${processId}/external-documents/${documentId}/extract`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export function listExternalDocumentVersions(processId: string, documentId: string) {
  return request<ExternalProcessDocumentVersion[]>(
    `/processes/${processId}/external-documents/${documentId}/versions`,
  );
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

export function createOpportunityDiscovery(payload: OpportunityDiscoveryRequest) {
  return request<OpportunityDiscoveryResponse>("/opportunities/discovery-runs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getOpportunityDiscovery(runId: string) {
  return request<OpportunityDiscoveryRunDetail>(`/opportunities/discovery-runs/${runId}`);
}

export function listOpportunities(filters: OpportunityInboxFilters = {}) {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") query.set(key, String(value));
  });
  return request<OpportunityInboxResponse>(`/opportunities?${query.toString()}`);
}

export function getOpportunity(opportunityId: string) {
  return request<OpportunityAssessmentDetail>(`/opportunities/${opportunityId}`);
}

export function reviewOpportunity(opportunityId: string, payload: OpportunityReviewRequest) {
  return request<OpportunityReviewResponse>(`/opportunities/${opportunityId}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function importOpportunity(opportunityId: string) {
  return request<ExternalProcurementImportResponse>(`/opportunities/${opportunityId}/import`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function requestOpportunityDeepAnalysis(opportunityId: string) {
  return request<OpportunityDeepAnalysisResponse>(
    `/opportunities/${opportunityId}/request-deep-analysis`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export function listMonitors() {
  return request<OpportunityMonitorList>("/opportunity-monitors");
}

export function createMonitor(payload: OpportunityMonitorCreateRequest) {
  return request<OpportunityMonitorDetail>("/opportunity-monitors", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function pauseMonitor(id: string) {
  return request<OpportunityMonitorDetail>(`/opportunity-monitors/${id}/pause`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function resumeMonitor(id: string) {
  return request<OpportunityMonitorDetail>(`/opportunity-monitors/${id}/resume`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function runMonitor(id: string) {
  return request<OpportunityMonitorManualRunResponse>(`/opportunity-monitors/${id}/run`, {
    method: "POST",
    body: JSON.stringify({ force: false }),
  });
}

export function listAlerts(filters: Record<string, string> = {}) {
  return request<OpportunityAlertList>(
    `/opportunity-alerts?${new URLSearchParams(filters).toString()}`,
  );
}

export function getUnreadAlertCount() {
  return request<OpportunityAlertUnreadCount>("/opportunity-alerts/unread-count");
}

export function actOnAlert(id: string, payload: OpportunityAlertActionRequest) {
  return request<OpportunityAlertActionResponse>(`/opportunity-alerts/${id}/actions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function notificationReadiness() {
  return request<NotificationReadiness>("/notification-delivery/readiness");
}
export function notificationStatistics() {
  return request<NotificationStatistics>("/notification-delivery/statistics");
}
export function listNotificationDestinations() {
  return request<NotificationDestinationList>("/notification-destinations");
}
export function createNotificationDestination(payload: NotificationDestinationCreateRequest) {
  return request<NotificationDestinationDetail>("/notification-destinations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
export function setNotificationDestination(id: string, action: "pause" | "resume") {
  return request<NotificationDestinationDetail>(`/notification-destinations/${id}/${action}`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}
export function testNotificationDestination(id: string) {
  return request<NotificationTestResponse>(`/notification-destinations/${id}/test`, {
    method: "POST",
    body: JSON.stringify({ message: "Prueba controlada desde preferencias" }),
  });
}
export function listNotificationSubscriptions() {
  return request<NotificationSubscriptionList>("/notification-subscriptions");
}
export function createNotificationSubscription(payload: NotificationSubscriptionCreateRequest) {
  return request<NotificationSubscriptionDetail>("/notification-subscriptions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
export function listNotificationDeliveries(status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<NotificationDeliveryList>(`/notification-deliveries${query}`);
}
export function getNotificationDelivery(id: string) {
  return request<NotificationDeliveryDetail>(`/notification-deliveries/${id}`);
}
export function operateNotificationDelivery(id: string, action: "retry" | "cancel") {
  return request<{ delivery_id: string; status: string }>(
    `/notification-deliveries/${id}/${action}`,
    { method: "POST", body: JSON.stringify({}) },
  );
}
export function runNotificationRetention(dryRun = true) {
  return request<NotificationRetentionResponse>("/notification-retention/run", {
    method: "POST",
    body: JSON.stringify({ dry_run: dryRun, batch_size: 500 }),
  });
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
    credentials: "include",
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
    { method: "POST", body: form, credentials: "include" },
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
