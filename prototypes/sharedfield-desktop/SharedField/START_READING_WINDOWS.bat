@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "READING_KEY_FILE=%~1"
if not defined READING_KEY_FILE set "READING_KEY_FILE=D:\Project\MyAIWorkspace\openrouter.txt"
where py >nul 2>nul
if errorlevel 1 goto TryPython
py -3 tools\start_reading.py --key-file "%READING_KEY_FILE%"
goto Done
:TryPython
python tools\start_reading.py --key-file "%READING_KEY_FILE%"
:Done
pause
