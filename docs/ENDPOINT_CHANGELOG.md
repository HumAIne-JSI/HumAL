# HumAL API Endpoint Changelog

**Date:** July 10, 2026

### ✅ CANONICAL XAI RESULT MODEL: `XaiResultFile` for all LIME outputs

**Purpose:** Unify LIME output shape across the in-process `explain_lime` path and the external RabbitMQ XAI worker. Replace duck-typed walkers with Pydantic-validated parsing at all I/O boundaries.

**Changes:**
- **`POST /xai/{al_instance_id}/explain_lime`** — response shape changed from `list[list[{class, top_words, error}]]` to `list[XaiResultFile]`. Each entry is now a structured object with `text`, `prediction {label, probabilities}`, `word_weights` (top-1 class only), `highlighted_tokens` (with `direction` and `intensity`), `index`, `error`, and `class_explanations` (per-class breakdowns).
- **`GET /xai/jobs/{job_id}`** — the `result` field now contains per-file validated `XaiResultFile` dicts instead of the raw MinIO payload. Old-format lists are coerced to `null`.
- **`update_xai_job`** — the duck-typed walker is removed. Results from MinIO are validated through `parse_xai_result`. Old-format results (`[{class, top_words, error}]`) are logged with `result: null` and a descriptive error.
- **`xai_rabbitmq_worker.py`** — now emits a single canonical `XaiResultFile` dict instead of a list of per-class dicts.
- **al_events payload** — for `action="lime"` events, the payload is now `{"ticket_id": ..., "result": <full XaiResultFile dict>, "error": ...}` (replacing `{"ticket_id": ..., "top_features": [...], "error": ...}`).
- **New Pydantic models**: `XaiResultFile`, `HighlightedToken`, `PredictionInfo`, `ClassExplanation` in `app/data_models/active_learning_dm.py` with `XaiResultFile.from_lime()` factory and `parse_xai_result()` parser.
- **Backward compatibility**: old-format result JSON files already stored in MinIO are gracefully handled — they are logged but produce `result: null` with an explanatory error. No runtime crash.

**Date:** July 10, 2026

### ✅ UPDATED BEHAVIOR: `POST /xai/{al_instance_id}/requests` — task-queue message schema v0.3

The message published to `TASK_QUEUE` now follows schema version **0.3**:

- **`version`** is now a JSON **number** (`float`), default `0.3` (was a string from `MESSAGE_VERSION`, default `"0.1"`). `MESSAGE_VERSION` must now be float-parseable.
- **`artifacts.raw_tickets`** is now a **single string** — the first available test-split dataset object from MinIO — instead of a `list[str]` of all dataset objects.
- The message is now built through the `XaiRequestMessage` / `XaiArtifacts` Pydantic models (`app/data_models/active_learning_dm.py`) to enforce the contract.
- **DuckDB unchanged:** the `xai_jobs.request_raw_tickets_locations` column remains a `VARCHAR[]` array storing the full list of dataset object names.
- Downstream impact: none — the XAI worker does not consume `raw_tickets` or `version` (inference is delegated to the API).

**Date:** July 9, 2026

### ✅ NEW LABELER SIGNALS: `is_tired`, `is_difficult`, `i_dont_know`

Three optional boolean fields added to `POST /activelearning/{id}/label-with-info`:

- **`is_tired`** / **`is_difficult`** — analysis-only; persisted to `label_decisions` with no effect on the unlabeled pool or retraining.
- **`i_dont_know`** — when `true`, the ticket is retired from the unlabeled pool (never re-surfaced via `GET /next`) and excluded from retraining. The `label` field becomes optional for these items.
- **`skipped_for_training`** — DuckDB generated column on `label_decisions` derived from `(i_dont_know IS TRUE)`. Not included in INSERT/UPDATE.
- **Backend behavior:** `label_with_info` partitions the batch into real labels and idk items; idk items skip `save_labels` and `apply_labels`, log an `action="i_dont_know"` event, and get added to an in-memory skip set (`storage.skipped_tickets`). `get_next_instances` filters skipped refs via `candidates=`. An all-idk batch skips `update_model` and `calculate_metrics`.
- **Restart survival:** `_load_from_persistence` rebuilds `skipped_tickets` by querying `label_decisions.skipped_for_training = TRUE` via `DuckDbPersistenceService.load_skipped_refs()`.
- **`num_labeled` metric** is unaffected (idk stays `MISSING_LABEL` in `y_train`).

