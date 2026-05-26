param(
    [string]$BackendUrl = "http://localhost:8000/api/v1",
    [string]$DemoDir = "data/demo"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$demoPath = Join-Path $repoRoot $DemoDir
$backend = $BackendUrl.TrimEnd("/")

powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "test-demo-data.ps1") -DemoDir $demoPath | Out-Null

$fixtures = @(
    @{ Name = "company_policy.md"; ContentType = "text/markdown" },
    @{ Name = "security_handbook.pdf"; ContentType = "application/pdf" },
    @{ Name = "team_faq.docx"; ContentType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" },
    @{ Name = "notes.txt"; ContentType = "text/plain" }
)

Add-Type -AssemblyName System.Net.Http

function Invoke-JsonPost {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    $response = Invoke-RestMethod -Method Post -Uri $Url -ContentType "application/json"
    return $response
}

function Send-DemoFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$ContentType
    )

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

$seeded = @()

foreach ($fixture in $fixtures) {
    $path = Join-Path $demoPath $fixture.Name
    $upload = Send-DemoFile -Path $path -ContentType $fixture.ContentType
    $fileId = $upload.data.id

    $parse = Invoke-JsonPost -Url "$backend/files/$fileId/parse"
    $chunks = Invoke-JsonPost -Url "$backend/files/$fileId/chunks/build"

    $seeded += [ordered]@{
        filename = $fixture.Name
        file_id = $fileId
        parse_status = $parse.data.status
        chunk_count = $chunks.data.total
    }
}

$result = [ordered]@{
    file_count = $seeded.Count
    chunk_count = ($seeded | ForEach-Object { $_.chunk_count } | Measure-Object -Sum).Sum
    files = $seeded
    result = "pass"
}

$result | ConvertTo-Json -Depth 5
