@echo off
echo Starting HumAL Development Environment...

REM Start backend
echo Starting backend on port 8000...
start "HumAL Backend" cmd /k "cd backend && ..\al_api_venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend on port 5173...
start "HumAL Frontend" cmd /k "cd frontend && npm run dev"

echo Both services are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo Opening browser tabs shortly...
timeout /t 8 /nobreak >nul
start "" http://localhost:5173
start "" http://localhost:8000/docs
pause
