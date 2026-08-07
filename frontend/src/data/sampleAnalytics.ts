/**
 * Sample benchmark session for the Analytics page when "Sample Data" is on.
 * Mirrors the schema in `backend/benchmarking_suite/smart_ticketing_env.json`.
 */
import type {
  BenchmarkSession,
  BenchmarkSessionSummary,
  BenchmarkOverview,
  InstanceInfo,
} from '@/types/api';

export const sampleInstanceInfo: InstanceInfo = {
  instance_id: 1,
  model_name: 'Logistic Regression',
  qs: 'uncertainty',
  classes: ['Service Desk', 'Hardware Support', 'Software Support', 'Network Operations'],
  f1_scores: [0.58, 0.67, 0.74, 0.79, 0.83],
  num_labeled: [32, 64, 96, 128, 160],
  mean_entropies: [0.82, 0.68, 0.55, 0.47, 0.42],
  accuracies: [0.61, 0.69, 0.76, 0.81, 0.85],
  roc_aucs_ovr_macro: [0.67, 0.75, 0.81, 0.86, 0.89],
  test_accuracy: 0.85,
  labeled_count: 160,
  total_count: 500,
};

export const sampleBenchmarkSession: BenchmarkSession = {
  sim_id: 'sample_st_al_instance_001',
  environment: {
    id: 'ST_AL_ENV',
    class: 'base.Environment',
    attributes: { task: 'active_learning_ticket_triage', domain: 'customer_support' },
  },
  agents: [
    { id: 'ORCH', class: 'base.Agent', model: 'system', affordances: ['create_al_instance', 'request_batch', 'request_prediction', 'model_checkpoint', 'process_start', 'process_end'] },
    { id: 'AL', class: 'base.Agent', model: 'ai', affordances: ['select_batch', 'compute_uncertainty'] },
    { id: 'LAB', class: 'base.Agent', model: 'human', affordances: ['confirm_label', 'override_label', 'select_ticket', 'inspect_ticket', 'filter_pool', 'open_page'] },
    { id: 'MOD', class: 'base.Agent', model: 'ai', affordances: ['train', 'predict', 'evaluate'] },
    { id: 'XAI', class: 'base.Agent', model: 'ai', affordances: ['lime', 'similar_tickets'] },
  ],
  objects: [
    { id: 'Pool', class: 'base.Object', attributes: { kind: 'unlabeled_pool' }, affordances: ['snapshot', 'update'] },
    { id: 'Sel', class: 'base.Object', attributes: { kind: 'selection_batch' }, affordances: ['create'] },
    { id: 'Ticket', class: 'base.Object', attributes: { kind: 'support_ticket' }, affordances: ['label'] },
    { id: 'Lbl', class: 'base.Object', attributes: { kind: 'label' }, affordances: ['confirm', 'override'] },
    { id: 'Mdl', class: 'base.Object', attributes: { kind: 'model' }, affordances: ['checkpoint', 'train', 'predict', 'evaluate'] },
    { id: 'Snap', class: 'base.Object', attributes: { kind: 'model_snapshot' }, affordances: ['create'] },
    { id: 'KB', class: 'base.Object', attributes: { kind: 'knowledge_base_article' }, affordances: ['retrieve'] },
  ],
  script: [
    { t: 0.0, agent: 'ORCH', action: 'process_start', object: 'Pool', effect: { instance_id: 1 } },
    { t: 0.45, agent: 'ORCH', action: 'create_al_instance', object: 'Pool', effect: { instance_id: 1, pool_size: 5000, embedding_model: 'all-MiniLM-L6-v2' }, latency_ms: 450 },
    { t: 1.0, agent: 'ORCH', action: 'request_batch', object: 'Pool', effect: { batch_size: 5 } },
    { t: 1.2, agent: 'AL', action: 'select_batch', object: 'Sel', effect: { batch_id: 'BATCH_001', ids: ['T001', 'T002', 'T003', 'T004', 'T005'], uncertainties: [0.92, 0.89, 0.87, 0.86, 0.85] }, latency_ms: 120 },
    { t: 2.0, agent: 'MOD', action: 'predict', object: 'Ticket', effect: { predictions: ['billing', 'tech', 'tech', 'other', 'billing'] }, latency_ms: 340 },
    { t: 2.5, agent: 'XAI', action: 'lime', object: 'Sel', effect: { batch_id: 'BATCH_001', n_tickets: 5 }, latency_ms: 820 },
    { t: 3.0, agent: 'XAI', action: 'similar_tickets', object: 'Sel', effect: { batch_id: 'BATCH_001' }, latency_ms: 450 },
    { t: 5.0, agent: 'LAB', action: 'confirm_label', object: 'Ticket', effect: { ticket_id: 'T001', label: 'billing' }, duration_s: 35 },
    { t: 8.0, agent: 'LAB', action: 'override_label', object: 'Ticket', effect: { ticket_id: 'T002', original_prediction: 'tech', new_label: 'billing' }, duration_s: 42 },
    { t: 11.0, agent: 'LAB', action: 'confirm_label', object: 'Ticket', effect: { ticket_id: 'T003', label: 'tech' }, duration_s: 28 },
    { t: 14.0, agent: 'LAB', action: 'override_label', object: 'Ticket', effect: { ticket_id: 'T004', original_prediction: 'other', new_label: 'tech' }, duration_s: 48 },
    { t: 17.0, agent: 'LAB', action: 'confirm_label', object: 'Ticket', effect: { ticket_id: 'T005', label: 'billing' }, duration_s: 30 },
    { t: 17.5, agent: 'MOD', action: 'train', object: 'Mdl', effect: { added_samples: 5, total_samples: 167 }, latency_ms: 18600 },
    { t: 36.1, agent: 'MOD', action: 'evaluate', object: 'Mdl', effect: { f1_score: 0.83, num_labeled: 167, mean_entropy: 0.42 }, latency_ms: 750 },
    { t: 36.5, agent: 'ORCH', action: 'model_checkpoint', object: 'Mdl', effect: { checkpoint_id: 'checkpoint-167' }, latency_ms: 420 },
  ],
};

export const sampleSessionSummary: BenchmarkSessionSummary = {
  sim_id: sampleBenchmarkSession.sim_id,
  instance_id: 1,
  started_at: Date.now() / 1000 - 3600,
  ended_at: null,
  num_events: sampleBenchmarkSession.script.length,
  agents_used: ['ORCH', 'AL', 'LAB', 'MOD', 'XAI'],
  is_active: true,
};

export const sampleOverview: BenchmarkOverview = {
  total_sessions: 1,
  active_sessions: 1,
  total_events: sampleBenchmarkSession.script.length,
  events_by_agent: { ORCH: 4, AL: 1, LAB: 5, MOD: 3, XAI: 2 },
  avg_events_per_session: sampleBenchmarkSession.script.length,
};
