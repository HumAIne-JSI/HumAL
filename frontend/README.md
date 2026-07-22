# HumAL - Presentation Guide

## What is HumAL?

**HumAL** (HumAIne Active Learning) is a full-stack platform that enables **human-in-the-loop machine learning** for IT service management. It combines traditional ML, Large Language Models (LLMs), and explainable AI to automate ticket classification and resolution generation.

---

## The Problem We Solve

| Challenge | Impact |
|-----------|--------|
| IT support teams are overwhelmed with ticket volume | Slow response times, frustrated users |
| Manual ticket routing causes delays | Tickets go to wrong teams, bouncing around |
| Training ML models requires massive labeled datasets | Expensive, time-consuming data labeling |
| AI predictions feel like "black boxes" | Low trust, reluctance to adopt |

**HumAL addresses all of these with a human-centered AI approach.**

---

## Key Features to Highlight

### 1. Active Learning Pipeline
- **Smart sample selection** - The system picks the most informative tickets for humans to label
- **Iterative training** - Model improves after every labeling batch
- **Reduced labeling effort** - Achieve high accuracy with fewer labeled examples
- **Multiple strategies**: Uncertainty, Margin, Entropy, Random sampling

### 2. Automated Ticket Classification
- Route tickets to the correct support team automatically
- Choose from multiple ML models:
  - Logistic Regression, Random Forest, SVM, Gradient Boosting, Neural Network
- Real-time predictions with confidence scores

### 3. RAG-Powered Resolution Generation
- Uses **Retrieval-Augmented Generation** (RAG) with OpenAI GPT
- Finds similar past tickets from a knowledge base
- Generates contextual first-reply responses
- Speeds up agent response time significantly

### 4. Explainable AI (XAI)
- **LIME explanations** show which words influenced the prediction
- **Similar ticket retrieval** provides context for decisions
- Builds trust and allows humans to verify AI recommendations

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│              Vue.js / TypeScript / Tailwind                  │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────┐
│                        Backend                               │
│                   FastAPI (Python)                           │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ Active       │ Inference    │ Resolution   │ XAI            │
│ Learning     │ Service      │ (RAG)        │ (LIME)         │
│ Service      │              │              │                │
├──────────────┴──────────────┴──────────────┴────────────────┤
│          scikit-learn │ PyTorch │ FAISS │ OpenAI           │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Vue 3, TypeScript, Vite, Tailwind CSS |
| **Backend** | FastAPI, Python 3.8+ |
| **ML/NLP** | scikit-learn, PyTorch, Sentence Transformers |
| **Vector Search** | FAISS (for similarity search) |
| **LLM** | OpenAI GPT (for resolution generation) |
| **XAI** | LIME (Local Interpretable Model-agnostic Explanations) |

---

## Demo Walkthrough

### Page 1: Training
- Create a new Active Learning instance
- Select model type and query strategy
- Watch accuracy metrics improve over iterations

### Page 2: Dispatch Labeling
- Human-in-the-loop labeling interface
- View model predictions + LIME explanations
- Assign correct team labels
- Model automatically retrains after each batch

### Page 3: Inference
- Input new ticket details
- Get instant team prediction with confidence
- See LIME explanation and similar tickets

### Page 4: Ticket Evolution
- Enter ticket information
- Generate AI-powered resolution using RAG
- Review similar past tickets and their solutions

---

## Key Metrics & Value Proposition

- **Reduced labeling effort**: Active learning typically needs 30-50% fewer labels than random sampling
- **Faster ticket routing**: Automated classification in milliseconds
- **Improved response time**: AI-generated resolutions as first drafts
- **Transparency**: Every prediction comes with an explanation

---

## Future Directions

- Multi-language support
- Integration with ITSM tools (ServiceNow, Jira Service Management)
- Continuous learning from production feedback
- Custom model fine-tuning

---

## Questions to Prepare For

1. **How does active learning reduce labeling costs?**
   - By strategically selecting uncertain samples, we maximize information gain per label

