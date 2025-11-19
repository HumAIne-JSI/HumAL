# HumAL API Documentation

## Overview

REST API for human-in-the-loop active learning workflows, ticket classification, and automated resolution generation.

**Base URL**: `http://localhost:8000`  
**Interactive Documentation**: `http://localhost:8000/docs`  
**Alternative Docs**: `http://localhost:8000/redoc`

## Authentication

Currently no authentication required for local development.

---

## API Endpoints

### Active Learning

#### Create New Active Learning Instance
```http
POST /activelearning/new
```

Create a new active learning instance with specified configuration.

**Request Body:**
```json
{
  "model_name": "string",
  "qs_strategy": "string",
  "class_list": ["team_a", "team_b", "team_c"],
  "train_data_path": "string",
  "test_data_path": "string",
  "al_type": "dispatch"
}
```

**Fields:**
- `model_name` (string): Name of the ML model to use
- `qs_strategy` (string): Query strategy for active learning
- `class_list` (array): List of possible class labels (teams)
- `train_data_path` (string): Path to training data CSV
- `test_data_path` (string): Path to test data CSV
- `al_type` (string): Type of active learning - either "dispatch" or "resolution"

**Response:**
```json
{
  "instance_id": 1
}
```

---

#### Get Next Unlabeled Instances
```http
GET /activelearning/{al_instance_id}/next?batch_size=1
```

Retrieve the next batch of unlabeled instances based on the query strategy.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID

**Query Parameters:**
- `batch_size` (integer, optional): Number of instances to retrieve (default: 1)

**Response:**
```json
{
  "query_idx": ["idx1", "idx2"]
}
```

---

#### Submit Labels
```http
PUT /activelearning/{al_instance_id}/label
```

Submit labels for instances and trigger model retraining.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID

**Request Body:**
```json
{
  "query_idx": ["idx1", "idx2"],
  "labels": ["team_a", "team_b"]
}
```

**Response:**
```json
{
  "message": "Labels updated"
}
```

---

#### Run Inference
```http
POST /activelearning/{al_instance_id}/infer
```

Run model inference on new ticket data.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID

**Request Body:**
```json
{
  "description_anon": "Cannot access email on mobile device",
  "title_anon": "Email access issue",
  "service_subcategory_name": "Email Support",
  "service_name": "IT Services",
  "team_name": "Support Team",
  "last_team_id_name": "Level 1 Support",
  "public_log_anon": "User reported issue with email access"
}
```

**Note:** All fields in the request body are optional. Only provide the fields that are available.

**Response:**
```json
[
  "mobile_support"
]
```

**Note:** The response is a list of predicted team labels (one prediction per input).

---

#### Get Instance Info
```http
GET /activelearning/{al_instance_id}/info
```

Get information about an active learning instance including metrics and training history.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID

**Response:**
```json
{
  "mean_entropies": [0.67, 0.58, 0.51],
  "f1_scores": [0.42, 0.55, 0.61],
  "num_labeled": [10, 20, 30]
}
```

---

#### Save Model
```http
POST /activelearning/{al_instance_id}/save
```

Save the trained model to disk and get a model ID for future reference.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID

**Response:**
```json
{
  "model_id": 3
}
```

---

#### Get All Instances
```http
GET /activelearning/instances
```

Get information about all active learning instances.

**Response:**
```json
{
  "instances": {
    "1": {
      "model_name": "logistic regression",
      "qs": "uncertainty sampling least confidence",
      "classes": [0, 1, 2, 3],
      "al_type": "dispatch"
    },
    "2": {
      "model_name": "random forest",
      "qs": "CLUE",
      "classes": [0, 1, 2],
      "al_type": "resolution"
    }
  }
}
```

---

#### Delete Instance
```http
DELETE /activelearning/{al_instance_id}
```

Delete an active learning instance and clean up associated resources.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID

**Response:**
```json
{
  "message": "Instance deleted"
}
```

---

### Resolution Generation

#### Generate Ticket Resolution
```http
POST /resolution/process
```

Generate automated first-reply response for IT support ticket using RAG + GPT.

**Request Body:**
```json
{
  "ticket_title": "VPN Connection Issue",
  "ticket_description": "User cannot connect to VPN from home",
  "service_category": "Network Services",
  "service_subcategory": "VPN Access",
  "top_k": 5,
  "force_rebuild": false
}
```

**Fields:**
- `ticket_title` (string, optional): Title of the ticket
- `ticket_description` (string, optional): Description of the ticket
- `service_category` (string, optional): Service category if available
- `service_subcategory` (string, optional): Service subcategory if available
- `top_k` (integer, optional): Number of similar tickets to retrieve (1-20, default: 5)
- `force_rebuild` (boolean, optional): Force rebuild of embeddings cache (default: false)

**Note:** At least one of `ticket_title` or `ticket_description` must be provided.

