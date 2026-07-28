# Build Ashwin_Iyer_CV.pdf and verify it stays one page with no overfull lines.
# Usage:  .\build.ps1   (Windows)   or   pwsh ./build.ps1   (macOS/Linux)
# Requires TeX Live (latexmk + lualatex).

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Resolve latexmk; on macOS, pwsh sessions may not have TeX Live's path_helper PATH.
$latexmk = "latexmk"
if (-not (Get-Command latexmk -ErrorAction SilentlyContinue)) {
    if (Test-Path "/Library/TeX/texbin/latexmk") {
        $latexmk = "/Library/TeX/texbin/latexmk"
    } else {
        Write-Error "latexmk not found. Install TeX Live and ensure latexmk is on PATH."
        exit 1
    }
}

& $latexmk -lualatex -g -interaction=nonstopmode Ashwin_Iyer_CV.tex
if ($LASTEXITCODE -ne 0) {
    Write-Error "LaTeX build failed (exit $LASTEXITCODE). See Ashwin_Iyer_CV.log."
    exit $LASTEXITCODE
}

# Guardrails: the resume must stay one page and inside the margins.
$log = Get-Content Ashwin_Iyer_CV.log -Raw
$failed = $false

if ($log -match "Output written on .*\((\d+) page") {
    $pages = [int]$Matches[1]
    Write-Host "Built Ashwin_Iyer_CV.pdf ($pages page(s))"
    if ($pages -ne 1) {
        Write-Warning "Resume is $pages pages - it must fit on ONE page. Trim content."
        $failed = $true
    }
}

$overfull = ([regex]::Matches($log, "Overfull")).Count
if ($overfull -gt 0) {
    Write-Warning "$overfull overfull line(s) poke past the margin - search 'Overfull' in Ashwin_Iyer_CV.log."
    $failed = $true
} else {
    Write-Host "No overfull lines."
}

if ($failed) { exit 2 }
