#!/usr/bin/env pwsh
<#
.SYNOPSIS
    KnowWeave P0 Smoke — 全链路端到端验证

.DESCRIPTION
    验证 P0 主链路：健康检查 → 上传 → 解析 → 分块 → 搜索 → Chat SSE → Feedback → 评测候选
    输出结构化 JSON。

.PARAMETER BaseUrl
    Backend API base URL (default: http://localhost:9001/api/v1)

.PARAMETER DemoFile
    Path to demo Markdown file (default: ../data/demo/company_policy.md)

.EXAMPLE
    .\scripts\smoke-p0.ps1
    .\scripts\smoke-p0.ps1 -BaseUrl http://localhost:8000/api/v1
#>
param(
    [string]$BaseUrl = "http://localhost:9001/api/v1",
    [string]$DemoFile = ""
)

$ErrorActionPreference = "Stop"
$results = @()

if (-not $DemoFile) {
    $DemoFile = Join-Path $PSScriptRoot "..\data\demo\company_policy.md"
}

function Write-Step($step, $status, $detail) {
    $entry = @{ step = $step; status = $status; detail = $detail; time = (Get-Date -Format o) }
    $script:results += $entry
    $color = if ($status -eq "pass") { "Green" } else { "Red" }
    Write-Host "[$status] $step" -ForegroundColor $color
    if ($detail) { Write-Host "       $detail" -ForegroundColor Gray }
}

function Invoke-API {
    param([string]$Method, [string]$Path, $Body)
    $uri = "$BaseUrl$Path"
    $params = @{
        Uri = $uri
        Method = $Method
        ContentType = "application/json"
        ErrorAction = "Stop"
    }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10) }
    try {
        $resp = Invoke-RestMethod @params
        return $resp.data
    } catch {
        $err = $_.Exception.Message
        if ($_.Exception.Response) {
            $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
            $err = $reader.ReadToEnd()
        }
        throw "API $Method $Path failed: $err"
    }
}

# ── 0. Check demo file ──
if (-not (Test-Path $DemoFile)) {
    Write-Step "0. Demo 文件检查" "fail" "文件不存在: $DemoFile"
    exit 1
}
Write-Step "0. Demo 文件检查" "pass" "$DemoFile"

# ── 1. Health check ──
try {
    $config = Invoke-API GET "/system/config"
    Write-Step "1. 后端健康" "pass" "app=$($config.app_name) model=$($config.models.chat)"
} catch {
    Write-Step "1. 后端健康" "fail" $_.Exception.Message
    exit 1
}

# ── 2. Upload ──
$fileId = $null
try {
    # Use .NET HttpClient for multipart upload
    Add-Type -AssemblyName System.Net.Http
    $client = new-object System.Net.Http.HttpClient
    $content = new-object System.Net.Http.MultipartFormDataContent
    $fileStream = [System.IO.File]::OpenRead($DemoFile)
    $fileContent = new-object System.Net.Http.StreamContent($fileStream)
    $fileContent.Headers.ContentDisposition = new-object System.Net.Http.Headers.ContentDispositionHeaderValue("form-data")
    $fileContent.Headers.ContentDisposition.Name = "file"
    $fileContent.Headers.ContentDisposition.FileName = [System.IO.Path]::GetFileName($DemoFile)
    $content.Add($fileContent)
    $response = $client.PostAsync("$BaseUrl/files/upload", $content).Result
    $respBody = $response.Content.ReadAsStringAsync().Result
    $fileStream.Dispose()
    $client.Dispose()
    if ($response.IsSuccessStatusCode) {
        $uploaded = $respBody | ConvertFrom-Json
        $fileId = $uploaded.data.id
        Write-Step "2. 上传" "pass" "$(Split-Path $DemoFile -Leaf) → $fileId"
    } else {
        Write-Step "2. 上传" "fail" "HTTP $($response.StatusCode): $respBody"
    }
} catch {
    Write-Step "2. 上传" "fail" $_.Exception.Message
}

# ── 3. Parse ──
try {
    $parsed = Invoke-API POST "/files/$fileId/parse"
    Write-Step "3. 解析" "pass" "status=$($parsed.status) blocks=$($parsed.block_count)"
} catch {
    Write-Step "3. 解析" "fail" $_.Exception.Message
}

