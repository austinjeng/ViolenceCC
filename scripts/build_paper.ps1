<#
.SYNOPSIS
    Compile the CGW '26 paper (paper/main.tex) locally with latexmk and open the PDF.

.DESCRIPTION
    Stands in for the Overleaf round-trip. Locates latexmk (MiKTeX) and perl
    (Strawberry Perl, required by MiKTeX's latexmk wrapper) by full-path probe so
    it works even in a shell whose PATH has not picked up the installers' changes.
    Runs latexmk in paper/ (pdflatex -> bibtex -> pdflatex x2, auto-installing
    missing CTAN packages on first build) and opens the resulting PDF.

.PARAMETER Clean
    Run `latexmk -C` first to wipe build artifacts, then do a full rebuild.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean
#>
[CmdletBinding()]
param(
    [switch]$Clean
)

$ErrorActionPreference = 'Continue'

# --- Repo paths (location-independent) ---
$scriptDir = $PSScriptRoot
$repoRoot  = Split-Path $scriptDir -Parent
$paperDir  = Join-Path $repoRoot 'paper'
$mainTex   = Join-Path $paperDir 'main.tex'

if (-not (Test-Path $mainTex)) {
    Write-Error "[build_paper] Cannot find paper\main.tex at $mainTex"
    exit 1
}

function Find-Exe {
    param([Parameter(Mandatory)][string]$Name, [string[]]$ProbeDirs)
    foreach ($d in $ProbeDirs) {
        if ($d) {
            $p = Join-Path $d $Name
            if (Test-Path $p) { return $p }
        }
    }
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

# --- Locate latexmk (do NOT rely on a refreshed PATH) ---
$miktexBin = Join-Path $env:LOCALAPPDATA 'Programs\MiKTeX\miktex\bin\x64'
$latexmk = Find-Exe -Name 'latexmk.exe' -ProbeDirs @($miktexBin)
if (-not $latexmk) {
    $hit = Get-ChildItem -Path $env:LOCALAPPDATA, $env:USERPROFILE -Recurse -Filter latexmk.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { $latexmk = $hit.FullName }
}
if (-not $latexmk) {
    Write-Error "[build_paper] latexmk.exe not found. Install MiKTeX first: winget install -e --id MiKTeX.MiKTeX --scope user"
    exit 1
}
# latexmk spawns pdflatex/bibtex by bare name -> the MiKTeX bin must be on PATH
# for those child processes (a fresh shell won't have picked it up yet).
$latexmkDir = Split-Path $latexmk -Parent
if (($env:PATH -split ';') -notcontains $latexmkDir) { $env:PATH = "$latexmkDir;$env:PATH" }

# --- Ensure Perl is on PATH (MiKTeX's latexmk wrapper needs a perl script engine) ---
$perlProbe = @('C:\Strawberry\perl\bin', (Join-Path $env:LOCALAPPDATA 'Programs\Strawberry\perl\bin'))
$perlExe = Find-Exe -Name 'perl.exe' -ProbeDirs $perlProbe
if (-not $perlExe) {
    $hit = Get-ChildItem -Path 'C:\Strawberry', $env:LOCALAPPDATA, $env:USERPROFILE -Recurse -Filter perl.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match 'Strawberry' } | Select-Object -First 1
    if ($hit) { $perlExe = $hit.FullName }
}
if ($perlExe) {
    $perlBin = Split-Path $perlExe -Parent
    if (($env:PATH -split ';') -notcontains $perlBin) { $env:PATH = "$perlBin;$env:PATH" }
    Write-Output "[build_paper] Using perl:    $perlExe"
} else {
    Write-Warning "[build_paper] perl.exe not found. latexmk needs Perl: winget install -e --id StrawberryPerl.StrawberryPerl. Attempting build anyway."
}

Write-Output "[build_paper] Using latexmk: $latexmk"
Write-Output "[build_paper] Paper dir:   $paperDir"

# --- Build (run inside paper/ so .latexmkrc and relative figure paths resolve) ---
$code = 0
Push-Location $paperDir
try {
    if ($Clean) {
        Write-Output "[build_paper] Cleaning build artifacts (latexmk -C)..."
        & $latexmk -C main.tex | Out-Host
    }
    Write-Output "[build_paper] Compiling main.tex (pdflatex -> bibtex -> pdflatex x2)..."
    # Engine flags (-interaction=nonstopmode -synctex=1) come from paper/.latexmkrc.
    & $latexmk -pdf main.tex | Out-Host
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}

# --- Result handling ---
$pdf = Join-Path $paperDir 'main.pdf'
if (-not (Test-Path $pdf)) {
    Write-Error "[build_paper] No PDF produced at $pdf (latexmk exit $code). See paper\main.log."
    if ($code -ne 0) { exit $code } else { exit 1 }
}

Write-Output "[build_paper] PDF built: $pdf"
Write-Output "[build_paper] Opening in default viewer..."
Invoke-Item $pdf

if ($code -ne 0) {
    Write-Warning "[build_paper] latexmk reported exit $code (PDF still produced; check log for unresolved refs/warnings)."
}
Write-Output "[build_paper] Done."
exit $code
