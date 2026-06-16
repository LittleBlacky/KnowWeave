#!/usr/bin/env pwsh
<#
.SYNOPSIS
    KnowWeave P0 Demo Seed — 一键灌入完整演示数据集

.DESCRIPTION
    1. 上传 data/demo/ 下所有文件
    2. 解析 → 分块 → AI 提取知识单元 → 生成 Wiki
    3. 提交几条 Feedback
    4. 生成 Evaluation Sample Candidates
    5. 输出 JSON 报告

.PARAMETER BaseUrl
    Backend API base URL (default: http://localhost:9001/api/v1)

.PARAMETER SkipAI
    Skip AI extraction and Wiki generation (faster for quick testing)

.EXAMPLE
    .\scripts\seed-demo.ps1
    .\scripts\seed-demo.ps1 -BaseUrl http://localhost:8000/api/v1 -SkipAI
#>
param(
    [string]$BaseUrl = "http://localhost:9001/api/v1",
    [switch]$SkipAI
)

$ErrorActionPreference = "Stop"
$results = @()
$seedDir = Join-Path $PSScriptRoot ".." "data" "demo"

function Write-Step($step, $status, $detail) {
    $entry = @{ step = $step; status = $status; detail = $detail; time = (Get-Date -Format o) }
    $results += $entry
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

# ── 1. Health check ──
try {
    $health = Invoke-API GET "/system/config"
    Write-Step "1. 健康检查" "pass" "app=$($health.app_name) env=$($health.environment)"
} catch {
    Write-Step "1. 健康检查" "fail" $_.Exception.Message
    $results | ConvertTo-Json -Depth 5
    exit 1
}

# ── 2. Upload demo files ──
$files = Get-ChildItem $seedDir -Filter *.md -ErrorAction SilentlyContinue
if (-not $files) {
    Write-Step "2. 上传文件" "fail" "未找到 demo 文件: $seedDir"
    $results | ConvertTo-Json -Depth 5
    exit 1
}

$fileIds = @()
foreach ($f in $files) {
    try {
        $form = @{ file = Get-Item $f.FullName }
        $uploaded = Invoke-RestMethod -Uri "$BaseUrl/files/upload" -Method Post -Form $form -ErrorAction Stop
        $fileIds += $uploaded.data.id
        Write-Step "2. 上传" "pass" "$($f.Name) → $($uploaded.data.id)"
    } catch {
        Write-Step "2. 上传" "fail" "$($f.Name): $_"
    }
}

if ($fileIds.Count -eq 0) {
    Write-Step "2. 上传文件" "fail" "无文件上传成功"
    $results | ConvertTo-Json -Depth 5
    exit 1
}

# ── 3. Parse first file ──
$targetFileId = $fileIds[0]
try {
    $parsed = Invoke-API POST "/files/$targetFileId/parse"
    Write-Step "3. 解析" "pass" "status=$($parsed.status) blocks=$($parsed.block_count)"
} catch {
    Write-Step "3. 解析" "fail" $_.Exception.Message
}

# ── 4. Build chunks ──
try {
    $chunks = Invoke-API POST "/files/$targetFileId/chunks/build"
    Write-Step "4. 分块" "pass" "chunks=$($chunks.total)"
} catch {
    Write-Step "4. 分块" "fail" $_.Exception.Message
}

# ── 5. AI extract knowledge units (skip if SkipAI) ──
if (-not $SkipAI) {
    try {
        $kus = Invoke-API POST "/knowledge-units/files/$targetFileId/generate?batch_size=6"
        Write-Step "5. AI 提取" "pass" "extracted=$($kus.extracted) skipped=$($kus.skipped_duplicates)"
    } catch {
        Write-Step "5. AI 提取" "fail" $_.Exception.Message
    }
} else {
    Write-Step "5. AI 提取" "pass" "(skipped)"
}

# ── 6. Generate Wiki ──
if (-not $SkipAI) {
    try {
        $wiki = Invoke-API POST "/files/$targetFileId/wiki"
        Write-Step "6. Wiki 生成" "pass" "title=$($wiki.title) status=$($wiki.status)"
    } catch {
        Write-Step "6. Wiki 生成" "fail" $_.Exception.Message
    }
} else {
    Write-Step "6. Wiki 生成" "pass" "(skipped)"
}

# ── 7. Submit feedbacks ──
try {
    $chunksList = Invoke-API GET "/files/$targetFileId/chunks"
    if ($chunksList.items.Count -gt 0) {
        $chunkId = $chunksList.items[0].id
        $fb1 = Invoke-API POST "/feedback" @{
            target_type = "chunk"
            target_id = $chunkId
            feedback_type = "chunk_low_quality"
            comment = "Demo: chunk 质量需要改善"
        }
        Write-Step "7. Feedback (chunk)" "pass" "id=$($fb1.id)"
    }
} catch {
    Write-Step "7. Feedback" "fail" $_.Exception.Message
}

# ── 8. Create evaluation candidate from feedback ──
try {
    $feedbackList = Invoke-API GET "/feedback?target_type=chunk"
    if ($feedbackList.items.Count -gt 0) {
        $eval = Invoke-RestMethod -Uri "$BaseUrl/feedback/$($feedbackList.items[0].id)/to-evaluation-sample" -Method Post -ContentType "application/json" -ErrorAction Stop
        Write-Step "8. 评测候选" "pass" "id=$($eval.data.id) question=$($eval.data.question)"
    }
} catch {
    Write-Step "8. 评测候选" "fail" $_.Exception.Message
}

# ── 9. Metrics ──
try {
    $metrics = Invoke-API GET "/evaluation/metrics"
    Write-Step "9. 评测指标" "pass" "total=$($metrics.total_samples)"
} catch {
    Write-Step "9. 评测指标" "fail" $_.Exception.Message
}

# ── Final report ──
$passCount = ($results | Where-Object { $_.status -eq "pass" }).Count
$failCount = ($results | Where-Object { $_.status -eq "fail" }).Count
Write-Host ""
Write-Host "=== Seed 完成: $passCount pass, $failCount fail ===" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })

$results | ConvertTo-Json -Depth 5
