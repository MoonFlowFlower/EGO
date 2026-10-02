@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 goto TryPython
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 goto TryPython
py -3 "%~dp0run.py" %*
exit /b %ERRORLEVEL%
:TryPython
where python >nul 2>nul
if errorlevel 1 goto NoPython
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 goto NoPython
python "%~dp0run.py" %*
exit /b %ERRORLEVEL%
:NoPython
echo Python 3.10 or newer is required. This package does not install or download anything.
echo Install or select a local Python interpreter, then run: python run.py shared
exit /b 2
