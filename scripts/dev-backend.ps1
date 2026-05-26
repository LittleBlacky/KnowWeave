$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$python = "python"

if ($env:KNOWWEAVE_PYTHON) {
  $python = $env:KNOWWEAVE_PYTHON
}

Push-Location $backendDir
try {
  & $python -m pip install -e ".[dev]"
  & $python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} finally {
  Pop-Location
}

