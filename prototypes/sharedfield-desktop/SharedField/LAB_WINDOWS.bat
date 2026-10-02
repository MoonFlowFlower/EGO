@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
call "%~dp0_windows_python.bat" serve %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo Startup failed. Read the error above. Port in use? Try: START_WINDOWS.bat --port 8766
pause
exit /b %RC%
