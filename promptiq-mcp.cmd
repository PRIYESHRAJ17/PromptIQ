@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"
set "DATABASE_URL=sqlite+aiosqlite:///%SCRIPT_DIR%promptiq.db"
set "PROMPTIQ_ZERO_PRICE_ENFORCEMENT=true"
set "PROMPTIQ_MCP_MODE=true"

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" -m promptiq.mcp.server %*
) else (
    python -m promptiq.mcp.server %*
)
endlocal
