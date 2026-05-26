param(
    [string]$BackendUrl = "http://localhost:8000/api/v1",
    [string]$DemoDir = "data/demo",
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$demoPath = Join-Path $repoRoot $DemoDir
$backend = $BackendUrl.TrimEnd("/")

if (-not $Python) {
    $Python = if ($env:KNOWWEAVE_PYTHON) { $env:KNOWWEAVE_PYTHON } else { "python" }
}

function Invoke-JsonGet {
    param([Parameter(Mandatory = $true)][string]$Url)
    return Invoke-RestMethod -Method Get -Uri $Url -TimeoutSec 15
}

function Invoke-JsonPost {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [object]$Body = $null
    )

    if ($null -eq $Body) {
        return Invoke-RestMethod -Method Post -Uri $Url -ContentType "application/json" -TimeoutSec 30
    }

    $json = $Body | ConvertTo-Json -Depth 8
    return Invoke-RestMethod -Method Post -Uri $Url -ContentType "application/json" -Body $json -TimeoutSec 30
}

function Send-SmokeFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ContentType
    )

    Add-Type -AssemblyName System.Net.Http
    $client = [System.Net.Http.HttpClient]::new()
    $form = [System.Net.Http.MultipartFormDataContent]::new()
    $stream = [System.IO.File]::OpenRead($Path)
    $fileContent = [System.Net.Http.StreamContent]::new($stream)
    $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse($ContentType)
    $form.Add($fileContent, "file", [System.IO.Path]::GetFileName($Path))

    try {
        $response = $client.PostAsync("$backend/files/upload", $form).GetAwaiter().GetResult()
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) {
            throw "Upload failed for $Path ($($response.StatusCode)): $body"
        }
        return $body | ConvertFrom-Json
    }
    finally {
        $stream.Dispose()
        $form.Dispose()
        $client.Dispose()
    }
}

function ConvertFrom-Sse {
    param([Parameter(Mandatory = $true)][string]$Text)

    $events = @()
    $blocks = $Text.Trim() -split "(`r?`n){2,}"
    foreach ($block in $blocks) {
        if (-not $block.Trim()) {
            continue
        }
        $eventName = ""
        $dataText = ""
        foreach ($line in ($block -split "`r?`n")) {
            if ($line.StartsWith("event: ")) {
                $eventName = $line.Substring(7)
            }
            elseif ($line.StartsWith("data: ")) {
                $dataText = $line.Substring(6)
            }
        }
        if ($eventName -and $dataText) {
            $events += [pscustomobject]@{
                event = $eventName
                data = ($dataText | ConvertFrom-Json)
            }
        }
    }
    return $events
}

function Assert-Truthy {
    param(
        [object]$Value,
        [string]$Message
    )
    if (-not $Value) {
        throw $Message
    }
}

$result = [ordered]@{
    backend_health = "fail"
    migration_ok = "fail"
    demo_data = "fail"
    file_id = $null
    chunk_count = 0
    retrieval_run_id = $null
    chat_message_id = $null
    feedback_id = $null
    evaluation_sample_id = $null
    result = "fail"
}

powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "test-demo-data.ps1") -DemoDir $demoPath | Out-Null
$result.demo_data = "pass"

Push-Location $backendDir
try {
    & $Python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "Alembic migration failed."
    }
    $result.migration_ok = "pass"
}
finally {
    Pop-Location
}

$health = Invoke-JsonGet -Url "$backend/health"
Assert-Truthy ($health.status -eq "ok") "Backend health did not return ok."
$result.backend_health = "pass"

$upload = Send-SmokeFile -Path (Join-Path $demoPath "company_policy.md") -ContentType "text/markdown"
$fileId = $upload.data.id
Assert-Truthy $fileId "Upload did not return file id."
$result.file_id = $fileId

$parse = Invoke-JsonPost -Url "$backend/files/$fileId/parse"
Assert-Truthy ($parse.data.status -eq "parse_succeeded") "Parse did not succeed."

$chunks = Invoke-JsonPost -Url "$backend/files/$fileId/chunks/build"
$chunkCount = [int]$chunks.data.total
Assert-Truthy ($chunkCount -gt 0) "Chunk build returned no chunks."
$result.chunk_count = $chunkCount

$search = Invoke-JsonPost -Url "$backend/search" -Body @{
    query = "manager approval"
    top_k = 3
}
Assert-Truthy $search.data.retrieval_run_id "Search did not return retrieval_run_id."
Assert-Truthy ($search.data.results.Count -gt 0) "Search did not return results."
$result.retrieval_run_id = $search.data.retrieval_run_id

$session = Invoke-JsonPost -Url "$backend/chat/sessions" -Body @{ title = "P0 smoke" }
$sessionId = $session.data.id
Assert-Truthy $sessionId "Chat session was not created."

$chatResponse = Invoke-WebRequest `
    -Method Post `
    -Uri "$backend/chat/sessions/$sessionId/messages" `
    -ContentType "application/json" `
    -Body (@{ question = "Who approves system access requests?"; top_k = 3 } | ConvertTo-Json) `
    -UseBasicParsing `
    -TimeoutSec 60

$events = ConvertFrom-Sse -Text $chatResponse.Content
$start = $events | Where-Object { $_.event -eq "start" } | Select-Object -First 1
$done = $events | Where-Object { $_.event -eq "done" } | Select-Object -First 1
Assert-Truthy $start "Chat SSE start event missing."
Assert-Truthy ($done.data.status -eq "completed") "Chat SSE did not complete."
$messageId = $start.data.message_id
Assert-Truthy $messageId "Chat SSE did not return message_id."
$result.chat_message_id = $messageId

$feedback = Invoke-JsonPost -Url "$backend/feedback" -Body @{
    target_type = "chat_message"
    target_id = $messageId
    feedback_type = "answer_wrong"
    comment = "P0 smoke feedback candidate."
    metadata = @{ source = "smoke-p0" }
}
Assert-Truthy $feedback.data.id "Feedback was not created."
$result.feedback_id = $feedback.data.id

$evaluation = Invoke-JsonPost -Url "$backend/feedback/$($feedback.data.id)/to-evaluation-sample"
Assert-Truthy $evaluation.data.id "Evaluation sample was not created."
$result.evaluation_sample_id = $evaluation.data.id

$result.result = "pass"
$result | ConvertTo-Json -Depth 8
