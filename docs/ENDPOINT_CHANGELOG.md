# HumAL API Endpoint Changelog

**Date:** April 22, 2026  
**Summary:** Updates to data router endpoints, new configuration endpoint, and async XAI request handling.

---

## Summary of Changes

1. **Data Router Restructuring** - Simplified path parameters
2. **Configuration Enhancement** - Added new capabilities endpoint
3. **XAI Router Expansion** - Added async request handling with job tracking

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

**Note:** The "result" field structure is not yet fully decided upon.

---
