# HumAL API

Base URL (local): `http://localhost:8000`

All endpoints accept and return JSON unless noted. Path and query parameters are listed per endpoint.

## Inference

### POST /activelearning/{al_instance_id}/infer

- Method: POST
- Path params: `al_instance_id` (integer)
- Request body format: Single `Data` object or an array of `Data` objects. A `Data` object contains:
	- `service_subcategory_name` (string, optional)
	- `team_name` (string, optional)
	- `service_name` (string, optional)
	- `last_team_id_name` (string, optional)
	- `title_anon` (string, optional)
	- `description_anon` (string, optional)
	- `public_log_anon` (string, optional)

Example request (single):
```bash
curl -X POST "http://localhost:8000/activelearning/1/infer" \
	-H "Content-Type: application/json" \
	-d "{\"title_anon\":\"VPN not working\",\"description_anon\":\"Cannot connect to VPN from home\"}"
```

Example request (batch):
```bash
curl -X POST "http://localhost:8000/activelearning/1/infer" \
	-H "Content-Type: application/json" \
	-d "[{\"title_anon\":\"VPN not working\"}, {\"title_anon\":\"Email issue\"}]"
```

Example response:
```json
["(GI-UX) Network Access", "Email Support Team"]
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
{"models": ["random forest", "logistic regression", "svm"]}
```

### GET /config/query-strategies

- Method: GET

Example request:
```bash
curl "http://localhost:8000/config/query-strategies"
```

Example response:
```json
{"strategies": ["random sampling", "uncertainty sampling entropy", "uncertainty sampling margin sampling", "uncertainty sampling least confidence", "CLUE"]}
```

## Data

### POST /data/tickets

- Method: POST
- Request body format: array of ticket indices (strings)

Example request:
```bash
curl -X POST "http://localhost:8000/data/tickets" \
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

### GET /data/teams

- Method: GET

Example request:
```bash
curl "http://localhost:8000/data/teams"
```

Example response:
```json
{"teams": ["Team A", "Team B"]}
```

### GET /data/categories

- Method: GET

Example request:
```bash
curl "http://localhost:8000/data/categories"
```

Example response:
```json
{"categories": ["Network", "Antivirus"]}
```

### GET /data/subcategories

- Method: GET

Example request:
```bash
curl "http://localhost:8000/data/subcategories"
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

## Asynchronous XAI (RabbitMQ Required)

### POST /xai/{al_instance_id}/requests

- Method: POST
- Path params: `al_instance_id` (integer)
- Query params:
	- `model_id` (integer, optional, default: 0)
	- `ticket_ref` (string, optional)
- Request body format: Data object

Example request:
```bash
curl -X POST "http://localhost:8000/xai/1/requests?model_id=0&ticket_ref=R-544314" \
	-H "Content-Type: application/json" \
	-d "{\"title_anon\":\"VPN not working\",\"description_anon\":\"Cannot connect to VPN\"}"
```

Example response:
```json
{
	"job_id": "550e8400-e29b-41d4-a716-446655440000",
	"status": "pending",
	"ticket_ref": "R-544314"
}
```

### GET /xai/jobs/{job_id}

- Method: GET
- Path params: `job_id` (string, UUID format)

Example request:
```bash
curl "http://localhost:8000/xai/jobs/550e8400-e29b-41d4-a716-446655440000"
```

Example response (pending):
```json
{
	"job_id": "550e8400-e29b-41d4-a716-446655440000",
	"status": "pending"
}
```

Example response (completed):
```json
{
	"job_id": "550e8400-e29b-41d4-a716-446655440000",
	"status": "completed",
	"result": {
		"top_words": [["vpn", 0.42], ["connect", 0.18]],
		"error": null
	}
}
```


