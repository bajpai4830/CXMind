param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path $backendDir)) {
    throw "Backend directory not found: $backendDir"
}

if (-not (Test-Path $frontendDir)) {
    throw "Frontend directory not found: $frontendDir"
}

Write-Host "Starting CXMind local dev environment..." -ForegroundColor Cyan

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating backend virtual environment..." -ForegroundColor Yellow
    python -m venv (Join-Path $backendDir ".venv")
}

if (-not $SkipInstall) {
    Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
    & $venvPython -m pip install -r (Join-Path $backendDir "requirements.txt")

    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
}

Write-Host "Applying backend migrations..." -ForegroundColor Yellow
Push-Location $backendDir
& $venvPython -m alembic -c alembic.ini upgrade head
Pop-Location

$backendCommand = @"
cd '$backendDir'
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
"@

$frontendCommand = @"
cd '$frontendDir'
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand | Out-Null

Write-Host ""
Write-Host "Started backend and frontend in new terminals." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend:  http://localhost:8000"
Write-Host "Swagger:  http://localhost:8000/docs"
Write-Host ""
Write-Host "Tip: Re-run with -SkipInstall to skip npm/pip install when already set up."
