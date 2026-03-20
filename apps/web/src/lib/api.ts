import axios, { type AxiosError } from "axios";
import Cookies from "js-cookie";

// ── Types partagés ────────────────────────────────────────────
export interface ProjectTemplate {
  id: string;
  name: string;
  icon: string;
  description: string;
  market_type: "travaux" | "services" | "fournitures";
  doc_types_expected: string[];
}

// Constante centralisée — évite toute dépendance à process.env non défini
const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  timeout: 30_000, // 30s par défaut
  headers: { "Content-Type": "application/json" },
});

// Inject access token
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401 with queued retry for concurrent requests
let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((prom) => {
    if (token) {
      prom.resolve(token);
    } else {
      prom.reject(error);
    }
  });
  failedQueue = [];
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as typeof error.config & { _retry?: boolean };
    if (error.response?.status === 401 && !original?._retry) {
      if (isRefreshing) {
        // Queue this request — it will be retried after refresh completes
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          original!.headers!["Authorization"] = `Bearer ${token}`;
          // Strip AbortSignal — it may already be aborted (React Query cancels the original)
          return api({ ...original!, signal: undefined });
        });
      }

      isRefreshing = true;
      original._retry = true;
      try {
        const { data } = await axios.post(
          `${BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        Cookies.set("access_token", data.access_token, {
          expires: 1 / 24, // 60 min
          sameSite: "lax",
          secure: process.env.NODE_ENV === "production",
        });
        original!.headers!["Authorization"] = `Bearer ${data.access_token}`;
        // Strip AbortSignal — it may already be aborted (React Query cancels the original)
        const retryConfig = { ...original, signal: undefined };
        processQueue(null, data.access_token);
        return api(retryConfig);
      } catch (refreshError) {
        processQueue(refreshError, null);
        Cookies.remove("access_token");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ── Auth ────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; password: string; full_name: string; org_name: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post<{ access_token: string; expires_in: number }>("/auth/login", data),
  logout: () => api.post("/auth/logout"),
  me: () => api.get("/auth/me"),
};

// ── Projects ─────────────────────────────────────────────────
export const projectsApi = {
  list: (params?: { skip?: number; limit?: number; status?: string; q?: string }) =>
    api.get("/projects", { params }),
  get: (id: string) => api.get(`/projects/${id}`),
  create: (data: object) => api.post("/projects", data),
  update: (id: string, data: object) => api.patch(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  pipeline: () => api.get("/projects/pipeline/stats"),
  // Win/Loss tracking (R4)
  updateResult: (
    id: string,
    data: {
      result: "won" | "lost" | "no_bid";
      result_amount_eur?: number | null;
      result_date?: string | null;
      result_notes?: string | null;
    }
  ) => api.patch(`/projects/${id}/result`, data),
  // Templates (R5)
  getTemplates: () => api.get<ProjectTemplate[]>("/projects/templates"),
};

// ── Documents ─────────────────────────────────────────────────
export const documentsApi = {
  list: (projectId: string) => api.get(`/projects/${projectId}/documents`),
  upload: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post(`/projects/${projectId}/documents/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getSignedUrl: (projectId: string, docId: string) =>
    api.get(`/projects/${projectId}/documents/${docId}/signed-url`),
  delete: (projectId: string, docId: string) =>
    api.delete(`/projects/${projectId}/documents/${docId}`),
};

// ── Analysis ──────────────────────────────────────────────────
export const analysisApi = {
  trigger: (projectId: string) => api.post(`/projects/${projectId}/analyze`, {}, { timeout: 120_000 }),
  status: (projectId: string) => api.get(`/projects/${projectId}/analyze/status`),
  summary: (projectId: string) => api.get(`/projects/${projectId}/summary`),
  checklist: (projectId: string, params?: { criticality?: string; status?: string; category?: string }) =>
    api.get(`/projects/${projectId}/checklist`, { params }),
  updateChecklistItem: (projectId: string, itemId: string, data: object) =>
    api.patch(`/projects/${projectId}/checklist/${itemId}`, data),
  criteria: (projectId: string) => api.get(`/projects/${projectId}/criteria`),
  // Go/No-Go
  gonogo: (projectId: string) => api.get(`/projects/${projectId}/gonogo`),
  // Chat DCE
  chat: (projectId: string, question: string) =>
    api.post(`/projects/${projectId}/chat`, { question }, { timeout: 120_000 }),
  // Writing assistant
  generateText: (projectId: string, itemId: string) =>
    api.post(`/projects/${projectId}/checklist/${itemId}/generate`, {}, { timeout: 120_000 }),
  // Timeline
  timeline: (projectId: string) => api.get(`/projects/${projectId}/timeline`),
  updateTimelineTask: (projectId: string, taskIndex: number, done: boolean) =>
    api.patch(`/projects/${projectId}/timeline/tasks/${taskIndex}`, null, { params: { done } }),
  // Analyse des risques CCAP
  ccapRisks: (projectId: string) => api.get(`/projects/${projectId}/ccap-risks`),
  // Deadlines / Alertes dates clés
  deadlines: (projectId: string) => api.get(`/projects/${projectId}/deadlines`),
  // Sprint V+W — Nouvelles analyses (LLM-backed: 120s timeout)
  rcAnalysis: (projectId: string) => api.get(`/projects/${projectId}/rc-analysis`, { timeout: 120_000 }),
  aeAnalysis: (projectId: string) => api.get(`/projects/${projectId}/ae-analysis`, { timeout: 120_000 }),
  cctpAnalysis: (projectId: string) => api.get(`/projects/${projectId}/cctp-analysis`, { timeout: 120_000 }),
  dcCheck: (projectId: string) => api.get(`/projects/${projectId}/dc-check`, { timeout: 120_000 }),
  conflicts: (projectId: string) => api.get(`/projects/${projectId}/conflicts`, { timeout: 120_000 }),
  questions: (projectId: string) => api.get(`/projects/${projectId}/questions`, { timeout: 120_000 }),
  scoringSimulation: (projectId: string) => api.get(`/projects/${projectId}/scoring-simulation`, { timeout: 120_000 }),
  dpgfPricing: (projectId: string) => api.get(`/projects/${projectId}/dpgf-pricing`, { timeout: 120_000 }),
  cashflowSimulation: (projectId: string) => api.get(`/projects/${projectId}/cashflow-simulation`, { timeout: 120_000 }),
  subcontracting: (projectId: string) => api.get(`/projects/${projectId}/subcontracting`, { timeout: 120_000 }),
};

// ── Company profile ────────────────────────────────────────────
export const companyApi = {
  getProfile: () => api.get("/company/profile"),
  updateProfile: (data: object) => api.put("/company/profile", data),
};

// ── Export ────────────────────────────────────────────────────
export const exportApi = {
  startPdf: (projectId: string) => api.post(`/projects/${projectId}/export/pdf`),
  startWord: (projectId: string) => api.post(`/projects/${projectId}/export/word`),
  startDpgfExcel: (projectId: string) =>
    api.post(`/projects/${projectId}/export/dpgf-excel`, {}, { responseType: "blob" }),
  startMemo: (projectId: string) =>
    api.post(`/projects/${projectId}/export/memo`, {}, { responseType: "blob" }),
  startPack: (projectId: string) =>
    api.post(`/projects/${projectId}/export/pack`),
  getStatus: (projectId: string, jobId: string) =>
    api.get(`/projects/${projectId}/export/${jobId}`),
};

// ── Fetch-based client (for pages that need raw Response) ────
const ORIGIN =
  process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") ||
  "http://localhost:8000";

/** Attempt a silent token refresh; returns new token or throws on failure. */
async function silentRefresh(): Promise<string> {
  const res = await fetch(`${ORIGIN}/api/v1/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Refresh failed");
  const data = await res.json();
  Cookies.set("access_token", data.access_token, {
    expires: 1 / 24, // 60 min
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
  });
  return data.access_token as string;
}

/** Wrapper: performs fetch, retries once after a silent token refresh on 401. */
async function fetchWithRefresh(
  path: string,
  init: RequestInit
): Promise<Response> {
  const token = Cookies.get("access_token") || "";
  const headers = { ...(init.headers as Record<string, string>), Authorization: `Bearer ${token}` };
  const res = await fetch(`${ORIGIN}${path}`, { ...init, headers, credentials: "include" });

  if (res.status === 401) {
    try {
      const newToken = await silentRefresh();
      const retryHeaders = { ...(init.headers as Record<string, string>), Authorization: `Bearer ${newToken}` };
      return fetch(`${ORIGIN}${path}`, { ...init, headers: retryHeaders, credentials: "include" });
    } catch {
      // Refresh failed → redirect to login
      if (typeof window !== "undefined") window.location.href = "/login";
      return res; // return original 401 response
    }
  }
  return res;
}

const JSON_HEADERS = { "Content-Type": "application/json" };

export const apiClient = {
  get: (path: string) =>
    fetchWithRefresh(path, { method: "GET", headers: JSON_HEADERS }),

  post: (path: string, body?: unknown) =>
    fetchWithRefresh(path, {
      method: "POST",
      headers: JSON_HEADERS,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  patch: (path: string, body?: unknown) =>
    fetchWithRefresh(path, {
      method: "PATCH",
      headers: JSON_HEADERS,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  delete: (path: string) =>
    fetchWithRefresh(path, { method: "DELETE", headers: JSON_HEADERS }),
};

// ── Library ───────────────────────────────────────────────────
export const libraryApi = {
  list: (params?: { tag?: string; category?: string; search?: string }) =>
    api.get("/library/snippets", { params }).then(r => r.data),
  create: (data: object) => api.post("/library/snippets", data).then(r => r.data),
  update: (id: string, data: object) => api.put(`/library/snippets/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/library/snippets/${id}`),
  use: (id: string) => api.post(`/library/snippets/${id}/use`).then(r => r.data),
};

// ── Annotations ───────────────────────────────────────────────
export const annotationsApi = {
  list: (projectId: string, itemId: string) =>
    api.get(`/projects/${projectId}/checklist/${itemId}/annotations`).then(r => r.data),
  create: (projectId: string, itemId: string, data: object) =>
    api.post(`/projects/${projectId}/checklist/${itemId}/annotations`, data).then(r => r.data),
  delete: (projectId: string, itemId: string, annotationId: string) =>
    api.delete(`/projects/${projectId}/checklist/${itemId}/annotations/${annotationId}`),
};

// ── Veille AO ─────────────────────────────────────────────────
export const veilleApi = {
  getConfig: () => api.get("/veille/config"),
  updateConfig: (data: {
    keywords?: string[];
    regions?: string[];
    cpv_codes?: string[];
    min_budget_eur?: number | null;
    max_budget_eur?: number | null;
    is_active?: boolean;
    ted_enabled?: boolean;
  }) => api.put("/veille/config", data),
  getResults: (params?: { is_read?: boolean; limit?: number; skip?: number }) =>
    api.get("/veille/results", { params }),
  markRead: (resultId: string) => api.post(`/veille/results/${resultId}/read`),
  sync: () => api.post("/veille/sync"),
};

// ── Knowledge (Glossaire BTP) ──────────────────────────────────
export const knowledgeApi = {
  listGlossary: () => api.get("/knowledge/glossary"),
  getTerm: (term: string) => api.get(`/knowledge/glossary/${encodeURIComponent(term)}`),
  extractTerms: (text: string) => api.post("/knowledge/glossary/extract", { text }),
  getThresholds: () => api.get("/knowledge/thresholds"),
  checkThreshold: (amount: number) => api.get(`/knowledge/thresholds/check/${amount}`),
  getCertifications: () => api.get("/knowledge/certifications"),
  getCpvCodes: () => api.get("/knowledge/cpv"),
};

// ── Analytics ─────────────────────────────────────────────────
export const analyticsApi = {
  getStats: () => api.get("/analytics/stats"),
  getActivity: (days?: number) =>
    api.get("/analytics/activity", days ? { params: { days } } : undefined),
};

// ── e-Attestations ────────────────────────────────────────────
export const attestationsApi = {
  checkCompany: (siret: string) =>
    api.get(`/attestations/company?siret=${encodeURIComponent(siret)}`).then(r => r.data),

  checkMyCompany: (siret: string) =>
    api.get(`/attestations/my-company?siret=${encodeURIComponent(siret)}`).then(r => r.data),
};

// ── Billing ───────────────────────────────────────────────────
export const billingApi = {
  getUsage: () => api.get("/billing/usage"),
  getSubscription: () => api.get("/billing/subscription"),
  createCheckout: (plan: "starter" | "pro" | "europe" | "business", successUrl: string, cancelUrl: string) =>
    api.post("/billing/checkout", {
      plan,
      success_url: successUrl,
      cancel_url: cancelUrl,
    }),
  createPortal: (returnUrl: string) =>
    api.post("/billing/portal", { return_url: returnUrl }),
};
