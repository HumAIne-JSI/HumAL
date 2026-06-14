# HumAL API Endpoint Changelog

**Date:** June 13, 2026  
**Summary:** JWT-based authentication replacing API-key auth.

---

## Latest Update

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
