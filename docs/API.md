# HumAL API

Base URL (local): `http://localhost:8000`

All endpoints accept and return JSON unless noted. Path and query parameters are listed per endpoint.

## Inference

### POST /activelearning/{al_instance_id}/infer

- Method: POST
- Path params: `al_instance_id` (integer)
- Request body format (Data):
	- `service_subcategory_name` (string, optional)
	- `team_name` (string, optional)
	- `service_name` (string, optional)
	- `last_team_id_name` (string, optional)
	- `title_anon` (string, optional)
	- `description_anon` (string, optional)
	- `public_log_anon` (string, optional)

Example request:
```bash
curl -X POST "http://localhost:8000/activelearning/1/infer" \
	-H "Content-Type: application/json" \
	-d "{\"title_anon\":\"VPN not working\",\"description_anon\":\"Cannot connect to VPN from home\"}"
```

Example response:
```json
["(GI-UX) Network Access"]
```

## Active Learning

### POST /activelearning/new

- Method: POST
- Request body format (NewInstance):
	- `model_name` (string, required)
	- `qs_strategy` (string, required)
	- `class_list` (array of string or integer or null, required)
	- `train_data_path` (string, required)
	- `test_data_path` (string, required)

Example request:
```bash
curl -X POST "http://localhost:8000/activelearning/new" \
	-H "Content-Type: application/json" \
	-d "{\"model_name\":\"svm\",\"qs_strategy\":\"uncertainty sampling\",\"class_list\":[\"team_a\",\"team_b\"],\"train_data_path\":\"backend/data/al_demo_train_data.csv\",\"test_data_path\":\"backend/data/al_demo_test_data.csv\"}"
```

Example response:
```json
{"instance_id": 1}
```

### GET /activelearning/{al_instance_id}/next

- Method: GET
- Path params: `al_instance_id` (integer)
- Query params: `batch_size` (integer, optional, default: 1)

Example request:
```bash
curl "http://localhost:8000/activelearning/1/next?batch_size=3"
```

Example response:
```json
{"query_idx": ["R-544314", "R-544315", "R-544316"]}
```

### PUT /activelearning/{al_instance_id}/label

- Method: PUT
- Path params: `al_instance_id` (integer)
- Request body format (LabelRequest):
	- `query_idx` (array of string or integer, required)
	- `labels` (array of string or integer or null, required)

Example request:
```bash
curl -X PUT "http://localhost:8000/activelearning/1/label" \
	-H "Content-Type: application/json" \
	-d "{\"query_idx\":[\"R-544314\",\"R-544315\"],\"labels\":[\"team_a\",\"team_b\"]}"
```

Example response:
```json
{"message": "Labels updated"}
```

### GET /activelearning/{al_instance_id}/info

- Method: GET
- Path params: `al_instance_id` (integer)

Example request:
```bash
curl "http://localhost:8000/activelearning/1/info"
```

Example response:
```json
{
	"mean_entropies": [0.91, 0.73],
	"f1_scores": [0.42, 0.58],
	"num_labeled": [25, 50]
}
```

### POST /activelearning/{al_instance_id}/save

- Method: POST
- Path params: `al_instance_id` (integer)

Example request:
```bash
curl -X POST "http://localhost:8000/activelearning/1/save"
```

Example response:
```json
{"model_id": 1}
```

### GET /activelearning/instances

- Method: GET

Example request:
```bash
curl "http://localhost:8000/activelearning/instances"
```

Example response:
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

### DELETE /activelearning/{al_instance_id}

- Method: DELETE
- Path params: `al_instance_id` (integer)

Example request:
```bash
curl -X DELETE "http://localhost:8000/activelearning/1"
```

Example response:
```json
{"message": "Instance deleted"}
```

## Configuration

### GET /config/models

- Method: GET

Example request:
```bash
curl "http://localhost:8000/config/models"
```

Example response:
```json
{"models": ["random_forest", "svm", "logistic_regression"]}
```

### GET /config/query-strategies

- Method: GET

Example request:
```bash
curl "http://localhost:8000/config/query-strategies"
```

Example response:
```json
{"strategies": ["random sampling", "uncertainty sampling", "value of information"]}
```

## Data

### POST /data/{al_instance_id}/tickets

- Method: POST
- Path params: `al_instance_id` (integer)
- Query params: `train_data_path` (string, optional; required when `al_instance_id` is 0)
- Request body format: array of ticket indices (strings)

Example request:
```bash
curl -X POST "http://localhost:8000/data/1/tickets" \
	-H "Content-Type: application/json" \
	-d "[\"R-544314\",\"R-544315\"]"
```

Example response:
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

### GET /data/{al_instance_id}/teams

