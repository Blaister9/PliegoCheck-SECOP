import type {
  ApiError,
  DocumentUploadResponse,
  ProcessCreate,
  ProcessDetail,
  ProcessList,
  ProcessStatus,
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

export function downloadUrl(processId: string, documentId: string) {
  return `${apiBaseUrl()}/processes/${processId}/documents/${documentId}/download`;
}
