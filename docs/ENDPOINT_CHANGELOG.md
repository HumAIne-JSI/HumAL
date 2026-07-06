# HumAL API Endpoint Changelog

**Date:** July 6, 2026

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