**Date:** July 8, 2026

### ✅ NEW MANUAL TEST: Live E2E + Real LIME RabbitMQ Worker

Two new scripts under `backend/tests/manual_tests/`:

- **`xai_rabbitmq_worker.py`** — A real LIME RabbitMQ worker (replaces
  `xai_rabbitmq_simulator.py` in intent, left in place). Consumes
  `TASK_QUEUE`, loads the ticket + model + encoders + `TicketVectorizer`
  from MinIO, runs `LimeTextExplainer` with `num_features=10`,
  `num_samples=1000` per top-k class, writes result JSON to
  `xai_results/{id}/{job_id}/result.json` in `smart-finance-results`, and
  publishes a completion message to `RESULT_QUEUE`. No mocks — uses real
  `SentenceTransformer` (locally cached) and real MinIO.
- **`e2e_live.py`** — Live end-to-end driver that starts uvicorn + the
  above worker as subprocesses against a real MinIO + RabbitMQ, then drives
  the full AL loop: capabilities → register → login → new → 10×[next,
  /data/tickets, infer_proba, nearest, xai/requests (async), poll
  xai/jobs until completed, simulated human delay, label-with-info] →
  export. Asserts MinIO artifacts, export ZIP, benchmarking JSON, and XAI
  result JSON. Hermetic (separate test DuckDB + per-instance MinIO
  cleanup on teardown). Not auto-discovered by `python -m pytest tests/`.
  Run directly: `python backend/tests/manual_tests/e2e_live.py`.

**Date:** July 7, 2026

### ✅ UPDATED BEHAVIOR: `GET /activelearning/{al_instance_id}/info` and per-iteration evaluation

**Purpose:** Expand the per-iteration evaluation to additional metrics and reduce the underlying model inference to a single pass.

**Behavior update:**
- `GET /activelearning/{al_instance_id}/info` now returns 11 parallel lists per instance, additive on top of the existing three: `accuracies`, `precisions_macro`, `precisions_weighted`, `recalls_macro`, `recalls_weighted`, `f1_per_class`, `confusion_matrices`, `roc_aucs_ovr_macro`. Existing fields (`mean_entropies`, `f1_scores`, `num_labeled`) are unchanged.
- `ActiveLearningService.calculate_metrics` now performs **one** `predict_proba` call on the test set; the hard-label predictions are derived from `argmax(proba)` followed by `le.inverse_transform(...)` and reused for accuracy, per-class F1, macro/weighted precision and recall, the confusion matrix, and ROC-AUC. The previous code called `predict_proba` (for entropy) **and** `predict` (for F1) on the same data — those two passes have been merged.
- The DuckDB `metrics` table gained 8 columns: `accuracy`, `precision_macro`, `precision_weighted`, `recall_macro`, `recall_weighted`, `f1_per_class` (JSON), `confusion_matrix` (JSON), `roc_auc_ovr_macro`. `SCHEMA_VERSION` is unchanged; existing local DuckDB files must be deleted once to pick up the new columns.
- ROC-AUC is one-vs-rest macro. For binary tasks the standard `roc_auc_score` is used; for multi-class tasks `label_binarize` + `multi_class='ovr'` + `average='macro'`. It is `null` (and produces no warning) when fewer than two true classes are present in the test set.
- The `evaluate` event payload (written via `_log_event`) also includes the new metric values for audit/export parity.
- The `GET /activelearning/{al_instance_id}/export` ZIP's `metrics.json` includes the new fields per iteration.
- No request/response shape removed; the change is purely additive.

---

**Date:** July 6, 2026

### ✅ UPDATED BEHAVIOR: `POST /activelearning/{al_instance_id}/infer` and `POST /activelearning/{al_instance_id}/infer_proba`

**Purpose:** Conditional authentication on inference endpoints so the external XAI service can call them without a user, while user-driven `query_idx` calls still require ownership.

