# HumAL API

Base URL (local): `http://localhost:8000`

All endpoints accept and return JSON unless noted. Path and query parameters are listed per endpoint.

## Inference

### POST /activelearning/{al_instance_id}/infer

**Description:** Evaluates new tickets against a trained active learning model to predict their resolution team or label. Supports processing a single ticket or a batch of tickets simultaneously.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |
| `query_idx` | query | array (string) | No | List of ticket references. Mutually exclusive with the request body. When provided, tickets are resolved by ref via the data service, predicted, and per-ticket events are logged. |

**Request Body (`application/json`):**  
Single `Data` object or an array of `Data` objects. **Mutually exclusive with `query_idx`:** provide either the body OR `query_idx`, never both, never neither (returns 400).

| Field | Type | Required | Description |
|---|---|---|---|
| `title_anon` | string | No | Anonymized ticket title |
| `description_anon` | string | No | Anonymized ticket description |
| `service_subcategory_name` | string | No | Subcategory of the service |
| `team_name` | string | No | Actual assigned team |
| `service_name` | string | No | Top-level service name |
| `last_team_id_name` | string | No | Previous team assignment |
| `public_log_anon` | string | No | Public communication logs |

**Event Logging:**
- **Body path (no `query_idx`):** No events are logged. Ad-hoc inference is unlogged.
- **`query_idx` path:** Two tiers of events are written to `al_events`:
  - **One** batch-level `request_prediction` event (`actor_type="system"`, `agent="orchestrator"`, `object_id=null`, `payload={"request_size": N, "ticket_ids": [refs...]}`), emitted by the router.
  - **One** `predict` event per ticket (`actor_type="ai"`, `agent="classifier_model"`, `object_id=<ref>`, `payload={"prediction": <class>}`), emitted by the service.

**Swagger-style UI Example:**

*Request Body Path (unlogged)*
```json
{
  "title_anon": "VPN not working"
}
```
*HTTP 200 OK*
```json
["(GI-UX) Network Access"]
```

*`query_idx` Path (logged per-ticket)*
```bash
POST /activelearning/1/infer?query_idx=R-1&query_idx=R-2
```
*HTTP 200 OK*
```json
[
  "(GI-UX) Network Access",
  "Email Support Team"
]
```

**cURL Example (body path):**
```bash
curl -X POST "http://localhost:8000/activelearning/1/infer" \
	-H "Content-Type: application/json" \
	-d "{\"title_anon\":\"VPN not working\"}"
```

**cURL Example (query_idx path):**
```bash
curl -X POST "http://localhost:8000/activelearning/1/infer?query_idx=R-1&query_idx=R-2"
```

### POST /xai/{al_instance_id}/nearest

**Description:** Returns two nearest-neighbor result sets in one response. `predicted_class_neighbors` contains one most-similar ticket per top predicted class, and `historical_neighbors` contains the most-similar labeled decisions that already store `xai_result` or `similar_tickets`. When a ticket reference is available, the structured `similar_tickets` payload is also persisted without raw title/description text and without recursive `xai_result` or `similar_tickets` content.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |
| `top_k` | query | integer | No (Default: 1) | Number of predicted classes to consider and number of historical neighbors to return |
| `model_id` | query | integer | No (Default: 0) | Model identifier |

**Request Body (`application/json`):**
Exactly one of the following must be provided:
`Data` object or `query_idx` list.

**Response Shape:**
```json
[
  {
    "query_idx": "R-544314",
    "predicted_class_neighbors": [
      {
        "ref": "R-123456",
        "label": "team_a",
        "similarity": 0.91,
        "best_sentence": "Printer is broken",
        "best_sentence_score": 0.82,
        "sentence_score_components": {
          "embedding_similarity": 0.9,
          "keyword_overlap": 0.1,
          "entity_overlap": 0.0
        }
      }
    ],
    "historical_neighbors": [
      {
        "ref": "R-222222",
        "label": "team_b",
        "similarity": 0.88,
        "best_sentence": "Need VPN access",
        "best_sentence_score": 0.79,
        "xai_result": {"top_words": [["vpn", 0.42]]},
        "similar_tickets": [{"ref": "R-111111", "similarity": 0.75}],
        "model_prediction": "team_b",
        "most_helpful_feature": "lime"
      }
    ]
  }
]
```

