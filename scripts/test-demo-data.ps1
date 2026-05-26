param(
    [string]$DemoDir = "data/demo"
)

$ErrorActionPreference = "Stop"

$requiredFiles = @(
    @{ Name = "company_policy.md"; Keywords = @("access", "approval", "evaluation") },
    @{ Name = "security_handbook.pdf"; Keywords = @("security", "approval", "evaluation") },
    @{ Name = "team_faq.docx"; Keywords = @("access", "security", "evaluation") },
    @{ Name = "notes.txt"; Keywords = @("security", "approval", "feedback") }
)

if (-not (Test-Path -LiteralPath $DemoDir -PathType Container)) {
    throw "Demo directory not found: $DemoDir"
}

foreach ($fileSpec in $requiredFiles) {
    $path = Join-Path $DemoDir $fileSpec.Name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing demo fixture: $path"
    }

    $item = Get-Item -LiteralPath $path
    if ($item.Length -le 0) {
        throw "Demo fixture is empty: $path"
    }

    $bytes = [System.IO.File]::ReadAllBytes($item.FullName)
    $latin1 = [System.Text.Encoding]::GetEncoding("iso-8859-1")
    $text = $latin1.GetString($bytes).ToLowerInvariant()
    if ($fileSpec.Name.EndsWith(".docx")) {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead($item.FullName)
        try {
            $entry = $zip.Entries | Where-Object { $_.FullName -eq "word/document.xml" } | Select-Object -First 1
            if (-not $entry) {
                throw "team_faq.docx does not contain word/document.xml."
            }
            $reader = New-Object System.IO.StreamReader($entry.Open())
            try {
                $text = $reader.ReadToEnd().ToLowerInvariant()
            }
            finally {
                $reader.Dispose()
            }
        }
        finally {
            $zip.Dispose()
        }
    }
    foreach ($keyword in $fileSpec.Keywords) {
        if (-not $text.Contains($keyword.ToLowerInvariant())) {
            throw "Demo fixture $($fileSpec.Name) does not contain keyword: $keyword"
        }
    }
}

$pdfPath = Join-Path $DemoDir "security_handbook.pdf"
$pdfHeader = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes($pdfPath), 0, 5)
if ($pdfHeader -ne "%PDF-") {
    throw "security_handbook.pdf is not a PDF fixture."
}

$docxPath = Join-Path $DemoDir "team_faq.docx"
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $docxPath))
    try {
        if (-not ($zip.Entries | Where-Object { $_.FullName -eq "word/document.xml" })) {
            throw "team_faq.docx does not contain word/document.xml."
        }
    }
    finally {
        $zip.Dispose()
    }
}
catch {
    throw "team_faq.docx is not a readable DOCX fixture. $($_.Exception.Message)"
}

Write-Output "demo_data_ok"