**Response:**
```json
{
  "classification": "vpn_request",
  "predicted_team": "Network Support",
  "team_confidence": 0.88,
  "response": "To resolve your VPN connection issue, please try the following steps:\n1. Check your internet connection...",
  "similar_replies": [
    {
      "ticket_ref": "TKT-1234",
      "similarity": 0.95,
      "title": "VPN not connecting",
      "description": "Cannot establish VPN connection",
      "response": "Previous resolution text..."
    }
  ],
  "retrieval_k": 5
}
```

---

#### Submit Resolution Feedback
```http
POST /resolution/feedback
```

Save user-approved/edited ticket resolution for continuous improvement. Adds the ticket to the knowledge base and updates embeddings incrementally.

**Request Body:**
```json
{
  "ticket_title": "VPN Connection Issue",
  "ticket_description": "User cannot connect to VPN from home",
  "edited_response": "To resolve your VPN connection issue:\n1. Verify your internet connection\n2. Check VPN credentials...",
  "predicted_team": "Network Support",
  "predicted_classification": "vpn_request",
  "service_name": "Network Services",
  "service_subcategory": "VPN Access"
}
```

**Fields:**
- `ticket_title` (string, required): Original ticket title
- `ticket_description` (string, required): Original ticket description
- `edited_response` (string, required): User-approved/edited response
- `predicted_team` (string, optional): Team assignment
- `predicted_classification` (string, optional): Ticket type classification
- `service_name` (string, optional): Service category
- `service_subcategory` (string, optional): Service subcategory

**Response:**
```json
{
  "success": true,
  "message": "Ticket saved successfully and embedding added to index",
  "ticket_ref": "TKT-2024-001",
  "new_kb_size": 1501,
  "embedding_added_incrementally": true,
  "embedding_invalidated": false
}
```

---

#### Rebuild Embeddings
```http
POST /resolution/rebuild-embeddings
```

Force full rebuild of embeddings cache from the knowledge base. This is a slow operation; prefer using `/feedback` endpoint which updates incrementally.

**Request Body:** None required

**Response:**
```json
{
  "rebuilt": true,
  "records": 1500,
  "embedding_dim": 384,
  "cache_file": "embeddings_cache/User_Request_last_team_ANON.csv_all-MiniLM-L6-v2_1762270175.npz",
  "cache_saved": true
}
```

---

### Data Management

#### Get Tickets by Indices
```http
POST /data/{al_instance_id}/tickets
```

Retrieve specific tickets by their indices.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID (use 0 for custom path)

**Request Parameters:**
- `indices` (array of strings, required): List of ticket reference IDs to retrieve
- `train_data_path` (string, optional): Path to training data CSV (required if al_instance_id is 0)

**Request Body:**
```json
{
  "indices": ["idx1", "idx2", "idx3"],
  "train_data_path": "backend/data/custom_data.csv"
}
```

**Note:** The `indices` and `train_data_path` are sent as function parameters, not wrapped in a JSON object.

**Response:**
```json
{
  "tickets": [
    {
      "Ref": "idx1",
      "Description_anon": "Laptop won't turn on",
      "Team->Name": "hardware_support",
      ...
    }
  ]
}
```

---

#### Get Available Teams
```http
GET /data/{al_instance_id}/teams?train_data_path=path/to/data.csv
```

Get list of available teams from the dataset.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID (use 0 for custom path)

**Query Parameters:**
- `train_data_path` (string, optional): Path to training data (required if al_instance_id is 0)

**Response:**
```json
{
  "teams": ["mobile_support", "email_team", "network_team", "hardware_support"]
}
```

---

#### Get Available Categories
```http
GET /data/{al_instance_id}/categories?train_data_path=path/to/data.csv
```

Get list of available service categories from the dataset.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID (use 0 for custom path)

**Query Parameters:**
- `train_data_path` (string, optional): Path to training data (required if al_instance_id is 0)

**Response:**
```json
{
  "categories": ["IT Services", "Network Services", "Hardware Support"]
}
```

---

#### Get Available Subcategories
```http
GET /data/{al_instance_id}/subcategories?train_data_path=path/to/data.csv
```

Get list of available service subcategories from the dataset.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID (use 0 for custom path)

**Query Parameters:**
- `train_data_path` (string, optional): Path to training data (required if al_instance_id is 0)

**Response:**
```json
{
  "subcategories": ["Email Support", "VPN Access", "Desktop Support"]
}
```

---

### Configuration

#### Get Available Models
```http
GET /config/models
```

List all available machine learning models.

**Response:**
```json
{
  "models": [
    "LogisticRegression",
    "RandomForest",
    "SVM"
  ]
}
```

---

#### Get Query Strategies
```http
GET /config/query-strategies
```

List all available active learning query strategies.

**Response:**
```json
{
  "strategies": [
    "UncertaintySampling",
    "MarginSampling",
    "EntropySampling",
    "RandomSampling",
    "QueryByCommittee"
  ]
}
```

