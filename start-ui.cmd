@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "%USERPROFILE%\.workbuddy-ai\mcp.json" (
    python app.py ui --config "%USERPROFILE%\.workbuddy-ai\mcp.json" --open
) else (
    python app.py ui --open
)
if errorlevel 1 pause
