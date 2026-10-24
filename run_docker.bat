@echo off
setlocal
cd /d "%~dp0"
where docker >nul 2>nul || (echo Docker was not found. Install Docker Desktop and start it. & pause & exit /b 1)
if not exist .env copy /y .env.example .env >nul
echo Building and starting SafeArena in Docker mode...
echo Dashboard: http://127.0.0.1:8000   (stop with Ctrl+C, then: docker compose down)
docker compose up --build
pause
