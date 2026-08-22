@echo off
title Ratio — Financial Document Intelligence Engine
echo ========================================================
echo   Ratio Financial Document Intelligence & Gap Detector
echo ========================================================
echo.
echo Starting offline engine server...
echo Access UI in your browser at http://localhost:8000
echo.

if exist "Ratio.exe" (
    start "" "Ratio.exe"
) else if exist "dist\Ratio\Ratio.exe" (
    start "" "dist\Ratio\Ratio.exe"
) else if exist "backend\app.py" (
    start "" http://localhost:8000
    cd backend
    python -m uvicorn app:app --host 0.0.0.0 --port 8000
) else (
    echo [ERROR] Ratio executable or backend files not found.
    pause
)