**Sentence Scoring:**
- `best_sentence_score = 0.7 * embedding_similarity + 0.2 * keyword_overlap + 0.1 * entity_overlap`
- `sentence_score_components` exposes the three weighted terms used in the score
- If a ticket has no sentences, `best_sentence` is `null` and `best_sentence_score` is `0.0`

**Neighbor Fields:**
- `reason` and `overlapping_terms` are no longer returned
- Historical neighbors include the persisted `xai_result`, `similar_tickets`, `model_prediction`, and `most_helpful_feature` metadata

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/xai/1/nearest?top_k=2" \
	-H "Content-Type: application/json" \
	-d "{\"title_anon\":\"VPN not working\",\"description_anon\":\"Cannot connect to VPN\"}"
```

### POST /activelearning/{al_instance_id}/infer_proba

**Description:** Evaluates new tickets against a trained active learning model to return class probabilities. Supports processing a single ticket or a batch of tickets simultaneously.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |
| `query_idx` | query | array (string) | No | List of ticket references. Mutually exclusive with the request body. When provided, tickets are resolved by ref via the data service, predicted, and per-ticket events are logged. |

**Request Body (`application/json`):**  
Single `Data` object or an array of `Data` objects. **Mutually exclusive with `query_idx`:** provide either the body OR `query_idx`, never both, never neither (returns 400).

| Field | Type | Required | Description |
|---|---|---|---|
| `title_anon` | string | No | Anonymized ticket title |
| `description_anon` | string | No | Anonymized ticket description |
| `service_subcategory_name` | string | No | Subcategory of the service |
| `team_name` | string | No | Actual assigned team |
| `service_name` | string | No | Top-level service name |
| `last_team_id_name` | string | No | Previous team assignment |
| `public_log_anon` | string | No | Public communication logs |

**Event Logging:**
- **Body path (no `query_idx`):** No events are logged. Ad-hoc inference is unlogged.
- **`query_idx` path:** Two tiers of events are written to `al_events`:
  - **One** batch-level `request_prediction` event (`actor_type="system"`, `agent="orchestrator"`, `object_id=null`, `payload={"request_size": N, "ticket_ids": [refs...]}`), emitted by the router.
  - **One** `predict` event per ticket (`actor_type="ai"`, `agent="classifier_model"`, `object_id=<ref>`, `payload={"classes": [...], "probabilities": [<row>]}`), emitted by the service.

**Swagger-style UI Example:**

*Request Body Path (unlogged)*
```json
{
  "title_anon": "VPN not working"
}
```
*HTTP 200 OK*
```json
{
  "classes": ["network_issue", "hardware", "software", "other"],
  "probabilities": [[0.7, 0.1, 0.1, 0.1]]
}
```

*`query_idx` Path (logged per-ticket)*
```bash
POST /activelearning/1/infer_proba?query_idx=R-1&query_idx=R-2
```
*HTTP 200 OK*
```json
{
  "classes": ["network_issue", "hardware", "software", "other"],
  "probabilities": [
    [0.7, 0.1, 0.1, 0.1],
    [0.05, 0.8, 0.1, 0.05]
  ]
}
```

**cURL Example (body path):**
```bash
curl -X POST "http://localhost:8000/activelearning/1/infer_proba" \
	-H "Content-Type: application/json" \
	-d "{\"title_anon\":\"VPN not working\"}"
```

**cURL Example (query_idx path):**
```bash
curl -X POST "http://localhost:8000/activelearning/1/infer_proba?query_idx=R-1&query_idx=R-2"
```


## User Management

### POST /users/register

**Description:** Registers a new user.

**Request Body (`application/json`):**
| Field | Type | Required | Description |
|---|---|---|---|
| `username` | string | **Yes** | Display name for the new user |
| `password` | string | **Yes** | Password for the new user |

**Swagger-style UI Example:**
*Request Payload*
```json
{
  "username": "my-user",
  "password": "my-password"
}
```
*HTTP 200 OK*
```json
{
  "user_id": "a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6",
  "username": "my-user"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/users/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "my-user", "password": "my-password"}'
```


### POST /users/login

**Description:** Authenticates a user and returns a JWT access token.

**Request Body (`application/json`):**
| Field | Type | Required | Description |
|---|---|---|---|
| `username` | string | **Yes** | Username |
| `password` | string | **Yes** | Password |

**Swagger-style UI Example:**
*Request Payload*
```json
{
  "username": "my-user",
  "password": "my-password"
}
```
*HTTP 200 OK*
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "my-user", "password": "my-password"}'
```


### GET /users/me

**Description:** Returns the identity of the currently authenticated user. If no `Authorization` header is provided, the system user is returned.

**Headers:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `Authorization` | header | string | No | Bearer JWT token for authentication |

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "user_id": "00000000-0000-0000-0000-000000000000",
  "username": "system"
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/users/me" \
  -H "Authorization: Bearer <your-jwt>"
```


## Authentication

All endpoints under `/activelearning/{al_instance_id}/*`, `/xai/{al_instance_id}/*`, `/xai/jobs/*`, and `/users/me` require authentication via an `Authorization: Bearer <jwt>` header.

1. Register a user with `POST /users/register`.
2. Obtain a token with `POST /users/login`.
3. Include the token in subsequent requests:
   ```bash
   curl -X POST "http://localhost:8000/activelearning/new" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <your-jwt>" \
     -d '{"model_name":"svm","qs_strategy":"uncertainty sampling","class_list":["team_a","team_b"]}'

If the `Authorization` header is omitted, the request is treated as the system user (`00000000-0000-0000-0000-000000000000`). Invalid or expired tokens return `401 Unauthorized`. AL instance operations are scoped to the authenticated user's owned instances.


## Active Learning

### POST /activelearning/new

**Description:** Initializes a new active learning instance, preparing the dataset, model, and sampling strategy for a new training job.

**Request Body (`application/json`):**
| Field | Type | Required | Description |
|---|---|---|---|
| `model_name` | string | **Yes** | Algorithm name (e.g. `svm`, `logistic regression`) |
| `qs_strategy` | string | **Yes** | Query strategy (e.g. `uncertainty sampling`) |
| `class_list` | array | **Yes** | List of all possible classification labels |
| `train_data_path` | string | **No** | File path to the training dataset (deprecated, unused) |
| `test_data_path` | string | **No** | File path to the test dataset (deprecated, unused) |

**Swagger-style UI Example:**
*Request Payload*
```json
{
  "model_name": "svm",
  "qs_strategy": "uncertainty sampling",
  "class_list": ["team_a", "team_b"]
}
```
*Note: `train_data_path` and `test_data_path` are still accepted for backward compatibility but are ignored by the server.*
*HTTP 200 OK*
```json
{
  "instance_id": 1
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/activelearning/new" \
	-H "Content-Type: application/json" \
  -d "{\"model_name\":\"svm\",\"qs_strategy\":\"uncertainty sampling\",\"class_list\":[\"team_a\",\"team_b\"]}"
```


### GET /activelearning/{al_instance_id}/next

**Description:** Retrieves the indices of the next most informative tickets from the unlabeled pool for human annotation, based on the selected query strategy.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |
| `batch_size` | query | integer | No (Default: 1) | Number of ticket indices to return |

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "query_idx": ["R-544314", "R-544315", "R-544316"]
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/activelearning/1/next?batch_size=3"
```


### PUT /activelearning/{al_instance_id}/label

**Description:** Submits human-assigned labels for specific tickets and seamlessly triggers a background model retraining round with the newly augmented dataset.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |

**Request Body (`application/json`):**
| Field | Type | Required | Description |
|---|---|---|---|
| `query_idx` | array | **Yes** | List of ticket indices being labeled |
| `labels` | array | **Yes** | Parallel list of assigned labels |

**Swagger-style UI Example:**
*Request Payload*
```json
{
  "query_idx": ["R-544314", "R-544315"],
  "labels": ["team_a", "team_b"]
}
```
*HTTP 200 OK*
```json
{
  "message": "Labels updated"
}
```

**cURL Example:**
```bash
curl -X PUT "http://localhost:8000/activelearning/1/label" \
	-H "Content-Type: application/json" \
	-d "{\"query_idx\":[\"R-544314\",\"R-544315\"],\"labels\":[\"team_a\",\"team_b\"]}"
```


### POST /activelearning/{al_instance_id}/label-with-info

**Description:** Submits human-assigned labels together with metadata such as review duration and model prediction. The API logs one event per labeled ticket (with a generated `meta_block` and `ticket_ref`), persists the decision metadata into `label_decisions`, and triggers benchmark exports when needed. The reviewer's `username` is automatically captured from the JWT token.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |

**Request Body (`application/json`):**
Array of `label_info` objects.
| Field | Type | Required | Description |
|---|---|---|---|
| `ticket_id` | string | **Yes** | Ticket reference being labeled |
| `label` | string | **Yes** | Human-assigned label |
| `model_prediction` | string or null | No | Model prediction shown to the reviewer |
| `start_time` | string (date-time) | **Yes** | RFC3339 timestamp when review started |
| `end_time` | string (date-time) | **Yes** | RFC3339 timestamp when review ended |
| `most_helpful_feature` | string or null | No | One of: `"lime"`, `"predicted_class_neighbors"`, `"historical_neighbors"`, `"model_prediction"` |

The stored `label_decisions` row is updated in stages and keeps the latest non-null values for `label`, `labeled_at`, `model_prediction`, `latency_ms`, and `most_helpful_feature`.

**Swagger-style UI Example:**
*Request Payload*
```json
[
  {
    "ticket_id": "R-544314",
    "label": "team_a",
    "model_prediction": "team_a",
    "start_time": "2026-05-20T10:00:00Z",
    "end_time": "2026-05-20T10:00:03Z",
    "most_helpful_feature": "lime"
  },
  {
    "ticket_id": "R-544315",
    "label": "team_b",
    "model_prediction": "team_a",
    "start_time": "2026-05-20T10:01:00Z",
    "end_time": "2026-05-20T10:01:04Z"
  }
]
```
*HTTP 200 OK*
```json
{
  "message": "Labels updated"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/activelearning/1/label-with-info" \
	-H "Content-Type: application/json" \
	-d "[{\"ticket_id\":\"R-544314\",\"label\":\"team_a\",\"model_prediction\":\"team_a\",\"start_time\":\"2026-05-20T10:00:00Z\",\"end_time\":\"2026-05-20T10:00:03Z\"}]"
```
### GET /activelearning/{al_instance_id}/info

**Description:** Returns the performance metrics tracking table (entropies, F1 scores, and query progression) for a given instance.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |

**Swagger-style UI Example:**

*HTTP 200 OK*
```json
{
  "mean_entropies": [0.91, 0.73],
  "f1_scores": [0.42, 0.58],
  "num_labeled": [25, 50]
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/activelearning/1/info"
```


### GET /activelearning/{al_instance_id}/export

**Description:** Exports all DuckDB-stored data for an AL instance as a downloadable ZIP of JSON files, suitable for offline analysis of labeling statistics. The response is a binary `application/zip` download.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |

**Authorization:** Requires the authenticated user to be the instance owner or a delegate (404 if the instance does not exist, 403 if not authorized).

**Response:** `application/zip` file download named `export_al_<id>_<timestamp>.zip`.

**ZIP layout:**
```
manifest.json                         # { schema_version, al_instance_id, exported_at, tables: {<name>: row_count} }
duckdb/
  al_instances.json                   # instance row (filtered by al_instance_id)
  labels.json                         # raw label rows for the instance (no majority merge)
  ground_truth_labels.json            # raw label rows for instance 0 (ground truth)
  label_decisions.json                # label decisions incl. xai_result, similar_tickets
  metrics.json                        # f1, mean_entropy, num_labeled per iteration
  model_paths.json                    # local model artifact paths
  al_events.json                      # all events incl. deserialized payload
  xai_jobs.json                       # XAI job rows
  instance_delegations.json           # delegate grants
  tickets.json                        # ALL tickets in the DB (global, both splits)
  users.json                          # users involved with the instance; password is null
```

Each `duckdb/*.json` is a JSON array of row objects. JSON columns (`al_events.payload`, `label_decisions.xai_result`, `label_decisions.similar_tickets`) are deserialized into nested objects; `al_instances.classes` and `xai_jobs.request_raw_tickets_locations`/`result_file_names` are JSON arrays. Datetimes are ISO strings.

**Notes:**
- Only DuckDB data is exported; MinIO binary artifacts (models, encoders, vectorized tickets) are not included.
- `labels.json` is filtered strictly to the requested instance; ground-truth labels from instance 0 are provided separately as `ground_truth_labels.json`. The two are not merged in the export.
- The `users.password` column is always `null` in the export.

**Swagger-style UI Example:**

*HTTP 200 OK (binary, saved to file)*
```
manifest.json         al_instances.json  ground_truth_labels.json  ...
duckdb/...
```

**cURL Example:**
```bash
curl "http://localhost:8000/activelearning/1/export" \
  -H "Authorization: Bearer <your-jwt>" \
  -o export_al_1.zip
```



### POST /activelearning/{al_instance_id}/save

**Description:** Forces serialization and saving of the current active learning model architecture into persistent storage.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "model_id": 1
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/activelearning/1/save"
```


### GET /activelearning/instances

**Description:** Lists all currently active instances tracked in the backend state memory.

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "instances": {
    "1": {
      "model": "LogisticRegression",
      "model_name": "logreg",
      "qs": "uncertainty sampling",
      "classes": [0, 1, 2]
    }
  }
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/activelearning/instances"
```


### DELETE /activelearning/{al_instance_id}

**Description:** Purges an active learning instance from backend tracking memory, terminating its operations.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "message": "Instance deleted"
}
```

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8000/activelearning/1"
```





## Configuration

### GET /config/models

**Description:** Polls the application for all dynamically supported machine learning classification algorithms.

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "models": ["random forest", "logistic regression", "svm"]
}
```


### GET /config/query-strategies

**Description:** Polls the application for all supported active learning querying strategies (heuristics).

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "strategies": [
    "random sampling", 
    "uncertainty sampling entropy", 
    "uncertainty sampling least confidence"
  ]
}
```


### GET /config/capabilities

**Description:** Polls the application for the set of optional capabilities currently enabled (for example, asynchronous XAI when RabbitMQ is configured).

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "capabilities": ["xai"]
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/config/capabilities"
```


## Data

### POST /data/tickets

**Description:** Fetches complete structural records (containing titles, descriptions, categories) matching a specific list of ticket index references.

**Request Body (`application/json`):**
Array of string ticket references, e.g. `["R-544314","R-544315"]`.

**Swagger-style UI Example:**
*Request Payload*
```json
[
  "R-544314",
  "R-544315"
]
```
*HTTP 200 OK*
```json
{
  "tickets": [
    {
      "Ref": "R-544314",
      "Title_anon": "VPN not working",
      "Description_anon": "Cannot connect to VPN",
      "Service->Name": "Network",
      "Service subcategory->Name": "VPN",
      "Team->Name": "Team A"
    }
  ]
}
```


### GET /data/teams

**Description:** Returns a deduplicated index of all valid dispatch teams existing in the configuration.

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "teams": ["Team A", "Team B"]
}
```


### GET /data/categories

**Description:** Returns a deduplicated index of all valid parent service categories available in the dataset.

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "categories": ["Network", "Antivirus"]
}
```


### GET /data/subcategories

**Description:** Returns a deduplicated index of all nested service subcategories belonging to parent areas in the dataset.

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "subcategories": ["Absence is missing in the current month.", "VPN routing"]
}
```


## XAI (Explainable AI)

### POST /xai/{al_instance_id}/explain_lime

**Description:** Calculates token-by-token (LIME) feature attribution for the top-k predicted classes of each ticket.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |
| `model_id` | query | integer | No (Default: 0) | Version ID of the persisted model |
| `top_k` | query | integer | No (Default: 1) | Number of top predicted classes to explain |
| `query_idx` | query | array | No | Pass multiple ticket indices (e.g. `?query_idx=A&query_idx=B`) |

**Request Body (`application/json`):**
Accepts a single `Data` structure representing ticket text. Provide **exactly one** of `ticket_data` (body) or `query_idx` (query parameter).

**Response Shape:**
```json
[
  [
    {
      "class": "Team A",
      "top_words": [
        ["vpn", 0.42],
        ["connect", 0.18]
      ],
      "error": null
    },
    {
      "class": "Team B",
      "top_words": [
        ["network", 0.12]
      ],
      "error": null
    }
  ]
]
```

**Persistence Behavior:**
- When `query_idx` is provided, each `query_idx` value is used as the ticket ref. **One `lime` event is logged per ticket** to `al_events` (`action="lime"`, `actor_type="ai"`, `agent="xai_lime"`, `object_id=<ref>`, `payload={"ticket_id": <ref>, "top_features": [...], "error": <str|null>}`), and the result is upserted into `label_decisions.xai_result` keyed by `(al_instance_id, ref)`.
- When `ticket_data` is provided, there is no ref. **No events are logged** and nothing is persisted to `label_decisions`.

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/xai/1/explain_lime?top_k=2" \
	-H "Content-Type: application/json" \
	-d "{\"title_anon\":\"VPN not working\",\"description_anon\":\"Cannot connect to VPN\"}"
```


### POST /xai/{al_instance_id}/nearest_ticket

**Description:** Recommends the structurally contextual "nearest neighbors" in embedding-space from the known historical dataset. When a ticket reference is available, the returned neighbor list is also persisted into `label_decisions.similar_tickets` with `title` and `description` retained for display, but with recursive `xai_result` and `similar_tickets` content stripped to avoid duplication and bloat.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |
| `model_id` | query | integer | No (Default: 0) | Version ID of the persisted model |
| `query_idx` | query | array | No | Ticket identifier arrays |

**Swagger-style UI Example:**
*HTTP 200 OK*
```json
{
  "nearest_ticket_ref": ["R-544310", "R-544311"],
  "nearest_ticket_label": ["team_a", "team_b"],
  "similarity_score": [0.91, 0.87]
}
```


## Asynchronous XAI (RabbitMQ)

### POST /xai/{al_instance_id}/requests

**Description:** Enqueues heavy, computationally intense XAI generation scripts backwards to job workers via message queues, issuing a tracked receipt ID safely.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |
| `model_id` | query | integer | No (Default: 0) | Version ID of the persisted model |
| `ticket_ref` | query | string | No | Tracking ID to assign metadata |

**Request Body (`application/json`):**
Accepts a single `Data` ticket representation chunk.

**Swagger-style UI Example:**
*Request Payload*
```json
{
  "title_anon": "VPN not working"
}
```
*HTTP 200 OK*
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```


### GET /xai/jobs/{job_id}

**Description:** Interrogates the RabbitMQ backend for the real-time processing status of a dispatched XAI calculation item and collects the payload if complete. When the job is completed, the returned XAI result is also persisted into `label_decisions.xai_result`.

**Parameters:**
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `job_id` | path | string (UUID) | **Yes** | Assigned job ticket ID from the queue |

**Swagger-style UI Example:**
*HTTP 200 OK (Pending)*
```json
{
  "status": "pending"
}
```
*HTTP 200 OK (Completed)*
```json
{
  "status": "completed",
  "result": {
    "top_words": [["vpn", 0.42]],
    "error": null
  },
  "result_location": "xai_results/job-id.json"
}
```

---

## Instance Delegation

### POST /activelearning/{al_instance_id}/delegate

**Description:**  
Delegates an AL instance to another user, granting them full access (label, infer, XAI, save, delete). Only the instance owner can delegate access.

**Parameters:**

| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance to delegate |

**Request Body (`application/json`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `username` | string | **Yes** | Username of the user to grant access to |

**Swagger-style UI Example:**

*Request Payload*
```json
{
  "username": "bob"
}
```
*HTTP 200 OK*
```json
{
  "username": "bob",
  "delegate_user_id": "123e4567-e89b-12d3-a456-426614174000",
  "granted_by": "987fcdeb-51a2-43d7-9012-3456789abcde",
  "granted_at": "2026-06-15T10:30:00"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/activelearning/1/delegate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "bob"}'
```

### DELETE /activelearning/{al_instance_id}/delegate/{username}

**Description:**  
Revokes a user's delegated access to an AL instance. Only the instance owner can revoke delegation.

**Parameters:**

| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |
| `username` | path | string | **Yes** | Username of the user to revoke access from |

**Swagger-style UI Example:**

*HTTP 200 OK*
```json
{
  "message": "Delegation revoked for user 'bob'"
}
```

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8000/activelearning/1/delegate/bob" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### GET /activelearning/{al_instance_id}/delegates

**Description:**  
Lists all users who have been delegated access to an instance. Only the instance owner can view the delegate list.

**Parameters:**

| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `al_instance_id` | path | integer | **Yes** | The ID of the active learning instance |

**Swagger-style UI Example:**

*HTTP 200 OK*
```json
{
  "delegates": [
    {
      "username": "bob",
      "delegate_user_id": "123e4567-e89b-12d3-a456-426614174000",
      "granted_by": "987fcdeb-51a2-43d7-9012-3456789abcde",
      "granted_at": "2026-06-15T10:30:00"
    },
    {
      "username": "charlie",
      "delegate_user_id": "456e7890-e89b-12d3-a456-426614174001",
      "granted_by": "987fcdeb-51a2-43d7-9012-3456789abcde",
      "granted_at": "2026-06-15T11:00:00"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/activelearning/1/delegates" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```