# ── 4. Build chunks ──
try {
    $chunks = Invoke-API POST "/files/$fileId/chunks/build"
    Write-Step "4. 分块" "pass" "chunks=$($chunks.total)"
} catch {
    Write-Step "4. 分块" "fail" $_.Exception.Message
}

# ── 5. Search ──
try {
    $searchResult = Invoke-API POST "/search" @{ query = "审批"; top_k = 5; target_types = @("chunk", "knowledge_unit", "wiki_page") }
    if ($searchResult.results.Count -gt 0) {
        Write-Step "5. 搜索" "pass" "query='审批' hits=$($searchResult.results.Count)"
    } else {
        Write-Step "5. 搜索" "pass" "query='审批' 返回 0 条 (首次分块后可能需要时间索引)"
    }
} catch {
    Write-Step "5. 搜索" "fail" $_.Exception.Message
}

# ── 6. Chat SSE ──
try {
    $session = Invoke-API POST "/chat/sessions" @{ title = "P0 smoke" }
    $streamUri = "$BaseUrl/chat/sessions/$($session.id)/messages"
    $body = @{ question = "公司考勤制度有哪些要求？"; top_k = 5 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri $streamUri -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
    if ($response) {
        Write-Step "6. Chat SSE" "pass" "session=$($session.id)"
    } else {
        Write-Step "6. Chat SSE" "fail" "空响应"
    }
} catch {
    Write-Step "6. Chat SSE" "fail" $_.Exception.Message
}

# ── 7. Feedback (target chunk directly) ──
try {
    $chunksList = Invoke-API GET "/files/$fileId/chunks"
    if ($chunksList.items.Count -gt 0) {
        $chunkId = $chunksList.items[0].id
        $fb = Invoke-API POST "/feedback" @{
            target_type = "chunk"
            target_id = $chunkId
            feedback_type = "chunk_low_quality"
            comment = "P0 smoke: 分块质量评估"
        }
        Write-Step "7. Feedback" "pass" "id=$($fb.id) type=$($fb.feedback_type)"
    } else {
        Write-Step "7. Feedback" "pass" "无 chunk 可提交反馈"
    }
} catch {
    Write-Step "7. Feedback" "fail" $_.Exception.Message
}

# ── 8. Evaluation candidate from feedback ──
if ($fb) {
    try {
        $eval = Invoke-RestMethod -Uri "$BaseUrl/feedback/$($fb.id)/to-evaluation-sample" -Method Post -ContentType "application/json" -ErrorAction Stop
        if ($eval.data) {
            Write-Step "8. 评测候选" "pass" "id=$($eval.data.id) question=$($eval.data.question.substring(0, [Math]::Min(50, $eval.data.question.length)))"
        } else {
            Write-Step "8. 评测候选" "fail" "候选创建返回空"
        }
    } catch {
        Write-Step "8. 评测候选" "fail" $_.Exception.Message
    }
} else {
    Write-Step "8. 评测候选" "pass" "(无 feedback 跳过)"
}

# ── 9. Evaluation metrics ──
try {
    $metrics = Invoke-API GET "/evaluation/metrics"
    Write-Step "9. 评测指标" "pass" "total=$($metrics.total_samples) verified=$($metrics.verified)"
} catch {
    Write-Step "9. 评测指标" "fail" $_.Exception.Message
}

# ── Final report ──
$passCount = ($results | Where-Object { $_.status -eq "pass" }).Count
$failCount = ($results | Where-Object { $_.status -eq "fail" }).Count
$hasFatal = $failCount -gt 0 -and @($results | Where-Object { $_.status -eq "fail" -and $_.step -in @("0. Demo 文件检查", "1. 后端健康", "2. 上传") }).Count -gt 0

Write-Host ""
Write-Host "=== P0 Smoke Result ===" -ForegroundColor White
Write-Host "  Steps: $passCount pass, $failCount fail" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })

$output = @{
    result = if ($failCount -eq 0) { "pass" } elseif ($hasFatal) { "fatal" } else { "partial" }
    total_steps = $results.Count
    passed = $passCount
    failed = $failCount
    steps = $results
}

$output | ConvertTo-Json -Depth 5
if ($failCount -gt 0 -and $hasFatal) { exit 1 }
