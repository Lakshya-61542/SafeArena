@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% scripts\docker_isolation_test.py %*
echo.
echo Exit code: %ERRORLEVEL%  (0 = pass, 1 = fail, 2 = inconclusive, 3 = Docker unavailable)
pause
