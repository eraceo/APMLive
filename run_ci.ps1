
<#
.SYNOPSIS
    Runs the CI pipeline locally: Formatting, Linting, Type Checking, and Testing.

.DESCRIPTION
    This script automates the quality checks that would run in a CI/CD environment.
    It ensures that code meets all standards before being committed.

.EXAMPLE
    .\run_ci.ps1
#>

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
    exit 1
}

function Assert-LastExitCode {
    param([string]$Message)
    if ($LASTEXITCODE -ne 0) {
        Write-Failure $Message
    }
}

# 1. Install/Verify Dependencies
Write-Step "Checking Dependencies"
pip install -q pytest pytest-cov black pylint mypy types-Pillow
Assert-LastExitCode "Failed to install dependencies."
Write-Success "Dependencies are installed."


# 2. Code Formatting (Black)
Write-Step "Checking Code Formatting (Black)"
python -m black --check src tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "Code is not formatted. Running black to fix..." -ForegroundColor Yellow
    python -m black src tests
    Assert-LastExitCode "Failed to format code."
    Write-Success "Code formatted."
} else {
    Write-Success "Code is properly formatted."
}

# 3. Type Checking (MyPy)
Write-Step "Running Static Type Checker (MyPy)"
python -m mypy src
Assert-LastExitCode "Type checks failed."
Write-Success "Type checks passed."

# 4. Linting (Pylint)
Write-Step "Running Linter (Pylint)"
# We allow some errors for now, but fail on critical ones
python -m pylint src --fail-under=9.0
Assert-LastExitCode "Linting score too low."
Write-Success "Linting passed (Score > 9.0)."

# 5. Unit Tests & Coverage
Write-Step "Running Tests with Coverage"
$env:PYTHONPATH = $PWD
python -m pytest --cov=src --cov-report=term --cov-fail-under=80
Assert-LastExitCode "Tests failed or coverage too low."
Write-Success "All tests passed with sufficient coverage."

Write-Host "`n🎉 CI PIPELINE PASSED SUCCESSFULLY! 🎉" -ForegroundColor Green