- Method: GET
- Path params: `al_instance_id` (integer)
- Query params: `train_data_path` (string, optional; required when `al_instance_id` is 0)

Example request:
```bash
curl "http://localhost:8000/data/1/teams"
```

Example response:
```json
{"teams": ["Team A", "Team B"]}
```

### GET /data/{al_instance_id}/categories

- Method: GET
- Path params: `al_instance_id` (integer)
- Query params: `train_data_path` (string, optional; required when `al_instance_id` is 0)

Example request:
```bash
curl "http://localhost:8000/data/1/categories"
```

Example response:
```json
{"categories": ["Network", "Antivirus"]}
```

### GET /data/{al_instance_id}/subcategories

- Method: GET
- Path params: `al_instance_id` (integer)
- Query params: `train_data_path` (string, optional; required when `al_instance_id` is 0)

Example request:
```bash
curl "http://localhost:8000/data/1/subcategories"
```

Example response:
```json
{"subcategories": ["Absence is missing in the current month."]}
```

## XAI

### POST /xai/{al_instance_id}/explain_lime

- Method: POST
- Path params: `al_instance_id` (integer)
- Query params:
	- `query_idx` (array of string, optional; use multiple query params)
	- `model_id` (integer, optional, default: 0)
- Request body format: Data object or `null`
- Note: Provide exactly one of `ticket_data` (body) or `query_idx` (query).

Example request (ticket data in body):
```bash
curl -X POST "http://localhost:8000/xai/1/explain_lime" \
	-H "Content-Type: application/json" \
	-d "{\"title_anon\":\"VPN not working\",\"description_anon\":\"Cannot connect to VPN\"}"
```

Example response:
```json
[
	{
		"top_words": [["vpn", 0.42], ["connect", 0.18]],
		"error": null
	}
]
```

### POST /xai/{al_instance_id}/nearest_ticket

- Method: POST
- Path params: `al_instance_id` (integer)
- Query params:
	- `query_idx` (array of string, optional; use multiple query params)
	- `model_id` (integer, optional, default: 0)
- Request body format: Data object or `null`
- Note: Provide exactly one of `ticket_data` (body) or `query_idx` (query).

Example request (by query idx):
```bash
curl -X POST "http://localhost:8000/xai/1/nearest_ticket?query_idx=R-544314&query_idx=R-544315"
```

Example response:
```json
{
	"nearest_ticket_ref": ["R-544310", "R-544311"],
	"nearest_ticket_label": ["team_a", "team_b"],
	"similarity_score": [0.91, 0.87]
}
```

## Resolution

### POST /resolution/process

- Method: POST
- Request body format (ResolutionRequest):
	- `ticket_title` (string, optional)
	- `ticket_description` (string, optional)
	- `service_category` (string, optional)
	- `service_subcategory` (string, optional)
	- `top_k` (integer, optional; default: 3, range: 1-20)
	- `force_rebuild` (boolean, optional; default: false)

Example request:
```bash
curl -X POST "http://localhost:8000/resolution/process" \
	-H "Content-Type: application/json" \
	-d "{\"ticket_title\":\"VPN not working\",\"ticket_description\":\"Cannot connect to VPN\",\"top_k\":3}"
```

Example response:
```json
{
	"classification": "vpn_request",
	"predicted_team": "Network Support",
	"team_confidence": 0.82,
	"response": "Thanks for reporting the VPN issue...",
	"similar_replies": [{"ticket_id": "R-544320", "reply": "..."}],
	"retrieval_k": 3
}
```

### POST /resolution/feedback

- Method: POST
- Request body format (FeedbackRequest):
	- `ticket_title` (string, required)
	- `ticket_description` (string, required)
	- `edited_response` (string, required)
	- `predicted_team` (string, optional)
	- `predicted_classification` (string, optional)
	- `service_name` (string, optional)
	- `service_subcategory` (string, optional)

Example request:
```bash
curl -X POST "http://localhost:8000/resolution/feedback" \
	-H "Content-Type: application/json" \
	-d "{\"ticket_title\":\"VPN not working\",\"ticket_description\":\"Cannot connect to VPN\",\"edited_response\":\"Please try resetting your VPN client...\"}"
```

Example response:
```json
{
	"success": true,
	"message": "Saved",
	"ticket_ref": "R-544321",
	"new_kb_size": 502,
	"embedding_added_incrementally": true,
	"embedding_invalidated": false
}
```

### POST /resolution/rebuild-embeddings

- Method: POST

Example request:
```bash
curl -X POST "http://localhost:8000/resolution/rebuild-embeddings"
```

Example response:
```json
{
	"rebuilt": true,
	"records": 500,
	"embedding_dim": 384,
	"cache_file": "embeddings_cache/kb_1700000000.npz",
	"cache_saved": true
}
```
