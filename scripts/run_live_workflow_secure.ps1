<#
.SYNOPSIS
    Secure In-Memory Windows PowerShell Wrapper for PromptIQ 12-Step Live AI Workflow.
.DESCRIPTION
    Safely captures the operator's Groq API key in memory using a secure string,
    temporarily assigns it to the child process environment, executes the 12-step
    workflow across GPT-OSS 120B and GPT-OSS 20B, and immediately purges the credential
    from memory and environment in a finally block.
    
    SECURITY INVARIANTS:
    - Never prints or echoes the secret key.
    - Never writes the secret to disk or any .env file.
    - Never passes the secret via command-line arguments.
    - Requires explicit -OptIn and -ConfirmFreePlan switches for live inference.
    - Disposes of secure memory buffers and clears process environment variables immediately.
    - Enforces zero mock fallbacks when running in live mode.
.PARAMETER Mode
    Execution mode: live (default), mock, or inspect.
.PARAMETER OptIn
    Explicit operator confirmation required to send live network requests.
.PARAMETER ConfirmFreePlan
    Explicit attestation that the operator verified cardless Free Plan status in Groq Console.
.EXAMPLE
    .\scripts\run_live_workflow_secure.ps1 -Mode inspect
    .\scripts\run_live_workflow_secure.ps1 -Mode mock
    .\scripts\run_live_workflow_secure.ps1 -Mode live -OptIn -ConfirmFreePlan
#>

[CmdletBinding()]
param(
    [ValidateSet("live", "mock", "inspect")]
    [string]$Mode = "live",
    [switch]$OptIn,
    [switch]$ConfirmFreePlan
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PROMPTIQ SECURE 12-STEP AI WORKFLOW LAUNCHER" -ForegroundColor Cyan
Write-Host "Mode: $Mode" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

$pythonExe = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

if ($Mode -eq "inspect") {
    Write-Host "[INSPECT] Reading system readiness, database, and credential status..." -ForegroundColor Gray
    & $pythonExe (Join-Path $PSScriptRoot "run_live_workflow.py") --mode inspect
    exit $LASTEXITCODE
}

if ($Mode -eq "mock") {
    Write-Host "[MOCK] Executing full 12-step workflow with deterministic mock adapter..." -ForegroundColor Gray
    & $pythonExe (Join-Path $PSScriptRoot "run_live_workflow.py") --mode mock
    exit $LASTEXITCODE
}

# Live Mode: Strict Safety Checks
if (-not $OptIn) {
    Write-Host "`n[ERROR] Missing mandatory -OptIn switch." -ForegroundColor Red
    Write-Host "Live multi-model execution requires explicit operator opt-in." -ForegroundColor Yellow
    Write-Host "Usage: .\scripts\run_live_workflow_secure.ps1 -Mode live -OptIn -ConfirmFreePlan" -ForegroundColor Yellow
    exit 2
}

if (-not $ConfirmFreePlan) {
    Write-Host "`n[ERROR] Missing mandatory -ConfirmFreePlan switch." -ForegroundColor Red
    Write-Host "Operator must verify in Groq Console (Settings > Billing: No card; Settings > Limits: Free Plan)" -ForegroundColor Yellow
    Write-Host "Usage: .\scripts\run_live_workflow_secure.ps1 -Mode live -OptIn -ConfirmFreePlan" -ForegroundColor Yellow
    exit 2
}

Write-Host "`nPlease enter your Groq API key." -ForegroundColor White
Write-Host "(Input is masked and will be stored strictly in memory for this session run)" -ForegroundColor DarkGray
$secureKey = Read-Host "Groq API Key" -AsSecureString

if ($null -eq $secureKey -or $secureKey.Length -eq 0) {
    Write-Host "`n[ERROR] No API key entered. Aborting live execution." -ForegroundColor Red
    exit 1
}

$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
$plainKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

$env:OPERATOR_GROQ_API_KEY = $plainKey
$env:MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK = "false"

try {
    Write-Host "`nLaunching 12-step live workflow..." -ForegroundColor Green
    & $pythonExe (Join-Path $PSScriptRoot "run_live_workflow.py") --mode live
    $exitCode = $LASTEXITCODE
}
finally {
    $env:OPERATOR_GROQ_API_KEY = $null
    Remove-Item Env:\OPERATOR_GROQ_API_KEY -ErrorAction SilentlyContinue
    $plainKey = $null
    $secureKey.Dispose()
    [GC]::Collect()
    Write-Host "`n[SECURITY] Operator credential purged from process memory and environment." -ForegroundColor Green
}

exit $exitCode