**Behavior update:**
- The instance-ownership access check (`require_instance_access`) has moved from the shared preamble (ran for both paths) to **inside the `query_idx` branch only**.
- **Body (ad-hoc `data`) path:** now runs with **no authentication and no ownership check**. Still logs nothing (unchanged audit). Enables service-to-service inference without a user/token.
- **`query_idx` path:** still requires the caller to be the instance owner or a delegate (404 if instance missing, 403 if not authorized). The access check now runs **before** the `request_prediction` event is written, so unauthorized `query_idx` attempts produce no events. Per-ticket `predict` event attribution to the calling user (or system user when no token) is unchanged.
- `Depends(get_current_user)` is retained on both endpoints; its no-token fallback to the system user is harmless on the body path and is the basis for system-user attribution on token-less `query_idx` calls.
- No request/response shape change. No new endpoints. No API keys.

---

### ✅ UPDATED BEHAVIOR: `POST /activelearning/new`

**Purpose:** AL instance IDs are now persistent and never reused.

**Behavior update:**
- The `instance_id` returned by `POST /activelearning/new` is now sourced from a persistent DuckDB sequence (`al_instance_id_seq`) instead of an in-memory `max(existing_ids) + 1` counter.
- IDs are monotonic: deleting an instance no longer frees its ID for reuse, and a backend pod restart no longer resets the counter. This makes instance names stable for benchmarking.
- ID `0` remains reserved for the ground-truth instance and is never issued.
- No request/response shape change — the response body is still `{"instance_id": <int>}`.

---

**Date:** June 26, 2026

### ✅ NEW ENDPOINT: `GET /activelearning/{al_instance_id}/export`

**Purpose:** Exports all DuckDB-stored data for an AL instance as a downloadable ZIP of JSON files for offline analysis of labeling statistics.

**Example Request:**
```bash
curl "http://localhost:8000/activelearning/1/export" \
  -H "Authorization: Bearer <your-jwt>" \
  -o export_al_1.zip
```

**Example Response:** Binary `application/zip` download named `export_al_<id>_<timestamp>.zip`.

**Behavior:**
- Returns a ZIP containing a `manifest.json` and one `duckdb/<table>.json` per table: `al_instances`, `labels`, `ground_truth_labels`, `label_decisions`, `metrics`, `model_paths`, `al_events`, `xai_jobs`, `instance_delegations`, `tickets`, `users`.
- Instance-scoped tables are filtered by `al_instance_id`; `tickets` is exported in full (global, both splits); `users` is scoped to users involved with the instance (owner, delegates, labelers, event actors, XAI job submitters) and the `password` column is set to `null`.
- Ground-truth labels from instance 0 are included as a separate `duckdb/ground_truth_labels.json` file; `labels.json` remains scoped strictly to the requested instance (the two are not merged in the export).
- JSON columns (`al_events.payload`, `label_decisions.xai_result`, `label_decisions.similar_tickets`) and array columns (`al_instances.classes`, `xai_jobs.request_raw_tickets_locations`, `xai_jobs.result_file_names`) are preserved as native JSON structures.
- MinIO binary artifacts (models, encoders, vectorized tickets, labels as joblib, ticket vectorizer, xai tickets, benchmarking, xai results) are NOT included.
- Authorization: instance owner or delegate only (404 if missing, 403 if not authorized), consistent with other instance endpoints.

---

**Date:** June 25, 2026  
**Summary:** Per-ticket ref handling for inference, per-ticket LIME logging, and correction of prior fictional entries.

---

### ✅ UPDATED BEHAVIOR: `POST /activelearning/{al_instance_id}/infer` and `POST /activelearning/{al_instance_id}/infer_proba`

**Behavior update:**
- The single request-level `ref` query parameter has been **removed**.
- Each endpoint now takes **mutually exclusive** parameters: either a `data` body (a `Data` object or `list[Data]`) OR a `query_idx` query parameter (a `list[str]` of ticket refs). Providing both or neither returns HTTP 400.
- **Body path (ad-hoc data, no `query_idx`):** no events are logged. The predictions are returned but nothing is written to `al_events`.
- **`query_idx` path (refs only, no body):** the router resolves the tickets by ref via the data service (404 if any ref is missing), then logs **two tiers** of events:
  - **One** batch-level `request_prediction` event (`actor_type="system"`, `agent="orchestrator"`, `object_id=null`, `payload={"request_size": N, "ticket_ids": [refs...]}`).
  - **One** `predict` event per ticket (`actor_type="ai"`, `agent="classifier_model"`, `object_id=<ref>`, `payload={"prediction": ...}` for `/infer` or `{"classes": [...], "probabilities": [<row>]}` for `/infer_proba`).

