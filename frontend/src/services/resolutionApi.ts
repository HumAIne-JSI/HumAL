import {
  ApiError,
  type ResolutionRetrieveRequest,
  type ResolutionRetrieveResponse,
  type ResolutionGenerateRequest,
  type ResolutionGenerateResponse,
  type ResolutionJudgeRequest,
  type ResolutionJudgeResponse,
  type ResolutionJudgeAndRetrieveResponse,
  type ResolutionFeedbackRequest,
  type ResolutionFeedbackResponse,
  type ResolutionFeedbackStatsResponse,
  type ResolutionSaveTicketRequest,
  type ResolutionSaveTicketResponse,
  type ResolutionConfigResponse,
} from '@/types/api';

// ---------------------------------------------------------------------------
// The Resolution Task API (`al-fr-api`) is a SEPARATE server from the main
// HumAL backend. The Resolution tab talks to it directly from the browser via
// `VITE_RESOLUTION_API_BASE_URL`. It has no authentication, so — unlike
// `services/api.ts` — we deliberately do NOT attach the JWT here.
// ---------------------------------------------------------------------------
const RAW_RESOLUTION_BASE_URL =
  import.meta.env.VITE_RESOLUTION_API_BASE_URL || 'https://al-fr-api.humaine-horizon.eu';
const RESOLUTION_BASE_URL = RAW_RESOLUTION_BASE_URL.replace(/\/+$/, '');

const RESOLUTION_ENDPOINTS = {
  HEALTH: '/health',
  CONFIG: '/config',
  RETRIEVE: '/retrieve',
  GENERATE: '/generate',
  JUDGE: '/judge',
  JUDGE_AND_RETRIEVE: '/judge_and_retrieve',
  FEEDBACK: '/feedback',
  FEEDBACK_STATS: '/feedback_stats',
  SAVE_TICKET: '/save_ticket',
} as const;

/** Low-level fetch wrapper for the resolution API. Throws {@link ApiError}. */
async function resolutionApiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${RESOLUTION_BASE_URL}${endpoint}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  } catch (err) {
    throw new ApiError(
      0,
      err instanceof Error ? err.message : 'Network error contacting the resolution service',
    );
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (body && typeof body === 'object' && 'detail' in body) {
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // Non-JSON error body — keep the default detail.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

function buildQuery(params: Record<string, string | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.append(key, value);
  }
  const s = search.toString();
  return s ? `?${s}` : '';
}

/** Typed client for the external Resolution Task API (`al-fr-api`). */
export const resolutionApiService = {
  /** Liveness check. */
  health: () => resolutionApiCall<{ status: string }>(RESOLUTION_ENDPOINTS.HEALTH),

  /** Current knowledge-base / feedback-db configuration. */
  getConfig: () => resolutionApiCall<ResolutionConfigResponse>(RESOLUTION_ENDPOINTS.CONFIG),

  /** Retrieve similar historical replies for a ticket. */
  retrieve: (data: ResolutionRetrieveRequest) =>
    resolutionApiCall<ResolutionRetrieveResponse>(RESOLUTION_ENDPOINTS.RETRIEVE, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** Generate a proposed reply (RAG). Returns classification + team + similar replies. */
  generate: (data: ResolutionGenerateRequest) =>
    resolutionApiCall<ResolutionGenerateResponse>(RESOLUTION_ENDPOINTS.GENERATE, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** Score a set of similar replies (LLM-as-judge quality gate). */
  judge: (data: ResolutionJudgeRequest) =>
    resolutionApiCall<ResolutionJudgeResponse>(RESOLUTION_ENDPOINTS.JUDGE, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** Combined retrieve + judge in a single call. */
  judgeAndRetrieve: (data: ResolutionJudgeRequest) =>
    resolutionApiCall<ResolutionJudgeAndRetrieveResponse>(RESOLUTION_ENDPOINTS.JUDGE_AND_RETRIEVE, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** Record human feedback (👍/👎) on a retrieved reply. */
  feedback: (data: ResolutionFeedbackRequest) =>
    resolutionApiCall<ResolutionFeedbackResponse>(RESOLUTION_ENDPOINTS.FEEDBACK, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** Aggregated feedback counts for a retrieved reply. */
  feedbackStats: (retrievedId: string, scopeKey?: string) =>
    resolutionApiCall<ResolutionFeedbackStatsResponse>(
      `${RESOLUTION_ENDPOINTS.FEEDBACK_STATS}${buildQuery({ retrieved_id: retrievedId, scope_key: scopeKey })}`,
    ),

  /** Persist an approved resolution into the knowledge base. */
  saveTicket: (data: ResolutionSaveTicketRequest) =>
    resolutionApiCall<ResolutionSaveTicketResponse>(RESOLUTION_ENDPOINTS.SAVE_TICKET, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

export type ResolutionApiService = typeof resolutionApiService;
