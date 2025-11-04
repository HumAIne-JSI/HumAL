# HumAL Development Setup

This guide will help you set up the HumAL application for development.

## Project Structure

```
HumAL/
├── backend/              
|   ├── app/              # FastAPI application
│   ├── data/             # CSV datasets (place your data here)
│   └── models/           # Saved models (joblib .pkl)
├── frontend/             # React + Vite frontend
├── start-dev.bat         # Windows startup script
├── start-dev.sh          # Unix/Linux startup script
├── requirements.txt      # Backend dependencies
├── install.py           # Automated dependency installer
├── .env                 # Environment configuration (create from .env.example)
└── SETUP.md             # This file
```

## Prerequisites

- **Python 3.8+** (for backend)
- **uv** or **pip** (for Python package management)
- **Node.js 18+** (for frontend)
- **npm** or **yarn** (for frontend package management)
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

**Unix/Linux/macOS:**
```bash
# Using the standalone installer (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

## Quick Start

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
   
   # Activate (Unix/Linux/macOS)
   source al_api_venv/bin/activate
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
- ✓ Install all frontend dependencies
- ✓ Verify the installation and display GPU/CPU status

4. Prepare data and models (required before using the app):
   ```bash
   # Unix/Linux/macOS
   mkdir -p backend/data backend/models

   # Windows PowerShell
   mkdir backend\data
   mkdir backend\models
   ```

   - Place CSV data files in `backend/data/`.
     - Resolution KB: `User_Request_last_team_ANON.csv`.
     - Active Learning datasets: `al_demo_test_data_res_classes.csv`, `al_demo_test_data.csv`, `al_demo_train_data_res_classes.csv`, `al_demo_train_data.csv`,  `al_demo_train_labels_dispatch.csv`, `al_demo_train_labels_res_classes.csv`, `al_demo_train_labels_resolution.csv`
   - Place pre-trained team classification and ticket type classification models in `backend/models/`.
      - `perfect_team_classifier/` folder
      - `ticket_classifier_model/` folder

### Option 2: Using Startup Scripts

**First-time setup:** You must run the automated installer (Option 1) at least once before using the startup scripts.

Before starting, ensure `backend/data/` and `backend/models/` exist and are populated as described above.

**Windows:**
```bash
# Double-click start-dev.bat or run:
start-dev.bat
```

**Unix/Linux/macOS:**
```bash
# Make executable (first time only)
chmod +x start-dev.sh
# Run
./start-dev.sh
```

### Option 3: Manual Setup

#### Backend Setup

1. Ensure you're in the project root (contains `install.py` and `requirements.txt`).

2. Create and activate virtual environment:
   ```bash
   # Create virtual environment
   uv venv al_api_venv
   
   # Activate (Windows)
   al_api_venv\Scripts\activate
   
   # Activate (Unix/Linux/macOS)
   source al_api_venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   # With uv (recommended)
   uv pip install -r requirements.txt
   
   # Or with pip
   pip install -r requirements.txt
   ```
4. Prepare data and models (required before using the app):
   ```bash
   # Unix/Linux/macOS
   mkdir -p backend/data backend/models

   # Windows PowerShell
   mkdir backend\data
   mkdir backend\models
   ```

   - Place CSV data files in `backend/data/`.
     - Resolution KB: `User_Request_last_team_ANON.csv`.
     - Active Learning datasets: `al_demo_test_data_res_classes.csv`, `al_demo_test_data.csv`, `al_demo_train_data_res_classes.csv`, `al_demo_train_data.csv`,  `al_demo_train_labels_dispatch.csv`, `al_demo_train_labels_res_classes.csv`, `al_demo_train_labels_resolution.csv`
   - Place pre-trained team classification and ticket type classification models in `backend/models/`.
      - `perfect_team_classifier/` folder
      - `ticket_classifier_model/` folder

5. Navigate to the backend directory:
   ```bash
   cd backend
   ```

6. Start the backend server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the frontend development server:
   ```bash
   npm run dev
   ```

## Access Points

After starting both services:

- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Interactive Docs**: http://localhost:8000/redoc

## Development Features

### CORS Configuration
The backend is configured to accept requests from:
- http://localhost:5173 (Vite default)
- http://localhost:3000 (Alternative React port)
- http://127.0.0.1:5173

### API Proxy
The frontend development server proxies API calls from `/api/*` to the backend at `http://localhost:8000`.

### Hot Reload
Both frontend and backend support hot reload:
- Frontend: Changes to React components refresh automatically
- Backend: Changes to Python files restart the FastAPI server

### TypeScript Support
The frontend includes comprehensive TypeScript types for all API endpoints and data models.

## API Integration

The frontend connects to the backend through:

1. **Typed API Service** (`frontend/src/services/api.ts`)
   - Handles all HTTP requests
   - Includes error handling and response typing
   - Uses environment variables for configuration

2. **TypeScript Types** (`frontend/src/types/api.ts`)
   - Matches backend Pydantic models
   - Provides type safety for API calls

## Environment Configuration

### Frontend Environment Variables
Set in your environment or create `.env.local`:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=HumAL - Development
```

### Backend Environment Variables
The backend uses:
- `HOST=0.0.0.0`
- `PORT=8000`
- `DEBUG=True`

## Troubleshooting

### PyTorch/CUDA Issues

**No GPU detected after installation:**
```bash
# Verify your CUDA installation
nvidia-smi

# Reinstall PyTorch with CUDA support
# Ensure you are in the project root
al_api_venv\Scripts\activate  # Windows
# or: source al_api_venv/bin/activate  # Unix/Linux/macOS
python install.py --reinstall-torch
```

**Force CPU-only installation:**
```bash
python install.py --cpu-only
```

**Switch between CPU and GPU versions:**
```bash
# To GPU version (if CUDA is available)
python install.py --reinstall-torch

# To CPU version
python install.py --reinstall-torch --cpu-only
```

### Port Conflicts
If you encounter port conflicts:
- Backend: Change port in `backend/app/main.py` (line 14)
- Frontend: Change port in `frontend/vite.config.ts`
- Update CORS origins in `backend/app/main.py` if you change frontend port

### Module Not Found
Make sure virtual environment is activated for backend:
```bash
# Windows
al_api_venv\Scripts\activate

# Unix/Linux/macOS
source al_api_venv/bin/activate
```

If packages are missing, reinstall with:
```bash
# Using the automated installer (recommended)
python install.py

# Or manually with uv/pip
uv pip install -r requirements.txt
# or: pip install -r requirements.txt
```

### Network Errors
Ensure both services are running and check:
1. Backend is accessible at http://localhost:8000
2. Frontend proxy configuration in `vite.config.ts`
3. CORS configuration in `backend/app/main.py`

## Available Pages

The frontend includes these predefined pages:
- **Home** (`/`) - Landing page
- **Training** (`/training`) - Model training interface
- **Dispatch Labeling** (`/dispatch-labeling`) - Label dispatch data
- **Ticket Resolution** (`/resolution-labeling`) - Generate automated responses
- **Inference** (`/inference`) - Run model inference