### ✅ UPDATED BEHAVIOR: `POST /xai/{al_instance_id}/explain_lime`

**Behavior update:**
- LIME events are now logged **per ticket** rather than per batch. For each non-`None` ticket ref, one `lime` event is written with `object_id=<ref>`, `payload={"ticket_id": <ref>, "top_features": [...], "error": <str|null>}`.
- When all `ticket_refs` are `None` (ad-hoc body path), no `lime` events are logged.
- The per-ticket `upsert_label_decision(ref=<ref>, xai_result=...)` is unchanged.

### ⚠️ RETRACTED: June 23, 2026 entry

The earlier June 23, 2026 block described:
- A `GET /activelearning/{al_instance_id}/benchmarking-report` HTTP endpoint — this endpoint **does not exist** in the codebase. Benchmarking is an automatic internal MinIO export triggered by `BenchmarkingService.export_if_needed` when a label count threshold is met.
- `predicted_class`, `ticket_ref`, and `meta_block` columns on `al_events` — these columns **do not exist**. The actual schema has only `object_id` (where refs live) and a JSON `payload` column.
- A 2-second proximity window for `meta_block` — this concept is not implemented anywhere in the source.

The real HAIC artifact shape is `{artifact_schema, schema_version, session_id, meta, decisions, events}` — see `docs/ARCHITECTURE.md` § HAIC Benchmarking Artifact.

---

**Date:** June 13, 2026  
**Summary:** JWT-based authentication replacing API-key auth.

---

**Date:** June 15, 2026

### ✅ UPDATED BEHAVIOR: `POST /xai/{al_instance_id}/explain_lime`

**Purpose:** Now supports multi-class LIME explanations and automatic persistence.

**Behavior update:**
- New query parameter `top_k` (default: 1) controls how many top predicted classes receive a LIME explanation.
- The response shape is now a list of lists: outer list = one entry per ticket; inner list = one class explanation per predicted class. Each class explanation contains `class`, `top_words`, and `error`.
- When `query_idx` is provided, the result is logged to `al_events` with `action="lime"` and also persisted into `label_decisions.xai_result` keyed by the `query_idx` value.
- When `ticket_data` is provided, the result is logged to `al_events` but **not** upserted into `label_decisions` because no ticket ref is available.
- Removed the idea of an explicit `ticket_ref` parameter; `query_idx` values serve as the persistence key.

## Latest Update

**Date:** June 15, 2026

### ✅ NEW ENDPOINT: `POST /activelearning/{al_instance_id}/delegate`

**Purpose:** Allows an instance owner to delegate (share) their AL instance with another user by username. The delegate gains full access (label, infer, XAI, save, delete) while the owner retains access.

**Example Request:**
```json
{
  "username": "bob"
}
```

**Example Response:**
```json
{
  "username": "bob",
  "delegate_user_id": "123e4567-e89b-12d3-a456-426614174000",
  "granted_by": "987fcdeb-51a2-43d7-9012-3456789abcde",
  "granted_at": "2026-06-15T10:30:00"
}
```

**Behavior:**
- Only the instance owner can delegate access.
- Delegation is by username (not UUID) for user-friendliness.
- Self-delegation is rejected with a clear error message.
- Delegated instances appear in the delegate's `GET /activelearning/instances` list indistinguishably from owned instances.
- Delegation is idempotent: delegating the same user twice does not error.

### ✅ NEW ENDPOINT: `DELETE /activelearning/{al_instance_id}/delegate/{username}`

**Purpose:** Revokes a user's delegated access to an instance. Only the instance owner can revoke delegation.

**Example Response:**
```json
{
  "message": "Delegation revoked for user 'bob'"
}
```

**Behavior:**
- Only the instance owner can revoke delegation.
- Revoking a non-existent delegation succeeds silently (no error).
- After revocation, the user can no longer access the instance.

### ✅ NEW ENDPOINT: `GET /activelearning/{al_instance_id}/delegates`

**Purpose:** Lists all users who have been delegated access to an instance.