2. **Why use LIME for explainability?**
   - Model-agnostic, works with any classifier, provides intuitive word-level explanations

3. **How does the RAG system work?**
   - Embeds tickets with Sentence Transformers, uses FAISS for similarity search, feeds context to GPT

4. **What about data privacy with OpenAI?**
   - Only ticket text is sent; can be configured for on-premise LLMs if needed

---

## Running Locally

### Prerequisites

- **Node.js 18+** / npm

### Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at http://localhost:5173.

The backend API URL is configured via `VITE_API_BASE_URL` in an `.env` file at the
`frontend/` root (copy `.env.example` to `.env`). It defaults to `http://localhost:8000`;
the deployed backend is `https://al-api.humaine-horizon.eu`.

Authentication is JWT-based: sign in (or register) on the `/login` page. The token is
stored locally and sent as `Authorization: Bearer <jwt>` on every request. Without a
token the backend falls back to a shared system user, but owner-only features (instance
delegation) require an account.

Run `npm run test:api` to smoke-test every backend endpoint the app depends on
(`VITE_API_BASE_URL` env or `--url <base>` selects the target server).





The two tabs are different views on the Analytics page
Benchmarking Suite (activeTab === 'benchmark')

Shows pre-recorded, complete agent runs — "sessions". Each session is a script of events from all agents (the human "LAB" agent plus AI agents), with per-agent event counts, latencies, and human decision durations. You pick a session → see its overview cards, a ScriptTimeline, and can export the raw JSON.
Backed by the useAnalyticsOverview / useSessions / useSession composables (originally /analytics/overview, /analytics/sessions, /analytics/sessions/{id}), whose data comes from benchmarking_suite/*.json.
It's retrospective: analyzing finished benchmark runs.
User Behavior (UserBehaviorDashboard.vue, activeTab === 'user-behavior')

Shows aggregated metrics of the current user's own interactions — overview, AI impact, XAI engagement, page engagement, ticket heatmap, event timeline, and funnel.
Backed by the useUserBehavior* composables. In mock mode these aggregate the client-side event log in useTelemetryStore via useUserBehaviorAggregator.ts.
It's live/interactive: reflecting what you're clicking, viewing, and labeling right now.
So: Benchmarking Suite = recorded multi-agent traces you replay/inspect. User Behavior = a real-time dashboard of your own telemetry stream.

When is data actually sent to the backend?
After the realignment to origin/humaine-al-api, the answer depends on the Mock toggle:

Mock mode ON → nothing goes to the backend. Every telemetry event (clicks, page views, tab changes, view-ticket, label decisions) is written only to the client-side useTelemetryStore, and both dashboards read from sample fixtures / client aggregation.

Mock mode OFF (live) → the branch backend has no generic /analytics/* telemetry endpoint, so:

Granular UX telemetry (clicks, open_page, tab_change, view_ticket_*, filters, etc.) is a no-op — see the early return in recordLab in useBenchmarkTelemetry.ts and the dropped postTelemetryEvent in router/index.ts. It is not sent anywhere.

The only telemetry that reaches the backend is a human label decision, sent at the moment you confirm or override a ticket, via POST /activelearning/{id}/label-with-info. That fires from:

useTicketQueue.ts (single confirm/override in TicketQueue/ManualQueue), and
Dispatching.vue (confirmPrediction / reassignTeam).
The payload carries ticket_id, label, model_prediction, start_time/end_time (decision timing), and optional explanation / most_helpful_feature. Server-side this logs an al_events row + stages a label_decision, and the benchmarking service exports to MinIO once enough confirm/override events accumulate.

Bulk labeling still uses PUT /activelearning/{id}/label (persists the label but is not the rich telemetry channel — no per-ticket timing).

In live mode both Analytics tabs render sample/empty data (guarded to avoid 404s), so they're effectively mock-only features with this backend.

In one sentence: in live mode the backend only receives telemetry when you label a ticket (through label-with-info); everything else the dashboards show is client-side only and, in mock mode, nothing is sent at all.








TODO:

- todo ticket per titilo evolution
