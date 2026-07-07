# HumAL Development Setup

This guide will help you set up the HumAL application for development.

## Project Structure

```
HumAL/
├── backend/              
|   ├── app/              # FastAPI application
│   ├── data/             # CSV datasets (place your data here)
│   └── models/           # Saved models (joblib .pkl)
├── docs/                 # Documentation
├── tests/                # Test suite
├── requirements.txt      # Backend dependencies
├── install.py           # Automated dependency installer
└── .env                 # Environment configuration (create from .env.example)
```

## Prerequisites

- **Python 3.8+** (for backend)
- **uv** or **pip** (for Python package management)
- **CUDA Toolkit** (optional, for GPU acceleration - will be auto-detected)

### Installing uv (Optional but Recommended)

The automated installer (`install.py`) can use either `uv` or `pip`. Using `uv` is recommended for faster package installation.

**Windows:**
```bash
# Using the standalone installer (recommended)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

## Installation & Setup

Choose one of the following installation methods. This is a one-time setup process.

### Option 1: Automated Installation (Recommended)

The automated installer detects your system configuration (CUDA version, package manager) and installs all backend dependencies with the appropriate PyTorch version.

1. Ensure you're in the project root (contains `install.py` and `requirements.txt`).

2. Create and activate virtual environment:
   ```bash
   # Create virtual environment with uv (recommended)
   uv venv al_api_venv
   
   # Or with Python's built-in venv
   python -m venv al_api_venv
   
   # Activate (Windows)
   al_api_venv\Scripts\activate
   ```

3. Run the automated installer (from project root):
   ```bash
   # Basic installation (auto-detects CUDA and package manager)
   python install.py
   
   # Force CPU-only installation
   python install.py --cpu-only
   
   # Force use of pip instead of uv
   python install.py --use-pip
   
   # Only reinstall PyTorch (useful for switching between CPU/CUDA)
   python install.py --reinstall-torch
   ```

   The installer will:
   - ✓ Auto-detect CUDA and install PyTorch with GPU support (if available)
   - ✓ Install all dependencies from requirements.txt
   - ✓ Verify the installation and display GPU/CPU status

4. Download the SpaCy model used by `/xai/{al_instance_id}/nearest` if it is not already present:
   ```bash
   python -m spacy download en_core_web_sm
   ```

   If you use a different model name, set `SPACY_MODEL_NAME` to match the model you installed.

5. Prepare data and models (required before using the app):
   ```bash
   # Windows PowerShell
   mkdir backend\data
   mkdir backend\models
   ```

  - Place CSV data files in `backend/data/`.
    - Active Learning datasets: `al_demo_train_data.csv`, `al_demo_test_data.csv`, `al_demo_train_labels_dispatch.csv`
   - Place pre-trained team classification and ticket type classification models in `backend/models/`.
      - `perfect_team_classifier/` folder
      - `ticket_classifier_model/` folder

6. Configure environment variables:
   ```bash
   # Copy .env.example to .env (if .env.example exists)
   # Windows PowerShell
   copy .env.example .env
   ```

### Option 2: Manual Installation

1. Ensure you're in the project root.

2. Create and activate virtual environment:
   ```bash
   # Create virtual environment
   uv venv al_api_venv
   
   # Activate (Windows)
   al_api_venv\Scripts\activate
   ```

3. Install backend dependencies:
   ```bash
   # With uv (recommended)
   uv pip install -r requirements.txt
   
   # Or with pip
   pip install -r requirements.txt
   ```

4. Install PyTorch (choose appropriate version):
   ```bash
   # CPU-only version
   pip install torch
   
   # CUDA version (check PyTorch website for your CUDA version)
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```

  - Place CSV data files in `backend/data/`.
    - Active Learning datasets: `al_demo_train_data.csv`, `al_demo_test_data.csv`, `al_demo_train_labels_dispatch.csv`
   - Place pre-trained team classification and ticket type classification models in `backend/models/`.
      - `perfect_team_classifier/` folder
      - `ticket_classifier_model/` folder

## Running the Application

After completing installation, choose one of the following methods to run the application.

### Option 1: Using Startup Scripts (Recommended)

**Prerequisites:** Complete installation (Option 1 or Option 2) at least once before using startup scripts.

Before starting, ensure:
- `backend/data/` and `backend/models/` exist and are populated

**Windows:**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Manual Startup

**Prerequisites:** Complete installation (Option 1 or Option 2) at least once.

#### Backend

1. Activate virtual environment:
   ```bash
   # Windows
   al_api_venv\Scripts\activate
   ```

2. Navigate to the backend directory:
   ```bash
   cd backend
   ```

3. Start the backend server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Access Points

After starting the backend:

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Schema Changes

The DuckDB schema is versioned. To make a schema change:

1. Edit the `CREATE TABLE` / `CREATE INDEX` statements in
   `backend/app/persistence/duckdb/schema.py`.
2. Increment the `SCHEMA_VERSION` constant at the top of that file.
3. Restart the backend — `init_database()` detects the version mismatch,
   drops all tables, and recreates them. **No data is preserved** (the DB is
   a metadata cache rebuildable from MinIO).

No manual DuckDB intervention or migration scripts are needed.

> **Pre-v1 convention.** Before the first public release, additive column
> changes (e.g. extra metric columns on `metrics`) may be made to the
> `CREATE TABLE` block without bumping `SCHEMA_VERSION`. In that case,
> developers with an existing local `backend/storage/db/humal.duckdb`
> must delete that file once so `init_database()` recreates it with the
> new columns.

### Tuning Lock Retry Behavior

The lock retry parameters are module-level constants in
`backend/app/persistence/duckdb/connection.py`:

- `_MAX_LOCK_RETRIES` (default: 10) — number of retry attempts after the
  initial failure.
- `_LOCK_RETRY_BACKOFF_SECONDS` (default: 1.0) — delay between retries.

Maximum wait before giving up: `_MAX_LOCK_RETRIES × _LOCK_RETRY_BACKOFF_SECONDS`
(default: ~10 seconds). Adjust these constants if your environment needs
longer or shorter retry windows.

## Testing

Tests live in `backend/tests/` and are run with `pytest` (no `pytest.ini` /
`pyproject.toml`; pytest defaults apply):

```
cd backend
python -m pytest tests/
```

The shared `backend/tests/conftest.py` performs module-level setup so the app
can be imported and exercised fully offline (no network, no Docker, no
MinIO/RabbitMQ):

- Sets `USE_RABBITMQ=0`, JWT signing vars, and the HuggingFace / Transformers
  offline flags.
- Redirects `DUCKDB_PATH`, `MODELS_DIR` and `ENCODERS_DIR` to a fresh temp
  directory under the OS temp dir (created with `tempfile.mkdtemp`), so
  tests never write into the real `backend/storage/`.
- Patches `app.core.minio_client.MinioClient` with a `MagicMock` so the
  import-time `MinioClient()` singleton never tries to log in.
- Replaces `SentenceTransformer` in `app.services.data_preprocessing`,
  `app.services.inference_svc` and `app.services.xai_svc` with a shared
  `MagicMock` whose `.encode(...)` returns a constant zero matrix of the
  right shape. This keeps the real `dispatch_team` / `inference` /
  `XaiService` code paths running without downloading the
  `all-MiniLM-L6-v2` model.
- Patches `spacy.load` with a `MagicMock`, so `XaiService._get_spacy_nlp`
  does not require the `en_core_web_sm` spacy model.
- Keeps `app.persistence.duckdb.connection.DEFAULT_DB_PATH` in sync with
  `DUCKDB_PATH` so `resolve_db_path(None)` matches the value tests import.

The existing service / persistence / router unit tests continue to work
because they locally override the global mocks (e.g.
`@patch("app.services.inference_svc.SentenceTransformer")` and
`monkeypatch.setattr("app.services.active_learning_svc.dispatch_team", ...)`)
take precedence over the conftest-level replacements.

### End-to-End Offline Test

`backend/tests/test_e2e_offline.py::test_e2e_offline_active_learning_loop`
exercises the real `ActiveLearningService`, `InferenceService` and
`XaiService` through FastAPI's `TestClient` (no live uvicorn, no Docker).
The flow:

1. Registers and logs in a user, capturing the JWT.
2. Creates an AL instance (real `create_instance` → `dispatch_team` →
   train → first `calculate_metrics`).
3. Asserts the async XAI endpoints (`POST /xai/{id}/requests` and
   `GET /xai/jobs/{uuid}`) return `503` with `USE_RABBITMQ=0`.
4. Runs **10 iterations** of
   `next → label-with-info → infer_proba → /xai/nearest → /xai/explain_lime`
   (all with `query_idx` so the real `data_service.get_tickets` /
   `find_nearest_by_idx` / `explain_lime` paths run).
5. Asserts persistence: `metrics` row count grew by 10, `al_events` has 10
   `confirm_label`/`override_label`, 10 `similar_tickets` and 10 `lime`
   rows, `label_decisions.xai_result` (and `similar_tickets`) is populated
   for every labeled ref, `/info` reflects a new iteration
   (`f1_scores` length +10, `num_labeled[-1]` increased), and exactly one
   `benchmark_export` event was logged on the 10th label.

The fixture seeds the temp DuckDB with 65 train tickets (50 labeled,
15 unlabeled — the AL pool) and 10 test tickets, then re-points the three
services' `local_artifacts_store` to fresh `tmp_path` directories so model
artifacts never touch `backend/storage/`. It also patches
`dependencies.startup_service` to a no-op so the FastAPI lifespan does not
pull data from MinIO.

Run it in isolation:

```
cd backend
python -m pytest tests/test_e2e_offline.py -v
```