**Example Response:**
```json
{
  "delegates": [
    {
      "username": "bob",
      "delegate_user_id": "123e4567-e89b-12d3-a456-426614174000",
      "granted_by": "987fcdeb-51a2-43d7-9012-3456789abcde",
      "granted_at": "2026-06-15T10:30:00"
    }
  ]
}
```

**Behavior:**
- Only the instance owner can view the delegate list.
- Returns an empty list if no delegations exist.

### ✅ UPDATED BEHAVIOR: `GET /activelearning/instances`

**Purpose:** Now includes both owned instances and delegated instances in the response.

**Behavior Change:**
- Previously: Only returned instances owned by the current user.
- Now: Returns instances owned by the current user OR delegated to the current user.
- Delegated instances appear indistinguishably from owned instances (no flag or marker).

### ✅ UPDATED BEHAVIOR: All AL instance endpoints

**Purpose:** Authorization now checks both ownership and delegation status.

**Behavior Change:**
- Previously: Only the instance owner could access instance-scoped endpoints.
- Now: Both the owner and any delegates can access instance-scoped endpoints with full permissions.
- Affected endpoints: `GET /{id}/next`, `PUT /{id}/label`, `POST /{id}/label-with-info`, `GET /{id}/info`, `POST /{id}/save`, `DELETE /{id}`, `POST /{id}/infer`, `POST /{id}/infer_proba`, `POST /xai/{id}/*`.

---

**Date:** June 14, 2026

### ❌ BREAKING CHANGE: `explanation` field removed, `most_helpful_feature` constrained

The `explanation` input field has been removed from `POST /activelearning/{al_instance_id}/label-with-info`. It is no longer stored in `label_decisions` or returned in historical neighbors.

The `most_helpful_feature` field is now constrained to one of `"lime"`, `"predicted_class_neighbors"`, `"historical_neighbors"`, or `"model_prediction"`. Previously it accepted any free text.

**Changes:**
- `explanation` removed from `LabelInfo` request model, `Neighbor` response model, `label_decisions` DB table, and all related code
- `most_helpful_feature` type changed from `Optional[str]` to `Optional[Literal["lime", "predicted_class_neighbors", "historical_neighbors", "model_prediction"]]`

---

**Date:** June 13, 2026

### ❌ BREAKING CHANGE: API-Key Authentication Replaced with JWT

The `X-API-Key` header has been removed. All authenticated endpoints now use `Authorization: Bearer <jwt>`.

**Changes:**
- `X-API-Key` header is no longer accepted; use `Authorization: Bearer <jwt>` instead
- `POST /users/register` no longer returns `api_key` in the response
- The `api_key` column has been removed from the DuckDB `users` table; the persistence service no longer generates, stores, or queries API keys
- New endpoint `POST /users/login` for obtaining a JWT access token
- When no token is provided, the request still falls back to the system user as before
- Invalid or expired tokens return `401 Unauthorized`

### ✅ NEW ENDPOINT: POST /users/login

```
Method: POST
Path: /users/login
Request body: {"username": "string", "password": "string"}
Returns: {"access_token": "string", "token_type": "bearer"}
```

