# HumAL Development Setup

This guide will help you set up the HumAL (Human-in-the-loop Active Learning) application for development.

## Project Structure

```
HumAL/
├── backend/          # FastAPI backend
├── frontend/         # React + Vite frontend
├── start-dev.bat     # Windows startup script
├── start-dev.sh      # Unix/Linux startup script
└── SETUP.md         # This file
```

## Prerequisites

- **Python 3.8+** (for backend)
- **uv** (for Python package management - [install guide](https://github.com/astral-sh/uv))
- **Node.js 18+** (for frontend)
- **npm** or **yarn** (for frontend package management)

### Installing uv

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

### Option 1: Using Startup Scripts (Recommended)

**First-time setup:** Before using the startup scripts, you must complete the manual setup steps below (at least once) to create the virtual environment and install dependencies.

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

### Option 2: Manual Setup

#### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

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
   uv pip install -r requirements.txt
   ```

4. Start the backend server:
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
uv pip install -r requirements.txt
```

### Network Errors
Ensure both services are running and check:
1. Backend is accessible at http://localhost:8000
2. Frontend proxy configuration in `vite.config.ts`
3. CORS configuration in `backend/app/main.py`

## Next Steps

The infrastructure is now ready! You can now:

1. **Connect pages to API endpoints** - Use the `apiService` from `frontend/src/services/api.ts`
2. **Add data visualization** - The project includes Recharts for charts
3. **Implement real-time features** - Add WebSocket support if needed
4. **Add authentication** - Extend the API with auth endpoints

## Available Pages

The frontend includes these predefined pages:
- **Home** (`/`) - Landing page
- **Training** (`/training`) - Model training interface
- **Dispatch Labeling** (`/dispatch-labeling`) - Label dispatch data
- **Resolution Labeling** (`/resolution-labeling`) - Label resolution data
- **Inference** (`/inference`) - Run model inference

Tell the developer which specific page you'd like to connect to the backend API first!
