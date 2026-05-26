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
    search_marker = $null
    files = @()
    total_chunk_count = 0
    retrieval_run_id = $null
    chat_message_id = $null
    wiki_id = $null
    knowledge_unit_id = $null
    feedback_ids = @()
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

$demoFiles = @(
    @{ Name = "company_policy.md"; ContentType = "text/markdown" },
    @{ Name = "notes.txt"; ContentType = "text/plain" },
    @{ Name = "security_handbook.pdf"; ContentType = "application/pdf" },
    @{ Name = "team_faq.docx"; ContentType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" }
)

foreach ($demoFile in $demoFiles) {
    $upload = Send-SmokeFile -Path (Join-Path $demoPath $demoFile.Name) -ContentType $demoFile.ContentType
    $fileId = $upload.data.id
    Assert-Truthy $fileId "Upload did not return file id for $($demoFile.Name)."
    $parse = Invoke-JsonPost -Url "$backend/files/$fileId/parse"
    Assert-Truthy ($parse.data.status -eq "parse_succeeded") "Parse did not succeed for $($demoFile.Name)."

    $blocks = Invoke-JsonGet -Url "$backend/files/$fileId/document-blocks"
    Assert-Truthy ($blocks.data.total -gt 0) "Document blocks missing for $($demoFile.Name)."

    $chunks = Invoke-JsonPost -Url "$backend/files/$fileId/rechunk"
    $chunkCount = [int]$chunks.data.total
    Assert-Truthy ($chunkCount -gt 0) "Chunk build returned no chunks for $($demoFile.Name)."
    $result.total_chunk_count += $chunkCount
    $result.files += [ordered]@{
        name = $demoFile.Name
        file_id = $fileId
        block_count = [int]$blocks.data.total
        chunk_count = $chunkCount
    }
}

$runMarker = "smokep0$((Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmssfff'))"
$result.search_marker = $runMarker
$markerPath = Join-Path $repoRoot ".tmp\$runMarker.md"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $markerPath) | Out-Null
Set-Content -LiteralPath $markerPath -Encoding UTF8 -Value @"
# $runMarker

$runMarker manager approval evidence.
"@

$markerUpload = Send-SmokeFile -Path $markerPath -ContentType "text/markdown"
$firstFileId = $markerUpload.data.id
Assert-Truthy $firstFileId "Marker upload did not return file id."
$markerParse = Invoke-JsonPost -Url "$backend/files/$firstFileId/parse"
Assert-Truthy ($markerParse.data.status -eq "parse_succeeded") "Marker parse did not succeed."
$markerBlocks = Invoke-JsonGet -Url "$backend/files/$firstFileId/document-blocks"
Assert-Truthy ($markerBlocks.data.total -gt 0) "Marker document blocks missing."
$markerChunks = Invoke-JsonPost -Url "$backend/files/$firstFileId/rechunk"
Assert-Truthy ($markerChunks.data.total -gt 0) "Marker chunk build returned no chunks."
$firstChunkId = $markerChunks.data.items[0].id

Assert-Truthy $firstFileId "No demo file was uploaded."
Assert-Truthy $firstChunkId "No demo chunk was created."

$knowledgeUnit = Invoke-JsonPost -Url "$backend/knowledge-units" -Body @{
    title = "$runMarker approval rule"
    unit_type = "rule"
    content = "$runMarker system access requests require manager approval."
    summary = "$runMarker manager approval is required for access."
    status = "pending_review"
    source_chunk_ids = @($firstChunkId)
}
Assert-Truthy $knowledgeUnit.data.id "Knowledge Unit was not created."
$result.knowledge_unit_id = $knowledgeUnit.data.id

$wiki = Invoke-JsonPost -Url "$backend/files/$firstFileId/wiki"
Assert-Truthy $wiki.data.id "Wiki draft was not created."
$result.wiki_id = $wiki.data.id

$search = Invoke-JsonPost -Url "$backend/search" -Body @{
    query = $runMarker
    target_types = @("file", "chunk", "knowledge_unit", "wiki_page")
    top_k = 10
}
Assert-Truthy $search.data.retrieval_run_id "Search did not return retrieval_run_id."
Assert-Truthy ($search.data.results.Count -gt 0) "Search did not return results."
$resultTypes = @($search.data.results | ForEach-Object { $_.result_type } | Select-Object -Unique)
foreach ($expectedType in @("file", "chunk", "knowledge_unit", "wiki_page")) {
    Assert-Truthy ($resultTypes -contains $expectedType) "Search did not return $expectedType result."
}
$result.retrieval_run_id = $search.data.retrieval_run_id

$session = Invoke-JsonPost -Url "$backend/chat/sessions" -Body @{ title = "P0 smoke" }
$sessionId = $session.data.id
Assert-Truthy $sessionId "Chat session was not created."

$chatResponse = Invoke-WebRequest `
    -Method Post `
    -Uri "$backend/chat/sessions/$sessionId/messages" `
    -ContentType "application/json" `
    -Body (@{ question = $runMarker; top_k = 3 } | ConvertTo-Json) `
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
$citationList = Invoke-JsonGet -Url "$backend/chat/messages/$messageId/citations"
Assert-Truthy ($citationList.data.total -gt 0) "Chat citations were not persisted."
$citationId = $citationList.data.items[0].id
Assert-Truthy $citationId "Citation id missing."

$feedbackSpecs = @(
    @{ target_type = "chat_message"; target_id = $messageId; feedback_type = "answer_wrong"; comment = "P0 smoke answer feedback." },
    @{ target_type = "chunk"; target_id = $firstChunkId; feedback_type = "chunk_low_quality"; comment = "P0 smoke chunk feedback." },
    @{ target_type = "wiki_page"; target_id = $result.wiki_id; feedback_type = "wiki_needs_update"; comment = "P0 smoke wiki feedback." },
    @{ target_type = "knowledge_unit"; target_id = $result.knowledge_unit_id; feedback_type = "retrieval_helpful"; comment = "P0 smoke KU feedback." },
    @{ target_type = "citation"; target_id = $citationId; feedback_type = "citation_helpful"; comment = "P0 smoke citation feedback." }
)

$feedback = $null
foreach ($feedbackSpec in $feedbackSpecs) {
    $createdFeedback = Invoke-JsonPost -Url "$backend/feedback" -Body @{
        target_type = $feedbackSpec.target_type
        target_id = $feedbackSpec.target_id
        feedback_type = $feedbackSpec.feedback_type
        comment = $feedbackSpec.comment
        metadata = @{ source = "smoke-p0" }
    }
    Assert-Truthy $createdFeedback.data.id "Feedback was not created for $($feedbackSpec.target_type)."
    $result.feedback_ids += $createdFeedback.data.id
    if ($feedbackSpec.target_type -eq "chat_message") {
        $feedback = $createdFeedback
    }
}

$feedbackList = Invoke-JsonGet -Url "$backend/feedback"
Assert-Truthy ($feedbackList.data.total -ge $feedbackSpecs.Count) "Feedback list did not include all smoke feedback."

$evaluation = Invoke-JsonPost -Url "$backend/feedback/$($feedback.data.id)/to-evaluation-sample"
Assert-Truthy $evaluation.data.id "Evaluation sample was not created."
$result.evaluation_sample_id = $evaluation.data.id

$result.result = "pass"
$result | ConvertTo-Json -Depth 8
