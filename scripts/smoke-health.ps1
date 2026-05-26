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

function Test-HttpEndpoint {
  param(
    [Parameter(Mandatory = $true)]
    [string] $Url
  )

  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
  } catch {
    return $false
  }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$runner = Get-ComposeRunner

$result = [ordered]@{
  postgres = "fail"
  backend_health = "skipped"
  frontend = "skipped"
  result = "fail"
}

Push-Location $repoRoot
try {
  Invoke-Compose -Runner $runner ps postgres *> $null
  if ($LASTEXITCODE -eq 0) {
    Invoke-Compose -Runner $runner exec -T postgres pg_isready -U knowweave -d knowweave *> $null
    if ($LASTEXITCODE -eq 0) {
      $result.postgres = "pass"
    }
  }
} finally {
  Pop-Location
}

if (Test-HttpEndpoint -Url "http://localhost:8000/api/v1/health") {
  $result.backend_health = "pass"
}

if (Test-Path (Join-Path $repoRoot "frontend") -PathType Container) {
  if (Test-HttpEndpoint -Url "http://localhost:3000/") {
    $result.frontend = "pass"
  } else {
    $result.frontend = "fail"
  }
}

if ($result.postgres -eq "pass" -and $result.backend_health -in @("pass", "skipped") -and $result.frontend -in @("pass", "skipped")) {
  $result.result = "pass"
}

$result | ConvertTo-Json

if ($result.result -ne "pass") {
  exit 1
}
