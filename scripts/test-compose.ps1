$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-ComposeRunner {
  $dockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue
  if ($dockerCompose) {
    return @{ Command = "docker-compose"; Args = @() }
  }

  $docker = Get-Command docker -ErrorAction SilentlyContinue
  if ($docker) {
    try {
      & docker compose version > $null 2> $null
      if ($LASTEXITCODE -eq 0) {
        return @{ Command = "docker"; Args = @("compose") }
      }
    } catch {
      # Docker exists but the compose plugin is unavailable.
    }
  }

  throw "Neither 'docker compose' nor 'docker-compose' is available."
}

function Invoke-Compose {
  param(
    [Parameter(Mandatory = $true)]
    [hashtable] $Runner,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ComposeArgs
  )

  $allArgs = @($Runner.Args) + @($ComposeArgs)
  & $Runner.Command @allArgs
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $repoRoot "docker-compose.yml"
$initSql = Join-Path $repoRoot "docker/postgres/init.sql"

if (-not (Test-Path $composeFile -PathType Leaf)) {
  throw "Missing docker-compose.yml"
}

if (-not (Test-Path $initSql -PathType Leaf)) {
  throw "Missing docker/postgres/init.sql"
}

$composeText = Get-Content -Path $composeFile -Raw
$requiredPatterns = @(
  "postgres:",
  "pgvector/pgvector:pg15",
  "5432:5432",
  "./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro",
  "postgres_data:",
  "pg_isready"
)

foreach ($pattern in $requiredPatterns) {
  if ($composeText -notlike "*$pattern*") {
    throw "docker-compose.yml missing required postgres setting: $pattern"
  }
}

$initSqlText = Get-Content -Path $initSql -Raw
foreach ($extension in @("vector", "pg_trgm")) {
  if ($initSqlText -notmatch "CREATE\s+EXTENSION\s+IF\s+NOT\s+EXISTS\s+$extension") {
    throw "docker/postgres/init.sql missing extension: $extension"
  }
}

$runner = Get-ComposeRunner
Push-Location $repoRoot
try {
  Invoke-Compose -Runner $runner config --quiet
  if ($LASTEXITCODE -ne 0) {
    throw "Compose config validation failed."
  }
} finally {
  Pop-Location
}

Write-Output "compose_config=pass"
Write-Output "postgres_service=pass"
Write-Output "init_sql=pass"
