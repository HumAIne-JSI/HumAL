import { useMutation } from '@tanstack/vue-query';
import { resolutionApiService } from '@/services/resolutionApi';
import { useMockModeStore } from '@/stores/useMockModeStore';
import { mockAssistedResolution, mockFeedbackStats } from '@/data/sampleResolution';
import type {
  ResolutionSimilarReply,
  ResolutionJudgeScore,
  ResolutionFeedbackRequest,
  ResolutionFeedbackResponse,
  ResolutionSaveTicketRequest,
  ResolutionSaveTicketResponse,
} from '@/types/api';
import type { QueryMeta } from '@/lib/queryClient';

/** Default number of neighbours to retrieve/generate against. */
export const DEFAULT_RESOLUTION_TOP_K = 5;

// Query keys for the resolution domain.
export const resolutionKeys = {
  all: ['resolution'] as const,
};

export interface UseResolutionOptions {
  meta?: QueryMeta;
}

/** Input for the one-click assisted-resolution flow. */
export interface AssistedResolutionInput {
  title: string;
  description: string;
  top_k?: number;
  /** Optional AL-inferred class hint (feeds the judge/retrieval, not generation). */
  predicted_class?: string;
  /** Optional AL-inferred team hint (feeds the judge/retrieval, not generation). */
  predicted_team?: string;
}

/** Combined view model assembled from /generate + /judge_and_retrieve. */
export interface AssistedResolution {
  classification: string;
  predicted_class: string;
  predicted_team: string;
  team_confidence: number;
  response: string;
  similar_replies: ResolutionSimilarReply[];
  retrieval_k: number;
  judge_scores: ResolutionJudgeScore[];
  votes_applied: number;
}

/**
 * Orchestrate the one-click assisted resolution:
 *  1. POST /generate — the proposed reply, classification, team and neighbours.
 *  2. POST /judge_and_retrieve — feedback-weighted re-ranking + quality scores
 *     (best-effort: the generated result is kept if judging fails).
 */
async function runAssistedResolution(input: AssistedResolutionInput): Promise<AssistedResolution> {
  const top_k = input.top_k ?? DEFAULT_RESOLUTION_TOP_K;

  const generated = await resolutionApiService.generate({
    title: input.title,
    description: input.description,
    top_k,
  });

  const predicted_class = input.predicted_class ?? generated.predicted_class ?? generated.classification;
  const predicted_team = input.predicted_team ?? generated.predicted_team;

  let judge_scores: ResolutionJudgeScore[] = [];
  let votes_applied = 0;
  let similar_replies = generated.similar_replies;

  try {
    const judged = await resolutionApiService.judgeAndRetrieve({
      title: input.title,
      description: input.description,
      similar_replies: generated.similar_replies,
      predicted_class,
      predicted_team,
      top_k,
    });
    judge_scores = judged.scores ?? [];
    votes_applied = judged.votes_applied ?? 0;
    if (judged.retrieved?.similar_replies?.length) {
      similar_replies = judged.retrieved.similar_replies;
    }
  } catch {
    // Judging is a best-effort quality gate — fall back to the generated result.
  }

  return {
    classification: generated.classification,
    predicted_class,
    predicted_team,
    team_confidence: generated.team_confidence,
    response: generated.response,
    similar_replies,
    retrieval_k: generated.retrieval_k,
    judge_scores,
    votes_applied,
  };
}

/**
 * One-click assisted resolution: generate a proposed reply and judge/re-rank the
 * similar replies behind a single mutation.
 *
 * @example
 * ```ts
 * const { mutateAsync: resolve, isPending } = useAssistedResolution();
 * const result = await resolve({ title, description, predicted_team });
 * ```
 */
export function useAssistedResolution(
  options?: UseResolutionOptions & {
    onSuccess?: (data: AssistedResolution) => void;
    onError?: (error: Error) => void;
  },
) {
  const mock = useMockModeStore();
  return useMutation({
    mutationFn: (input: AssistedResolutionInput) =>
      mock.mockEnabled ? Promise.resolve(mockAssistedResolution(input)) : runAssistedResolution(input),
    onSuccess: options?.onSuccess,
    onError: options?.onError,
    meta: options?.meta,
  });
}

/**
 * Record human feedback (👍 label=1 / 👎 label=0) on a retrieved reply.
 */
export function useResolutionFeedback(
  options?: UseResolutionOptions & {
    onSuccess?: (data: ResolutionFeedbackResponse, variables: ResolutionFeedbackRequest) => void;
  },
) {
  const mock = useMockModeStore();
  return useMutation({
    mutationFn: (data: ResolutionFeedbackRequest) =>
      mock.mockEnabled ? Promise.resolve({ ok: true }) : resolutionApiService.feedback(data),
    onSuccess: options?.onSuccess,
    meta: options?.meta,
  });
}

/** Fetch aggregated feedback stats for a retrieved reply (imperative, silent). */
export function useFeedbackStats(options?: UseResolutionOptions) {
  const mock = useMockModeStore();
  return useMutation({
    mutationFn: ({ retrievedId, scopeKey }: { retrievedId: string; scopeKey?: string }) =>
      mock.mockEnabled
        ? Promise.resolve(mockFeedbackStats(retrievedId))
        : resolutionApiService.feedbackStats(retrievedId, scopeKey),
    meta: { silent: true, ...options?.meta },
  });
}

/** Persist an approved resolution into the knowledge base (POST /save_ticket). */
export function useSaveResolvedTicket(
  options?: UseResolutionOptions & {
    onSuccess?: (data: ResolutionSaveTicketResponse) => void;
  },
) {
  const mock = useMockModeStore();
  return useMutation({
    mutationFn: (data: ResolutionSaveTicketRequest) =>
      mock.mockEnabled
        ? Promise.resolve({ ok: true } as ResolutionSaveTicketResponse)
        : resolutionApiService.saveTicket(data),
    onSuccess: options?.onSuccess,
    meta: options?.meta,
  });
}

/**
 * Convenience hook bundling the whole resolution workflow.
 *
 * @example
 * ```ts
 * const { resolve, sendFeedback, saveTicket, fetchStats, result } = useResolution();
 * ```
 */
export function useResolution(options?: UseResolutionOptions) {
  const assisted = useAssistedResolution({ meta: options?.meta });
  const feedback = useResolutionFeedback({ meta: options?.meta });
  const stats = useFeedbackStats({ meta: options?.meta });
  const save = useSaveResolvedTicket({ meta: options?.meta });

  return {
    resolve: assisted.mutate,
    resolveAsync: assisted.mutateAsync,
    sendFeedback: feedback.mutate,
    sendFeedbackAsync: feedback.mutateAsync,
    fetchStats: stats.mutateAsync,
    saveTicket: save.mutate,
    saveTicketAsync: save.mutateAsync,
    result: assisted.data,
    isResolving: assisted.isPending,
    isSendingFeedback: feedback.isPending,
    isSaving: save.isPending,
    resolveError: assisted.error,
  };
}
