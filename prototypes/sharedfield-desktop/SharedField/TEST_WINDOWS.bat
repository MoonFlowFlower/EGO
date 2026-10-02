@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
call "%~dp0_windows_python.bat" test %*
set "RC=%ERRORLEVEL%"
pause
exit /b %RC%
