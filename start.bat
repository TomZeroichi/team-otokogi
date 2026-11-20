@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "DATA_DIR=%CD%\data"
set "COOKIE_SECURE=0"
python -m pip install -r requirements.txt || (pause & exit /b 1)
echo.
echo TEAM狭気: http://localhost:8000/
echo Press Ctrl+C to stop the server.
python -m uvicorn app:app --host 0.0.0.0 --port 8000
pause