**Purpose:** Authenticate a user and receive a JWT access token for subsequent requests.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "my-user", "password": "my-password"}'
```

**Example Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### ❌ CHANGED: POST /users/register

`api_key` is no longer returned in the registration response. The response body is now `{"user_id": "uuid", "username": "string"}`.

### ❌ CHANGED: Authentication mechanism

All protected endpoints (`/activelearning/{al_instance_id}/*`, `/xai/{al_instance_id}/*`, `/xai/jobs/*`, `/users/me`) now expect `Authorization: Bearer <jwt>` instead of `X-API-Key`. Missing tokens still fall back to the system user.

---

## Previous Updates

**Date:** June 11, 2026  
**Summary:** User authentication, API-key-based ownership enforcement on AL instances, and user management endpoints.

---

### ✅ NEW ENDPOINTS: User Management

Two new endpoints under `/users/` for API-key-based user management.

#### `POST /users/register`

```
Method: POST
Path: /users/register
Request body: {"username": "string"}
Returns: {"user_id": "uuid", "username": "string", "api_key": "string"}
```

**Purpose:** Register a new user and receive an auto-generated API key. The API key must be sent as the `X-API-Key` header on subsequent requests to authenticated endpoints.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/users/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "my-user"}'
```

**Example Response:**
```json
{
  "user_id": "a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6",
  "username": "my-user",
  "api_key": "abcdef1234567890abcdef1234567890"
}
```

#### `GET /users/me`

```
Method: GET
Path: /users/me
Headers: X-API-Key (string, optional)
Returns: {"user_id": "uuid", "username": "string"}
```

**Purpose:** Return the identity of the authenticated user. When no `X-API-Key` is sent, returns the system user identity.

**Example Request:**
```bash
curl "http://localhost:8000/users/me" \
  -H "X-API-Key: abcdef1234567890abcdef1234567890"
```

---

### ✅ NEW BEHAVIOR: API-Key Authentication for Protected Endpoints

All endpoints under `/activelearning/{al_instance_id}/*`, `/xai/{al_instance_id}/*`, and `/xai/jobs/*` now require valid AL instance ownership.

**Behavior changes:**
- Add `X-API-Key` header to requests to associate actions with your user
- When `X-API-Key` is absent, the system user (`00000000-0000-0000-0000-000000000000`) is used
- Operations on an AL instance are only allowed if the instance's `user_id` matches the authenticated user
- `GET /activelearning/instances` only returns instances owned by the authenticated user
- Invalid API keys return `401 Unauthorized`

**Error Response:**
```json
{
  "detail": "Invalid API Key"
}
```

---

## Previous Updates

---

## Summary of Changes

1. **Data Router Restructuring** - Simplified path parameters
2. **Configuration Enhancement** - Added new capabilities endpoint
3. **XAI Router Expansion** - Added async request handling with job tracking

---

## Latest Update

**Date:** June 2, 2026

### ✅ UPDATED BEHAVIOR: `POST /activelearning/new`

The `train_data_path` and `test_data_path` fields are now optional on the new active-learning instance request and are ignored by the server.

**Behavior update:**
- `train_data_path` and `test_data_path` remain accepted for backward compatibility
- The service no longer reads, validates, stores, or persists these request fields
- The fields will be removed in a future API version

---

**Date:** May 27, 2026

### ✅ UPDATED BEHAVIOR: `POST /xai/{al_instance_id}/nearest`

The nearest-neighbor endpoint now returns two result lists in one response: `predicted_class_neighbors` and `historical_neighbors`.

**Behavior update:**
- `predicted_class_neighbors` returns one best neighbor per top predicted class
- `historical_neighbors` returns the most similar rows from `label_decisions` that already have non-empty `xai_result` or `similar_tickets`
- Neighbor scoring now includes `best_sentence`, `best_sentence_score`, and `sentence_score_components` using the weighted formula `0.7 * embedding_similarity + 0.2 * keyword_overlap + 0.1 * entity_overlap`
- Deprecated neighbor fields `reason` and `overlapping_terms` are no longer returned
- Historical neighbors now include persisted metadata fields: `xai_result`, `similar_tickets`, `model_prediction`, and `most_helpful_feature`
- Stored `label_decisions.similar_tickets` payloads are now structured with `title` and `description` preserved for readability, while recursive `xai_result` and `similar_tickets` content is stripped to avoid duplication and bloat

---

## Detailed Changes

### Data Router (`/data`)

#### ❌ REMOVED / CHANGED: `POST /data/{al_instance_id}/tickets`

**Previous Definition:**
```
Method: POST
Path params: al_instance_id (integer)
Query params: train_data_path (string, optional; required when al_instance_id is 0)
Request body: array of ticket indices (strings)
```

**New Definition:**
```
Method: POST
Path: /data/tickets
Request body: list[str] - indices of tickets to retrieve
```

**Changes:**
- Removed `al_instance_id` path parameter
- Removed `train_data_path` query parameter
- Simplified to direct index lookup without instance context

---

#### ❌ CHANGED: `GET /data/{al_instance_id}/teams`

**Previous Definition:**
```
Method: GET
Path params: al_instance_id (integer)
Query params: train_data_path (string, optional; required when al_instance_id is 0)
```

**New Definition:**
```
Method: GET
Path: /data/teams
```

**Changes:**
- Removed `al_instance_id` path parameter
- Removed `train_data_path` query parameter
- Now retrieves teams globally from the dataset

---

#### ❌ CHANGED: `GET /data/{al_instance_id}/categories`

**Previous Definition:**
```
Method: GET
Path params: al_instance_id (integer)
Query params: train_data_path (string, optional; required when al_instance_id is 0)
```

**New Definition:**
```
Method: GET
Path: /data/categories
```

**Changes:**
- Removed `al_instance_id` path parameter
- Removed `train_data_path` query parameter
- Now retrieves categories globally from the dataset

---

#### ❌ CHANGED: `GET /data/{al_instance_id}/subcategories`

**Previous Definition:**
```
Method: GET
Path params: al_instance_id (integer)
Query params: train_data_path (string, optional; required when al_instance_id is 0)
```

**New Definition:**
```
Method: GET
Path: /data/subcategories
```

**Changes:**
- Removed `al_instance_id` path parameter
- Removed `train_data_path` query parameter
- Now retrieves subcategories globally from the dataset

---

### Configuration Router (`/config`)

#### ✅ NEW ENDPOINT: `GET /config/capabilities`

```
Method: GET
Path: /config/capabilities
Returns: Dictionary containing available capability names
```

**Purpose:** Retrieve all available system capabilities for feature detection and UI rendering.

**Example Request:**
```bash
curl "http://localhost:8000/config/capabilities"
```

**Example Response:**
```json
{
  "capabilities": ["xai"]
}
```

**Explanation:** For now, the list can only contain "xai" element. If it is empty, then "xai" is not available (this happens, when rabbitmq is not available) and its endpoints shouldn't be called.

---

### XAI Router (`/xai`)

#### ✅ NEW ENDPOINT: `POST /xai/{al_instance_id}/requests`

```
Method: POST
Path: /xai/{al_instance_id}/requests
Path params: al_instance_id (integer)
Query params: 
  - model_id (integer, optional; default: 0)
  - ticket_ref (string, optional)
Request body: Data object
Returns: {"job_id": uuid}
```

**Purpose:** Submit an XAI explanation request for asynchronous processing via RabbitMQ. The request is persisted to MinIO and queued for processing.

**Requirements:**
- RabbitMQ must be enabled (USE_RABBITMQ=1)
- Valid al_instance_id
- Trained model

**Example Request:**
```bash
curl -X POST "http://localhost:8000/xai/1/requests" \
  -H "Content-Type: application/json" \
  -d "{\"title_anon\":\"VPN not working\",\"description_anon\":\"Cannot connect to VPN\"}"
```

**Example Response:**
```json
{
  "job_id": "a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6"
}
```

---

#### ✅ NEW ENDPOINT: `GET /xai/jobs/{job_id}`

```
Method: GET
Path: /xai/jobs/{job_id}
Path params: job_id (UUID)
Returns: Job status and results (when complete)
```

**Purpose:** Retrieve the status and results of a previously submitted XAI request.

**Requirements:**
- RabbitMQ must be enabled (USE_RABBITMQ=1)
- Valid job_id

**Response Statuses:**
- `queued` - Request is in the queue
- `processing` - Request is being processed
- `completed` - Request complete with results in `result` field
- `failed` - Request failed

**Example Request (In Progress):**
```bash
curl "http://localhost:8000/xai/jobs/a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6"
```

**Example Response (In Progress):**
```json
{
  "status": "processing",
  "result": null
}
```

**Example Response (Completed):**
```json
{
  "status": "completed",
  "result": {
    "top_words": [["vpn", 0.42], ["connect", 0.18]],
    "error": null
  },
  "result_location": "xai-results/path/to/result"
}
```

**Behavior update:** Completed job payloads are now persisted into `label_decisions.xai_result` so the tracked XAI output stays associated with the originating ticket reference or SHA.

---

#### ✅ UPDATED BEHAVIOR: `POST /xai/{al_instance_id}/nearest_ticket`

**Behavior update:** When a ticket reference is available, nearest-neighbor results are now persisted into `label_decisions.similar_tickets` with `title` and `description` retained for display, while recursive `xai_result` and `similar_tickets` content is stripped to avoid duplication and bloat.

**Note:** The "result" field structure is not yet fully decided upon.

---
