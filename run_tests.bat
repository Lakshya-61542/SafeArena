@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
if not exist .venv\Scripts\python.exe %PY% -m venv .venv
.venv\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -r requirements.txt
.venv\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -r requirements-dev.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
echo.
echo Exit code: %ERRORLEVEL%
pause
