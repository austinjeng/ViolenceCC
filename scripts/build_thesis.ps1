<#
.SYNOPSIS
    Compile the master's thesis (thesis/main.tex) locally with latexmk.
    NON-INTERACTIVE by default: no PDF viewer opens unless -Open is passed.

.DESCRIPTION
    Modeled on scripts/build_paper.ps1. Locates latexmk (MiKTeX) and perl
    (Strawberry Perl, required by MiKTeX's latexmk wrapper) by full-path probe so
    it works even in a shell whose PATH has not picked up the installers' changes.
    Preflight: HARD-asserts the vendored thesis/IEEEtranN.bst exists (repo-
    controlled), then REPORTS (non-blocking) kpsewhich resolution per required
    package -- absence is NOT an error because MiKTeX auto-installs missing CTAN
    packages during the latexmk run (--enable-installer in thesis/.latexmkrc);
    the report only makes a later build failure diagnosable.
    Post-build: scans thesis/main.log and exits nonzero on LaTeX errors ("!"
    lines) or undefined references/citations.

.PARAMETER Clean
    Run `latexmk -C` first to wipe build artifacts, then do a full rebuild.

.PARAMETER Open
    Open the built PDF in the default viewer (opt-in; default is non-interactive).

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean
#>
[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$Open
)

$ErrorActionPreference = 'Continue'

# --- Repo paths (location-independent) ---
$scriptDir = $PSScriptRoot
$repoRoot  = Split-Path $scriptDir -Parent
$thesisDir = Join-Path $repoRoot 'thesis'
$mainTex   = Join-Path $thesisDir 'main.tex'

if (-not (Test-Path $mainTex)) {
    Write-Error "[build_thesis] Cannot find thesis\main.tex at $mainTex"
    exit 1
}

# --- Preflight 1 (HARD): the vendored bibliography style must exist ---
# BibTeX searches the working directory first, so the vendored copy wins over
# any MiKTeX-installed IEEEtranN.bst when latexmk runs inside thesis/.
$bst = Join-Path $thesisDir 'IEEEtranN.bst'
if (-not (Test-Path $bst)) {
    Write-Error "[build_thesis] Vendored thesis\IEEEtranN.bst is MISSING at $bst. The bibliography must resolve via the repo-controlled copy (spec S3); restore it from git before building."
    exit 1
}
Write-Output "[build_thesis] Vendored .bst: $bst (present)"

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
    Write-Error "[build_thesis] latexmk.exe not found. Install MiKTeX first: winget install -e --id MiKTeX.MiKTeX --scope user"
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
    Write-Output "[build_thesis] Using perl:    $perlExe"
} else {
    Write-Warning "[build_thesis] perl.exe not found. latexmk needs Perl: winget install -e --id StrawberryPerl.StrawberryPerl. Attempting build anyway."
}

Write-Output "[build_thesis] Using latexmk: $latexmk"
Write-Output "[build_thesis] Thesis dir:  $thesisDir"

# --- Preflight 2 (REPORT-only): kpsewhich resolution per required package ---
# Absence is NOT an error: MiKTeX installs packages on demand during the build.
$requiredPkgs = @(
    'natbib', 'booktabs', 'multirow', 'graphicx', 'geometry', 'setspace',
    'caption', 'subcaption', 'microtype', 'amsmath', 'amssymb', 'array', 'tikz',
    'lmodern'
)
$kpsewhich = Find-Exe -Name 'kpsewhich.exe' -ProbeDirs @($miktexBin)
if ($kpsewhich) {
    Write-Output "[build_thesis] Package preflight (report-only; missing packages auto-install during build):"
    foreach ($pkg in $requiredPkgs) {
        $res = & $kpsewhich "$pkg.sty" 2>$null
        if ($res) {
            Write-Output "[build_thesis]   $pkg.sty -> $res"
        } else {
            Write-Output "[build_thesis]   $pkg.sty -> NOT preinstalled (MiKTeX will install on demand)"
        }
    }
} else {
    Write-Warning "[build_thesis] kpsewhich.exe not found; skipping package resolution report."
}

# --- Build (run inside thesis/ so .latexmkrc, the vendored .bst and relative figure paths resolve) ---
$code = 0
Push-Location $thesisDir
try {
    if ($Clean) {
        Write-Output "[build_thesis] Cleaning build artifacts (latexmk -C)..."
        & $latexmk -C main.tex | Out-Host
    }
    Write-Output "[build_thesis] Compiling main.tex (pdflatex -> bibtex -> pdflatex x2)..."
    # Engine flags (-interaction=nonstopmode -synctex=1) come from thesis/.latexmkrc.
    & $latexmk -pdf main.tex | Out-Host
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}

# --- Result handling ---
$pdf = Join-Path $thesisDir 'main.pdf'
if (-not (Test-Path $pdf)) {
    Write-Error "[build_thesis] No PDF produced at $pdf (latexmk exit $code). See thesis\main.log."
    if ($code -ne 0) { exit $code } else { exit 1 }
}

# --- Post-build log scan (NEW vs build_paper.ps1): fail on errors / undefined refs ---
$logPath = Join-Path $thesisDir 'main.log'
$scanFailed = $false
if (Test-Path $logPath) {
    $logLines = Get-Content $logPath
    $errorLines     = @($logLines | Where-Object { $_ -match '^!' })
    $undefRefBlock  = @($logLines | Where-Object { $_ -match 'There were undefined references' })
    $undefCitations = @($logLines | Where-Object { $_ -match 'Citation .* undefined' })
    $undefRefs      = @($logLines | Where-Object { $_ -match 'Reference .* undefined' })

    if ($errorLines.Count -gt 0) {
        Write-Output "[build_thesis] LOG SCAN: $($errorLines.Count) LaTeX error line(s) ('!'):"
        $errorLines | Select-Object -First 10 | ForEach-Object { Write-Output "[build_thesis]   $_" }
        $scanFailed = $true
    }
    if ($undefRefBlock.Count -gt 0) {
        Write-Output "[build_thesis] LOG SCAN: 'There were undefined references' found."
        $scanFailed = $true
    }
    if ($undefCitations.Count -gt 0) {
        Write-Output "[build_thesis] LOG SCAN: $($undefCitations.Count) undefined citation(s):"
        $undefCitations | Select-Object -First 10 | ForEach-Object { Write-Output "[build_thesis]   $_" }
        $scanFailed = $true
    }
    if ($undefRefs.Count -gt 0) {
        Write-Output "[build_thesis] LOG SCAN: $($undefRefs.Count) undefined reference(s):"
        $undefRefs | Select-Object -First 10 | ForEach-Object { Write-Output "[build_thesis]   $_" }
        $scanFailed = $true
    }
    if (-not $scanFailed) {
        Write-Output "[build_thesis] LOG SCAN: clean (no errors, no undefined refs/citations)."
    }
} else {
    Write-Error "[build_thesis] thesis\main.log not found; cannot verify the build."
    exit 1
}

Write-Output "[build_thesis] PDF built: $pdf"

if ($Open) {
    Write-Output "[build_thesis] Opening in default viewer (-Open)..."
    Invoke-Item $pdf
}

if ($scanFailed) {
    Write-Error "[build_thesis] Log scan FAILED (see above). Fix errors/undefined refs and rebuild."
    exit 1
}
if ($code -ne 0) {
    Write-Warning "[build_thesis] latexmk reported exit $code (PDF still produced; check log for warnings)."
    exit $code
}
Write-Output "[build_thesis] Done."
exit 0
