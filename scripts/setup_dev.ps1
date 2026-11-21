# PromptIQ PowerShell Development Setup Script
# Enforces pure-Python SQLAlchemy for Windows Smart App Control compliance

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " PromptIQ Development Environment Setup (Windows / SAC)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Set environment variable to bypass C-extensions
$env:DISABLE_SQLALCHEMY_CEXT = "1"
Write-Host "[1/3] Environment variable set: DISABLE_SQLALCHEMY_CEXT=1" -ForegroundColor Green

# Verify virtual environment
if (Test-Path ".\.venv\Scripts\python.exe") {
    Write-Host "[2/3] Virtual environment detected at .\.venv" -ForegroundColor Green
    & ".\.venv\Scripts\python.exe" "scripts\setup_dev.py"
} else {
    Write-Host "[2/3] Virtual environment not found at .\.venv. Creating..." -ForegroundColor Yellow
    python -m venv .venv
    & ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
    & ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"
    & ".\.venv\Scripts\python.exe" "scripts\setup_dev.py"
}

Write-Host "[3/3] Ready! Run tests with: .\.venv\Scripts\pytest" -ForegroundColor Green
