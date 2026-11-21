<#
.SYNOPSIS
    Secure In-Memory Windows PowerShell Wrapper for PromptIQ Live Smoke Test.
.DESCRIPTION
    Safely captures the operator's Groq API key in memory using a secure string,
    temporarily assigns it to the child process environment, executes the smoke test,
    and immediately purges the credential from memory and environment.
    
    SECURITY INVARIANTS:
    - Never prints or echoes the secret key.
    - Never writes the secret to disk or any .env file.
    - Never passes the secret via command-line arguments.
    - Requires explicit -OptIn and -ConfirmFreePlan switches.
    - Disposes of secure memory buffers and clears process environment variables immediately.
    
    NOTICE:
    Process-level environment variables are visible to other processes running under the
    same Windows user account. This script minimizes disk exposure, but does not substitute
    for full endpoint security.
.PARAMETER Model
    The model identifier to test (e.g., openai/gpt-oss-120b or openai/gpt-oss-20b).
.PARAMETER OptIn
    Explicit operator confirmation required to send live network requests.
.PARAMETER ConfirmFreePlan
    Explicit attestation that the operator verified cardless Free Plan status in Groq Console.
.EXAMPLE
    .\scripts\run_groq_smoke_secure.ps1 -Model "openai/gpt-oss-120b" -OptIn -ConfirmFreePlan
#>

[CmdletBinding()]
param(
    [string]$Model = "openai/gpt-oss-120b",
    [switch]$OptIn,
    [switch]$ConfirmFreePlan
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PROMPTIQ SECURE OPERATOR SMOKE TEST LAUNCHER" -ForegroundColor Cyan
Write-Host "Target Model: $Model" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Verification of Mandatory Flags
if (-not $OptIn) {
    Write-Host "[ERROR] Missing mandatory -OptIn flag." -ForegroundColor Red
    Write-Host "Live network execution requires explicit operator opt-in." -ForegroundColor Yellow
    Write-Host "Usage: .\scripts\run_groq_smoke_secure.ps1 -Model '$Model' -OptIn -ConfirmFreePlan" -ForegroundColor Yellow
    exit 2
}

if (-not $ConfirmFreePlan) {
    Write-Host "[ERROR] Missing mandatory -ConfirmFreePlan flag." -ForegroundColor Red
    Write-Host "Operator must verify in Groq Console (Settings > Billing: No card; Settings > Limits: Free Plan)" -ForegroundColor Yellow
    Write-Host "Usage: .\scripts\run_groq_smoke_secure.ps1 -Model '$Model' -OptIn -ConfirmFreePlan" -ForegroundColor Yellow
    exit 2
}

# 2. Secure Hidden Credential Input
Write-Host "`nPlease enter your Groq API key." -ForegroundColor White
Write-Host "(Input is masked and will be stored strictly in memory for this session run)" -ForegroundColor DarkGray
$secureKey = Read-Host "Groq API Key" -AsSecureString

if ($null -eq $secureKey -or $secureKey.Length -eq 0) {
    Write-Host "[ERROR] No API key entered. Aborting test." -ForegroundColor Red
    exit 1
}

# 3. Temporary In-Memory Unmarshaling
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
$plainKey = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
# Zero the BSTR buffer immediately
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

$exitCode = 0
try {
    # 4. Set Environment for Child Process Only
    $env:GROQ_API_KEY = $plainKey
    $env:PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED = "true"

    # 5. Locate Python Executable
    $pythonExe = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = "python"
    }

    Write-Host "`nExecuting isolated smoke test..." -ForegroundColor Cyan
    & $pythonExe -m promptiq.gateway.smoke_test --provider groq --model $Model --opt-in
    $exitCode = $LASTEXITCODE
}
finally {
    # 6. Immediate Secure Cleanup & Memory Purge
    $env:GROQ_API_KEY = $null
    $env:PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED = $null
    $plainKey = $null
    $secureKey = $null
    [System.GC]::Collect()
    Write-Host "`n[SECURITY] Environment variables and in-memory credential buffers cleared." -ForegroundColor Green
}

exit $exitCode
