import type {
  ResolutionFeedbackStatsResponse,
  ResolutionJudgeScore,
  ResolutionSimilarReply,
} from '@/types/api';
import type { AssistedResolution, AssistedResolutionInput } from '@/composables/api/useResolution';

// Local-only deterministic data used when the application is in mock mode.
const sampleReplies: ResolutionSimilarReply[] = [
  {
    retrieved_id: 'mock-reply-001',
    first_reply:
      'Please restart the affected service and confirm whether the issue persists. If it does, attach the latest service logs so the support team can investigate further.',
    Title_anon: 'Service unavailable after deployment',
    Description_anon: 'The production service stopped responding immediately after a deployment.',
    enhanced_score: 0.94,
    feedback_lift: 0.08,
    confidence_gated: true,
    al_weight: 0.25,
  },
  {
    retrieved_id: 'mock-reply-002',
    first_reply:
      'Check the account permissions and retry the request. If access is still denied, provide the account name and requested resource to the service desk.',
    Title_anon: 'User cannot access an internal application',
    Description_anon: 'A user receives an access denied message when opening an internal application.',
    enhanced_score: 0.86,
    feedback_lift: 0.04,
    confidence_gated: true,
    al_weight: 0.2,
  },
  {
    retrieved_id: 'mock-reply-003',
    first_reply:
      'Clear the local application cache and sign in again. If the problem continues, try the same action from a different browser or device.',
    Title_anon: 'Application page does not load correctly',
    Description_anon: 'The application page is incomplete after the user signs in.',
    enhanced_score: 0.78,
    feedback_lift: 0.02,
    confidence_gated: false,
    al_weight: 0.15,
  },
];

const sampleJudgeScores: ResolutionJudgeScore[] = [
  { retrieved_id: 'mock-reply-001', score: 0.94, rationale: 'Strongly matches the reported service issue.' },
  { retrieved_id: 'mock-reply-002', score: 0.86, rationale: 'Related support workflow with a weaker match.' },
  { retrieved_id: 'mock-reply-003', score: 0.78, rationale: 'General troubleshooting guidance.' },
];

export function mockAssistedResolution(input: AssistedResolutionInput): AssistedResolution {
  const retrievalK = Math.max(1, Math.min(input.top_k ?? 5, sampleReplies.length));
  const predictedClass = input.predicted_class ?? 'access_request';
  const predictedTeam = input.predicted_team ?? 'Service Desk';
  const subject = input.title.trim() || 'the reported issue';

  return {
    classification: predictedClass,
    predicted_class: predictedClass,
    predicted_team: predictedTeam,
    team_confidence: 0.87,
    response: `Hello, we reviewed "${subject}". Please follow the troubleshooting steps above and reply with the result if the issue remains.`,
    similar_replies: sampleReplies.slice(0, retrievalK),
    retrieval_k: retrievalK,
    judge_scores: sampleJudgeScores.slice(0, retrievalK),
    votes_applied: 0,
  };
}

export function mockFeedbackStats(retrievedId: string): ResolutionFeedbackStatsResponse {
  return {
    db: 'mock-feedback',
    retrieved_id: retrievedId,
    raw_count: 4,
    agg: [['mock', 3, 1]],
  };
}
