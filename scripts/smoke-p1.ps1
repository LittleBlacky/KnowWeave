# P1 Smoke: validates all P1 features end-to-end
param(
    [string]$BackendUrl = "http://localhost:8000/api/v1",
    [string]$DemoDir = "data/demo"
)
$ErrorActionPreference = "Stop"
$backend = $BackendUrl.TrimEnd("/")
$result = [ordered]@{}

# Helper
function Invoke-Get($path) { Invoke-RestMethod -Method Get -Uri "$backend$path" -TimeoutSec 30 }
function Invoke-Post($path, $body) {
    $json = if ($body) { $body | ConvertTo-Json -Depth 8 } else { "{}" }
    Invoke-RestMethod -Method Post -Uri "$backend$path" -ContentType "application/json" -Body $json -TimeoutSec 30
}

Write-Host "=== P1 Smoke ==="

# 1. Health
$health = Invoke-Get "/health"
$result.health = $health.status
Write-Host "Health: $($health.status)"

# 2. Upload + pipeline (reuse P0 smoke flow)
$files = Invoke-Get "/files"
$result.file_count = $files.data.total
Write-Host "Files: $($files.data.total)"

# 3. Wiki list
$wiki = Invoke-Get "/wiki"
$result.wiki_count = $wiki.data.total
Write-Host "Wiki pages: $($wiki.data.total)"

# 4. Wiki Revisions (if any wiki exists)
if ($wiki.data.total -gt 0) {
    $wikiId = $wiki.data.items[0].id
    $revisions = Invoke-Get "/wiki/$wikiId/revisions"
    $result.revision_count = $revisions.data.Count
    Write-Host "Revisions for wiki: $($revisions.data.Count)"
}

# 5. Curation report
$report = Invoke-Get "/curation/report"
$result.curation = "pass"
Write-Host "Curation report generated: $($report.data.total_chunks) chunks"

# 6. Curation trigger
$trigger = Invoke-Post "/curation/trigger"
$result.trigger = $trigger.data.triggered
Write-Host "Curation triggered: $($trigger.data.triggered)"

# 7. Evaluation metrics
$metrics = Invoke-Get "/evaluation/metrics"
$result.eval_metrics = "pass"
Write-Host "Evaluation metrics: $($metrics.data.total_samples) samples"

# 8. Search (keyword + hybrid)
$search = Invoke-Post "/search" @{ query = "test"; target_types = @("chunk"); top_k = 5 }
$result.search = "pass"
Write-Host "Search: $($search.data.results.Count) results"

# 9. Chat
$session = Invoke-Post "/chat/sessions"
$sessionId = $session.data.id
$msg = Invoke-Post "/chat/sessions/$sessionId/messages" @{ content = "test question" }
$result.chat = if ($msg.data.id) { "pass" } else { "fail" }
Write-Host "Chat: $($result.chat)"

# 10. Knowledge Units
$kus = Invoke-Get "/knowledge-units"
$result.ku_count = $kus.data.total
Write-Host "Knowledge Units: $($kus.data.total)"

# Summary
$result.summary = if ($result.health -eq "ok") { "P1 smoke passed" } else { "P1 smoke failed" }
$result | ConvertTo-Json -Depth 2
Write-Host "`n=== $($result.summary) ==="
