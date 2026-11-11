param (
    [switch]$Serve,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $scriptDir "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "[!] Virtual environment not detected at backend\.venv." -ForegroundColor Yellow
    Write-Host "[*] Creating virtual environment and installing dependencies..." -ForegroundColor Cyan
    python -m venv (Join-Path $scriptDir "backend\.venv")
    & $pythonExe -m pip install -e (Join-Path $scriptDir "backend")
}

$runnerScript = Join-Path $scriptDir "scripts\run_local.py"

if ($Serve) {
    & $pythonExe $runnerScript --serve --port $Port
} else {
    & $pythonExe $runnerScript
}
