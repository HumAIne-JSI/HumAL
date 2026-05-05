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

4. Prepare data and models (required before using the app):
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

5. Configure environment variables:
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

6. Prepare data and models (required before using the app):
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

7. Configure environment variables:
   ```bash
   # Copy .env.example to .env (if .env.example exists)
   # Windows PowerShell
   copy .env.example .env
   ```

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
