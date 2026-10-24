@echo off
setlocal
cd /d "%~dp0"
title SafeArena (local mode)

where py >nul 2>nul && (set "PY=py -3") || (where python >nul 2>nul && (set "PY=python") || (
  echo Python 3.10+ was not found. Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  pause & exit /b 1))

if not exist .venv\Scripts\python.exe (
  echo Creating virtual environment...
  %PY% -m venv .venv || (echo Failed to create the virtual environment. & pause & exit /b 1)
)
echo Installing dependencies...
.venv\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -r requirements.txt || (echo Dependency install failed. & pause & exit /b 1)
if not exist .env copy /y .env.example .env >nul

echo.
echo SafeArena is starting at http://127.0.0.1:8000  (Ctrl+C to stop)
start "" http://127.0.0.1:8000
.venv\Scripts\python.exe run_local.py
pause
