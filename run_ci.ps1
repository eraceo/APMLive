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

# 1. Install/Verify Dependencies
Write-Step "Checking Dependencies"
try {
    pip install -q pytest pytest-cov black pylint mypy types-Pillow
    Write-Success "Dependencies are installed."
} catch {
    Write-Failure "Failed to install dependencies."
}

# 2. Code Formatting (Black)
Write-Step "Checking Code Formatting (Black)"
try {
    python -m black --check src tests
    Write-Success "Code is properly formatted."
} catch {
    Write-Host "Code is not formatted. Running black to fix..." -ForegroundColor Yellow
    python -m black src tests
    Write-Success "Code formatted."
}

# 3. Type Checking (MyPy)
Write-Step "Running Static Type Checker (MyPy)"
try {
    python -m mypy src
    Write-Success "Type checks passed."
} catch {
    Write-Failure "Type checks failed."
}

# 4. Linting (Pylint)
Write-Step "Running Linter (Pylint)"
# We allow some errors for now, but fail on critical ones
try {
    python -m pylint src --fail-under=9.0
    Write-Success "Linting passed (Score > 9.0)."
} catch {
    Write-Failure "Linting score too low."
}

# 5. Unit Tests & Coverage
Write-Step "Running Tests with Coverage"
try {
    $env:PYTHONPATH = $PWD
    python -m pytest --cov=src --cov-report=term --cov-fail-under=80
    Write-Success "All tests passed with sufficient coverage."
} catch {
    Write-Failure "Tests failed or coverage too low."
}

Write-Host "`n🎉 CI PIPELINE PASSED SUCCESSFULLY! 🎉" -ForegroundColor Green