---

### Explainable AI (XAI)

#### Get LIME Explanation
```http
POST /xai/{al_instance_id}/explain_lime
```

Get LIME-based explanation for model predictions.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID

**Query Parameters:**
- `query_idx` (array of strings, optional): Ticket reference IDs to explain (mutually exclusive with ticket_data)
- `model_id` (integer, optional): Model version (default: 0)

**Request Body (Option 1 - New Ticket Data):**
```json
{
  "ticket_data": {
    "title_anon": "Email access issue",
    "description_anon": "Email not syncing on iPhone",
    "service_name": "IT Services",
    "service_subcategory_name": "Email Support",
    "team_name": "Support Team",
    "last_team_id_name": "Level 1 Support",
    "public_log_anon": "User reported issue"
  }
}
```

**Request Body (Option 2 - Existing Ticket by Index):**
Use `query_idx` query parameter instead of body. Example: `?query_idx=idx1&query_idx=idx2`

**Note:** Provide exactly one of `ticket_data` (in body) or `query_idx` (as query parameter), not both.

**Response:**
```json
[
  {
    "top_words": [
      ["iPhone", 0.45],
      ["email", 0.32],
      ["syncing", 0.18],
      ["mobile", 0.12]
    ],
    "error": null
  }
]
```

---

#### Find Nearest Similar Tickets
```http
POST /xai/{al_instance_id}/nearest_ticket
```

Find most similar tickets in the training set using embeddings.

**Path Parameters:**
- `al_instance_id` (integer): Active learning instance ID

**Query Parameters:**
- `query_idx` (array of strings, optional): Ticket reference IDs to find nearest neighbors for (mutually exclusive with ticket_data)
- `model_id` (integer, optional): Model version (default: 0)

**Request Body (Option 1 - New Ticket Data):**
```json
{
  "ticket_data": {
    "title_anon": "Shared drive access issue",
    "description_anon": "Cannot access shared drive",
    "service_name": "IT Services",
    "service_subcategory_name": "Network Services"
  }
}
```

**Request Body (Option 2 - Existing Ticket by Index):**
Use `query_idx` query parameter instead of body. Example: `?query_idx=idx1&query_idx=idx2`

**Note:** Provide exactly one of `ticket_data` (in body) or `query_idx` (as query parameter), not both.

**Response (when using ticket_data):**
```json
{
  "nearest_ticket_ref": "TKT-789",
  "nearest_ticket_label": "network_team",
  "similarity_score": 0.94
}
```

**Response (when using query_idx with multiple indices):**
```json
{
  "nearest_ticket_ref": ["TKT-789", "TKT-456"],
  "nearest_ticket_label": ["network_team", "network_team"],
  "similarity_score": [0.94, 0.89]
}
```

---

## CORS Configuration

The API accepts requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (Alternative React port)
- `http://127.0.0.1:5173`

---

## Examples

### Active Learning (short)

```bash
# 1) Create a new AL instance (uses demo CSVs)
curl -X POST http://localhost:8000/activelearning/new \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "svm",
    "qs_strategy": "uncertainty sampling least confidence",
    "class_list": ["team_a", "team_b", "team_c"],
    "train_data_path": "data/al_demo_train_data.csv",
    "test_data_path": "data/al_demo_test_data.csv",
    "al_type": "dispatch"
  }'

# 2) Get next unlabeled instance(s)
curl -X GET "http://localhost:8000/activelearning/1/next?batch_size=1"

# 3) Submit labels for the returned indices
curl -X PUT http://localhost:8000/activelearning/1/label \
  -H "Content-Type: application/json" \
  -d '{
    "query_idx": ["IDX_FROM_STEP_2"],
    "labels": ["team_a"]
  }'

# 4) Check metrics/history
curl -X GET http://localhost:8000/activelearning/1/info

# 5) Run inference with a new ticket
curl -X POST http://localhost:8000/activelearning/1/infer \
  -H "Content-Type: application/json" \
  -d '{"title_anon": "Email access issue", "description_anon": "Cannot access email on mobile device"}'
```

### Resolution (short)

```bash
# 1) Generate a first-reply for a ticket
curl -X POST http://localhost:8000/resolution/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_title": "Cannot access VPN",
    "ticket_description": "Getting connection timeout error when connecting to VPN",
    "service_category": "Network",
    "service_subcategory": "VPN",
    "top_k": 3
  }'

# 2) Save feedback (adds single embedding incrementally)
curl -X POST http://localhost:8000/resolution/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_title": "Password reset needed",
    "ticket_description": "User needs password reset for their account",
    "edited_response": "Hello! I'\''ve reset your password. Please check your email.",
    "predicted_team": "IT Support",
    "predicted_classification": "password_reset",
    "service_name": "Account Management",
    "service_subcategory": "Password"
  }'
```

---


## API Versioning

Current version: `v1.0.0`  
No versioning prefix in URLs for initial release.

