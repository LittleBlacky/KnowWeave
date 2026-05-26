$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "frontend"

if (-not (Test-Path $frontendDir -PathType Container)) {
  Write-Error "Frontend directory not found. Complete T004 before running this script."
}

Push-Location $frontendDir
try {
  pnpm install
  pnpm dev
} finally {
  Pop-Location
}

