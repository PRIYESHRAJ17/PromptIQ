<#
.SYNOPSIS
    Secure In-Memory Windows PowerShell Wrapper for PromptIQ Live Multi-Model Collaboration.
.DESCRIPTION
    Safely captures the operator's Groq API key in memory using a secure string,
    temporarily assigns it to the child process environment, executes the 5-stage
    live collaboration workflow across GPT-OSS 120B and GPT-OSS 20B, and immediately
    purges the credential from memory and environment in a finally block.
    
    SECURITY INVARIANTS:
    - Never prints or echoes the secret key.
    - Never writes the secret to disk or any .env file.
    - Never passes the secret via command-line arguments.
    - Requires explicit -OptIn and -ConfirmFreePlan switches.
    - Disposes of secure memory buffers and clears process environment variables immediately.
    - Enforces zero mock fallbacks ($env:MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK = "false").
    
    NOTICE:
    Process-level environment variables are visible to other processes running under the
    same Windows user account. This script minimizes disk exposure, but does not substitute
    for full endpoint security.
.PARAMETER Profile
    The collaboration execution profile (default: STANDARD).
.PARAMETER OptIn
    Explicit operator confirmation required to send live network requests.
.PARAMETER ConfirmFreePlan
    Explicit attestation that the operator verified cardless Free Plan status in Groq Console.
.EXAMPLE
    .\scripts\run_groq_collaboration_secure.ps1 -OptIn -ConfirmFreePlan
#>

[CmdletBinding()]
param(
    [string]$Profile = "STANDARD",
    [switch]$OptIn,
    [switch]$ConfirmFreePlan
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PROMPTIQ SECURE MULTI-MODEL COLLABORATION LAUNCHER" -ForegroundColor Cyan
Write-Host "Stage Sequence: Stage A (120B Gen) -> Stage B (20B Critic) -> Stage C (Det Verif) -> Stage D (120B Rev) -> Stage E (Final Verif)" -ForegroundColor Gray
Write-Host "Profile: $Profile" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Verification of Mandatory Flags
if (-not $OptIn) {
    Write-Host "[ERROR] Missing mandatory -OptIn flag." -ForegroundColor Red
    Write-Host "Live multi-model execution requires explicit operator opt-in." -ForegroundColor Yellow
    Write-Host "Usage: .\scripts\run_groq_collaboration_secure.ps1 -OptIn -ConfirmFreePlan" -ForegroundColor Yellow
    exit 2
}

if (-not $ConfirmFreePlan) {
    Write-Host "[ERROR] Missing mandatory -ConfirmFreePlan flag." -ForegroundColor Red
    Write-Host "Operator must verify in Groq Console (Settings > Billing: No card; Settings > Limits: Free Plan)" -ForegroundColor Yellow
    Write-Host "Usage: .\scripts\run_groq_collaboration_secure.ps1 -OptIn -ConfirmFreePlan" -ForegroundColor Yellow
    exit 2
}

# 2. Secure Hidden Credential Input
Write-Host "`nPlease enter your Groq API key." -ForegroundColor White
Write-Host "(Input is masked and will be stored strictly in memory for this session run)" -ForegroundColor DarkGray
$secureKey = Read-Host "Groq API Key" -AsSecureString

if ($null -eq $secureKey -or $secureKey.Length -eq 0) {
    Write-Host "[ERROR] No API key entered. Aborting collaboration." -ForegroundColor Red
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
    # Strict fail-closed: never fall back to mock during live multi-model execution
    $env:MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK = "false"
    $env:MANAGED_INFERENCE_PRIMARY_ROUTE = "groq"

    # 5. Locate Python Executable
    $pythonExe = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = "python"
    }

    Write-Host "`nExecuting isolated multi-model collaboration..." -ForegroundColor Cyan
    & $pythonExe -m promptiq.orchestrator.collaboration_cli --opt-in --profile $Profile
    $exitCode = $LASTEXITCODE
}
finally {
    # 6. Immediate Secure Cleanup & Memory Purge
    $env:GROQ_API_KEY = $null
    $env:PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED = $null
    $env:MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK = $null
    $env:MANAGED_INFERENCE_PRIMARY_ROUTE = $null
    $plainKey = $null
    $secureKey = $null
    [System.GC]::Collect()
    Write-Host "`n[SECURITY] Environment variables and in-memory credential buffers cleared." -ForegroundColor Green
}

exit $exitCode
